import argparse
import os

from app.tools.enhance_tool_registry_with_llm import enhance_tool_registry_with_llm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, help="Path to the target project")
    parser.add_argument(
        "--provider",
        default="ollama",
        choices=["ollama", "deepseek"],
        help="LLM provider",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name. If omitted, use provider-specific default.",
    )
    parser.add_argument(
        "--target-class-name",
        default="OrderUtils",
        help="Only enhance one target class",
    )
    args = parser.parse_args()

    provider = args.provider
    model = args.model

    if model is None:
        if provider == "ollama":
            model = "qwen3.5:9b"
        elif provider == "deepseek":
            model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    state = enhance_tool_registry_with_llm(
        project_root=args.project_root,
        tool_registry_json_path="outputs/tool_registry.json",
        output_json="outputs/tool_registry_enhanced.json",
        output_md="outputs/tool_registry_enhanced.md",
        provider=provider,
        model=model,
        target_class_name=args.target_class_name,
    )

    print("=== Enhanced Tool Registry Built ===")
    print(f"Project Root: {state['project_root']}")
    print(f"Generated At: {state['generated_at']}")
    print(f"Provider: {state['provider']}")
    print(f"Model: {state['model']}")
    print(f"Enhanced Tool Class Count: {state['enhanced_tool_class_count']}")
    print(f"Enhanced Method Count: {state['enhanced_method_count']}")
    print("JSON: outputs/tool_registry_enhanced.json")
    print("MD: outputs/tool_registry_enhanced.md")


if __name__ == "__main__":
    main()