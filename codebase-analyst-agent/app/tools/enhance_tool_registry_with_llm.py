from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json

from app.services.prompt_loader import build_system_prompt, load_and_render_prompt
from app.services.llm_client import generate_with_ollama, generate_with_deepseek

def enhance_tool_registry_with_llm(
    project_root: str,
    tool_registry_json_path: str = "outputs/tool_registry.json",
    output_json: str = "outputs/tool_registry_enhanced.json",
    output_md: str = "outputs/tool_registry_enhanced.md",
    provider: str = "ollama",
    model: str = "qwen3.5:9b",
    target_class_name: str | None = None,
) -> dict:
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    registry_path = Path(tool_registry_json_path)
    if not registry_path.exists() or not registry_path.is_file():
        raise ValueError(f"Invalid tool registry json path: {tool_registry_json_path}")

    base_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    tool_classes = base_registry.get("tool_classes", [])

    enhanced_tool_classes = []

    for tool_class in tool_classes:
        class_name = tool_class["class_name"]

        if target_class_name and class_name != target_class_name:
            continue

        file_path = tool_class["file_path"]
        java_source = (root / file_path).read_text(encoding="utf-8", errors="ignore")

        enhanced = _enhance_single_tool_class(
            provider=provider,
            model=model,
            tool_class=tool_class,
            java_source=java_source,
        )

        merged = _merge_tool_class(tool_class, enhanced)
        enhanced_tool_classes.append(merged)

    enhanced_method_count = sum(len(item.get("methods", [])) for item in enhanced_tool_classes)

    state = {
        "project_root": str(root),
        "source_tool_registry_json": str(registry_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "provider": provider,
        "model": model,
        "enhanced_tool_class_count": len(enhanced_tool_classes),
        "enhanced_method_count": enhanced_method_count,
        "tool_classes": enhanced_tool_classes,
    }

    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(render_enhanced_tool_registry_markdown(state), encoding="utf-8")

    return state


def _enhance_single_tool_class(
    provider: str,
    model: str,
    tool_class: dict,
    java_source: str,
) -> dict:
    system_prompt = build_system_prompt(
        "shared/system_base.txt",
        "shared/output_json_rules.txt",
        "tool_registry/enhance_tool_registry_system.txt",
    )

    user_prompt = load_and_render_prompt(
        "tool_registry/enhance_tool_registry_user.txt",
        {
            "class_name": tool_class["class_name"],
            "package_name": tool_class.get("package_name", ""),
            "file_path": tool_class["file_path"],
            "methods_json": json.dumps(tool_class["methods"], ensure_ascii=False, indent=2),
            "java_source": java_source,
        },
    )

    provider = provider.strip().lower()

    if provider == "ollama":
        raw_response = generate_with_ollama(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0,
            timeout=300,
            show_thinking=False,
            think=False,
        )
    elif provider == "deepseek":
        raw_response = generate_with_deepseek(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0,
            timeout=300,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return _safe_parse_json(raw_response)

def _safe_parse_json(raw_text: str) -> dict:
    raw_text = raw_text.strip()

    # 兼容模型把 JSON 包进 ```json ... ```
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Model did not return valid JSON. Raw response:\n{raw_text}")

    json_text = raw_text[start:end + 1]
    return json.loads(json_text)


def _merge_tool_class(base_tool_class: dict, enhanced: dict) -> dict:
    enhanced_methods_by_name = {
        item["method_name"]: item
        for item in enhanced.get("methods", [])
        if "method_name" in item
    }

    merged_methods = []
    for method in base_tool_class.get("methods", []):
        extra = enhanced_methods_by_name.get(method["method_name"], {})
        merged_methods.append({
            **method,
            "method_summary": extra.get("method_summary", ""),
            "usage_suggestion": extra.get("usage_suggestion", ""),
            "reuse_advice": extra.get("reuse_advice", ""),
        })

    return {
        **base_tool_class,
        "class_role": enhanced.get("class_role", ""),
        "class_summary": enhanced.get("class_summary", ""),
        "primary_use_cases": enhanced.get("primary_use_cases", []),
        "methods": merged_methods,
    }


def render_enhanced_tool_registry_markdown(state: dict) -> str:
    lines = [
        "# Enhanced Tool Registry",
        "",
        f"- Root: `{state['project_root']}`",
        f"- Source Tool Registry JSON: `{state['source_tool_registry_json']}`",
        f"- Generated At: `{state['generated_at']}`",
        f"- Provider: `{state['provider']}`",
        f"- Model: `{state['model']}`",
        f"- Enhanced Tool Class Count: `{state['enhanced_tool_class_count']}`",
        f"- Enhanced Method Count: `{state['enhanced_method_count']}`",
        "",
    ]

    for tool_class in state["tool_classes"]:
        lines.append(f"## {tool_class['class_name']}")
        lines.append("")
        lines.append(f"- Package: `{tool_class.get('package_name', '')}`")
        lines.append(f"- File Path: `{tool_class['file_path']}`")
        lines.append(f"- Class Role: `{tool_class.get('class_role', '')}`")
        lines.append(f"- Class Summary: {tool_class.get('class_summary', '')}")

        use_cases = tool_class.get("primary_use_cases", [])
        if use_cases:
            lines.append("- Primary Use Cases:")
            for item in use_cases:
                lines.append(f"  - {item}")

        lines.append("")
        lines.append("### Methods")
        lines.append("")

        for method in tool_class.get("methods", []):
            params_str = ", ".join(
                f"{param['type']} {param['name']}".strip()
                for param in method.get("parameters", [])
            )
            signature = (
                f"{method['visibility']} "
                f"{'static ' if method['is_static'] else ''}"
                f"{method['return_type']} "
                f"{method['method_name']}({params_str})"
            )

            lines.append(f"#### {method['method_name']}")
            lines.append(f"- Signature: `{signature}`")
            lines.append(f"- Method Summary: {method.get('method_summary', '')}")
            lines.append(f"- Usage Suggestion: {method.get('usage_suggestion', '')}")
            lines.append(f"- Reuse Advice: `{method.get('reuse_advice', '')}`")
            lines.append("")

    return "\n".join(lines)