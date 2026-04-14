from __future__ import annotations

import argparse
import os

from app.tools.build_project_tree_state import build_project_tree_state
from app.tools.build_directory_index_state import build_directory_index_state
from app.tools.build_folder_semantics_state import build_folder_semantics_state
from app.tools.build_tool_registry_state import build_tool_registry_state
from app.tools.enhance_tool_registry_with_llm import enhance_tool_registry_with_llm
from app.tools.recommend_tool_reuse import recommend_tool_reuse


def run_local_states(project_root: str, max_depth: int) -> None:
    print("=== Running Local State Pipeline ===")

    tree_state = build_project_tree_state(
        project_root=project_root,
        output_json="outputs/project_tree.json",
        output_md="outputs/project_tree.md",
        max_depth=max_depth,
    )
    print(f"[OK] project_tree -> outputs/project_tree.json / outputs/project_tree.md")
    print(f"     root={tree_state['project_root']}")

    directory_index_state = build_directory_index_state(
        tree_json_path="outputs/project_tree.json",
        output_json="outputs/directory_index.json",
        output_md="outputs/directory_index.md",
    )
    print(f"[OK] directory_index -> outputs/directory_index.json / outputs/directory_index.md")
    print(f"     directory_count={directory_index_state['directory_count']}")

    folder_semantics_state = build_folder_semantics_state(
        directory_index_json_path="outputs/directory_index.json",
        output_json="outputs/folder_semantics.json",
        output_md="outputs/folder_semantics.md",
    )
    print(f"[OK] folder_semantics -> outputs/folder_semantics.json / outputs/folder_semantics.md")
    print(f"     semantic_count={folder_semantics_state['semantic_count']}")

    tool_registry_state = build_tool_registry_state(
        project_root=project_root,
        directory_index_json_path="outputs/directory_index.json",
        output_json="outputs/tool_registry.json",
        output_md="outputs/tool_registry.md",
    )
    print(f"[OK] tool_registry -> outputs/tool_registry.json / outputs/tool_registry.md")
    print(f"     tool_class_count={tool_registry_state['tool_class_count']}, method_count={tool_registry_state['method_count']}")


def run_llm_steps(
    project_root: str,
    provider: str,
    model: str | None,
    target_class_name: str,
    query: str | None,
    top_k: int,
) -> None:
    print("=== Running LLM Pipeline ===")

    resolved_model = resolve_model(provider=provider, model=model)

    enhanced_state = enhance_tool_registry_with_llm(
        project_root=project_root,
        tool_registry_json_path="outputs/tool_registry.json",
        output_json="outputs/tool_registry_enhanced.json",
        output_md="outputs/tool_registry_enhanced.md",
        provider=provider,
        model=resolved_model,
        target_class_name=target_class_name,
    )
    print(f"[OK] tool_registry_enhanced -> outputs/tool_registry_enhanced.json / outputs/tool_registry_enhanced.md")
    print(f"     provider={enhanced_state['provider']}, model={enhanced_state['model']}, enhanced_tool_class_count={enhanced_state['enhanced_tool_class_count']}")

    if query:
        recommendation_state = recommend_tool_reuse(
            project_root=project_root,
            query=query,
            enhanced_registry_json_path="outputs/tool_registry_enhanced.json",
            output_json="outputs/tool_reuse_recommendation.json",
            output_md="outputs/tool_reuse_recommendation.md",
            provider=provider,
            model=resolved_model,
            top_k=top_k,
        )
        print(f"[OK] tool_reuse_recommendation -> outputs/tool_reuse_recommendation.json / outputs/tool_reuse_recommendation.md")
        print(f"     query={recommendation_state['query']}")
    else:
        print("[SKIP] recommend_tool_reuse")
        print("       未传 --query，因此只执行增强步骤，不执行复用推荐。")


def resolve_model(provider: str, model: str | None) -> str:
    if model:
        return model

    if provider == "ollama":
        return "qwen3.5:9b"

    return os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, help="Path to the target project")

    parser.add_argument(
        "--stage",
        required=True,
        choices=["local_states", "llm_steps", "all"],
        help="Run local states, llm steps, or all",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Max depth for project tree scan",
    )

    parser.add_argument(
        "--provider",
        default="deepseek",
        choices=["ollama", "deepseek"],
        help="LLM provider for llm_steps/all",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Model name. If omitted, provider-specific default will be used.",
    )

    parser.add_argument(
        "--target-class-name",
        default="OrderUtils",
        help="Target class for tool registry enhancement",
    )

    parser.add_argument(
        "--query",
        default=None,
        help="Query for recommend_tool_reuse. If omitted, llm_steps will only run enhancement.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=2,
        help="Top candidate methods for recommend_tool_reuse",
    )

    args = parser.parse_args()

    if args.stage in {"local_states", "all"}:
        run_local_states(
            project_root=args.project_root,
            max_depth=args.max_depth,
        )

    if args.stage in {"llm_steps", "all"}:
        run_llm_steps(
            project_root=args.project_root,
            provider=args.provider,
            model=args.model,
            target_class_name=args.target_class_name,
            query=args.query,
            top_k=args.top_k,
        )


if __name__ == "__main__":
    main()