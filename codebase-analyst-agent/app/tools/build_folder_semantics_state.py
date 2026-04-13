from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json


SEMANTIC_RULES = {
    "controller": {
        "semantic_type": "controller_layer",
        "description": "该目录通常作为接口入口层，负责接收请求、参数转换，并调用 service 层完成业务处理。",
        "recommended_contents": ["Controller 类", "接口路由定义", "简单参数校验"],
        "upstream_dependencies": [],
        "downstream_dependencies": ["service", "dto", "vo"],
    },
    "service": {
        "semantic_type": "service_layer",
        "description": "该目录通常承载业务逻辑实现，负责协调领域对象、工具类和数据访问层。",
        "recommended_contents": ["Service 接口", "Service 实现类", "业务流程编排"],
        "upstream_dependencies": ["controller"],
        "downstream_dependencies": ["repository", "domain", "util", "dto", "vo"],
    },
    "repository": {
        "semantic_type": "repository_layer",
        "description": "该目录通常负责数据访问逻辑，与数据库、缓存或外部存储交互。",
        "recommended_contents": ["Repository 类", "DAO", "数据查询与保存逻辑"],
        "upstream_dependencies": ["service"],
        "downstream_dependencies": ["domain", "entity"],
    },
    "domain": {
        "semantic_type": "domain_model_layer",
        "description": "该目录通常存放核心领域模型，表达业务中的主要对象和状态。",
        "recommended_contents": ["领域模型", "核心实体对象", "业务状态对象"],
        "upstream_dependencies": ["service", "repository"],
        "downstream_dependencies": [],
    },
    "dto": {
        "semantic_type": "dto_layer",
        "description": "该目录通常存放数据传输对象，用于接口入参或跨层传递数据。",
        "recommended_contents": ["请求 DTO", "传输对象", "输入参数模型"],
        "upstream_dependencies": ["controller", "service"],
        "downstream_dependencies": [],
    },
    "vo": {
        "semantic_type": "vo_layer",
        "description": "该目录通常存放视图对象或返回对象，用于接口输出和展示层封装。",
        "recommended_contents": ["返回 VO", "展示对象", "接口响应模型"],
        "upstream_dependencies": ["controller", "service"],
        "downstream_dependencies": [],
    },
    "config": {
        "semantic_type": "config_layer",
        "description": "该目录通常负责项目配置相关内容，例如 Bean 配置、序列化配置或基础框架配置。",
        "recommended_contents": ["配置类", "Bean 定义", "框架初始化配置"],
        "upstream_dependencies": [],
        "downstream_dependencies": [],
    },
    "util": {
        "semantic_type": "utility_layer",
        "description": "该目录通常存放通用工具类，提供可复用的独立辅助能力。",
        "recommended_contents": ["工具类", "静态辅助方法", "格式化/校验/转换逻辑"],
        "upstream_dependencies": ["controller", "service", "repository"],
        "downstream_dependencies": [],
    },
    "resources": {
        "semantic_type": "resource_layer",
        "description": "该目录通常存放配置文件、模板文件或静态资源，是项目的资源与配置承载位置。",
        "recommended_contents": ["application.yml", "配置文件", "模板或静态资源"],
        "upstream_dependencies": [],
        "downstream_dependencies": [],
    },
    "java_source_root": {
        "semantic_type": "java_source_root",
        "description": "该目录是 Java 主源码根路径，用于组织生产代码包结构。",
        "recommended_contents": ["主源码包路径", "业务代码目录"],
        "upstream_dependencies": [],
        "downstream_dependencies": ["controller", "service", "repository", "domain", "dto", "vo", "config", "util"],
    },
    "java_test_root": {
        "semantic_type": "java_test_root",
        "description": "该目录是 Java 测试源码根路径，用于组织测试代码和测试上下文。",
        "recommended_contents": ["测试类", "测试上下文", "测试辅助代码"],
        "upstream_dependencies": [],
        "downstream_dependencies": [],
    },
}


def build_folder_semantics_state(
    directory_index_json_path: str = "outputs/directory_index.json",
    output_json: str = "outputs/folder_semantics.json",
    output_md: str = "outputs/folder_semantics.md",
) -> dict:
    source_path = Path(directory_index_json_path)
    if not source_path.exists() or not source_path.is_file():
        raise ValueError(f"Invalid directory index json path: {directory_index_json_path}")

    directory_index_state = json.loads(source_path.read_text(encoding="utf-8"))
    directories = directory_index_state.get("directories", [])

    semantics = []
    for item in directories:
        test_context_semantic = _build_test_context_semantic(item)
        if test_context_semantic is not None:
            semantics.append(test_context_semantic)
            continue

        category = item.get("matched_category", "unknown")
        semantic_rule = SEMANTIC_RULES.get(category)

        if semantic_rule is None:
            semantics.append(_build_unknown_semantic(item))
            continue

        semantics.append({
            "path": item["path"],
            "category": category,
            "semantic_type": semantic_rule["semantic_type"],
            "description": semantic_rule["description"],
            "recommended_contents": semantic_rule["recommended_contents"],
            "upstream_dependencies": semantic_rule["upstream_dependencies"],
            "downstream_dependencies": semantic_rule["downstream_dependencies"],
            "reason": item.get("match_reason", ""),
            "parent_path": item.get("parent_path", ""),
            "contains_java_files": item.get("contains_java_files", False),
        })

    state = {
        "project_root": directory_index_state.get("project_root", ""),
        "source_directory_index_json": str(source_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "semantic_count": len(semantics),
        "semantics": semantics,
    }

    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_md_path = Path(output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(render_folder_semantics_markdown(state), encoding="utf-8")

    return state


def _build_unknown_semantic(item: dict) -> dict:
    return {
        "path": item["path"],
        "category": item.get("matched_category", "unknown"),
        "semantic_type": "unknown",
        "description": "当前目录尚未命中明确的语义规则，后续可结合项目上下文进一步细化。",
        "recommended_contents": [],
        "upstream_dependencies": [],
        "downstream_dependencies": [],
        "reason": item.get("match_reason", ""),
        "parent_path": item.get("parent_path", ""),
        "contains_java_files": item.get("contains_java_files", False),
    }


def render_folder_semantics_markdown(state: dict) -> str:
    lines = [
        "# Folder Semantics",
        "",
        f"- Root: `{state['project_root']}`",
        f"- Source Directory Index JSON: `{state['source_directory_index_json']}`",
        f"- Generated At: `{state['generated_at']}`",
        f"- Semantic Count: `{state['semantic_count']}`",
        "",
        "## Folder Semantics",
        "",
    ]

    for item in state["semantics"]:
        lines.append(f"### {item['path']}")
        lines.append("")
        lines.append(f"- Category: `{item['category']}`")
        lines.append(f"- Semantic Type: `{item['semantic_type']}`")
        lines.append(f"- Parent Path: `{item['parent_path'] or '/'}`")
        lines.append(f"- Contains Java Files: `{'yes' if item['contains_java_files'] else 'no'}`")
        lines.append(f"- Reason: {item['reason']}")
        lines.append(f"- Description: {item['description']}")

        if item["recommended_contents"]:
            lines.append("- Recommended Contents:")
            for content in item["recommended_contents"]:
                lines.append(f"  - {content}")

        if item["upstream_dependencies"]:
            lines.append("- Upstream Dependencies:")
            for dep in item["upstream_dependencies"]:
                lines.append(f"  - {dep}")

        if item["downstream_dependencies"]:
            lines.append("- Downstream Dependencies:")
            for dep in item["downstream_dependencies"]:
                lines.append(f"  - {dep}")

        lines.append("")

    return "\n".join(lines)

def _build_test_context_semantic(item: dict) -> dict | None:
    path = item.get("path", "").lower()
    category = item.get("matched_category", "unknown")

    if not path.startswith("src/test/java/"):
        return None

    mapping = {
        "controller": {
            "semantic_type": "test_controller_context",
            "description": "该目录位于测试源码路径下，主要用于组织 controller 相关测试类，而不是生产接口入口实现。",
            "recommended_contents": ["Controller 测试类", "接口测试上下文", "请求/响应断言逻辑"],
            "upstream_dependencies": [],
            "downstream_dependencies": ["service", "dto", "vo"],
        },
        "service": {
            "semantic_type": "test_service_context",
            "description": "该目录位于测试源码路径下，主要用于组织 service 相关测试类，而不是生产业务实现。",
            "recommended_contents": ["Service 测试类", "业务测试上下文", "Mock/Stub 测试辅助逻辑"],
            "upstream_dependencies": [],
            "downstream_dependencies": ["repository", "domain", "dto", "vo", "util"],
        },
        "repository": {
            "semantic_type": "test_repository_context",
            "description": "该目录位于测试源码路径下，主要用于组织 repository 相关测试类，而不是生产数据访问实现。",
            "recommended_contents": ["Repository 测试类", "持久层测试上下文", "数据准备与断言逻辑"],
            "upstream_dependencies": [],
            "downstream_dependencies": ["domain", "entity"],
        },
        "dto": {
            "semantic_type": "test_dto_context",
            "description": "该目录位于测试源码路径下，主要用于 DTO 相关测试数据构造与传输对象验证。",
            "recommended_contents": ["DTO 测试构造", "请求参数样例", "边界值测试数据"],
            "upstream_dependencies": [],
            "downstream_dependencies": [],
        },
        "vo": {
            "semantic_type": "test_vo_context",
            "description": "该目录位于测试源码路径下，主要用于 VO 相关断言和返回对象校验。",
            "recommended_contents": ["VO 断言", "返回结果校验", "展示对象测试样例"],
            "upstream_dependencies": [],
            "downstream_dependencies": [],
        },
        "util": {
            "semantic_type": "test_utility_context",
            "description": "该目录位于测试源码路径下，主要用于测试工具、测试辅助方法或断言辅助能力。",
            "recommended_contents": ["测试工具类", "断言辅助方法", "测试数据构造工具"],
            "upstream_dependencies": [],
            "downstream_dependencies": [],
        },
    }

    semantic_rule = mapping.get(category)
    if semantic_rule is None:
        return None

    return {
        "path": item["path"],
        "category": category,
        "semantic_type": semantic_rule["semantic_type"],
        "description": semantic_rule["description"],
        "recommended_contents": semantic_rule["recommended_contents"],
        "upstream_dependencies": semantic_rule["upstream_dependencies"],
        "downstream_dependencies": semantic_rule["downstream_dependencies"],
        "reason": item.get("match_reason", ""),
        "parent_path": item.get("parent_path", ""),
        "contains_java_files": item.get("contains_java_files", False),
    }