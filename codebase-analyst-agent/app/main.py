import argparse
from app.tools.build_project_tree_state import build_project_tree_state
from app.tools.build_directory_index_state import build_directory_index_state
from app.tools.build_folder_semantics_state import build_folder_semantics_state
from app.tools.build_tool_registry_state import build_tool_registry_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, help="Path to the target project")
    parser.add_argument("--max-depth", type=int, default=8, help="Max directory depth")
    args = parser.parse_args()

    tree_state = build_project_tree_state(
        project_root=args.project_root,
        output_json="outputs/project_tree.json",
        output_md="outputs/project_tree.md",
        max_depth=args.max_depth,
    )

    directory_index_state = build_directory_index_state(
        tree_json_path="outputs/project_tree.json",
        output_json="outputs/directory_index.json",
        output_md="outputs/directory_index.md",
    )

    folder_semantics_state = build_folder_semantics_state(
        directory_index_json_path="outputs/directory_index.json",
        output_json="outputs/folder_semantics.json",
        output_md="outputs/folder_semantics.md",
    )

    tool_registry_state = build_tool_registry_state(
        project_root=args.project_root,
        directory_index_json_path="outputs/directory_index.json",
        output_json="outputs/tool_registry.json",
        output_md="outputs/tool_registry.md",
    )

    print("=== Project Tree State Built ===")
    print(f"Project Root: {tree_state['project_root']}")
    print(f"Generated At: {tree_state['generated_at']}")
    print("JSON: outputs/project_tree.json")
    print("MD: outputs/project_tree.md")

    print("\n=== Directory Index State Built ===")
    print(f"Project Root: {directory_index_state['project_root']}")
    print(f"Generated At: {directory_index_state['generated_at']}")
    print(f"Directory Count: {directory_index_state['directory_count']}")
    print("JSON: outputs/directory_index.json")
    print("MD: outputs/directory_index.md")

    print("\n=== Folder Semantics State Built ===")
    print(f"Project Root: {folder_semantics_state['project_root']}")
    print(f"Generated At: {folder_semantics_state['generated_at']}")
    print(f"Semantic Count: {folder_semantics_state['semantic_count']}")
    print("JSON: outputs/folder_semantics.json")
    print("MD: outputs/folder_semantics.md")

    print("\n=== Tool Registry State Built ===")
    print(f"Project Root: {tool_registry_state['project_root']}")
    print(f"Generated At: {tool_registry_state['generated_at']}")
    print(f"Tool Class Count: {tool_registry_state['tool_class_count']}")
    print(f"Method Count: {tool_registry_state['method_count']}")
    print("JSON: outputs/tool_registry.json")
    print("MD: outputs/tool_registry.md")


if __name__ == "__main__":
    main()