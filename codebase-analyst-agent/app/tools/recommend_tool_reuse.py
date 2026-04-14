from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json

from app.services.prompt_loader import build_system_prompt, load_and_render_prompt
from app.services.llm_client import generate_with_ollama, generate_with_deepseek


def recommend_tool_reuse(
    project_root: str,
    query: str,
    enhanced_registry_json_path: str = "outputs/tool_registry_enhanced.json",
    output_json: str = "outputs/tool_reuse_recommendation.json",
    output_md: str = "outputs/tool_reuse_recommendation.md",
    provider: str = "deepseek",
    model: str = "deepseek-chat",
    top_k: int = 2,
) -> dict:
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    if not query or not query.strip():
        raise ValueError("Query must not be empty.")

    registry_path = Path(enhanced_registry_json_path)
    if not registry_path.exists() or not registry_path.is_file():
        raise ValueError(f"Invalid enhanced tool registry path: {enhanced_registry_json_path}")

    enhanced_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    flat_methods = _flatten_methods(enhanced_registry)

    candidates = _prepare_candidates(methods=flat_methods)
    recommendation = _llm_recommend(
        query=query,
        candidates=candidates,
        provider=provider,
        model=model,
    )

    state = {
        "project_root": str(root),
        "source_tool_registry_enhanced_json": str(registry_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "provider": provider,
        "model": model,
        "query": query,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "recommendation": recommendation,
    }

    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(render_tool_reuse_markdown(state), encoding="utf-8")

    return state


def _flatten_methods(enhanced_registry: dict) -> list[dict]:
    methods = []

    for tool_class in enhanced_registry.get("tool_classes", []):
        class_name = tool_class.get("class_name", "")
        class_summary = tool_class.get("class_summary", "")
        primary_use_cases = tool_class.get("primary_use_cases", [])
        file_path = tool_class.get("file_path", "")

        for method in tool_class.get("methods", []):
            methods.append({
                "class_name": class_name,
                "file_path": file_path,
                "class_summary": class_summary,
                "primary_use_cases": primary_use_cases,
                "method_name": method.get("method_name", ""),
                "parameters": method.get("parameters", []),
                "return_type": method.get("return_type", ""),
                "visibility": method.get("visibility", ""),
                "is_static": method.get("is_static", False),
                "method_summary": method.get("method_summary", ""),
                "usage_suggestion": method.get("usage_suggestion", ""),
                "reuse_advice": method.get("reuse_advice", ""),
            })

    return methods


def _prepare_candidates(methods: list[dict]) -> list[dict]:
    candidates = []

    for method in methods:
        candidate = dict(method)
        candidate.pop("score", None)
        candidates.append(candidate)

    candidates.sort(key=lambda x: (x.get("class_name", ""), x.get("method_name", "")))
    return candidates


def _llm_recommend(query: str, candidates: list[dict], provider: str, model: str) -> dict:
    if not candidates:
        return {
            "query": query,
            "decision": "create_new_tool",
            "recommended_class": "",
            "recommended_method": "",
            "reason": "当前增强工具注册表中没有可供判断的候选方法，建议新建工具。",
            "usage_suggestion": "建议新增独立工具类或扩展现有工具目录。",
            "reuse_advice": "create_new_tool",
        }

    system_prompt = build_system_prompt(
        "shared/system_base.txt",
        "shared/output_json_rules.txt",
        "tool_reuse/recommend_tool_reuse_system.txt",
    )

    user_prompt = load_and_render_prompt(
        "tool_reuse/recommend_tool_reuse_user.txt",
        {
            "query": query,
            "candidate_methods_json": json.dumps(candidates, ensure_ascii=False, indent=2),
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

    parsed = _safe_parse_json(raw_response)
    return _normalize_recommendation(parsed, query=query)


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


def _normalize_recommendation(parsed: dict, query: str) -> dict:
    allowed_decisions = {"reuse_existing", "reuse_with_wrapper", "create_new_tool"}

    decision = str(parsed.get("decision", "")).strip()
    if decision not in allowed_decisions:
        decision = "create_new_tool"

    final_recommendation = parsed.get("final_recommendation") or {}
    if not isinstance(final_recommendation, dict):
        final_recommendation = {}

    alternatives = parsed.get("alternatives") or []
    if not isinstance(alternatives, list):
        alternatives = []
    alternatives = [item for item in alternatives if isinstance(item, dict)][:1]

    ranking = parsed.get("ranking") or []
    if not isinstance(ranking, list):
        ranking = []
    normalized_ranking = []
    for item in ranking[:2]:
        if not isinstance(item, dict):
            continue
        normalized_ranking.append({
            "class_name": item.get("class_name", ""),
            "method_name": item.get("method_name", ""),
            "rank": item.get("rank", len(normalized_ranking) + 1),
            "reason": item.get("reason", ""),
        })

    if decision == "create_new_tool":
        final_recommendation = {
            "recommended_class": "",
            "recommended_method": "",
            "reason": final_recommendation.get("reason", parsed.get("reason", "")),
            "usage_suggestion": final_recommendation.get("usage_suggestion", parsed.get("usage_suggestion", "")),
            "reuse_advice": "create_new_tool",
        }
    else:
        final_recommendation = {
            "recommended_class": final_recommendation.get("recommended_class", ""),
            "recommended_method": final_recommendation.get("recommended_method", ""),
            "reason": final_recommendation.get("reason", parsed.get("reason", "")),
            "usage_suggestion": final_recommendation.get("usage_suggestion", parsed.get("usage_suggestion", "")),
            "reuse_advice": final_recommendation.get("reuse_advice", parsed.get("reuse_advice", "")),
        }

    return {
        "query": parsed.get("query", query),
        "decision": decision,
        "final_recommendation": final_recommendation,
        "alternatives": [
            {
                "recommended_class": item.get("recommended_class", ""),
                "recommended_method": item.get("recommended_method", ""),
                "reason": item.get("reason", ""),
                "usage_suggestion": item.get("usage_suggestion", ""),
                "reuse_advice": item.get("reuse_advice", ""),
            }
            for item in alternatives
        ],
        "ranking": normalized_ranking,
    }


def render_tool_reuse_markdown(state: dict) -> str:
    recommendation = state["recommendation"]
    final_recommendation = recommendation.get("final_recommendation", {})
    alternatives = recommendation.get("alternatives", [])
    ranking = recommendation.get("ranking", [])
    display_candidates = state["candidates"][:2]

    lines = [
        "# Tool Reuse Recommendation",
        "",
        f"- Generated At: `{state['generated_at']}`",
        f"- Query: `{state['query']}`",
        f"- Provider: `{state['provider']}`",
        f"- Model: `{state['model']}`",
        f"- Candidate Count: `{state['candidate_count']}`",
        "",
        "## Final Recommendation",
        "",
        f"- Decision: `{recommendation['decision']}`",
        f"- Recommended Class: `{final_recommendation.get('recommended_class', '')}`",
        f"- Recommended Method: `{final_recommendation.get('recommended_method', '')}`",
        f"- Reason: {final_recommendation.get('reason', '')}",
        f"- Usage Suggestion: {final_recommendation.get('usage_suggestion', '')}",
        f"- Reuse Advice: `{final_recommendation.get('reuse_advice', '')}`",
        "",
    ]

    lines.append("## Alternatives")
    lines.append("")
    if not alternatives:
        lines.append("- No alternatives.")
        lines.append("")
    else:
        for item in alternatives:
            lines.extend([
                f"### {item.get('recommended_class', '')}.{item.get('recommended_method', '')}",
                "",
                f"- Reason: {item.get('reason', '')}",
                f"- Usage Suggestion: {item.get('usage_suggestion', '')}",
                f"- Reuse Advice: `{item.get('reuse_advice', '')}`",
                "",
            ])

    lines.append("## Ranking")
    lines.append("")
    if not ranking:
        lines.append("- No ranking returned.")
        lines.append("")
    else:
        for item in ranking:
            lines.extend([
                f"### Rank {item.get('rank', '')}: {item.get('class_name', '')}.{item.get('method_name', '')}",
                "",
                f"- Reason: {item.get('reason', '')}",
                "",
            ])

    lines.append("## Candidate Methods")
    lines.append("")

    if not display_candidates:
        lines.append("- No candidates found.")
        lines.append("")
        return "\n".join(lines)

    for candidate in display_candidates:
        params_str = ", ".join(
            f"{param.get('type', '')} {param.get('name', '')}".strip()
            for param in candidate.get("parameters", [])
        )
        signature = (
            f"{candidate.get('visibility', '')} "
            f"{'static ' if candidate.get('is_static', False) else ''}"
            f"{candidate.get('return_type', '')} "
            f"{candidate.get('method_name', '')}({params_str})"
        ).strip()

        lines.extend([
            f"### {candidate['class_name']}.{candidate['method_name']}",
            "",
            f"- File Path: `{candidate['file_path']}`",
            f"- Signature: `{signature}`",
            f"- Class Summary: {candidate.get('class_summary', '')}",
            f"- Method Summary: {candidate.get('method_summary', '')}",
            f"- Usage Suggestion: {candidate.get('usage_suggestion', '')}",
            f"- Reuse Advice: `{candidate.get('reuse_advice', '')}`",
            "",
        ])

    return "\n".join(lines)