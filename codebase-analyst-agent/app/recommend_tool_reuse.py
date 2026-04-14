import argparse
import os

from app.tools.recommend_tool_reuse import recommend_tool_reuse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, help="Path to the target project")
    parser.add_argument("--query", required=True, help="Tool reuse query")
    parser.add_argument(
        "--provider",
        default="deepseek",
        choices=["ollama", "deepseek"],
        help="LLM provider",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name. If omitted, use provider-specific default.",
    )
    parser.add_argument("--top-k", type=int, default=2, help="Top candidate methods")

    args = parser.parse_args()

    model = args.model
    if model is None:
        if args.provider == "ollama":
            model = "qwen3.5:9b"
        else:
            model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    state = recommend_tool_reuse(
        project_root=args.project_root,
        query=args.query,
        enhanced_registry_json_path="outputs/tool_registry_enhanced.json",
        output_json="outputs/tool_reuse_recommendation.json",
        output_md="outputs/tool_reuse_recommendation.md",
        provider=args.provider,
        model=model,
        top_k=args.top_k,
    )

    recommendation = state["recommendation"]
    final_recommendation = recommendation.get("final_recommendation", {})
    alternatives = recommendation.get("alternatives", [])
    ranking = recommendation.get("ranking", [])

    print("=== Tool Reuse Recommendation Built ===")
    print(f"Project Root: {state['project_root']}")
    print(f"Generated At: {state['generated_at']}")
    print(f"Provider: {state['provider']}")
    print(f"Model: {state['model']}")
    print(f"Query: {state['query']}")
    print(f"Candidate Count: {state['candidate_count']}")
    print(f"Decision: {recommendation.get('decision', '')}")
    print(
        f"Final Recommendation: "
        f"{final_recommendation.get('recommended_class', '')}."
        f"{final_recommendation.get('recommended_method', '')}"
    )
    print(f"Alternative Count: {len(alternatives)}")
    print(f"Ranking Count: {len(ranking)}")
    print("JSON: outputs/tool_reuse_recommendation.json")
    print("MD: outputs/tool_reuse_recommendation.md")

if __name__ == "__main__":
    main()