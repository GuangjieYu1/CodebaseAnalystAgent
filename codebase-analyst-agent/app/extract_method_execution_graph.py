import argparse

from app.tools.explain_method_tools.extract_method_execution_graph import (
    extract_method_execution_graph,
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
        "--tree-depth",
        type=int,
        default=1,
        help="Recursive call tracing depth. 1 means only current method calls, 3 means trace 3 levels.",
    )
    parser.add_argument(
        "--tool-registry-enhanced-json-path",
        default="outputs/tool_registry_enhanced.json",
        help="Path to tool_registry_enhanced.json",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/method_execution_graph.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--output-md",
        default="outputs/method_execution_path.md",
        help="Output Markdown path",
    )
    parser.add_argument(
        "--llm-provider",
        default="heuristic",
        choices=["heuristic", "ollama", "deepseek"],
        help="Business flow generation provider.",
    )
    parser.add_argument(
        "--llm-model",
        default="",
        help="Model name for the selected provider. Empty means use provider default.",
    )
    parser.add_argument(
        "--deepseek-api-key",
        default="",
        help="Optional DeepSeek API key. If omitted, falls back to DEEPSEEK_API_KEY env var.",
    )

    args = parser.parse_args()

    state = extract_method_execution_graph(
        project_root=args.project_root,
        file_path=args.file_path,
        method_name=args.method_name,
        tree_depth=args.tree_depth,
        tool_registry_enhanced_json_path=args.tool_registry_enhanced_json_path,
        output_json=args.output_json,
        output_md=args.output_md,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        deepseek_api_key=args.deepseek_api_key,
    )

    print("=== Method Execution Graph Built ===")
    print(f"Project Root: {state['project_root']}")
    print(f"Generated At: {state['generated_at']}")
    print(f"File Path: {state['file_path']}")
    print(f"Package Name: {state['package_name']}")
    print(f"Class Name: {state['class_name']}")
    print(f"Method Name: {state['method_name']}")
    print(f"Method Signature: {state['method_signature']}")
    print(f"Tree Depth: {state['tree_depth']}")
    print(f"Tree Node Count: {state['tree_stats']['node_count']}")
    print(f"Call Step Count: {state['stats']['call_step_count']}")
    print(f"Branch Count: {state['stats']['branch_count']}")
    print(f"Internal Method Count: {state['stats']['internal_method_count']}")
    print(f"Tool Method Count: {state['stats']['tool_method_count']}")
    print(f"Library Value Method Count: {state['stats']['library_value_method_count']}")
    print(f"External Interface Call Count: {state['stats']['external_interface_call_count']}")
    print(f"External Static Method Count: {state['stats']['external_static_method_count']}")
    print(f"External Instance Method Count: {state['stats']['external_instance_method_count']}")
    print(f"Unknown Call Count: {state['stats']['unknown_call_count']}")
    main_flow_view = state.get("main_flow_view", {})
    if main_flow_view:
        print(f"Main Flow Visible Call Step Count: {main_flow_view.get('visible_call_step_count', 0)}")
        print(f"Main Flow Hidden Call Step Count: {main_flow_view.get('hidden_call_step_count', 0)}")

    business_flow_view = state.get("business_flow_view", {})
    if business_flow_view:
        print(f"Business Flow Step Count: {business_flow_view.get('business_step_count', 0)}")
        print(f"Business Flow Generation Mode: {business_flow_view.get('generation_mode', '')}")
        if business_flow_view.get('llm_provider'):
            print(f"Business Flow LLM Provider: {business_flow_view.get('llm_provider', '')}")
        if business_flow_view.get('llm_model'):
            print(f"Business Flow LLM Model: {business_flow_view.get('llm_model', '')}")
        if business_flow_view.get('fallback_reason'):
            print(f"Business Flow Fallback Reason: {business_flow_view.get('fallback_reason', '')}")
    print(f"JSON: {args.output_json}")
    print(f"Markdown: {args.output_md}")


if __name__ == "__main__":
    main()