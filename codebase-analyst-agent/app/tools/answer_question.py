from app.tools.find_key_files import find_key_files
from app.tools.summarize_file import summarize_file
from pathlib import Path


def answer_question(project_root: str, question: str, max_files: int = 3) -> dict:
    if not question or not question.strip():
        raise ValueError("Question must not be empty.")

    recommended_files = find_key_files(project_root, question, limit=max_files)

    summaries = []
    for item in recommended_files:
        # 在循环里
        file_path = item["file"]
        full_path = (Path(project_root).resolve() / file_path).resolve()

        if not full_path.exists() or not full_path.is_file():
            summaries.append({
                "file": file_path,
                "reason": item["reason"],
                "summary": "这是一个目录或不可读取文件，当前跳过单文件摘要。",
                "key_symbols": [],
            })
            continue

        try:
            summary = summarize_file(project_root, file_path)
            summaries.append({
                "file": file_path,
                "reason": item["reason"],
                "summary": summary["summary"],
                "key_symbols": summary["key_symbols"],
            })
        except Exception as e:
            summaries.append({
                "file": file_path,
                "reason": item["reason"],
                "summary": f"文件摘要失败：{e}",
                "key_symbols": [],
            })

    conclusion = _build_conclusion(question, summaries)

    return {
        "question": question,
        "conclusion": conclusion,
        "evidence": summaries,
        "notes": _build_notes(question, summaries),
    }


def _build_conclusion(question: str, summaries: list[dict]) -> str:
    q = question.lower()

    files = [item["file"] for item in summaries]

    if not summaries:
        return "当前没有找到足够的相关文件，暂时无法回答该问题。"

    if "入口" in question or "启动" in question or "main" in q:
        return f"项目入口大概率在 {', '.join(files)}，其中靠前文件更值得优先查看。"

    if "配置" in question or "环境变量" in question or "config" in q or "env" in q:
        return f"项目配置相关内容建议优先查看 {', '.join(files)}。"

    if "工具" in question or "scan" in q or "stack" in q or "检测" in question:
        return f"项目工具能力主要集中在 {', '.join(files)} 这些文件中。"

    if "测试" in question or "test" in q:
        return f"和测试相关的内容建议优先查看 {', '.join(files)}。"

    return f"针对当前问题，建议优先阅读这些文件：{', '.join(files)}。"


def _build_notes(question: str, summaries: list[dict]) -> list[str]:
    notes = []

    if not summaries:
        notes.append("当前回答基于文件推荐结果，尚未获得可用摘要。")
        return notes

    notes.append("当前回答基于规则推荐文件和单文件摘要，尚未做跨文件调用链分析。")

    if any("摘要失败" in item["summary"] for item in summaries):
        notes.append("部分文件摘要失败，当前结论可能不完整。")

    if len(summaries) < 2:
        notes.append("当前证据文件较少，结论可信度有限。")

    return notes