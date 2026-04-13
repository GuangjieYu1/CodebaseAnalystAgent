from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re


def build_tool_registry_state(
    project_root: str,
    directory_index_json_path: str = "outputs/directory_index.json",
    output_json: str = "outputs/tool_registry.json",
    output_md: str = "outputs/tool_registry.md",
) -> dict:
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    index_path = Path(directory_index_json_path)
    if not index_path.exists() or not index_path.is_file():
        raise ValueError(f"Invalid directory index json path: {directory_index_json_path}")

    directory_index_state = json.loads(index_path.read_text(encoding="utf-8"))
    directories = directory_index_state.get("directories", [])

    tool_dirs = [
        item["path"]
        for item in directories
        if item.get("matched_category") == "util"
    ]

    tool_classes = []
    all_methods = []

    for dir_path in tool_dirs:
        full_dir = root / dir_path
        if not full_dir.exists() or not full_dir.is_dir():
            continue

        for java_file in sorted(full_dir.rglob("*.java")):
            class_info = _parse_java_tool_class(root, java_file)
            if class_info is None:
                continue

            tool_classes.append(class_info)
            all_methods.extend(class_info["methods"])

    state = {
        "project_root": str(root),
        "source_directory_index_json": str(index_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tool_class_count": len(tool_classes),
        "method_count": len(all_methods),
        "tool_classes": tool_classes,
    }

    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(render_tool_registry_markdown(state), encoding="utf-8")

    return state


def _parse_java_tool_class(root: Path, java_file: Path) -> dict | None:
    content = java_file.read_text(encoding="utf-8", errors="ignore")

    class_name = _extract_java_class_name(content)
    if not class_name:
        return None

    package_name = _extract_java_package(content)
    methods = _extract_java_methods(content, java_file.relative_to(root), class_name)

    return {
        "class_name": class_name,
        "package_name": package_name,
        "file_path": str(java_file.relative_to(root)),
        "method_count": len(methods),
        "methods": methods,
    }


def _extract_java_package(content: str) -> str:
    match = re.search(r"^\s*package\s+([\w\.]+);", content, flags=re.MULTILINE)
    return match.group(1) if match else ""


def _extract_java_class_name(content: str) -> str:
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", content)
    return match.group(1) if match else ""


def _extract_java_methods(content: str, file_path: Path, class_name: str) -> list[dict]:
    pattern = re.compile(
        r"^\s*(public|protected|private)\s+"
        r"(static\s+)?"
        r"([\w\<\>\[\],\s\?]+?)\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*"
        r"\(([^)]*)\)",
        flags=re.MULTILINE,
    )

    methods = []
    for match in pattern.finditer(content):
        visibility = match.group(1).strip()
        is_static = bool(match.group(2))
        return_type = " ".join(match.group(3).split())
        method_name = match.group(4).strip()
        raw_params = match.group(5).strip()

        # 跳过构造器
        if method_name == class_name:
            continue

        methods.append({
            "class_name": class_name,
            "file_path": str(file_path),
            "method_name": method_name,
            "parameters": _parse_parameters(raw_params),
            "return_type": return_type,
            "is_static": is_static,
            "visibility": visibility,
            "summary": _build_method_summary(method_name, return_type, raw_params),
        })

    return methods


def _parse_parameters(raw_params: str) -> list[dict]:
    if not raw_params:
        return []

    results = []
    for part in raw_params.split(","):
        piece = " ".join(part.strip().split())
        if not piece:
            continue

        tokens = piece.split(" ")
        if len(tokens) == 1:
            results.append({
                "type": tokens[0],
                "name": "",
            })
        else:
            results.append({
                "type": " ".join(tokens[:-1]),
                "name": tokens[-1],
            })

    return results


def _build_method_summary(method_name: str, return_type: str, raw_params: str) -> str:
    if raw_params:
        return f"方法 `{method_name}` 接收参数 `{raw_params}`，返回 `{return_type}`。"
    return f"方法 `{method_name}` 无参数，返回 `{return_type}`。"


def render_tool_registry_markdown(state: dict) -> str:
    lines = [
        "# Tool Registry",
        "",
        f"- Root: `{state['project_root']}`",
        f"- Source Directory Index JSON: `{state['source_directory_index_json']}`",
        f"- Generated At: `{state['generated_at']}`",
        f"- Tool Class Count: `{state['tool_class_count']}`",
        f"- Method Count: `{state['method_count']}`",
        "",
        "## Tool Classes",
        "",
    ]

    for tool_class in state["tool_classes"]:
        lines.append(f"### {tool_class['class_name']}")
        lines.append("")
        lines.append(f"- Package: `{tool_class['package_name']}`")
        lines.append(f"- File Path: `{tool_class['file_path']}`")
        lines.append(f"- Method Count: `{tool_class['method_count']}`")
        lines.append("")

        if tool_class["methods"]:
            lines.append("| Method | Visibility | Static | Return Type | Parameters |")
            lines.append("| --- | --- | --- | --- | --- |")
            for method in tool_class["methods"]:
                params_str = ", ".join(
                    f"{param['type']} {param['name']}".strip()
                    for param in method["parameters"]
                )
                lines.append(
                    f"| {method['method_name']} | {method['visibility']} | "
                    f"{'yes' if method['is_static'] else 'no'} | "
                    f"{method['return_type']} | {params_str} |"
                )
            lines.append("")

    return "\n".join(lines)