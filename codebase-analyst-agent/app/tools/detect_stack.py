"""技术栈检测工具。

根据项目根目录下常见的配置文件和依赖声明，推断语言、构建工具、框架和容器化方案。
"""

from pathlib import Path


def detect_stack(project_root: str) -> dict:
    # 规范化输入路径，并确保目标确实是一个存在的项目目录。
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {project_root}")

    # 返回结构尽量保持稳定，方便上层服务或 CLI 直接消费。
    result = {
        "languages": [],
        "build_tool": None,
        "frameworks": [],
        "config_files": [],
        "containerization": [],
    }

    def add_unique(items: list, value: str):
        # 避免重复添加同一个识别结果，保持输出简洁。
        if value not in items:
            items.append(value)

    def file_exists(name: str) -> bool:
        # 只检查项目根目录下的关键文件，不做全量深度搜索。
        return (root / name).exists()

    # ---------- language & build tool ----------
    # 通过常见构建文件或依赖文件快速推断项目主要语言和构建方式。
    if file_exists("requirements.txt") or file_exists("pyproject.toml"):
        add_unique(result["languages"], "Python")
        if file_exists("requirements.txt"):
            add_unique(result["config_files"], "requirements.txt")
        if file_exists("pyproject.toml"):
            add_unique(result["config_files"], "pyproject.toml")

    if file_exists("pom.xml"):
        add_unique(result["languages"], "Java")
        result["build_tool"] = "Maven"
        add_unique(result["config_files"], "pom.xml")

    if file_exists("build.gradle") or file_exists("build.gradle.kts"):
        add_unique(result["languages"], "Java")
        result["build_tool"] = "Gradle"
        if file_exists("build.gradle"):
            add_unique(result["config_files"], "build.gradle")
        if file_exists("build.gradle.kts"):
            add_unique(result["config_files"], "build.gradle.kts")

    if file_exists("package.json"):
        add_unique(result["languages"], "JavaScript/TypeScript")
        if result["build_tool"] is None:
            # 仅在尚未识别出更明确的构建工具时，才回退为 npm。
            result["build_tool"] = "npm"
        add_unique(result["config_files"], "package.json")

    # ---------- containerization ----------
    # 识别容器化相关文件，便于判断部署方式和运行环境。
    if file_exists("Dockerfile"):
        add_unique(result["containerization"], "Docker")
        add_unique(result["config_files"], "Dockerfile")

    if file_exists("docker-compose.yml") or file_exists("docker-compose.yaml"):
        add_unique(result["containerization"], "Docker Compose")
        if file_exists("docker-compose.yml"):
            add_unique(result["config_files"], "docker-compose.yml")
        if file_exists("docker-compose.yaml"):
            add_unique(result["config_files"], "docker-compose.yaml")

    # ---------- common app config ----------
    # 补充记录一些常见应用配置文件，帮助后续定位项目入口配置。
    for name in ["application.yml", "application.yaml", "application.properties", ".env.example"]:
        if file_exists(name):
            add_unique(result["config_files"], name)

    # ---------- framework detection ----------
    # 对依赖文件做轻量级文本匹配，粗略识别常见 Python 框架。
    requirements_path = root / "requirements.txt"
    if requirements_path.exists():
        try:
            requirements_text = requirements_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "fastapi" in requirements_text:
                add_unique(result["frameworks"], "FastAPI")
            if "flask" in requirements_text:
                add_unique(result["frameworks"], "Flask")
            if "django" in requirements_text:
                add_unique(result["frameworks"], "Django")
            if "langchain" in requirements_text:
                add_unique(result["frameworks"], "LangChain")
        except Exception:
            # 这里只做增强识别，读取失败不应影响整体扫描结果。
            pass

    # 通过 package.json 粗略判断前后端 JavaScript/TypeScript 框架。
    package_json_path = root / "package.json"
    if package_json_path.exists():
        try:
            package_text = package_json_path.read_text(encoding="utf-8", errors="ignore").lower()
            if '"react"' in package_text or '"react-dom"' in package_text:
                add_unique(result["frameworks"], "React")
            if '"vue"' in package_text:
                add_unique(result["frameworks"], "Vue")
            if '"express"' in package_text:
                add_unique(result["frameworks"], "Express")
            if '"next"' in package_text:
                add_unique(result["frameworks"], "Next.js")
        except Exception:
            pass

    # 通过 Maven 依赖内容识别 Spring Boot。
    pom_path = root / "pom.xml"
    if pom_path.exists():
        try:
            pom_text = pom_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "spring-boot" in pom_text:
                add_unique(result["frameworks"], "Spring Boot")
        except Exception:
            pass

    # Gradle 项目可能使用 Groovy DSL 或 Kotlin DSL，两种构建文件都要检查。
    gradle_paths = [root / "build.gradle", root / "build.gradle.kts"]
    for gradle_path in gradle_paths:
        if gradle_path.exists():
            try:
                gradle_text = gradle_path.read_text(encoding="utf-8", errors="ignore").lower()
                if "spring-boot" in gradle_text:
                    add_unique(result["frameworks"], "Spring Boot")
            except Exception:
                pass

    # 返回一份基于启发式规则的检测结果，不保证百分之百准确，但足够用于快速理解项目。
    return result
