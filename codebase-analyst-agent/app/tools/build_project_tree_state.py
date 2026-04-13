from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json


IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "target",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "out",
}


def build_project_tree_state(
    project_root: str,
    output_json: str = "outputs/project_tree.json",
    output_md: str = "outputs/project_tree.md",
    max_depth: int = 4,
) -> dict:
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    tree = _build_tree(root, root, depth=0, max_depth=max_depth)

    state = {
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "max_depth": max_depth,
        "ignored_dirs": sorted(list(IGNORE_DIRS)),
        "tree": tree,
    }

    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_content = render_project_tree_markdown(state)
    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(md_content, encoding="utf-8")

    return state


def _build_tree(root: Path, current: Path, depth: int, max_depth: int) -> list[dict]:
    if depth > max_depth:
        return []

    result = []

    try:
        children = sorted(
            current.iterdir(),
            key=lambda p: (p.is_file(), p.name.lower())
        )
    except PermissionError:
        return []

    for child in children:
        if _should_ignore_path(child):
            continue

        relative_path = str(child.relative_to(root))
        node = {
            "name": child.name,
            "path": relative_path,
            "type": "directory" if child.is_dir() else "file",
            "depth": depth,
            "children": [],
        }

        if child.is_dir():
            node["children"] = _build_tree(root, child, depth + 1, max_depth)

        result.append(node)

    return result


def _should_ignore_path(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def render_project_tree_markdown(state: dict) -> str:
    lines = [
        "# Project Tree",
        "",
        f"- Root: `{state['project_root']}`",
        f"- Generated At: `{state['generated_at']}`",
        f"- Max Depth: `{state['max_depth']}`",
        "",
        "## Tree",
        "",
    ]

    for node in state["tree"]:
        _append_node_markdown(lines, node, indent=0)

    return "\n".join(lines)


def _append_node_markdown(lines: list[str], node: dict, indent: int) -> None:
    prefix = "  " * indent + "- "
    suffix = "/" if node["type"] == "directory" else ""
    lines.append(f"{prefix}{node['name']}{suffix}")

    for child in node.get("children", []):
        _append_node_markdown(lines, child, indent + 1)