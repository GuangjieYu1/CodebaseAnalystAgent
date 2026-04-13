from __future__ import annotations

from pathlib import Path


PROMPT_ROOT = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(relative_path: str) -> str:
    """
    从 app/prompts 下读取指定 prompt 文件。

    示例:
        load_prompt("shared/system_base.txt")
        load_prompt("tool_registry/enhance_tool_registry_user.txt")
    """
    path = PROMPT_ROOT / relative_path
    if not path.exists() or not path.is_file():
        raise ValueError(f"Prompt file not found: {relative_path}")
    return path.read_text(encoding="utf-8")


def render_prompt(template: str, variables: dict[str, str]) -> str:
    """
    用 variables 替换模板中的 {{key}} 占位符。
    未提供的占位符保持原样，方便后续排查问题。
    """
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def load_and_render_prompt(relative_path: str, variables: dict[str, str]) -> str:
    """
    读取并渲染 prompt。
    """
    template = load_prompt(relative_path)
    return render_prompt(template, variables)


def build_system_prompt(*relative_paths: str) -> str:
    """
    按顺序加载多个 system prompt 文件，并用空行拼接。
    适合把 shared + task-specific prompt 合并成一个 system prompt。
    """
    contents = [load_prompt(path).strip() for path in relative_paths]
    return "\n\n".join(content for content in contents if content)