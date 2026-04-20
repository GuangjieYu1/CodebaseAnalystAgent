
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import os
from urllib import request, error
from tree_sitter_language_pack import get_language

from app.services.prompt_loader import build_system_prompt, load_and_render_prompt


class TreeSitterDependencyError(RuntimeError):
    pass


class JavaLanguageLoadError(RuntimeError):
    pass


LOW_VALUE_METHODS = {
    "trim",
    "toUpperCase",
    "toLowerCase",
    "isEmpty",
    "contains",
    "append",
    "toString",
    "equals",
    "compareTo",
    "add",
    "put",
    "get",
    "substring",
    "startsWith",
    "endsWith",
    "size",
    "length",
    "hashCode",
    "valueOf",
}

INTERFACE_HINTS = {"client", "feign", "rpc", "gateway", "api", "remote", "sdk"}
BRANCH_NODE_TYPES = {
    "if_statement": "if",
    "return_statement": "return",
    "throw_statement": "throw",
    "switch_expression": "switch",
    "switch_statement": "switch",
    "catch_clause": "catch",
}


def extract_method_execution_graph(
    project_root: str,
    file_path: str,
    method_name: str,
    tree_depth: int = 1,
    tool_registry_enhanced_json_path: str = "outputs/tool_registry_enhanced.json",
    output_json: str = "outputs/method_execution_graph.json",
    output_md: str = "outputs/method_execution_path.md",
    llm_provider: str = "heuristic",
    llm_model: str = "",
    deepseek_api_key: str = "",
) -> dict:
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")
    if tree_depth < 1:
        raise ValueError(f"tree_depth must be >= 1, got: {tree_depth}")

    target_file = root / file_path
    if not target_file.exists() or not target_file.is_file():
        raise ValueError(f"Invalid file path: {file_path}")

    java_source = target_file.read_text(encoding="utf-8", errors="ignore")
    source_bytes = java_source.encode("utf-8")
    tool_registry_enhanced = _load_tool_registry_enhanced(tool_registry_enhanced_json_path)

    parser = _build_java_parser()
    tree = parser.parse(source_bytes)
    syntax_root = tree.root_node

    package_name = _extract_package_name(syntax_root, source_bytes)
    class_node = _find_primary_class_node(syntax_root)
    if class_node is None:
        raise ValueError(f"No class declaration found in file: {file_path}")

    class_name = _extract_class_name(class_node, source_bytes)
    method_node = _find_method_node(class_node, method_name, source_bytes)
    if method_node is None:
        raise ValueError(f"Method not found: {method_name}")

    method_signature = _extract_method_signature(method_node, source_bytes)
    method_source = _node_text(method_node, source_bytes)
    method_start_line = method_node.start_point[0] + 1

    # Debug helpers for inspecting tree-sitter Java node structure.
    # Uncomment when investigating missing method_invocation extraction.
    # _debug_dump_method_named_nodes(method_node, source_bytes)
    # _debug_dump_method_invocations(method_node, source_bytes)
    # _debug_dump_nodes_by_type(
    #     method_node,
    #     source_bytes,
    #     {
    #         "method_invocation",
    #         "field_access",
    #         "identifier",
    #         "argument_list",
    #         "object_creation_expression",
    #     },
    # )

    raw_call_steps = _extract_call_steps_ts(method_node, source_bytes)
    call_steps = [
        _classify_call_step(
            step=step,
            current_class_name=class_name,
            tool_registry_enhanced=tool_registry_enhanced,
        )
        for step in raw_call_steps
    ]

    branches = _extract_branch_items_ts(method_node, source_bytes)
    stats = _build_stats(call_steps, branches)

    root_execution_node = _build_method_execution_tree_ts(
        class_node=class_node,
        source_bytes=source_bytes,
        current_file_path=file_path,
        current_class_name=class_name,
        current_package_name=package_name,
        method_name=method_name,
        method_signature=method_signature,
        method_node=method_node,
        method_start_line=method_start_line,
        tool_registry_enhanced=tool_registry_enhanced,
        remaining_depth=tree_depth,
        visited=set(),
    )

    main_flow_view = _build_main_flow_view(call_steps, branches)
    business_flow_view = _build_business_flow_view(
        main_flow_view=main_flow_view,
        class_name=class_name,
        method_name=method_name,
        method_signature=method_signature,
        method_source=method_source,
        branches=branches,
        llm_provider=llm_provider,
        llm_model=llm_model,
        deepseek_api_key=deepseek_api_key,
    )
    standard_input = _build_standard_input_example(
        method_signature=method_signature,
        method_name=method_name,
        method_source=method_source,
    )
    return_paths = _build_return_path_items(
        method_source=method_source,
        method_signature=method_signature,
        standard_input=standard_input,
    )

    requested_llm_provider = (llm_provider or os.getenv("METHOD_FLOW_LLM_PROVIDER", "heuristic")).strip().lower()
    requested_llm_model = (llm_model or os.getenv("METHOD_FLOW_LLM_MODEL", "")).strip()
    if requested_llm_provider and requested_llm_provider != "heuristic":
        try:
            business_steps, visible_steps = _enrich_execution_simulation_with_llm(
                class_name=class_name,
                package_name=package_name,
                file_path=file_path,
                method_name=method_name,
                method_signature=method_signature,
                method_source=method_source,
                business_steps=business_flow_view.get("business_steps", []),
                visible_call_steps=main_flow_view.get("visible_call_steps", []),
                branches=branches,
                standard_input=standard_input,
                return_paths=return_paths,
                provider=requested_llm_provider,
                model=requested_llm_model,
                deepseek_api_key=deepseek_api_key,
            )
            business_flow_view["business_steps"] = business_steps
            main_flow_view["visible_call_steps"] = visible_steps
        except Exception:
            pass

    state = {
        "project_root": str(root),
        "file_path": file_path,
        "package_name": package_name,
        "class_name": class_name,
        "method_name": method_name,
        "method_signature": method_signature,
        "tree_depth": tree_depth,
        "root_node": root_execution_node,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tool_registry_enhanced_json_path": tool_registry_enhanced_json_path,
        "method_source": method_source,
        "standard_input": standard_input,
        "return_paths": return_paths,
        "call_steps": call_steps,
        "branches": branches,
        "stats": stats,
        "tree_stats": {
            "node_count": _count_tree_nodes(root_execution_node),
        },
        "main_flow_view": main_flow_view,
        "business_flow_view": business_flow_view,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "output_json": output_json,
        "output_md": output_md,
    }
    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_text = _render_method_execution_markdown(state)
    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(md_text, encoding="utf-8")

    return state


# =========================
# tree-sitter setup
# =========================


def _build_java_parser():
    try:
        from tree_sitter import Parser
    except ImportError as e:
        raise TreeSitterDependencyError(
            "Missing dependency: tree-sitter. Install with `pip install tree-sitter tree-sitter-languages` "
            "or `pip install tree-sitter tree-sitter-language-pack`."
        ) from e

    language = _load_java_language()
    try:
        return Parser(language)
    except TypeError:
        parser = Parser()
        parser.set_language(language)
        return parser



def _load_java_language():
    try:
        from tree_sitter_language_pack import get_language
        return get_language("java")
    except ImportError:
        pass
    except Exception as e:
        raise JavaLanguageLoadError(f"Failed to load Java language from tree-sitter-language-pack: {e}") from e

    try:
        from tree_sitter_languages import get_language
        return get_language("java")
    except ImportError:
        pass
    except Exception as e:
        raise JavaLanguageLoadError(f"Failed to load Java language from tree-sitter-languages: {e}") from e

    raise TreeSitterDependencyError(
        "No Java grammar loader found. Install one of: `pip install tree-sitter-language-pack` "
        "or `pip install tree-sitter-languages`."
    )


# =========================
# shared helpers
# =========================


def _load_tool_registry_enhanced(tool_registry_enhanced_json_path: str) -> dict:
    path = Path(tool_registry_enhanced_json_path)
    if not path.exists() or not path.is_file():
        return {"tool_classes": []}
    return json.loads(path.read_text(encoding="utf-8"))



def _node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")



def _named_children(node):
    return [child for child in node.children if child.is_named]



def _walk_named_nodes(node):
    yield node
    for child in getattr(node, "named_children", []):
        yield from _walk_named_nodes(child)



def _extract_identifier_text(node, source_bytes: bytes) -> str:
    if node is None:
        return ""
    return _node_text(node, source_bytes).strip()


def _debug_dump_method_named_nodes(method_node, source_bytes: bytes) -> None:
    print("\n=== DEBUG: METHOD NAMED NODES START ===")
    for node in _walk_named_nodes(method_node):
        text = _node_text(node, source_bytes).strip().replace("\n", "\\n")
        if len(text) > 180:
            text = text[:180] + "..."
        print(
            f"type={node.type:<28} "
            f"range=({node.start_point[0] + 1},{node.start_point[1]})-({node.end_point[0] + 1},{node.end_point[1]}) "
            f"text={text}"
        )
    print("=== DEBUG: METHOD NAMED NODES END ===\n")



def _debug_dump_method_invocations(method_node, source_bytes: bytes) -> None:
    print("\n=== DEBUG: METHOD INVOCATIONS START ===")
    found = 0

    for node in _walk_named_nodes(method_node):
        if node.type != "method_invocation":
            continue

        found += 1
        print("\n--- invocation ---")
        print(f"text: {_node_text(node, source_bytes).strip()}")
        print(f"start_line: {node.start_point[0] + 1}")
        print(f"child_by_field_name('name'): {_safe_debug_field_text(node, 'name', source_bytes)}")
        print(f"child_by_field_name('object'): {_safe_debug_field_text(node, 'object', source_bytes)}")
        print(f"child_count: {len(node.children)}")

        print("children:")
        for i, child in enumerate(node.children):
            child_text = _node_text(child, source_bytes).strip().replace("\n", "\\n")
            if len(child_text) > 120:
                child_text = child_text[:120] + "..."
            try:
                field_name = node.field_name_for_child(i)
            except Exception:
                field_name = None

            print(
                f"  - idx={i:<2} "
                f"type={child.type:<24} "
                f"named={str(child.is_named):<5} "
                f"field={field_name!s:<12} "
                f"text={child_text}"
            )

    if found == 0:
        print("No method_invocation nodes found.")

    print("=== DEBUG: METHOD INVOCATIONS END ===\n")



def _debug_dump_nodes_by_type(method_node, source_bytes: bytes, target_types: set[str]) -> None:
    print("\n=== DEBUG: TARGET NODE TYPES START ===")
    found = 0
    for node in _walk_named_nodes(method_node):
        if node.type not in target_types:
            continue
        found += 1
        text = _node_text(node, source_bytes).strip().replace("\n", "\\n")
        if len(text) > 180:
            text = text[:180] + "..."
        print(
            f"type={node.type:<28} "
            f"line={node.start_point[0] + 1:<4} "
            f"text={text}"
        )
    if found == 0:
        print("No matching nodes found.")
    print("=== DEBUG: TARGET NODE TYPES END ===\n")



def _safe_debug_field_text(node, field_name: str, source_bytes: bytes) -> str:
    field_node = node.child_by_field_name(field_name)
    if field_node is None:
        return "<None>"
    text = _node_text(field_node, source_bytes).strip().replace("\n", "\\n")
    if len(text) > 120:
        text = text[:120] + "..."
    return text


# =========================
# package / class / method lookup
# =========================


def _extract_package_name(root_node, source_bytes: bytes) -> str:
    for child in _named_children(root_node):
        if child.type == "package_declaration":
            for sub in child.children:
                if sub.type in {"scoped_identifier", "identifier"}:
                    return _node_text(sub, source_bytes).strip()
    return ""



def _find_primary_class_node(root_node):
    for child in _walk_named_nodes(root_node):
        if child.type == "class_declaration":
            return child
    return None



def _extract_class_name(class_node, source_bytes: bytes) -> str:
    name_node = class_node.child_by_field_name("name")
    return _extract_identifier_text(name_node, source_bytes)



def _find_method_node(class_node, method_name: str, source_bytes: bytes):
    for node in _walk_named_nodes(class_node):
        if node.type != "method_declaration":
            continue
        name_node = node.child_by_field_name("name")
        if _extract_identifier_text(name_node, source_bytes) == method_name:
            return node
    return None



def _extract_method_signature(method_node, source_bytes: bytes) -> str:
    body_node = method_node.child_by_field_name("body")
    if body_node is None:
        return _node_text(method_node, source_bytes).strip()
    return source_bytes[method_node.start_byte:body_node.start_byte].decode("utf-8", errors="ignore").strip()


# =========================
# call extraction
# =========================


def _extract_call_steps_ts(method_node, source_bytes: bytes) -> list[dict]:
    body_node = method_node.child_by_field_name("body")
    if body_node is None:
        return []

    call_steps: list[dict] = []
    step_index = 1

    for node in _walk_named_nodes(body_node):
        if node.type != "method_invocation":
            continue

        method_name = _extract_method_invocation_name(node, source_bytes)
        if not method_name:
            continue

        qualifier = _extract_method_invocation_qualifier(node, source_bytes)
        call_steps.append({
            "step_index": step_index,
            "call_text": _node_text(node, source_bytes).strip(),
            "callee_method_name": method_name,
            "raw_prefix": qualifier,
            "source_line_hint": node.start_point[0] + 1,
        })
        step_index += 1

    return _deduplicate_call_steps(call_steps)


def _extract_method_invocation_name(invocation_node, source_bytes: bytes) -> str:
    name_node = invocation_node.child_by_field_name("name")
    if name_node is not None:
        return _extract_identifier_text(name_node, source_bytes)

    identifiers = [child for child in invocation_node.children if child.type == "identifier"]
    if identifiers:
        return _extract_identifier_text(identifiers[-1], source_bytes)
    return ""



def _extract_method_invocation_qualifier(invocation_node, source_bytes: bytes) -> str:
    object_node = invocation_node.child_by_field_name("object")
    if object_node is not None:
        return _node_text(object_node, source_bytes).strip()
    return ""



def _deduplicate_call_steps(call_steps: list[dict]) -> list[dict]:
    seen = set()
    deduped = []

    for step in call_steps:
        key = (
            step.get("source_line_hint"),
            step.get("call_text"),
            step.get("callee_method_name"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(step)

    for idx, step in enumerate(deduped, start=1):
        step["step_index"] = idx

    return deduped


# =========================
# branch extraction
# =========================


def _extract_branch_items_ts(method_node, source_bytes: bytes) -> list[dict]:
    body_node = method_node.child_by_field_name("body")
    if body_node is None:
        return []

    branches = []
    branch_index = 1

    for node in _walk_named_nodes(body_node):
        if node.type not in BRANCH_NODE_TYPES:
            continue

        branches.append({
            "branch_index": branch_index,
            "branch_type": BRANCH_NODE_TYPES[node.type],
            "condition_text": _extract_branch_condition_text(node, source_bytes),
            "source_line_hint": node.start_point[0] + 1,
        })
        branch_index += 1

    return branches



def _extract_branch_condition_text(node, source_bytes: bytes) -> str:
    if node.type == "if_statement":
        condition = node.child_by_field_name("condition")
        return _node_text(condition, source_bytes).strip() if condition else _node_text(node, source_bytes).strip()

    if node.type in {"switch_expression", "switch_statement"}:
        condition = node.child_by_field_name("condition")
        return _node_text(condition, source_bytes).strip() if condition else _node_text(node, source_bytes).strip()

    if node.type == "catch_clause":
        parameter = node.child_by_field_name("parameter")
        return _node_text(parameter, source_bytes).strip() if parameter else _node_text(node, source_bytes).strip()

    return _node_text(node, source_bytes).strip()


# =========================
# call classification
# =========================


def _classify_call_step(
    step: dict,
    current_class_name: str,
    tool_registry_enhanced: dict,
) -> dict:
    prefix = step.get("raw_prefix", "")
    method_name = step.get("callee_method_name", "")

    LIBRARY_VALUE_METHODS = {
        "compareTo",
        "equals",
        "contains",
        "isEmpty",
        "add",
        "append",
        "toString",
        "subtract",
        "trim",
        "toUpperCase",
        "toLowerCase",
    }

    LIBRARY_VALUE_PREFIXES = {
        "amount",
        "discount",
        "payableAmount",
        "customerName",
        "orderNo",
        "status",
        "tags",
        "issues",
        "snapshot",
        "normalizedTag",
        "rawCustomerName",
        "rawOrderNo",
        "rawStatus",
        "tag",
    }

    tool_ref = _find_tool_method_ref(tool_registry_enhanced, prefix, method_name)
    if tool_ref:
        return {
            "step_index": step["step_index"],
            "call_text": step["call_text"],
            "callee_method_name": method_name,
            "callee_class_name": tool_ref["class_name"],
            "call_type": "tool_method",
            "source_line_hint": step["source_line_hint"],
            "tool_method_ref": {
                "class_name": tool_ref["class_name"],
                "method_name": tool_ref["method_name"],
            },
            "interface_ref": None,
        }

    if _looks_like_external_interface(prefix):
        return {
            "step_index": step["step_index"],
            "call_text": step["call_text"],
            "callee_method_name": method_name,
            "callee_class_name": prefix or "",
            "call_type": "external_interface_call",
            "source_line_hint": step["source_line_hint"],
            "tool_method_ref": None,
            "interface_ref": {
                "interface_name": prefix or "",
                "is_cross_boundary": True,
            },
        }

    if prefix and (
        method_name in LIBRARY_VALUE_METHODS
        or prefix.split(".")[0] in LIBRARY_VALUE_PREFIXES
    ):
        return {
            "step_index": step["step_index"],
            "call_text": step["call_text"],
            "callee_method_name": method_name,
            "callee_class_name": prefix,
            "call_type": "library_value_method",
            "source_line_hint": step["source_line_hint"],
            "tool_method_ref": None,
            "interface_ref": None,
        }

    if prefix:
        if prefix[:1].isupper():
            return {
                "step_index": step["step_index"],
                "call_text": step["call_text"],
                "callee_method_name": method_name,
                "callee_class_name": prefix,
                "call_type": "external_static_method",
                "source_line_hint": step["source_line_hint"],
                "tool_method_ref": None,
                "interface_ref": None,
            }

        return {
            "step_index": step["step_index"],
            "call_text": step["call_text"],
            "callee_method_name": method_name,
            "callee_class_name": prefix,
            "call_type": "external_instance_method",
            "source_line_hint": step["source_line_hint"],
            "tool_method_ref": None,
            "interface_ref": None,
        }

    return {
        "step_index": step["step_index"],
        "call_text": step["call_text"],
        "callee_method_name": method_name,
        "callee_class_name": current_class_name,
        "call_type": "internal_method",
        "source_line_hint": step["source_line_hint"],
        "tool_method_ref": None,
        "interface_ref": None,
    }

def _find_tool_method_ref(tool_registry_enhanced: dict, class_name: str, method_name: str) -> dict | None:
    if not class_name:
        return None

    simple_class_name = class_name.split(".")[-1]
    for tool_class in tool_registry_enhanced.get("tool_classes", []):
        if tool_class.get("class_name") != simple_class_name:
            continue
        for method in tool_class.get("methods", []):
            if method.get("method_name") == method_name:
                return {
                    "class_name": tool_class.get("class_name", ""),
                    "method_name": method.get("method_name", ""),
                }
    return None



def _looks_like_external_interface(prefix: str) -> bool:
    lowered = prefix.lower()
    return bool(prefix) and any(marker in lowered for marker in INTERFACE_HINTS)


# =========================
# recursive tree building
# =========================


def _build_method_execution_tree_ts(
    class_node,
    source_bytes: bytes,
    current_file_path: str,
    current_class_name: str,
    current_package_name: str,
    method_name: str,
    method_signature: str,
    method_node,
    method_start_line: int,
    tool_registry_enhanced: dict,
    remaining_depth: int,
    visited: set[tuple[str, str]],
) -> dict:
    visit_key = (current_file_path, method_name)
    if visit_key in visited:
        return {
            "file_path": current_file_path,
            "class_name": current_class_name,
            "package_name": current_package_name,
            "method_name": method_name,
            "method_signature": method_signature,
            "source_line_hint": method_start_line,
            "call_type": "internal_method",
            "children": [],
            "truncated": False,
            "cycle_detected": True,
        }

    local_visited = set(visited)
    local_visited.add(visit_key)

    raw_call_steps = _extract_call_steps_ts(method_node, source_bytes)
    enriched_steps = [
        _classify_call_step(
            step=step,
            current_class_name=current_class_name,
            tool_registry_enhanced=tool_registry_enhanced,
        )
        for step in raw_call_steps
    ]

    node = {
        "file_path": current_file_path,
        "class_name": current_class_name,
        "package_name": current_package_name,
        "method_name": method_name,
        "method_signature": method_signature,
        "source_line_hint": method_start_line,
        "call_type": "internal_method",
        "children": [],
        "truncated": remaining_depth <= 1,
        "cycle_detected": False,
    }

    if remaining_depth <= 1:
        node["children"] = [
            {
                **step,
                "children": [],
                "truncated": True,
                "cycle_detected": False,
            }
            for step in enriched_steps
        ]
        return node

    for step in enriched_steps:
        child = {
            **step,
            "children": [],
            "truncated": False,
            "cycle_detected": False,
        }

        if step["call_type"] == "internal_method":
            child_method_node = _find_method_node(class_node, step["callee_method_name"], source_bytes)
            if child_method_node is not None:
                child_signature = _extract_method_signature(child_method_node, source_bytes)
                child_start_line = child_method_node.start_point[0] + 1
                subtree = _build_method_execution_tree_ts(
                    class_node=class_node,
                    source_bytes=source_bytes,
                    current_file_path=current_file_path,
                    current_class_name=current_class_name,
                    current_package_name=current_package_name,
                    method_name=step["callee_method_name"],
                    method_signature=child_signature,
                    method_node=child_method_node,
                    method_start_line=child_start_line,
                    tool_registry_enhanced=tool_registry_enhanced,
                    remaining_depth=remaining_depth - 1,
                    visited=local_visited,
                )
                child["children"] = subtree.get("children", [])
                child["truncated"] = subtree.get("truncated", False)
                child["cycle_detected"] = subtree.get("cycle_detected", False)

        node["children"].append(child)

    return node


# =========================
# stats
# =========================


def _build_stats(call_steps: list[dict], branches: list[dict]) -> dict:
    stats = {
        "call_step_count": len(call_steps),
        "branch_count": len(branches),
        "internal_method_count": 0,
        "tool_method_count": 0,
        "library_value_method_count": 0,
        "external_interface_call_count": 0,
        "external_static_method_count": 0,
        "external_instance_method_count": 0,
        "unknown_call_count": 0,
    }

    for step in call_steps:
        call_type = step.get("call_type", "unknown_call")
        if call_type == "internal_method":
            stats["internal_method_count"] += 1
        elif call_type == "tool_method":
            stats["tool_method_count"] += 1
        elif call_type == "library_value_method":
            stats["library_value_method_count"] += 1
        elif call_type == "external_interface_call":
            stats["external_interface_call_count"] += 1
        elif call_type == "external_static_method":
            stats["external_static_method_count"] += 1
        elif call_type == "external_instance_method":
            stats["external_instance_method_count"] += 1
        else:
            stats["unknown_call_count"] += 1

    return stats
def _count_tree_nodes(node: dict) -> int:
    count = 1
    for child in node.get("children", []):
        count += _count_tree_nodes(child)
    return count

def _build_main_flow_view(call_steps: list[dict], branches: list[dict]) -> dict:
    visible_steps = []
    hidden_steps = []

    visible_index = 1
    for step in call_steps:
        step_copy = dict(step)
        step_copy["llm_summary"] = ""
        step_copy["llm_simulated_input"] = ""
        step_copy["llm_simulated_output"] = ""

        if _should_hide_in_main_flow(step_copy):
            hidden_steps.append(step_copy)
        else:
            step_copy["main_flow_index"] = visible_index
            visible_steps.append(step_copy)
            visible_index += 1

    return {
        "visible_call_steps": visible_steps,
        "hidden_call_steps": hidden_steps,
        "visible_call_step_count": len(visible_steps),
        "hidden_call_step_count": len(hidden_steps),
        "branch_count": len(branches),
    }

def _should_hide_in_main_flow(step: dict) -> bool:
    method_name = step.get("callee_method_name", "")
    call_type = step.get("call_type", "")
    prefix = (step.get("callee_class_name") or "").split(".")[0]

    if method_name in MAIN_FLOW_KEEP_METHODS:
        return False

    if call_type == "library_value_method" and method_name in MAIN_FLOW_HIDE_METHODS:
        return True

    if call_type == "library_value_method" and prefix == "snapshot":
        return True

    return False



def _build_business_flow_view(
    main_flow_view: dict,
    class_name: str,
    method_name: str,
    method_signature: str,
    method_source: str,
    branches: list[dict],
    llm_provider: str,
    llm_model: str,
    deepseek_api_key: str,
) -> dict:
    steps = [dict(step) for step in main_flow_view.get("visible_call_steps", [])]
    if not steps:
        return {
            "business_steps": [],
            "business_step_count": 0,
            "generation_mode": "empty",
            "final_summary": f"方法 {method_name} 当前未提取到可用的主流程步骤。",
        }

    llm_provider = (llm_provider or os.getenv("METHOD_FLOW_LLM_PROVIDER", "heuristic")).strip().lower()
    llm_model = (llm_model or os.getenv("METHOD_FLOW_LLM_MODEL", "")).strip()

    if llm_provider and llm_provider != "heuristic":
        try:
            return _build_business_flow_view_with_llm(
                steps=steps,
                branches=branches,
                class_name=class_name,
                method_name=method_name,
                method_signature=method_signature,
                method_source=method_source,
                provider=llm_provider,
                model=llm_model,
                deepseek_api_key=deepseek_api_key,
            )
        except Exception as e:
            return _build_business_flow_view_heuristic(
                steps,
                fallback_reason=str(e),
                method_name=method_name,
            )

    return _build_business_flow_view_heuristic(
        steps,
        fallback_reason="llm_disabled",
        method_name=method_name,
    )


def _build_business_flow_view_with_llm(
    steps: list[dict],
    branches: list[dict],
    class_name: str,
    method_name: str,
    method_signature: str,
    method_source: str,
    provider: str,
    model: str,
    deepseek_api_key: str,
) -> dict:
    prompt = _build_business_flow_llm_prompt(
        steps=steps,
        branches=branches,
        class_name=class_name,
        method_name=method_name,
        method_signature=method_signature,
        method_source=method_source,
    )

    raw_response = _call_business_flow_llm(
        provider=provider,
        model=model,
        prompt=prompt,
        deepseek_api_key=deepseek_api_key,
    )

    parsed = _safe_parse_json_from_text(raw_response)
    raw_business_steps = parsed.get("business_steps", []) if isinstance(parsed, dict) else []

    indexed_steps = {step.get("main_flow_index"): step for step in steps}
    business_steps = []

    for idx, item in enumerate(raw_business_steps, start=1):
        call_step_indices = item.get("call_step_indices", []) if isinstance(item, dict) else []
        matched_steps = [indexed_steps[i] for i in call_step_indices if i in indexed_steps]
        if not matched_steps:
            continue

        title = _infer_business_step_title(matched_steps)
        step_summary = _infer_business_step_summary(matched_steps, title)
        business_steps.append({
            "step_index": idx,
            "title": title,
            "llm_summary": "",
            "llm_simulated_input": "",
            "llm_simulated_output": "",
            "step_summary": step_summary,
            "summary": step_summary,
            "step_input": _infer_business_step_input(matched_steps, title),
            "step_output": _infer_business_step_output(matched_steps, title),
            "call_steps": matched_steps,
            "call_step_count": len(matched_steps),
            "line_range": {
                "start": min(step.get("source_line_hint", -1) for step in matched_steps),
                "end": max(step.get("source_line_hint", -1) for step in matched_steps),
            },
            "method_names": sorted({
                step.get("callee_method_name", "")
                for step in matched_steps
                if step.get("callee_method_name")
            }),
            "call_step_indices": call_step_indices,
        })

    return {
        "business_steps": business_steps,
        "business_step_count": len(business_steps),
        "generation_mode": "llm",
        "llm_provider": provider,
        "llm_model": model,
        "final_summary": _build_final_execution_summary(business_steps, method_name),
    }


def _build_business_flow_view_heuristic(steps: list[dict], fallback_reason: str, method_name: str) -> dict:
    clusters = _cluster_main_flow_steps(steps)
    business_steps = []

    for idx, cluster in enumerate(clusters, start=1):
        title = _infer_business_step_title(cluster)
        step_summary = _infer_business_step_summary(cluster, title)
        business_steps.append({
            "step_index": idx,
            "title": title,
            "llm_summary": "",
            "llm_simulated_input": "",
            "llm_simulated_output": "",
            "step_summary": step_summary,
            "summary": step_summary,
            "step_input": _infer_business_step_input(cluster, title),
            "step_output": _infer_business_step_output(cluster, title),
            "call_steps": cluster,
            "call_step_count": len(cluster),
            "line_range": {
                "start": min(step.get("source_line_hint", -1) for step in cluster),
                "end": max(step.get("source_line_hint", -1) for step in cluster),
            },
            "method_names": sorted({
                step.get("callee_method_name", "")
                for step in cluster
                if step.get("callee_method_name")
            }),
            "call_step_indices": [step.get("main_flow_index") for step in cluster if step.get("main_flow_index")],
        })

    return {
        "business_steps": business_steps,
        "business_step_count": len(business_steps),
        "generation_mode": "heuristic",
        "fallback_reason": fallback_reason,
        "final_summary": _build_final_execution_summary(business_steps, method_name),
    }


def _enrich_execution_simulation_with_llm(
    class_name: str,
    package_name: str,
    file_path: str,
    method_name: str,
    method_signature: str,
    method_source: str,
    business_steps: list[dict],
    visible_call_steps: list[dict],
    branches: list[dict],
    standard_input: dict,
    return_paths: list[dict],
    provider: str,
    model: str,
    deepseek_api_key: str,
) -> tuple[list[dict], list[dict]]:
    if not business_steps and not visible_call_steps:
        return business_steps, visible_call_steps

    system_prompt = build_system_prompt(
        "shared/system_base.txt",
        "shared/output_json_rules.txt",
        "method_execution/enrich_graph_execution_system.txt",
    )
    user_prompt = load_and_render_prompt(
        "method_execution/enrich_graph_execution_user.txt",
        {
            "class_name": class_name,
            "package_name": package_name,
            "file_path": file_path,
            "method_name": method_name,
            "method_signature": method_signature,
            "method_source": method_source,
            "standard_input_json": json.dumps(standard_input, ensure_ascii=False, indent=2),
            "return_paths_json": json.dumps(return_paths, ensure_ascii=False, indent=2),
            "branches_json": json.dumps(branches, ensure_ascii=False, indent=2),
            "business_steps_json": json.dumps(business_steps, ensure_ascii=False, indent=2),
            "visible_call_steps_json": json.dumps(visible_call_steps, ensure_ascii=False, indent=2),
        },
    )
    raw_response = _call_business_flow_llm(
        provider=provider,
        model=model,
        prompt=user_prompt,
        deepseek_api_key=deepseek_api_key,
        system_prompt=system_prompt,
    )
    parsed = _safe_parse_json_from_text(raw_response)

    business_map = {
        item.get("step_index"): item
        for item in parsed.get("business_steps", [])
        if isinstance(item, dict) and item.get("step_index") is not None
    }
    visible_map = {
        item.get("main_flow_index"): item
        for item in parsed.get("visible_call_steps", [])
        if isinstance(item, dict) and item.get("main_flow_index") is not None
    }

    enriched_business_steps = [
        _merge_llm_simulation_fields(step, business_map.get(step.get("step_index")))
        for step in business_steps
    ]
    enriched_visible_call_steps = [
        _merge_llm_simulation_fields(step, visible_map.get(step.get("main_flow_index")))
        for step in visible_call_steps
    ]
    return enriched_business_steps, enriched_visible_call_steps


def _merge_llm_simulation_fields(step: dict, llm_item: dict | None) -> dict:
    llm_item = llm_item or {}
    merged = dict(step)
    merged["llm_summary"] = llm_item.get("llm_summary", "") or merged.get("llm_summary", "")
    merged["llm_simulated_input"] = llm_item.get("llm_simulated_input", "") or merged.get("llm_simulated_input", "")
    merged["llm_simulated_output"] = llm_item.get("llm_simulated_output", "") or merged.get("llm_simulated_output", "")
    return merged


def _cluster_main_flow_steps(steps: list[dict]) -> list[list[dict]]:
    if not steps:
        return []

    sorted_steps = sorted(steps, key=lambda s: (s.get("source_line_hint", -1), s.get("main_flow_index", 0)))
    clusters: list[list[dict]] = []
    current_cluster: list[dict] = [sorted_steps[0]]

    for step in sorted_steps[1:]:
        previous = current_cluster[-1]
        previous_line = previous.get("source_line_hint", -1)
        current_line = step.get("source_line_hint", -1)

        if _should_split_business_cluster(previous, step, previous_line, current_line):
            clusters.append(current_cluster)
            current_cluster = [step]
        else:
            current_cluster.append(step)

    clusters.append(current_cluster)
    return clusters


def _should_split_business_cluster(previous: dict, current: dict, previous_line: int, current_line: int) -> bool:
    line_gap = current_line - previous_line
    if line_gap >= 5:
        return True

    previous_bucket = _infer_business_bucket(previous)
    current_bucket = _infer_business_bucket(current)
    if previous_bucket != current_bucket and line_gap >= 2:
        return True

    previous_prefix = (previous.get("callee_class_name") or "").split(".")[0]
    current_prefix = (current.get("callee_class_name") or "").split(".")[0]
    if previous_prefix == "snapshot" and current_prefix != "snapshot":
        return True
    if previous_prefix != "snapshot" and current_prefix == "snapshot" and line_gap >= 1:
        return True

    return False


def _infer_business_bucket(step: dict) -> str:
    method_name = step.get("callee_method_name", "")
    prefix = (step.get("callee_class_name") or "").split(".")[0]
    call_text = step.get("call_text", "")

    if prefix == "snapshot" or method_name in {"append", "toString"}:
        return "rendering"

    if method_name in {"trim", "toUpperCase", "toLowerCase", "substring", "startsWith", "endsWith"}:
        return "normalization"

    if method_name in {"contains", "add"} and prefix in {"tags", "issues"}:
        return "collection_handling"

    if method_name in {"isEmpty", "equals", "compareTo"}:
        return "validation_and_decision"

    if method_name in {"subtract", "add", "multiply", "divide"}:
        return "calculation"

    if "new " in call_text:
        return "construction"

    if method_name:
        return "general_logic"

    return "other"


def _infer_business_step_title(cluster: list[dict]) -> str:
    buckets = [_infer_business_bucket(step) for step in cluster]
    bucket_counts: dict[str, int] = {}
    for bucket in buckets:
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    dominant_bucket = max(bucket_counts.items(), key=lambda item: item[1])[0]
    method_names = {step.get("callee_method_name", "") for step in cluster}
    prefixes = {(step.get("callee_class_name") or "").split(".")[0] for step in cluster}
    call_text_joined = " ".join(step.get("call_text", "") for step in cluster).lower()

    if method_names & {"sort", "naturalOrder"}:
        return "结果排序与返回"

    if (
        method_names & {"removeIf"}
        or "count > 1" in call_text_joined
        or "count ＞ 1" in call_text_joined
        or (method_names == {"get"} and prefixes & {"frequencyMap"})
    ):
        return "重复项筛选"

    if prefixes & {"frequencyMap"} or method_names & {"getOrDefault", "put"}:
        return "频次统计"

    if dominant_bucket == "normalization":
        return "输入标准化处理"

    if dominant_bucket == "collection_handling":
        if "tags" in prefixes:
            return "集合内容校验与去重"
        if "issues" in prefixes:
            return "问题项收集"
        return "集合操作处理"

    if dominant_bucket == "validation_and_decision":
        if "compareTo" in method_names and "subtract" in method_names:
            return "金额计算与阈值判断"
        if "equals" in method_names or "isEmpty" in method_names:
            return "条件校验与分支判断"
        return "规则判断"

    if dominant_bucket == "calculation":
        return "数值计算处理"

    if dominant_bucket == "rendering":
        return "结果构建与输出"

    if dominant_bucket == "construction":
        return "对象初始化"

    return "业务逻辑处理"


def _infer_business_step_summary(cluster: list[dict], title: str) -> str:
    method_names = [step.get("callee_method_name", "") for step in cluster if step.get("callee_method_name")]
    unique_methods = sorted(set(method_names))
    line_start = min(step.get("source_line_hint", -1) for step in cluster)
    line_end = max(step.get("source_line_hint", -1) for step in cluster)

    if title == "条件校验与分支判断":
        return "该步骤检查输入或当前候选值是否有效，并决定是提前返回、跳过当前项，还是继续进入后续处理。"

    if title == "输入标准化处理":
        return "该步骤对原始输入做清洗和规范化处理，例如裁剪前后缀、统一格式，并过滤掉无效内容。"

    if title == "频次统计":
        return "该步骤遍历规范化后的元素并更新 frequencyMap，记录每个候选值的出现次数。"

    if title == "重复项筛选":
        return "该步骤根据频次统计结果筛选真正重复出现的元素，只保留满足条件的候选项。"

    if title == "结果排序与返回":
        return "该步骤对最终结果进行排序，并输出当前方法的最终返回值。"

    if title == "结果构建与输出":
        return "该步骤把前面累计得到的字段和状态组装成最终结果，并准备返回给调用方。"

    if unique_methods:
        method_part = "、".join(unique_methods[:5])
        return f"该步骤主要围绕 {method_part} 等调用展开，集中处理 {title}，代码范围约在第 {line_start} 到 {line_end} 行。"

    return f"该步骤集中处理 {title}，代码范围约在第 {line_start} 到 {line_end} 行。"


def _infer_business_step_input(cluster: list[dict], title: str) -> str:
    title_lower = title.lower()
    method_names = {step.get("callee_method_name", "") for step in cluster if step.get("callee_method_name")}
    prefixes = {
        (step.get("callee_class_name") or "").split(".")[0]
        for step in cluster
        if step.get("callee_class_name")
    }
    call_texts = [step.get("call_text", "") for step in cluster if step.get("call_text")]
    joined = " ".join(call_texts).lower()

    if "标准化" in title or "规范化" in title or "normal" in title_lower:
        return "原始输入集合或原始字符串，以及当前待清洗的候选值。"

    if title == "频次统计":
        return "已经完成规范化的元素序列，以及用于累计计数的 frequencyMap 中间状态。"

    if title == "重复项筛选":
        return "频次统计结果、候选元素列表，以及当前用于过滤重复项的判定条件。"

    if title == "结果排序与返回":
        return "已经筛选完成的结果集合，以及排序规则或比较器。"

    if "条件校验" in title or "规则判断" in title or "validation" in title_lower:
        return "当前方法参数、已生成的中间变量，以及用于判断是否继续执行的条件状态。"

    if "问题项收集" in title or "issues" in prefixes:
        return "前面校验阶段得到的异常标记、缺失字段信息或非法状态判断结果。"

    if "集合" in title or prefixes & {"tags", "issues", "frequencyMap", "seenOnce", "duplicates", "result"}:
        if "frequencymap" in joined:
            return "已经规范化的元素序列，以及用于累计出现次数的 frequencyMap 状态。"
        if "seenonce" in joined:
            return "已处理过的元素集合，以及当前遍历到的候选元素。"
        if "tags" in prefixes:
            return "当前标签集合、候选标签值，以及已有去重结果。"
        if "issues" in prefixes:
            return "当前问题项集合，以及新命中的问题标识。"
        return "当前步骤涉及的集合状态，以及本轮准备写入或比对的元素。"

    if "金额" in title or "数值计算" in title or method_names & {"subtract", "add", "multiply", "divide", "compareTo"}:
        return "金额、折扣、阈值等数值型中间状态，以及前置判断结果。"

    if "结果构建" in title or "输出" in title or "snapshot" in prefixes or "append" in method_names:
        return "前面步骤累计得到的核心字段、标志位和集合状态。"

    if "return" in joined:
        return "当前已收敛的中间结果，以及决定是否提前返回的条件。"

    return "上一步产生的中间状态，以及当前步骤所依赖的局部变量。"


def _infer_business_step_output(cluster: list[dict], title: str) -> str:
    title_lower = title.lower()
    method_names = {step.get("callee_method_name", "") for step in cluster if step.get("callee_method_name")}
    prefixes = {
        (step.get("callee_class_name") or "").split(".")[0]
        for step in cluster
        if step.get("callee_class_name")
    }
    call_texts = [step.get("call_text", "") for step in cluster if step.get("call_text")]
    joined = " ".join(call_texts).lower()

    if "标准化" in title or "规范化" in title or "normal" in title_lower:
        return "得到可继续参与后续处理的规范化结果，异常或无效内容会被清理或跳过。"

    if title == "频次统计":
        return "得到按元素聚合后的频次统计结果，可直接用于后续重复项筛选。"

    if title == "重复项筛选":
        return "得到只包含真正重复元素的候选结果集合。"

    if title == "结果排序与返回":
        return "得到排序后的最终结果，并完成当前方法的返回。"

    if "条件校验" in title or "规则判断" in title or "validation" in title_lower:
        return "产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。"

    if "问题项收集" in title or "issues" in prefixes:
        return "更新后的问题项集合，用于后续风险判断、兜底处理或最终输出。"

    if "集合" in title or prefixes & {"tags", "issues", "frequencyMap", "seenOnce", "duplicates", "result"}:
        if "frequencymap" in joined:
            return "得到按元素聚合后的频次统计结果，可直接用于重复项筛选。"
        if "seenonce" in joined:
            return "得到首轮出现记录或重复候选集合，为后续去重判断提供依据。"
        if "tags" in prefixes:
            return "得到去重后的标签集合或更新后的标签状态。"
        if "result" in prefixes or "duplicates" in prefixes:
            return "得到筛选后的目标结果集合，保留当前阶段真正需要返回的元素。"
        return "更新后的集合状态，可供下一步继续读写或筛选。"

    if "金额" in title or "数值计算" in title or method_names & {"subtract", "add", "multiply", "divide", "compareTo"}:
        return "得到新的金额结果、阈值判断结论或修正后的数值状态。"

    if "结果构建" in title or "输出" in title or "snapshot" in prefixes or "append" in method_names:
        return "得到可直接返回或接近最终返回形态的结果字符串、快照对象或汇总结果。"

    if "return" in joined:
        return "返回当前步骤收敛出的结果，并结束当前方法或结束当前分支。"

    return "形成当前阶段的中间结果，供后续步骤继续消费。"


def _build_final_execution_summary(business_steps: list[dict], method_name: str) -> str:
    if not business_steps:
        if method_name:
            return f"方法 {method_name} 当前未提取到可用的主流程步骤。"
        return "当前未提取到可用的主流程步骤。"

    display_name = method_name or "当前方法"
    parts = []
    for idx, step in enumerate(business_steps, start=1):
        title = step.get("title", f"步骤 {idx}")
        step_output = (step.get("step_output", "") or "").rstrip("。；;")
        lead = "先" if idx == 1 else "然后"
        if idx == len(business_steps):
            lead = "最后"
        if idx not in {1, len(business_steps)}:
            lead = "接着"
        sentence = f"{lead}处理“{title}”"
        if step_output:
            sentence += f"，{step_output}"
        parts.append(sentence)

    return f"方法 {display_name} 的主流程可以概括为：{'；'.join(parts)}。"


def _build_business_flow_llm_prompt(
    steps: list[dict],
    branches: list[dict],
    class_name: str,
    method_name: str,
    method_signature: str,
    method_source: str,
) -> str:
    payload = {
        "class_name": class_name,
        "method_name": method_name,
        "method_signature": method_signature,
        "visible_call_steps": steps,
        "branches": branches,
        "method_source": method_source,
    }

    return (
        "你是一个Java方法执行路径归并器。\n"
        "你的任务是基于给定的方法签名、源码、主流程调用步骤和分支信息，"
        "将这些调用步骤归并成 4 到 8 个更高层的业务步骤。\n"
        "要求：\n"
        "1. 只能基于输入内容归并，不要臆造不存在的步骤。\n"
        "2. 每个业务步骤必须引用 call_step_indices，使用 main_flow_index。\n"
        "3. 业务步骤顺序必须与代码执行顺序一致。\n"
        "4. 输出必须是 JSON 对象，格式为：\n"
        "{\n"
        "  \"business_steps\": [\n"
        "    {\n"
        "      \"title\": \"步骤标题\",\n"
        "      \"summary\": \"步骤摘要\",\n"
        "      \"call_step_indices\": [1,2,3]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "5. 不要输出 markdown，不要输出解释，不要输出代码块。\n\n"
        f"输入数据：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _call_business_flow_llm(
    provider: str,
    model: str,
    prompt: str,
    deepseek_api_key: str = "",
    system_prompt: str = "",
) -> str:
    provider = provider.strip().lower()

    if provider == "ollama":
        if not model:
            model = os.getenv("METHOD_FLOW_LLM_MODEL", "qwen3.5:9b")
        final_prompt = prompt
        if system_prompt.strip():
            final_prompt = f"{system_prompt.strip()}\n\n{prompt}"
        body = json.dumps({
            "model": model,
            "prompt": final_prompt,
            "stream": False,
        }).encode("utf-8")
        req = request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")

    if provider == "deepseek":
        api_key = (deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")).strip()
        if not api_key:
            raise RuntimeError("Missing DEEPSEEK_API_KEY for deepseek provider")
        if not model:
            model = os.getenv("METHOD_FLOW_LLM_MODEL", "deepseek-chat")
        body = json.dumps({
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "You are a precise JSON-only Java method business flow summarizer.",
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "stream": False,
            "response_format": {"type": "json_object"},
        }).encode("utf-8")
        req = request.Request(
            "https://api.deepseek.com/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                error_body = ""
            if error_body:
                raise RuntimeError(f"DeepSeek HTTP error: {e.code} {e.reason} | body: {error_body}") from e
            raise RuntimeError(f"DeepSeek HTTP error: {e.code} {e.reason}") from e

    raise RuntimeError(f"Unsupported METHOD_FLOW_LLM_PROVIDER: {provider}")


def _safe_parse_json_from_text(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Model did not return valid JSON. Raw response:\n{raw_text}")

    return json.loads(raw_text[start:end + 1])

def _has_llm_simulation_content(step: dict) -> bool:
    return any([
        step.get("llm_summary"),
        step.get("llm_simulated_input"),
        step.get("llm_simulated_output"),
    ])


def _render_method_execution_markdown(state: dict) -> str:
    business_flow_view = state.get("business_flow_view", {})
    business_steps = business_flow_view.get("business_steps", [])
    main_flow_view = state.get("main_flow_view", {})
    visible_steps = main_flow_view.get("visible_call_steps", [])
    hidden_steps = main_flow_view.get("hidden_call_steps", [])

    branch_mermaid = _render_execution_branch_mermaid(
        method_name=state.get("method_name", ""),
        branches=state.get("branches", []),
        business_steps=business_steps,
    )

    business_mermaid = _render_business_summary_mermaid(
        method_name=state.get("method_name", ""),
        business_steps=business_steps,
        branches=state.get("branches", []),
        generation_mode=business_flow_view.get("generation_mode", ""),
    )

    standard_input = state.get("standard_input") or _build_standard_input_example(
        method_signature=state.get("method_signature", ""),
        method_name=state.get("method_name", ""),
        method_source=state.get("method_source", ""),
    )
    return_paths = state.get("return_paths") or _build_return_path_items(
        method_source=state.get("method_source", ""),
        method_signature=state.get("method_signature", ""),
        standard_input=standard_input,
    )
    expected_output_text = _estimate_expected_output_for_standard_input(
        method_name=state.get("method_name", ""),
        method_signature=state.get("method_signature", ""),
        method_source=state.get("method_source", ""),
        standard_input=standard_input,
        business_steps=business_steps,
    )
    final_summary = business_flow_view.get("final_summary") or _build_final_execution_summary(
        business_steps,
        state.get("method_name", ""),
    )

    lines = []
    lines.append(f"# 方法执行路径说明：{state.get('method_name', '')}")
    lines.append("")
    lines.append("## 1. 基本信息")
    lines.append("")
    lines.append(f"- 类名：`{state.get('class_name', '')}`")
    lines.append(f"- 文件：`{state.get('file_path', '')}`")
    lines.append(f"- 方法签名：")
    lines.append("")
    lines.append("```java")
    lines.append(state.get("method_signature", ""))
    lines.append("```")
    lines.append("")

    lines.append("## 2. 标准输入模拟")
    lines.append("")
    for item in standard_input.get("inputs", []):
        lines.append(f"- `{item['name']}` ({item['type']}): `{item['value']}`")
    lines.append("")
    lines.append("### 预期输出")
    lines.append("")
    lines.append(f"- `{expected_output_text}`")
    lines.append("")

    lines.append("## 3. 方法整体总结")
    lines.append("")
    lines.append(final_summary)
    lines.append("")

    lines.append("## 4. 业务步骤模拟视图")
    lines.append("")
    if not business_steps:
        lines.append("- 未提取到业务步骤。")
        lines.append("")

    for step in business_steps:
        if business_flow_view.get("generation_mode") == "llm":
            lines.append(f"### <span style=\"color:#c62828;\">步骤 {step['step_index']}：{step['title']}</span>")
        else:
            lines.append(f"### 步骤 {step['step_index']}：{step['title']}")
        lines.append("")

        if _has_llm_simulation_content(step):
            lines.append("#### LLM 模拟结论")
            lines.append("")
            lines.append(f"- 精确总结：{step.get('llm_summary', '')}")
            lines.append(f"- 模拟输入：{step.get('llm_simulated_input', '')}")
            lines.append(f"- 模拟输出：{step.get('llm_simulated_output', '')}")
            lines.append("")

        lines.append("#### 程序推断 / 程序证据")
        lines.append("")
        line_range = step.get("line_range", {})
        lines.append(f"- 代码行范围：`{line_range.get('start', '?')} - {line_range.get('end', '?')}`")
        lines.append(f"- 命中调用数：`{step.get('call_step_count', 0)}`")
        lines.append(f"- 程序步骤总结：{step.get('step_summary') or step.get('summary', '')}")
        lines.append(f"- 程序步骤输入：{step.get('step_input', '')}")
        lines.append(f"- 程序步骤输出：{step.get('step_output', '')}")
        if step.get("call_steps"):
            lines.append("- 命中调用：")
            for call in step.get("call_steps", []):
                lines.append(
                    f"  - line=`{call.get('source_line_hint', '?')}` | "
                    f"`{call.get('call_text', '')}` | type=`{call.get('call_type', '')}`"
                )
        lines.append("")

    lines.append("## 5. 低层调用步骤详细视图")
    lines.append("")
    if not visible_steps:
        lines.append("- 未提取到主流程调用步骤。")
        lines.append("")

    for step in visible_steps:
        title = step.get("callee_method_name") or step.get("call_text", "")
        lines.append(f"### 调用 {step.get('main_flow_index', '?')}：{title}")
        lines.append("")

        if _has_llm_simulation_content(step):
            lines.append("#### LLM 模拟结论")
            lines.append("")
            lines.append(f"- 精确总结：{step.get('llm_summary', '')}")
            lines.append(f"- 模拟输入：{step.get('llm_simulated_input', '')}")
            lines.append(f"- 模拟输出：{step.get('llm_simulated_output', '')}")
            lines.append("")

        lines.append("#### 程序推断 / 程序证据")
        lines.append("")
        lines.append(f"- 调用文本：`{step.get('call_text', '')}`")
        lines.append(f"- 源码行号：`{step.get('source_line_hint', '?')}`")
        lines.append(f"- 被调类：`{step.get('callee_class_name', '')}`")
        lines.append(f"- 调用类型：`{step.get('call_type', '')}`")
        tool_ref = step.get("tool_method_ref")
        if tool_ref:
            lines.append(f"- Tool 引用：`{tool_ref.get('class_name', '')}.{tool_ref.get('method_name', '')}`")
        interface_ref = step.get("interface_ref")
        if interface_ref:
            lines.append(f"- 接口风险提示：{interface_ref.get('risk_hint', '')}")
        lines.append("")

    lines.append("## 6. 返回路径摘要")
    lines.append("")
    if return_paths:
        for item in return_paths:
            lines.append(
                f"- line=`{item.get('line_no', '?')}` | "
                f"`return {item.get('expression', '')}` -> {item.get('description', '')}"
            )
    else:
        lines.append("- 未识别到明显返回路径。")
    lines.append("")

    lines.append("## 7. 调试附录")
    lines.append("")
    lines.append("### 业务流程 Mermaid 图")
    lines.append("")
    lines.append("```mermaid")
    lines.append(business_mermaid)
    lines.append("```")
    lines.append("")

    lines.append("### 分支执行 Mermaid 图")
    lines.append("")
    lines.append("```mermaid")
    lines.append(branch_mermaid)
    lines.append("```")
    lines.append("")

    if hidden_steps:
        lines.append("### 隐藏调用步骤")
        lines.append("")
        for step in hidden_steps:
            lines.append(
                f"- `{step.get('call_text', '')}` | type=`{step.get('call_type', '')}` | line=`{step.get('source_line_hint', '?')}`"
            )
        lines.append("")

    lines.append("### 分支信息")
    lines.append("")
    for branch in state.get("branches", []):
        lines.append(
            f"- [{branch.get('branch_index', '?')}] "
            f"`{branch.get('branch_type', '')}` "
            f"| line=`{branch.get('source_line_hint', '?')}` "
            f"| {branch.get('condition_text', '')}"
        )

    lines.append("")
    lines.append("### 方法源码")
    lines.append("")
    lines.append("```java")
    lines.append(state.get("method_source", ""))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)

def _render_execution_branch_mermaid(
    method_name: str,
    branches: list[dict],
    business_steps: list[dict],
) -> str:
    lines = []
    lines.append("flowchart TD")
    method_label = _sanitize_mermaid_label(f"{method_name}()")
    lines.append(f'    M0["{method_label}"]')

    business_step_nodes = _build_business_step_anchor_nodes(business_steps)
    branch_groups = _group_branches_by_business_step(branches, business_steps)
    terminal_counter = 1

    if not business_step_nodes and not branches:
        lines.append('    T0(["No branches extracted"])')
        lines.append("    M0 --> T0")
        return "\n".join(lines)

    previous_step_node_id = "M0"
    for anchor in business_step_nodes:
        node_id = anchor["node_id"]
        label = anchor["label"]
        lines.append(f'    {node_id}["{label}"]')
        lines.append(f"    {previous_step_node_id} --> {node_id}")
        previous_step_node_id = node_id

        grouped_branches = branch_groups.get(node_id, [])
        if not grouped_branches:
            continue

        previous_branch_node_id = None
        for idx, branch in enumerate(grouped_branches, start=1):
            branch_index = branch.get("branch_index", 0)
            branch_type = branch.get("branch_type", "branch")
            condition_text = branch.get("condition_text", "")
            source_line = branch.get("source_line_hint", "?")

            branch_node_id = f"B{branch_index}"
            branch_label = f"{branch_type} @L{source_line}: {condition_text}"
            branch_label = _sanitize_mermaid_label(branch_label)
            branch_label = _truncate_mermaid_label(branch_label, 80)

            if branch_type in {"if", "switch", "catch"}:
                lines.append(f'    {branch_node_id}{{"{branch_label}"}}')
            else:
                lines.append(f'    {branch_node_id}["{branch_label}"]')

            if idx == 1:
                lines.append(f"    {node_id} --> {branch_node_id}")
            elif previous_branch_node_id is not None:
                lines.append(f"    {previous_branch_node_id} --> {branch_node_id}")

            if branch_type in {"return", "throw"}:
                terminal_node_id = f"T{terminal_counter}"
                terminal_counter += 1
                terminal_label = _sanitize_mermaid_label(f"{branch_type.upper()} @L{source_line}")
                lines.append(f'    {terminal_node_id}(["{terminal_label}"])')
                lines.append(f"    {branch_node_id} --> {terminal_node_id}")
                previous_branch_node_id = None
            else:
                true_node_id = f"{branch_node_id}_Y"
                false_node_id = f"{branch_node_id}_N"
                lines.append(f'    {true_node_id}["进入分支"]')
                lines.append(f'    {false_node_id}["跳过分支"]')
                lines.append(f"    {branch_node_id} -->|Y| {true_node_id}")
                lines.append(f"    {branch_node_id} -->|N| {false_node_id}")
                previous_branch_node_id = true_node_id

    remaining_branches = branch_groups.get("__ungrouped__", [])
    if remaining_branches:
        lines.append('    U0["未归组分支"]')
        lines.append("    M0 --> U0")
        previous_branch_node_id = None
        for idx, branch in enumerate(remaining_branches, start=1):
            branch_index = branch.get("branch_index", 0)
            branch_type = branch.get("branch_type", "branch")
            condition_text = branch.get("condition_text", "")
            source_line = branch.get("source_line_hint", "?")

            branch_node_id = f"UB{branch_index}"
            branch_label = f"{branch_type} @L{source_line}: {condition_text}"
            branch_label = _sanitize_mermaid_label(branch_label)
            branch_label = _truncate_mermaid_label(branch_label, 80)

            if branch_type in {"if", "switch", "catch"}:
                lines.append(f'    {branch_node_id}{{"{branch_label}"}}')
            else:
                lines.append(f'    {branch_node_id}["{branch_label}"]')

            if idx == 1:
                lines.append(f"    U0 --> {branch_node_id}")
            elif previous_branch_node_id is not None:
                lines.append(f"    {previous_branch_node_id} --> {branch_node_id}")

            if branch_type in {"return", "throw"}:
                terminal_node_id = f"T{terminal_counter}"
                terminal_counter += 1
                terminal_label = _sanitize_mermaid_label(f"{branch_type.upper()} @L{source_line}")
                lines.append(f'    {terminal_node_id}(["{terminal_label}"])')
                lines.append(f"    {branch_node_id} --> {terminal_node_id}")
                previous_branch_node_id = None
            else:
                true_node_id = f"{branch_node_id}_Y"
                false_node_id = f"{branch_node_id}_N"
                lines.append(f'    {true_node_id}["进入分支"]')
                lines.append(f'    {false_node_id}["跳过分支"]')
                lines.append(f"    {branch_node_id} -->|Y| {true_node_id}")
                lines.append(f"    {branch_node_id} -->|N| {false_node_id}")
                previous_branch_node_id = true_node_id

    return "\n".join(lines)


def _render_business_summary_mermaid(
    method_name: str,
    business_steps: list[dict],
    branches: list[dict],
    generation_mode: str = "",
) -> str:
    lines = []
    lines.append("flowchart TD")

    root_label = _sanitize_mermaid_label(f"{method_name} 业务流程")
    lines.append(f'    BM0["{root_label}"]')

    if not business_steps:
        lines.append('    BMT0(["No business steps"])')
        lines.append("    BM0 --> BMT0")
        return "\n".join(lines)

    condition_map = _build_business_step_condition_map(business_steps, branches)
    business_node_ids = []
    condition_node_ids = []

    for idx, step in enumerate(business_steps):
        step_index = step.get("step_index", 0)
        title = step.get("title", f"业务步骤 {step_index}")
        title = _sanitize_mermaid_label(title)
        title = _truncate_mermaid_label(title, 28)

        step_node_id = f"BS{step_index}"
        business_node_ids.append(step_node_id)
        lines.append(f'    {step_node_id}["{step_index}. {title}"]')

        if idx == 0:
            lines.append(f"    BM0 --> {step_node_id}")

    for idx, step in enumerate(business_steps):
        step_index = step.get("step_index", 0)
        step_node_id = f"BS{step_index}"
        next_step_node_id = f"BS{business_steps[idx + 1].get('step_index', 0)}" if idx + 1 < len(business_steps) else "BME"
        conditions = condition_map.get(step_index, [])

        if not conditions:
            lines.append(f"    {step_node_id} --> {next_step_node_id}")
            continue

        decision = _infer_business_step_decision(step, conditions)
        positive_target = decision["positive_target"]
        negative_target = decision["negative_target"]

        # 如果两条路都去同一个地方，而且不是 terminal，就不要画条件节点
        if positive_target == negative_target and positive_target != "terminal":
            lines.append(f"    {step_node_id} --> {positive_target}")
            continue

        condition_id = f"BC{step_index}"
        condition_label = _sanitize_mermaid_label(decision["condition_label"])
        condition_label = _truncate_mermaid_label(condition_label, 30)
        condition_node_ids.append(condition_id)
        lines.append(f'    {condition_id}{{"{condition_label}"}}')
        lines.append(f"    {step_node_id} --> {condition_id}")

        positive_label = _sanitize_mermaid_label(decision["positive_label"])
        negative_label = _sanitize_mermaid_label(decision["negative_label"])

        if positive_target == "terminal":
            terminal_id = f"BT{step_index}Y"
            terminal_text = _sanitize_mermaid_label(decision["positive_terminal_text"])
            lines.append(f'    {terminal_id}(["{terminal_text}"])')
            lines.append(f"    {condition_id} -->|{positive_label}| {terminal_id}")
        else:
            lines.append(f"    {condition_id} -->|{positive_label}| {positive_target}")

        if negative_target == "terminal":
            terminal_id = f"BT{step_index}N"
            terminal_text = _sanitize_mermaid_label(decision["negative_terminal_text"])
            lines.append(f'    {terminal_id}(["{terminal_text}"])')
            lines.append(f"    {condition_id} -->|{negative_label}| {terminal_id}")
        else:
            lines.append(f"    {condition_id} -->|{negative_label}| {negative_target}")

    lines.append('    BME(["End"])')

    if generation_mode == "llm" and business_node_ids:
        lines.append("    classDef ai fill:#ffe6e6,stroke:#ff4d4f,color:#c62828,stroke-width:2px")
        lines.append(f"    class {','.join(business_node_ids)} ai")

    if condition_node_ids:
        lines.append("    classDef cond fill:#fff8e1,stroke:#ffb300,color:#8d6e63,stroke-width:1px")
        lines.append(f"    class {','.join(condition_node_ids)} cond")

    return "\n".join(lines)


def _infer_business_step_decision(step: dict, conditions: list[str]) -> dict:
    step_index = step.get("step_index", 0)
    title = (step.get("title", "") or "").lower()
    summary = (step.get("summary", "") or "").lower()
    condition_label = conditions[0] if conditions else "条件判断"
    next_step_target = f"BS{step_index + 1}"

    if "输入有效性" in title or "输入验证" in title or "检查输入" in title or "valid" in summary:
        return {
            "condition_label": "输入是否有效",
            "positive_label": "有效",
            "negative_label": "无效",
            "positive_target": next_step_target,
            "negative_target": "terminal",
            "positive_terminal_text": "",
            "negative_terminal_text": "返回空结果 / 提前结束",
        }

    if "严格模式" in title:
        return {
            "condition_label": "是否触发严格模式返回",
            "positive_label": "是",
            "negative_label": "否",
            "positive_target": "terminal",
            "negative_target": next_step_target,
            "positive_terminal_text": "严格模式提前返回",
            "negative_terminal_text": "",
        }

    if "风险" in title:
        return {
            "condition_label": "是否命中高风险条件",
            "positive_label": "命中",
            "negative_label": "未命中",
            "positive_target": next_step_target,
            "negative_target": next_step_target,
            "positive_terminal_text": "",
            "negative_terminal_text": "",
        }

    if "输出" in title or "返回" in title or "快照" in title:
        return {
            "condition_label": "是否生成最终结果",
            "positive_label": "是",
            "negative_label": "否",
            "positive_target": "terminal",
            "negative_target": "terminal",
            "positive_terminal_text": "输出最终结果",
            "negative_terminal_text": "结束",
        }

    if "规范化" in title or "清理" in title or "预处理" in title:
        return {
            "condition_label": "是否存在可保留内容",
            "positive_label": "有",
            "negative_label": "无",
            "positive_target": next_step_target,
            "negative_target": next_step_target,
            "positive_terminal_text": "",
            "negative_terminal_text": "",
        }

    if "映射" in title or "统计" in title or "提取" in title or "排序" in title:
        return {
            "condition_label": "是否继续后续处理",
            "positive_label": "继续",
            "negative_label": "跳过",
            "positive_target": next_step_target,
            "negative_target": next_step_target,
            "positive_terminal_text": "",
            "negative_terminal_text": "",
        }

    return {
        "condition_label": condition_label,
        "positive_label": "是",
        "negative_label": "否",
        "positive_target": next_step_target,
        "negative_target": next_step_target,
        "positive_terminal_text": "",
        "negative_terminal_text": "",
    }

def _estimate_expected_output_for_standard_input(
    method_name: str,
    method_signature: str,
    method_source: str,
    standard_input: dict,
    business_steps: list[dict],
) -> str:
    return_paths = _build_return_path_items(method_source, method_signature, standard_input)
    if return_paths:
        if len(return_paths) == 1:
            return f"按当前源码推断，最终会{return_paths[0]['description']}。"

        early_paths = [item["description"] for item in return_paths[:-1]]
        final_description = return_paths[-1]["description"]
        return (
            "按当前源码推断，该方法存在多条返回路径："
            f"提前结束时可能{'；'.join(early_paths)}；"
            f"主路径最终{final_description}。"
        )

    if business_steps:
        last_step_output = (business_steps[-1].get("step_output", "") or "").rstrip("。；;")
        if last_step_output:
            return f"按当前主流程推断，最终会{last_step_output}。"
        return f"{method_name}(...) 会按业务步骤顺序执行，并返回与分支命中情况对应的结果。"
    return standard_input.get("expected_output", "N/A")

def _build_business_step_condition_map(business_steps: list[dict], branches: list[dict]) -> dict[int, list[str]]:
    condition_map: dict[int, list[str]] = {}
    grouped = _group_branches_by_business_step(branches, business_steps)

    for step in business_steps:
        step_index = step.get("step_index", 0)
        node_id = f"S{step_index}"
        grouped_branches = grouped.get(node_id, [])
        conditions = []
        for branch in grouped_branches:
            branch_type = branch.get("branch_type", "")
            condition_text = branch.get("condition_text", "")
            if branch_type in {"if", "switch", "catch"} and condition_text:
                summarized = _summarize_condition_text_for_business(condition_text)
                if summarized:
                    conditions.append(summarized)

        if conditions:
            deduped_conditions = []
            seen = set()
            for item in conditions:
                if item in seen:
                    continue
                seen.add(item)
                deduped_conditions.append(item)
            condition_map[step_index] = deduped_conditions

    return condition_map

def _summarize_condition_text_for_business(condition_text: str) -> str:
    lowered = condition_text.lower()

    if "== null" in lowered or ".isempty()" in lowered:
        return "输入是否为空"
    if "startswith" in lowered or "endswith" in lowered or "substring" in lowered:
        return "是否满足格式清洗条件"
    if "contains" in lowered:
        return "是否命中特定标记"
    if "compareto" in lowered or ">" in condition_text or "<" in condition_text:
        return "是否满足阈值条件"
    if "strictmode" in lowered:
        return "是否启用严格模式"
    if "invalid" in lowered:
        return "是否存在无效输入"
    if "negative" in lowered:
        return "是否存在非法数值"
    if "discount" in lowered and "amount" in lowered:
        return "折扣是否超出允许范围"
    if "manualreview" in lowered or "urgent" in lowered or "vip" in lowered:
        return "是否命中业务标签条件"
    if "count" in lowered:
        return "是否满足重复出现条件"

    return "是否命中当前条件"

def _build_standard_input_example(method_signature: str, method_name: str, method_source: str) -> dict:
    lower_signature = method_signature.lower()
    if "buildnormalizedordersnapshot" in method_name.lower() or "rawcustomername" in lower_signature:
        return {
            "inputs": [
                {"name": "rawCustomerName", "type": "String", "value": "Alice"},
                {"name": "rawOrderNo", "type": "String", "value": "ORD-20260417-001"},
                {"name": "rawStatus", "type": "String", "value": "paid"},
                {"name": "rawAmount", "type": "BigDecimal", "value": "12000"},
                {"name": "discountAmount", "type": "BigDecimal", "value": "1000"},
                {"name": "rawTags", "type": "List<String>", "value": "[vip, urgent]"},
                {"name": "strictMode", "type": "boolean", "value": "false"},
            ],
            "expected_output": "输出结果会根据当前源码中的实际 return 路径决定。",
        }

    parameter_items = _extract_parameter_items_from_signature(method_signature)
    inputs = []
    for param_type, param_name in parameter_items:
        inputs.append({
            "name": param_name,
            "type": param_type,
            "value": _default_example_value_for_type(param_type, param_name),
        })

    if "normalizeandextractstillduplicateditems" in method_name.lower():
        return {
            "inputs": [
                {"name": "rawItems", "type": "List<String>", "value": "['tmp-a', 'a', 'B_copy', 'b', 'temp-a']"},
            ],
            "expected_output": "输出结果会根据当前源码中的实际 return 路径决定。",
        }

    return {
        "inputs": inputs,
        "expected_output": f"{method_name}(...) 的返回结果取决于实际分支命中情况。",
    }


def _build_return_path_items(method_source: str, method_signature: str, standard_input: dict) -> list[dict]:
    return_statements = _extract_return_statements(method_source)
    parameter_names = {
        param_name
        for _, param_name in _extract_parameter_items_from_signature(method_signature)
    }
    items = []
    for item in return_statements:
        items.append({
            "line_no": item["line_no"],
            "expression": item["expression"],
            "description": _describe_return_expression(
                expression=item["expression"],
                parameter_names=parameter_names,
                standard_input=standard_input,
            ),
        })
    return items


def _extract_return_statements(method_source: str) -> list[dict]:
    return_statements = []

    for line_no, line in enumerate(method_source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if not stripped.startswith("return "):
            continue

        expression = stripped[len("return "):].strip()
        if expression.endswith(";"):
            expression = expression[:-1].strip()

        return_statements.append({
            "line_no": line_no,
            "expression": expression,
        })

    return return_statements


def _describe_return_expression(expression: str, parameter_names: set[str], standard_input: dict) -> str:
    lowered = expression.lower()

    if expression.startswith("new ArrayList") or expression.startswith("Collections.emptyList"):
        return "返回空列表"

    if expression.startswith("new HashMap") or expression.startswith("Collections.emptyMap"):
        return "返回空 Map"

    if expression in parameter_names:
        sample_value = _lookup_input_example_value(standard_input, expression)
        if sample_value:
            return f"返回输入参数 `{expression}` 本身（示例值：`{sample_value}`）"
        return f"返回输入参数 `{expression}` 本身"

    if expression.endswith(".toString()"):
        if "snapshot" in lowered or "builder" in lowered:
            return "返回组装完成的字符串结果"
        return f"返回表达式 `{expression}` 对应的字符串结果"

    if expression.lower().endswith("finalresult") or expression.lower().endswith("result"):
        return f"返回结果变量 `{expression}` 当前收敛出的内容"

    if expression.startswith("\"") or expression.startswith("'"):
        return "返回当前分支拼装出的固定格式字符串"

    return f"返回表达式 `{expression}` 的当前值"


def _lookup_input_example_value(standard_input: dict, param_name: str) -> str:
    for item in standard_input.get("inputs", []):
        if item.get("name") == param_name:
            return item.get("value", "")
    return ""


def _extract_parameter_items_from_signature(method_signature: str) -> list[tuple[str, str]]:
    start = method_signature.find("(")
    end = method_signature.rfind(")")
    if start == -1 or end == -1 or end <= start:
        return []

    raw_params = method_signature[start + 1:end].strip()
    if not raw_params:
        return []

    parts = [item.strip() for item in raw_params.split(",") if item.strip()]
    result = []
    for part in parts:
        pieces = part.split()
        if len(pieces) >= 2:
            param_name = pieces[-1]
            param_type = " ".join(pieces[:-1])
            result.append((param_type, param_name))
    return result


def _default_example_value_for_type(param_type: str, param_name: str) -> str:
    lowered_type = param_type.lower()
    lowered_name = param_name.lower()

    if "string" in lowered_type:
        if "status" in lowered_name:
            return "sample_status"
        if "name" in lowered_name:
            return "sample_name"
        return "sample_text"
    if "boolean" in lowered_type or lowered_type == "bool":
        return "false"
    if "int" in lowered_type or "long" in lowered_type or "short" in lowered_type:
        return "1"
    if "double" in lowered_type or "float" in lowered_type or "bigdecimal" in lowered_type:
        return "1.0"
    if "list" in lowered_type or "set" in lowered_type:
        return "[]"
    if "map" in lowered_type:
        return "{}"
    return "sample_value"

def _group_branches_by_business_step(branches: list[dict], business_steps: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}

    for step in business_steps:
        node_id = f"S{step.get('step_index', 0)}"
        line_range = step.get("line_range", {})
        start_line = line_range.get("start", -1)
        end_line = line_range.get("end", -1)
        matched = []
        for branch in branches:
            line = branch.get("source_line_hint", -1)
            if start_line <= line <= end_line:
                matched.append(branch)
        if matched:
            grouped[node_id] = matched

    used_branch_ids = {
        branch.get("branch_index")
        for items in grouped.values()
        for branch in items
    }
    ungrouped = [
        branch for branch in branches
        if branch.get("branch_index") not in used_branch_ids
    ]
    if ungrouped:
        grouped["__ungrouped__"] = ungrouped

    return grouped



def _build_business_step_anchor_nodes(business_steps: list[dict]) -> list[dict]:
    anchors = []
    for step in business_steps:
        step_index = step.get("step_index", 0)
        title = step.get("title", f"业务步骤 {step_index}")
        line_range = step.get("line_range", {})
        start_line = line_range.get("start", "?")
        end_line = line_range.get("end", "?")
        anchors.append({
            "node_id": f"S{step_index}",
            "label": _sanitize_mermaid_label(f"步骤 {step_index}: {title} ({start_line}-{end_line})"),
        })
    return anchors



def _sanitize_mermaid_label(text: str) -> str:
    sanitized = text.replace("\n", " ").replace("\r", " ")
    sanitized = sanitized.replace('"', "'")
    sanitized = sanitized.replace("{", "(").replace("}", ")")
    sanitized = sanitized.replace("[", "(").replace("]", ")")
    sanitized = sanitized.replace("<", "＜").replace(">", "＞")
    sanitized = sanitized.replace("`", "'")
    sanitized = sanitized.replace("|", "/")
    sanitized = sanitized.replace(";", "")
    sanitized = " ".join(sanitized.split())
    return sanitized



def _truncate_mermaid_label(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."

MAIN_FLOW_HIDE_METHODS = {
    "append",
    "toString",
    "trim",
    "toUpperCase",
    "toLowerCase",
    "add",
}

MAIN_FLOW_KEEP_METHODS = {
    "compareTo",
    "equals",
    "contains",
    "isEmpty",
    "subtract",
}
