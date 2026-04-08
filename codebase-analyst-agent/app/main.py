import argparse
from app.tools.scan_project import scan_project
from app.tools.detect_stack import detect_stack
from app.tools.find_key_files import find_key_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, help="Path to the target project")
    parser.add_argument("--question", required=False, default="", help="Question about the project")
    args = parser.parse_args()

    scan_result = scan_project(args.project_root)
    stack_result = detect_stack(args.project_root)
    key_file_result = find_key_files(args.project_root, args.question)

    print("=== Project Scan Result ===")
    print(f"Project Root: {scan_result['project_root']}")

    print("\nTop-Level Tree:")
    for line in scan_result["tree"]:
        print(line)

    print("\nCandidate Key Files:")
    for item in scan_result["key_files"]:
        print(f"- {item}")

    print("\n=== Stack Detection Result ===")
    print(f"Languages: {stack_result['languages']}")
    print(f"Build Tool: {stack_result['build_tool']}")
    print(f"Frameworks: {stack_result['frameworks']}")
    print(f"Config Files: {stack_result['config_files']}")
    print(f"Containerization: {stack_result['containerization']}")

    print("\n=== Recommended Files ===")
    print(f"Question: {args.question}")
    for item in key_file_result:
        print(f"- {item['file']} | {item['reason']}")


if __name__ == "__main__":
    main()