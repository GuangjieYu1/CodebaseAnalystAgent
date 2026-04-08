"""目录树构建工具。

用于生成指定目录的浅层树形结构，方便快速查看项目布局。
"""

from pathlib import Path
from app.utils.path_utils import should_ignore_path


def build_shallow_tree(root: Path, max_depth: int = 2) -> list[str]:
    # 按行保存目录树的文本结果，供上层直接打印或展示。
    lines: list[str] = []

    def walk(current: Path, depth: int):
        # 超过限定深度后停止递归，避免输出过深的目录结构。
        if depth > max_depth:
            return

        try:
            # 目录优先、文件在后，并按名称排序，保证输出稳定且更易阅读。
            children = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            # 没有权限访问的目录直接跳过，避免扫描中断。
            return

        for child in children:
            # 跳过不需要参与分析的依赖目录、缓存目录和构建产物。
            if should_ignore_path(child):
                continue

            relative = child.relative_to(root)
            indent = "  " * depth
            # 目录名后补 "/"，便于和普通文件区分。
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{indent}{relative.name}{suffix}")

            if child.is_dir():
                # 继续向下遍历子目录，构建下一层树结构。
                walk(child, depth + 1)

    # 从根目录开始递归构建整棵浅层目录树。
    walk(root, 0)
    return lines
