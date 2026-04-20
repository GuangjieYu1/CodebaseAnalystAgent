from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re

from app.services.prompt_loader import build_system_prompt, load_and_render_prompt
from app.services.llm_client import generate_with_ollama, generate_with_deepseek


def explain_method_execution_path(
    project_root: str,
    file_path: str,
    method_name: str,
    provider: str = "deepseek",
    model: str = "deepseek-reasoner",
    tool_registry_enhanced_json_path: str = "outputs/tool_registry_enhanced.json",
    output_json: str = "outputs/method_execution_path.json",
    output_md: str = "outputs/method_execution_path.md",
) -> dict:
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    target_file = root / file_path
    if not target_file.exists() or not target_file.is_file():
        raise ValueError(f"Invalid file path: {file_path}")

    java_source = target_file.read_text(encoding="utf-8", errors="ignore")

    tool_registry_enhanced = _load_tool_registry_enhanced(tool_registry_enhanced_json_path)
    package_name = _extract_java_package(java_source)
    class_name = _extract_java_class_name(java_source)

    method_source = _extract_method_source(java_source, method_name)
    if not method_source:
        raise ValueError(f"Failed to extract method source for method: {method_name}")

    method_signature = _extract_method_signature(method_source, method_name)
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

    raw_call_items = _extract_call_items(method_source)
    branch_items = _extract_branch_items(method_source)

    enriched_call_items = _enrich_call_items(
        raw_call_items=raw_call_items,
        current_class_name=class_name,
        tool_registry_enhanced=tool_registry_enhanced,
    )

    try:
        execution_explanation = _explain_execution_path_with_llm(
            provider=provider,
            model=model,
            class_name=class_name,
            package_name=package_name,
            file_path=file_path,
            method_name=method_name,
            method_signature=method_signature,
            method_source=method_source,
            java_source=java_source,
            call_items=enriched_call_items,
            branch_items=branch_items,
            standard_input=standard_input,
            return_paths=return_paths,
        )
    except Exception:
        execution_explanation = {
            "method_summary": "",
            "steps": [],
            "branches": [],
        }

    steps = _merge_steps_with_context(
        llm_steps=execution_explanation.get("steps", []),
        enriched_call_items=enriched_call_items,
        tool_registry_enhanced=tool_registry_enhanced,
    )

    method_summary = execution_explanation.get("method_summary", "")
    branches = _merge_branch_items(
        llm_branches=execution_explanation.get("branches", []),
        extracted_branches=branch_items,
    )

    try:
        mermaid = _generate_mermaid_with_llm(
            provider=provider,
            model=model,
            method_name=method_name,
            method_summary=method_summary,
            steps=steps,
            branches=branches,
        )
    except Exception:
        mermaid = "flowchart TD"

    state = {
        "project_root": str(root),
        "file_path": file_path,
        "class_name": class_name,
        "package_name": package_name,
        "method_name": method_name,
        "method_signature": method_signature,
        "method_source": method_source,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "provider": provider,
        "model": model,
        "method_summary": method_summary,
        "steps": steps,
        "branches": branches,
        "standard_input": standard_input,
        "return_paths": return_paths,
        "mermaid": mermaid,
        "final_markdown_path": output_md,
    }

    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(
        render_method_execution_markdown(state),
        encoding="utf-8",
    )

    return state


def _load_tool_registry_enhanced(tool_registry_enhanced_json_path: str) -> dict:
    path = Path(tool_registry_enhanced_json_path)
    if not path.exists() or not path.is_file():
        return {"tool_classes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_java_package(java_source: str) -> str:
    match = re.search(r"^\s*package\s+([\w\.]+);", java_source, flags=re.MULTILINE)
    return match.group(1) if match else ""


def _extract_java_class_name(java_source: str) -> str:
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", java_source)
    return match.group(1) if match else ""


def _extract_method_source(java_source: str, method_name: str) -> str:
    pattern = re.compile(
        rf"(public|protected|private)\s+(static\s+)?[\w<>\[\],\s?]+\s+{re.escape(method_name)}\s*\([^)]*\)\s*\{{",
        flags=re.MULTILINE,
    )

    match = pattern.search(java_source)
    if not match:
        return ""

    start = match.start()
    brace_start = java_source.find("{", match.end() - 1)
    if brace_start == -1:
        return java_source[start:match.end()]

    depth = 0
    end = brace_start

    for idx in range(brace_start, len(java_source)):
        ch = java_source[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = idx + 1
                break

    return java_source[start:end]


def _extract_method_signature(method_source: str, method_name: str) -> str:
    first_line = method_source.split("{", 1)[0].strip()
    return " ".join(first_line.split())


def _extract_call_items(method_source: str) -> list[dict]:
    """
    第一版：轻量正则提取调用项。
    识别三类：
    - foo(...)
    - obj.foo(...)
    - ClassName.foo(...)
    """
    lines = method_source.splitlines()
    call_items = []
    step_index = 1

    call_pattern = re.compile(
        r"(?P<prefix>\b[A-Za-z_][A-Za-z0-9_]*\.)?(?P<method>[A-Za-z_][A-Za-z0-9_]*)\s*\(",
    )

    ignored_keywords = {
        "if", "for", "while", "switch", "catch", "return", "throw", "new", "else", "try", "super", "this",
    }
    method_declaration_pattern = re.compile(
        r"^(public|protected|private)\s+(static\s+)?[\w<>\[\],\s?]+\s+[A-Za-z_][A-Za-z0-9_]*\s*\(",
    )

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if method_declaration_pattern.match(stripped):
            continue

        for match in call_pattern.finditer(stripped):
            prefix = match.group("prefix") or ""
            method = match.group("method")

            if method in ignored_keywords:
                continue

            call_text = _extract_call_text(stripped, match.start())
            call_items.append({
                "step_index": step_index,
                "call_text": call_text,
                "raw_prefix": prefix[:-1] if prefix.endswith(".") else prefix,
                "callee_method_name": method,
                "source_line_hint": line_no,
            })
            step_index += 1

    return call_items


def _extract_call_text(line: str, start_idx: int) -> str:
    """
    第一版：从起始位置开始，做一个轻量括号平衡提取。
    """
    depth = 0
    end_idx = start_idx

    for idx in range(start_idx, len(line)):
        ch = line[idx]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end_idx = idx + 1
                break

    return line[start_idx:end_idx].strip()


def _extract_branch_items(method_source: str) -> list[dict]:
    branch_items = []
    lines = method_source.splitlines()
    branch_index = 1

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        if stripped.startswith("if ") or stripped.startswith("if(") or stripped.startswith("if ("):
            branch_items.append({
                "branch_index": branch_index,
                "branch_type": "if",
                "condition_text": stripped,
                "effect": "条件成立时进入对应分支逻辑",
                "source_line_hint": line_no,
            })
            branch_index += 1
            continue

        if stripped.startswith("else if"):
            branch_items.append({
                "branch_index": branch_index,
                "branch_type": "else_if",
                "condition_text": stripped,
                "effect": "前置条件未命中时继续判断当前分支",
                "source_line_hint": line_no,
            })
            branch_index += 1
            continue

        if stripped.startswith("else"):
            branch_items.append({
                "branch_index": branch_index,
                "branch_type": "else",
                "condition_text": stripped,
                "effect": "当前置条件均未命中时进入兜底逻辑",
                "source_line_hint": line_no,
            })
            branch_index += 1
            continue

        if "throw " in stripped:
            branch_items.append({
                "branch_index": branch_index,
                "branch_type": "throw",
                "condition_text": stripped,
                "effect": "可能抛出异常并中断后续流程",
                "source_line_hint": line_no,
            })
            branch_index += 1
            continue

        if stripped.startswith("return "):
            branch_items.append({
                "branch_index": branch_index,
                "branch_type": "return",
                "condition_text": stripped,
                "effect": "提前返回",
                "source_line_hint": line_no,
            })
            branch_index += 1

    return branch_items


def _enrich_call_items(
    raw_call_items: list[dict],
    current_class_name: str,
    tool_registry_enhanced: dict,
) -> list[dict]:
    enriched = []

    for item in raw_call_items:
        prefix = item.get("raw_prefix", "")
        method_name = item["callee_method_name"]

        matched_tool = _find_tool_method(tool_registry_enhanced, prefix, method_name)

        if matched_tool:
            enriched.append({
                **item,
                "callee_class_name": matched_tool["class_name"],
                "call_type": "tool_method",
                "tool_method_context": {
                    "class_summary": matched_tool.get("class_summary", ""),
                    "method_summary": matched_tool.get("method_summary", ""),
                    "actual_output_semantics": matched_tool.get("actual_output_semantics", ""),
                    "usage_suggestion": matched_tool.get("usage_suggestion", ""),
                },
                "interface_context": None,
            })
            continue

        if _looks_like_external_interface(prefix):
            enriched.append({
                **item,
                "callee_class_name": prefix or "",
                "call_type": "external_interface_call",
                "tool_method_context": None,
                "interface_context": {
                    "is_cross_boundary": True,
                    "risk_hint": "该步骤涉及系统外部接口调用，存在网络延迟、超时和远程失败风险。",
                },
            })
            continue

        if prefix:
            if prefix[:1].isupper():
                enriched.append({
                    **item,
                    "callee_class_name": prefix,
                    "call_type": "external_static_method",
                    "tool_method_context": None,
                    "interface_context": None,
                })
            else:
                enriched.append({
                    **item,
                    "callee_class_name": prefix,
                    "call_type": "external_instance_method",
                    "tool_method_context": None,
                    "interface_context": None,
                })
            continue

        enriched.append({
            **item,
            "callee_class_name": current_class_name,
            "call_type": "internal_method",
            "tool_method_context": None,
            "interface_context": None,
        })

    return enriched


def _find_tool_method(tool_registry_enhanced: dict, class_name: str, method_name: str) -> dict | None:
    if not class_name:
        return None

    for tool_class in tool_registry_enhanced.get("tool_classes", []):
        if tool_class.get("class_name") != class_name:
            continue

        for method in tool_class.get("methods", []):
            if method.get("method_name") == method_name:
                return {
                    "class_name": tool_class.get("class_name", ""),
                    "class_summary": tool_class.get("class_summary", ""),
                    "method_summary": method.get("method_summary", ""),
                    "actual_output_semantics": method.get("actual_output_semantics", ""),
                    "usage_suggestion": method.get("usage_suggestion", ""),
                }

    return None


def _looks_like_external_interface(prefix: str) -> bool:
    lowered = prefix.lower()
    markers = [
        "client", "feign", "rpc", "api", "gateway", "remote", "sdk",
    ]
    return any(marker in lowered for marker in markers)


def _explain_execution_path_with_llm(
    provider: str,
    model: str,
    class_name: str,
    package_name: str,
    file_path: str,
    method_name: str,
    method_signature: str,
    method_source: str,
    java_source: str,
    call_items: list[dict],
    branch_items: list[dict],
    standard_input: dict,
    return_paths: list[dict],
) -> dict:
    system_prompt = build_system_prompt(
        "shared/system_base.txt",
        "shared/output_json_rules.txt",
        "method_execution/explain_method_execution_system.txt",
    )

    user_prompt = load_and_render_prompt(
        "method_execution/explain_method_execution_user.txt",
        {
            "class_name": class_name,
            "package_name": package_name,
            "file_path": file_path,
            "method_name": method_name,
            "method_signature": method_signature,
            "method_source": method_source,
            "standard_input_json": json.dumps(standard_input, ensure_ascii=False, indent=2),
            "return_paths_json": json.dumps(return_paths, ensure_ascii=False, indent=2),
            "branches_json": json.dumps(branch_items, ensure_ascii=False, indent=2),
            "call_items_json": json.dumps(call_items, ensure_ascii=False, indent=2),
            "java_source": java_source,
        },
    )

    raw_response = _call_llm(
    provider=provider,
    model=model,
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    )
    print("\n=== RAW EXECUTION EXPLANATION RESPONSE START ===\n")
    print(raw_response)
    print("\n=== RAW EXECUTION EXPLANATION RESPONSE END ===\n")
    return _safe_parse_json(raw_response)


def _merge_branch_items(llm_branches: list[dict], extracted_branches: list[dict]) -> list[dict]:
    if not llm_branches and not extracted_branches:
        return []

    if not llm_branches:
        return extracted_branches

    merged = []
    for idx, item in enumerate(llm_branches):
        extracted = extracted_branches[idx] if idx < len(extracted_branches) else {}
        merged.append({
            "branch_index": item.get("branch_index", extracted.get("branch_index", idx + 1)),
            "branch_type": item.get("branch_type", extracted.get("branch_type", "branch")),
            "condition_text": item.get("condition_text", extracted.get("condition_text", "")),
            "effect": item.get("effect", extracted.get("effect", "")),
            "source_line_hint": extracted.get("source_line_hint"),
        })

    if len(extracted_branches) > len(llm_branches):
        merged.extend(extracted_branches[len(llm_branches):])

    return merged


def _generate_mermaid_with_llm(
    provider: str,
    model: str,
    method_name: str,
    method_summary: str,
    steps: list[dict],
    branches: list[dict],
) -> str:
    system_prompt = build_system_prompt(
        "shared/system_base.txt",
        "method_execution/generate_method_mermaid_system.txt",
    )

    user_prompt = load_and_render_prompt(
        "method_execution/generate_method_mermaid_user.txt",
        {
            "method_name": method_name,
            "execution_path_json": json.dumps(
                {
                    "method_summary": method_summary,
                    "steps": steps,
                    "branches": branches,
                },
                ensure_ascii=False,
                indent=2,
            ),
        },
    )

    raw_response = _call_llm(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return raw_response.strip()


def _call_llm(
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    provider = provider.strip().lower()

    if provider == "ollama":
        return generate_with_ollama(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0,
            timeout=300,
            show_thinking=False,
            think=False,
        )

    if provider == "deepseek":
        return generate_with_deepseek(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0,
            timeout=300,
        )

    raise ValueError(f"Unsupported provider: {provider}")


def _safe_parse_json(raw_text: str) -> dict:
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


def _merge_steps_with_context(
    llm_steps: list[dict],
    enriched_call_items: list[dict],
    tool_registry_enhanced: dict,
) -> list[dict]:
    merged = []

    for idx, call_item in enumerate(enriched_call_items):
        llm_step = llm_steps[idx] if idx < len(llm_steps) else {}
        llm_summary = llm_step.get("llm_summary") or llm_step.get("summary", "")
        llm_simulated_input = llm_step.get("llm_simulated_input") or llm_step.get("expected_input", "")
        llm_simulated_output = llm_step.get("llm_simulated_output") or llm_step.get("expected_output", "")

        merged.append({
            "step_index": llm_step.get("step_index", call_item.get("step_index", idx + 1)),
            "call_text": llm_step.get("call_text", call_item.get("call_text", "")),
            "callee_method_name": llm_step.get("callee_method_name", call_item.get("callee_method_name", "")),
            "callee_class_name": llm_step.get("callee_class_name", call_item.get("callee_class_name", "")),
            "call_type": llm_step.get("call_type", call_item.get("call_type", "unknown_call")),
            "source_line_hint": call_item.get("source_line_hint"),
            "llm_summary": llm_summary,
            "llm_simulated_input": llm_simulated_input,
            "llm_simulated_output": llm_simulated_output,
            "summary": llm_summary,
            "expected_input": llm_simulated_input,
            "expected_output": llm_simulated_output,
            "preconditions": llm_step.get("preconditions", []),
            "boundary_conditions": llm_step.get("boundary_conditions", []),
            "tool_method_context": call_item.get("tool_method_context"),
            "interface_context": call_item.get("interface_context"),
            "notes": llm_step.get("notes", ""),
        })

    return merged


def _build_standard_input_example(method_signature: str, method_name: str, method_source: str) -> dict:
    lower_signature = method_signature.lower()
    lower_method_name = method_name.lower()

    if "normalizeandextractstillduplicateditems" in lower_method_name or "rawitems" in lower_signature:
        return {
            "inputs": [
                {"name": "rawItems", "type": "List<String>", "value": "['tmp-a', 'a', 'B_copy', 'b', 'temp-a']"},
            ],
            "intermediate_states": [
                "规范化后得到 sanitizedItems = [a, a, b, b, a]",
                "频次统计得到 frequencyMap = {a=3, b=2}",
                "最终只保留出现次数大于 1 的元素",
            ],
            "expected_output": "输出结果会根据当前源码中的实际 return 路径决定。",
        }

    params = _extract_parameters_from_signature(method_signature)
    inputs = []
    for param_type, param_name in params:
        inputs.append({
            "name": param_name,
            "type": param_type,
            "value": _default_example_value_for_type(param_type, param_name),
        })

    return {
        "inputs": inputs,
        "intermediate_states": [],
        "expected_output": "输出结果会根据当前源码中的实际 return 路径决定。",
    }


def _build_return_path_items(method_source: str, method_signature: str, standard_input: dict) -> list[dict]:
    return_statements = _extract_return_statements(method_source)
    parameter_names = {
        param_name
        for _, param_name in _extract_parameters_from_signature(method_signature)
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


def _estimate_expected_output_for_standard_input(
    method_name: str,
    method_signature: str,
    method_source: str,
    standard_input: dict,
) -> str:
    return_paths = _build_return_path_items(method_source, method_signature, standard_input)
    if not return_paths:
        return standard_input.get("expected_output", f"{method_name}(...) 的返回结果取决于实际分支命中情况。")

    if len(return_paths) == 1:
        return f"按当前源码推断，最终会{return_paths[0]['description']}。"

    early_paths = "；".join(item["description"] for item in return_paths[:-1])
    final_path = return_paths[-1]["description"]
    return f"按当前源码推断，该方法存在多条返回路径：提前结束时可能{early_paths}；主路径最终{final_path}。"


def _extract_parameters_from_signature(method_signature: str) -> list[tuple[str, str]]:
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


def render_method_execution_markdown(state: dict) -> str:
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
    expected_output = _estimate_expected_output_for_standard_input(
        method_name=state.get("method_name", ""),
        method_signature=state.get("method_signature", ""),
        method_source=state.get("method_source", ""),
        standard_input=standard_input,
    )

    lines = [
        "# 方法执行路径说明",
        "",
        f"- 生成时间：`{state['generated_at']}`",
        f"- 文件路径：`{state['file_path']}`",
        f"- 类名：`{state['class_name']}`",
        f"- 方法名：`{state['method_name']}`",
        f"- Provider：`{state['provider']}`",
        f"- Model：`{state['model']}`",
        "",
        "## 方法摘要（AI 生成）",
        "",
        state.get("method_summary", "") or "未生成方法级 LLM 总结。",
        "",
        "## 执行步骤",
        "",
    ]

    for step in state.get("steps", []):
        lines.append(f"### Step {step['step_index']} - {step.get('callee_method_name', '')}")
        lines.append("")

        has_llm_content = any([
            step.get("llm_summary"),
            step.get("llm_simulated_input"),
            step.get("llm_simulated_output"),
        ])
        if has_llm_content:
            lines.append("#### LLM 模拟结论")
            lines.append("")
            lines.append(f"- 精确总结：{step.get('llm_summary', '')}")
            lines.append(f"- 模拟输入：{step.get('llm_simulated_input', '')}")
            lines.append(f"- 模拟输出：{step.get('llm_simulated_output', '')}")
            lines.append("")

        lines.append("#### 程序推断 / 程序证据")
        lines.append("")
        lines.append(f"- 调用文本：`{step.get('call_text', '')}`")
        if step.get("source_line_hint") is not None:
            lines.append(f"- 源码行号：`{step.get('source_line_hint')}`")
        lines.append(f"- 被调类：`{step.get('callee_class_name', '')}`")
        lines.append(f"- 调用类型：`{step.get('call_type', '')}`")
        lines.append(f"- 兼容摘要字段：{step.get('summary', '')}")
        lines.append(f"- 兼容输入字段：{step.get('expected_input', '')}")
        lines.append(f"- 兼容输出字段：{step.get('expected_output', '')}")

        preconditions = step.get("preconditions", [])
        lines.append("- 前置条件：")
        if preconditions:
            for item in preconditions:
                lines.append(f"  - {item}")
        else:
            lines.append("  - 无")

        boundaries = step.get("boundary_conditions", [])
        lines.append("- 边界条件：")
        if boundaries:
            for item in boundaries:
                lines.append(f"  - {item}")
        else:
            lines.append("  - 无")

        tool_ctx = step.get("tool_method_context")
        if tool_ctx:
            lines.append("- Tool 方法上下文（程序从 tool registry 补充）：")
            lines.append(f"  - 类摘要：{tool_ctx.get('class_summary', '')}")
            lines.append(f"  - 方法摘要：{tool_ctx.get('method_summary', '')}")
            lines.append(f"  - 实际输出语义：{tool_ctx.get('actual_output_semantics', '')}")
            lines.append(f"  - 使用建议：{tool_ctx.get('usage_suggestion', '')}")

        interface_ctx = step.get("interface_context")
        if interface_ctx:
            lines.append("- 接口上下文（程序推断）：")
            lines.append(f"  - 是否跨边界：`{str(interface_ctx.get('is_cross_boundary', False)).lower()}`")
            lines.append(f"  - 风险提示：{interface_ctx.get('risk_hint', '')}")

        notes = step.get("notes", "")
        if notes:
            lines.append(f"- 备注：{notes}")

        lines.append("")

    lines.append("## 返回路径摘要（程序推断）")
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

    lines.append("## 分支提示（程序提取）")
    lines.append("")
    branches = state.get("branches", [])
    if branches:
        for item in branches:
            line_hint = item.get("source_line_hint")
            branch_type = item.get("branch_type", "branch")
            lines.append(
                f"- [{item.get('branch_index', '?')}] `{branch_type}`"
                f" | line=`{line_hint if line_hint is not None else '?'} `"
                f" | {item.get('condition_text', '')}"
            )
            effect = item.get("effect", "")
            if effect:
                lines.append(f"  - {effect}")
    else:
        lines.append("- 未识别到明显分支。")
    lines.append("")

    lines.append("## 标准输入模拟（程序构造）")
    lines.append("")
    lines.append("### 标准输入")
    lines.append("")
    for item in standard_input.get("inputs", []):
        lines.append(f"- `{item['name']}` ({item['type']}): `{item['value']}`")
    lines.append("")

    intermediate_states = standard_input.get("intermediate_states", [])
    if intermediate_states:
        lines.append("### 参考中间状态")
        lines.append("")
        for item in intermediate_states:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("### 预期输出")
    lines.append("")
    lines.append(f"- `{expected_output}`")
    lines.append("")

    lines.append("## Mermaid（AI 生成）")
    lines.append("")
    lines.append("```mermaid")
    lines.append(state.get("mermaid", "flowchart TD"))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)
