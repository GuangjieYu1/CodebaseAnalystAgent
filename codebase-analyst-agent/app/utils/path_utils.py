"""路径处理工具。

用于判断某个路径是否应该在项目扫描过程中被忽略。
"""

from pathlib import Path

# 这些目录通常是依赖、构建产物、缓存或编辑器配置，不需要纳入代码分析。
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


def should_ignore_path(path: Path) -> bool:
    # 只要路径的任意一层目录命中了忽略名单，就跳过该路径。
    return any(part in IGNORE_DIRS for part in path.parts)
