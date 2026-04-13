from pathlib import Path
import re


def summarize_file(project_root: str, file_path: str) -> dict:
    root = Path(project_root).resolve()
    target = (root / file_path).resolve()

    if not target.exists() or not target.is_file():
        raise ValueError(f"Invalid file path: {file_path}")

    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        raise ValueError(f"Failed to read file: {file_path}, error: {e}")

    suffix = target.suffix.lower()
    file_type = _detect_file_type(suffix)

    imports = []
    key_symbols = []
    module_or_class_name = target.stem
    notes = []

    if file_type == "python":
        imports = _extract_python_imports(content)
        classes = _extract_python_classes(content)
        functions = _extract_python_functions(content)

        if classes:
            module_or_class_name = classes[0]

        key_symbols = classes + functions
        summary = _build_python_summary(target.name, classes, functions)
    else:
        summary = f"该文件类型暂未做深入解析，当前只支持基础识别。"

    return {
        "file_path": str(target.relative_to(root)),
        "file_type": file_type,
        "module_or_class_name": module_or_class_name,
        "imports_or_dependencies": imports,
        "key_symbols": key_symbols,
        "summary": summary,
        "notes": notes,
    }


def _detect_file_type(suffix: str) -> str:
    mapping = {
        ".py": "python",
        ".java": "java",
        ".md": "markdown",
        ".txt": "text",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
    }
    return mapping.get(suffix, "unknown")


def _extract_python_imports(content: str) -> list[str]:
    results = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("import ") or line.startswith("from "):
            results.append(line)
    return results


def _extract_python_classes(content: str) -> list[str]:
    return re.findall(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", content, flags=re.MULTILINE)


def _extract_python_functions(content: str) -> list[str]:
    return re.findall(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", content, flags=re.MULTILINE)


def _build_python_summary(file_name: str, classes: list[str], functions: list[str]) -> str:
    lower_name = file_name.lower()

    if lower_name == "main.py":
        return "该文件看起来像项目入口文件，可能负责解析输入参数并调用核心流程。"
    if lower_name == "config.py":
        return "该文件看起来负责项目配置管理，可能处理环境变量或运行参数。"
    if lower_name == "scan_project.py":
        return "该文件看起来负责扫描项目目录、提取目录树和关键文件信息。"
    if lower_name == "detect_stack.py":
        return "该文件看起来负责识别项目技术栈、配置文件和容器化线索。"
    if lower_name == "find_key_files.py":
        return "该文件看起来负责根据问题推荐优先阅读的关键文件。"

    parts = []
    if classes:
        parts.append(f"定义了类：{', '.join(classes)}")
    if functions:
        parts.append(f"定义了函数：{', '.join(functions)}")

    if parts:
        return "该文件是一个 Python 模块，" + "；".join(parts) + "。"

    return "该文件是一个 Python 模块，但当前未提取到明显的类或函数定义。"