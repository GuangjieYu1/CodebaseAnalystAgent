#!/usr/bin/env python3

from pathlib import Path
import argparse
import re

from app.tools.answer_question import answer_question


def load_questions(questions_file: str) -> list[str]:
    path = Path(questions_file)
    if not path.exists():
        raise ValueError(f"Questions file not found: {questions_file}")

    content = path.read_text(encoding="utf-8")
    questions = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^\d+\.\s+(.*)$", line)
        if match:
            questions.append(match.group(1).strip())

    return questions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, help="Path to the target project")
    parser.add_argument(
        "--questions-file",
        default="examples/sample_questions.md",
        help="Path to the sample questions markdown file",
    )
    parser.add_argument(
        "--output-file",
        default="outputs/sample_answers.md",
        help="Path to save the answers",
    )
    args = parser.parse_args()

    questions = load_questions(args.questions_file)
    output_lines = ["# Sample Question Answers", ""]

    for idx, question in enumerate(questions, start=1):
        print(f"\n=== Question {idx} ===")
        print(question)

        try:
            result = answer_question(args.project_root, question)

            print(f"Conclusion: {result['conclusion']}")
            print("Evidence:")
            for item in result["evidence"]:
                print(f"- {item['file']} | {item['summary']}")
            print("Notes:")
            for note in result["notes"]:
                print(f"- {note}")

            output_lines.append(f"## {idx}. {question}")
            output_lines.append("")
            output_lines.append(f"**Conclusion:** {result['conclusion']}")
            output_lines.append("")
            output_lines.append("**Evidence:**")
            for item in result["evidence"]:
                output_lines.append(f"- `{item['file']}`: {item['summary']}")
            output_lines.append("")
            output_lines.append("**Notes:**")
            for note in result["notes"]:
                output_lines.append(f"- {note}")
            output_lines.append("")

        except Exception as e:
            print(f"Error: {e}")
            output_lines.append(f"## {idx}. {question}")
            output_lines.append("")
            output_lines.append(f"**Error:** {e}")
            output_lines.append("")

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output_lines), encoding="utf-8")

    print(f"\nSaved answers to: {output_path}")


if __name__ == "__main__":
    main()