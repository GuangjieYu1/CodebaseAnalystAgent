import argparse
import os

from app.tools.explain_method_tools.explain_method_execution_path import (
    explain_method_execution_path,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        required=True,
        help="Path to the target project",
    )
    parser.add_argument(
        "--file-path",
        required=True,
        help="Relative Java file path inside the target project",
    )
    parser.add_argument(
        "--method-name",
        required=True,
        help="Target method name",
    )
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
    parser.add_argument(
        "--tool-registry-enhanced-json-path",
        default="outputs/tool_registry_enhanced.json",
        help="Path to tool_registry_enhanced.json",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/method_execution_path.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--output-md",
        default="outputs/method_execution_path.md",
        help="Output Markdown path",
    )

    args = parser.parse_args()

    model = args.model
    if model is None:
        if args.provider == "ollama":
            model = "qwen3.5:9b"
        else:
            model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    state = explain_method_execution_path(
        project_root=args.project_root,
        file_path=args.file_path,
        method_name=args.method_name,
        provider=args.provider,
        model=model,
        tool_registry_enhanced_json_path=args.tool_registry_enhanced_json_path,
        output_json=args.output_json,
        output_md=args.output_md,
    )

    print("=== Method Execution Path Built ===")
    print(f"Project Root: {state['project_root']}")
    print(f"Generated At: {state['generated_at']}")
    print(f"File Path: {state['file_path']}")
    print(f"Class Name: {state['class_name']}")
    print(f"Method Name: {state['method_name']}")
    print(f"Provider: {state['provider']}")
    print(f"Model: {state['model']}")
    print(f"Step Count: {len(state.get('steps', []))}")
    print(f"Branch Count: {len(state.get('branches', []))}")
    print(f"JSON: {args.output_json}")
    print(f"MD: {args.output_md}")


if __name__ == "__main__":
    main()