"""关键文件推荐工具。

根据用户问题，从项目里挑出最值得优先阅读的文件，并给出推荐原因。

示例:
    question = "项目入口在哪？"
    可能优先返回:
    - app/main.py
    - app/agent.py

    question = "配置文件在哪里？"
    可能优先返回:
    - .env.example
    - app/config.py
    - requirements.txt
"""

from pathlib import Path
from app.utils.path_utils import should_ignore_path


# 默认问题为空时，优先返回这批“项目总览型”文件。
# 这些文件通常能帮助你快速判断项目怎么启动、怎么配置、主流程在哪里。
DEFAULT_PRIORITY_FILES = [
    "README.md",
    "requirements.txt",
    ".env.example",
    "app/main.py",
    "app/agent.py",
    "app/config.py",
]


# 针对常见提问场景建立简单规则:
# 只要问题里包含某些关键词，就优先推荐对应路径，并附上推荐原因。
# 例如:
# - "入口在哪" 会命中 ["入口", "启动", "main", "run", "开始"]
# - "怎么配置环境变量" 会命中 ["配置", "环境变量", "env", "config"]
QUESTION_RULES = [
    {
        "keywords": ["入口", "启动", "main", "run", "开始"],
        "paths": ["app/main.py", "app/agent.py"],
        "reason": "这些文件可能定义了项目入口或主执行流程",
    },
    {
        "keywords": ["配置", "环境变量", "env", "config"],
        "paths": [".env.example", "app/config.py", "requirements.txt"],
        "reason": "这些文件可能包含配置、环境变量或依赖信息",
    },
    {
        "keywords": ["工具", "扫描", "检测", "stack", "scan", "tool"],
        "paths": ["app/tools/", "app/tools/scan_project.py", "app/tools/detect_stack.py"],
        "reason": "这些文件可能定义了工具能力或扫描逻辑",
    },
    {
        "keywords": ["提示词", "prompt", "总结", "问答"],
        "paths": ["app/prompts/", "app/prompts/system_prompt.txt", "app/prompts/answer_question.txt"],
        "reason": "这些文件可能定义了提示词或问答模板",
    },
    {
        "keywords": ["测试", "test", "单测"],
        "paths": ["tests/", "tests/test_detect_stack.py", "tests/test_find_key_files.py"],
        "reason": "这些文件可能与测试和验证有关",
    },
    {
        "keywords": ["agent", "流程", "工作流"],
        "paths": ["app/agent.py", "app/services/answer_service.py"],
        "reason": "这些文件可能定义了 Agent 主流程或回答服务",
    },
]


def _normalize_question(question: str | None) -> str:
    # 统一去掉首尾空白并转成小写，减少后续关键词匹配的分支处理。
    return (question or "").strip().lower()


def _collect_all_files(project_root: Path) -> list[str]:
    # 扫描项目下的全部文件，并跳过依赖目录、缓存目录和构建产物。
    files = []
    for path in project_root.rglob("*"):
        if should_ignore_path(path):
            continue
        if path.is_file():
            files.append(str(path.relative_to(project_root)))
    return sorted(files)


def _path_exists(candidate: str, all_files: list[str]) -> bool:
    # 兼容两种候选目标:
    # 1. 普通文件，如 "app/main.py"
    # 2. 目录前缀，如 "app/tools/"，表示该目录下有任意文件即可算命中
    if candidate.endswith("/"):
        prefix = candidate
        return any(file.startswith(prefix) for file in all_files)
    return candidate in all_files


def find_key_files(project_root: str, question: str | None = None, limit: int = 8) -> list[dict]:
    # 先校验项目根目录，避免对无效路径做扫描。
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    # all_files 是后续所有推荐判断的基础数据。
    all_files = _collect_all_files(root)
    q = _normalize_question(question)

    results: list[dict] = []
    seen: set[str] = set()

    def add_result(file_path: str, reason: str):
        # 目录规则会写成 "app/tools/"，对外返回时统一去掉尾部 "/"。
        normalized_path = file_path.rstrip("/")
        # 已经加入过的路径不重复返回。
        if normalized_path in seen:
            return
        # 规则里写了路径，不代表项目里一定存在；不存在就跳过。
        if not _path_exists(file_path, all_files):
            return
        seen.add(normalized_path)
        results.append({
            "file": normalized_path,
            "reason": reason,
        })

    if not q:
        # 用户没有给具体问题时，返回一组通用且信息密度高的默认文件。
        for candidate in DEFAULT_PRIORITY_FILES:
            add_result(candidate, "默认优先文件，适合快速理解项目")
        return results[:limit]

    # 第一阶段: 用预定义规则做语义较粗的匹配。
    # 例如 question = "扫描逻辑在哪" 时，会优先推荐 app/tools/ 相关文件。
    for rule in QUESTION_RULES:
        if any(keyword in q for keyword in rule["keywords"]):
            for candidate in rule["paths"]:
                add_result(candidate, rule["reason"])

    # 第二阶段 fallback: 如果规则命中不够，再尝试把问题拆成关键词去匹配文件名。
    # 例如 question = "detect stack" 时，可能匹配到 app/tools/detect_stack.py。
    if len(results) < limit and q:
        keywords = [kw for kw in q.replace("？", " ").replace("?", " ").split() if kw]
        for file_path in all_files:
            lowered = file_path.lower()
            if any(kw in lowered for kw in keywords):
                add_result(file_path, "根据问题关键词匹配到相关文件")
                if len(results) >= limit:
                    break

    # 第三阶段: 如果前两步都没有找到合适结果，退回默认优先文件，避免返回空列表。
    if not results:
        for candidate in DEFAULT_PRIORITY_FILES:
            add_result(candidate, "未命中问题规则，返回默认优先文件")
            if len(results) >= limit:
                break

    # 最终只返回限制数量以内的推荐结果。
    return results[:limit]
