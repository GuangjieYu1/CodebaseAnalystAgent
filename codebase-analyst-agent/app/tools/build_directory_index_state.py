from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json


CATEGORY_RULES = [
    ("java_test_root", ["/src/test/java", "src/test/java/"]),
    ("java_source_root", ["/src/main/java", "src/main/java/"]),
    ("resources", ["/src/main/resources", "/src/test/resources", "src/main/resources/", "src/test/resources/"]),
    ("test", ["/test", "test/"]),
    ("controller", ["/controller", "controller/"]),
    ("service", ["/service", "service/"]),
    ("repository", ["/repository", "repository/"]),
    ("dao", ["/dao", "dao/"]),
    ("mapper", ["/mapper", "mapper/"]),
    ("domain", ["/domain", "domain/"]),
    ("model", ["/model", "model/"]),
    ("entity", ["/entity", "entity/"]),
    ("dto", ["/dto", "dto/"]),
    ("vo", ["/vo", "vo/"]),
    ("config", ["/config", "config/"]),
    ("util", ["/util", "util/", "/utils", "utils/"]),
]


def build_directory_index_state(
    tree_json_path: str = "outputs/project_tree.json",
    output_json: str = "outputs/directory_index.json",
    output_md: str = "outputs/directory_index.md",
) -> dict:
    tree_path = Path(tree_json_path)
    if not tree_path.exists() or not tree_path.is_file():
        raise ValueError(f"Invalid tree json path: {tree_json_path}")

    tree_state = json.loads(tree_path.read_text(encoding="utf-8"))
    tree_nodes = tree_state.get("tree", [])

    directories: list[dict] = []
    for node in tree_nodes:
        _collect_directories(node, directories)

    state = {
        "project_root": tree_state.get("project_root", ""),
        "source_tree_json": str(tree_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "directory_count": len(directories),
        "directories": directories,
    }

    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(render_directory_index_markdown(state), encoding="utf-8")

    return state



def _collect_directories(node: dict, directories: list[dict]) -> None:
    if node.get("type") != "directory":
        return

    children = node.get("children", [])
    child_dir_count = sum(1 for child in children if child.get("type") == "directory")
    child_file_count = sum(1 for child in children if child.get("type") == "file")
    contains_java_files = any(
        child.get("type") == "file" and child.get("name", "").endswith(".java")
        for child in children
    )

    category, reason = _match_category(node.get("path", ""))

    directories.append(
        {
            "path": node.get("path", ""),
            "name": node.get("name", ""),
            "depth": node.get("depth", 0),
            "parent_path": _parent_path(node.get("path", "")),
            "child_dir_count": child_dir_count,
            "child_file_count": child_file_count,
            "matched_category": category,
            "match_reason": reason,
            "contains_java_files": contains_java_files,
        }
    )

    for child in children:
        _collect_directories(child, directories)



def _match_category(path: str) -> tuple[str, str]:
    normalized = "/" + path.strip("/").lower()
    stripped = path.strip("/").lower()
    last_segment = stripped.split("/")[-1] if stripped else ""

    # 1. 先处理测试源码目录，避免 src/test/.../service 被误判为 service
    if normalized.startswith("/src/test/"):
        if "/src/test/resources" in normalized:
            return "resources", "路径位于 src/test/resources 下"

        # 更具体的 test 目录角色优先
        if last_segment == "controller":
            return "controller", "测试源码目录下的 controller 语境"
        if last_segment == "service":
            return "service", "测试源码目录下的 service 语境"
        if last_segment == "repository":
            return "repository", "测试源码目录下的 repository 语境"
        if last_segment == "dao":
            return "dao", "测试源码目录下的 dao 语境"
        if last_segment == "mapper":
            return "mapper", "测试源码目录下的 mapper 语境"
        if last_segment == "domain":
            return "domain", "测试源码目录下的 domain 语境"
        if last_segment == "model":
            return "model", "测试源码目录下的 model 语境"
        if last_segment == "entity":
            return "entity", "测试源码目录下的 entity 语境"
        if last_segment == "dto":
            return "dto", "测试源码目录下的 dto 语境"
        if last_segment == "vo":
            return "vo", "测试源码目录下的 vo 语境"
        if last_segment == "config":
            return "config", "测试源码目录下的 config 语境"
        if last_segment in {"util", "utils"}:
            return "util", "测试源码目录下的 util 语境"

        if "/src/test/java" in normalized:
            return "java_test_root", "路径位于 src/test/java 下"
        return "test", "路径位于 src/test 下"

    # 2. resources 单独优先处理
    if "/src/main/resources" in normalized or "/src/test/resources" in normalized:
        return "resources", "路径位于 resources 目录下"

    # 3. 再处理具体业务目录角色，让它们优先于 java_source_root
    for category, patterns in CATEGORY_RULES:
        if category in {"java_test_root", "java_source_root", "resources", "test"}:
            continue

        if category == "util" and last_segment == "utils":
            return category, "目录名为 utils"

        if last_segment == category:
            return category, f"目录名为 {category}"

        for pattern in patterns:
            if pattern in normalized:
                return category, f"路径中包含 {pattern.strip('/')}"

    # 4. 再处理 Java 主源码根目录
    if normalized == "/src/main/java" or normalized.endswith("/src/main/java"):
        return "java_source_root", "目录为 src/main/java"

    if "/src/main/java/" in normalized:
        return "java_source_root", "路径位于 src/main/java 下"

    # 5. 最后兜底
    for category, patterns in CATEGORY_RULES:
        if category in {"java_test_root", "java_source_root", "resources", "test"}:
            if last_segment == category:
                return category, f"目录名为 {category}"
            for pattern in patterns:
                if pattern in normalized:
                    return category, f"路径中包含 {pattern.strip('/')}"

    return "unknown", "未命中已知目录分类规则"



def _parent_path(path: str) -> str:
    parts = path.strip("/").split("/")
    if len(parts) <= 1:
        return ""
    return "/".join(parts[:-1])



def render_directory_index_markdown(state: dict) -> str:
    lines = [
        "# Directory Index",
        "",
        f"- Root: `{state['project_root']}`",
        f"- Source Tree JSON: `{state['source_tree_json']}`",
        f"- Generated At: `{state['generated_at']}`",
        f"- Directory Count: `{state['directory_count']}`",
        "",
        "## Directories",
        "",
        "| Path | Depth | Category | Parent Path | Child Dirs | Child Files | Java Files | Reason |",
        "| --- | ---: | --- | --- | ---: | ---: | --- | --- |",
    ]

    for item in state["directories"]:
        lines.append(
            "| {path} | {depth} | {category} | {parent_path} | {child_dirs} | {child_files} | {java_files} | {reason} |".format(
                path=item["path"] or "/",
                depth=item["depth"],
                category=item["matched_category"],
                parent_path=item["parent_path"] or "/",
                child_dirs=item["child_dir_count"],
                child_files=item["child_file_count"],
                java_files="yes" if item["contains_java_files"] else "no",
                reason=item["match_reason"],
            )
        )

    return "\n".join(lines)
