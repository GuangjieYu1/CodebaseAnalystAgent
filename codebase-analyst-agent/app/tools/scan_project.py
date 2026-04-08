"""项目扫描工具。

负责读取目标项目目录，生成浅层目录树，并筛选常见的关键文件。
"""

from pathlib import Path
from app.utils.path_utils import should_ignore_path
from app.utils.tree_utils import build_shallow_tree

# 这组文件名用于粗略识别项目的重要配置文件和入口文件。
KEY_FILE_NAMES = {
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    "application.yml",
    "application.yaml",
    "application.properties",
}


def scan_project(project_root: str, max_depth: int = 2) -> dict:
    # 规范化项目根目录路径，并校验它是否真实存在且为目录。
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    # 生成限定深度的目录树，便于快速了解项目顶层结构。
    tree = build_shallow_tree(root, max_depth=max_depth)

    # 遍历项目文件，筛掉无需关注的路径后收集候选关键文件。
    key_files = []
    for path in root.rglob("*"):
        if should_ignore_path(path):
            continue
        if path.is_file() and path.name in KEY_FILE_NAMES:
            key_files.append(str(path.relative_to(root)))

    # 返回统一的扫描结果，供 CLI 或上层服务继续使用。
    return {
        "project_root": str(root),
        "tree": tree,
        "key_files": sorted(key_files),
    }
