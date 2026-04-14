# Codebase Analyst Agent

一个面向本地代码仓库的代码分析原型项目。

这个仓库当前的主线目标，不是“自动改代码”，而是先把下面这条分析链路打通：

1. 扫描项目结构
2. 生成稳定的中间状态
3. 借助 LLM 对工具类做语义增强
4. 基于增强后的注册表给出工具复用建议

当前实现对 Java 项目更友好，尤其适合带有 `controller / service / repository / util` 这类目录结构的项目。

## 1. 当前定位

这个项目现在同时包含两条能力线：

- 主线 pipeline：
  面向 Java 项目，先构建本地分析状态，再做 LLM 增强和工具复用推荐。
- 早期原型能力：
  保留了更通用的规则型工具，例如技术栈识别、关键文件推荐、单文件摘要和简单问答。

如果你是第一次使用这个仓库，建议优先使用 `app/run_pipeline.py`，它代表当前主线流程。

## 2. 当前能力

### 2.1 本地状态构建

不依赖 LLM，直接基于本地文件系统和规则生成结构化状态：

- 项目树状态 `project_tree`
- 目录索引状态 `directory_index`
- 目录语义状态 `folder_semantics`
- 工具注册表状态 `tool_registry`

这些步骤的目标是先把“代码结构”转成稳定 JSON / Markdown 产物，便于后续增强、调试和复用。

### 2.2 LLM 语义增强

在本地状态基础上，针对工具类执行语义增强：

- 读取 `tool_registry.json`
- 加载 prompt 模板
- 调用 Ollama 或 DeepSeek
- 输出增强后的 `tool_registry_enhanced.json` / `tool_registry_enhanced.md`

增强内容主要包括：

- 工具类整体职责
- 方法摘要
- 使用建议
- 复用建议 `reuse_advice`

### 2.3 工具复用推荐

在增强后的工具注册表上，进一步根据用户需求判断：

- 是否可以复用现有方法
- 是直接复用，还是需要包一层
- 如果不适合复用，是否应新建工具

输出结果包括：

- 最终建议
- 候选方法排序
- 备选方法

### 2.4 早期规则型原型

仓库里还保留了早期的规则驱动工具，用于快速探索：

- `detect_stack.py`：识别基础技术栈
- `find_key_files.py`：根据问题推荐关键文件
- `summarize_file.py`：做单文件摘要
- `answer_question.py`：基于推荐文件和摘要回答简单问题
- `run_sample_questions.py`：批量跑示例问题

这部分能力仍然可用，但它不是当前最主要的演进方向。

## 3. 核心流程

当前推荐的完整流程如下：

1. `build_project_tree_state`
   扫描项目目录，生成项目树。
2. `build_directory_index_state`
   对目录做索引和初步分类。
3. `build_folder_semantics_state`
   结合分类结果，为目录补充语义说明。
4. `build_tool_registry_state`
   从工具目录中抽取 Java 工具类和方法签名。
5. `enhance_tool_registry_with_llm`
   基于 prompt 和源码，对工具类做语义增强。
6. `recommend_tool_reuse`
   根据用户需求，从增强后的方法集合中给出复用建议。

## 4. 快速开始

### 4.1 环境要求

- Python 3.10+
- 当前仓库主要依赖 Python 标准库
- 如果要运行 LLM 阶段，需要二选一：
  - 本地 Ollama
  - DeepSeek API

`requirements.txt` 当前没有额外第三方依赖声明，因此本地状态阶段基本可以直接运行。

### 4.2 配置 LLM

#### 方案 A：使用 Ollama

先确保本地 Ollama 服务可用，例如：

```bash
ollama serve
```

运行时可通过 `--provider ollama` 指定提供方，模型默认是 `qwen3.5:9b`。

#### 方案 B：使用 DeepSeek

在项目根目录创建 `.env`，或直接设置环境变量：

```env
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

`app/services/llm_client.py` 内置了一个最小 `.env` 读取器，会自动读取项目根目录下的 `.env`。

## 5. 运行方式

### 5.1 仅运行本地状态阶段

```bash
python -m app.run_pipeline \
  --project-root ../demo_java_order_system \
  --stage local_states \
  --max-depth 10
```

这会生成：

- `outputs/project_tree.json`
- `outputs/project_tree.md`
- `outputs/directory_index.json`
- `outputs/directory_index.md`
- `outputs/folder_semantics.json`
- `outputs/folder_semantics.md`
- `outputs/tool_registry.json`
- `outputs/tool_registry.md`

### 5.2 仅运行 LLM 增强阶段

```bash
python -m app.run_pipeline \
  --project-root ../demo_java_order_system \
  --stage llm_steps \
  --provider deepseek \
  --target-class-name OrderUtils
```

这会基于已有的 `outputs/tool_registry.json` 生成：

- `outputs/tool_registry_enhanced.json`
- `outputs/tool_registry_enhanced.md`

### 5.3 跑完整链路

```bash
python -m app.run_pipeline \
  --project-root ../demo_java_order_system \
  --stage all \
  --provider deepseek \
  --target-class-name OrderUtils \
  --query "我想要一个输入一个列表，返回一个这个列表去重后的方法" \
  --top-k 2
```

完整链路会额外输出：

- `outputs/tool_reuse_recommendation.json`
- `outputs/tool_reuse_recommendation.md`

### 5.4 本地状态旧入口

如果你只想快速跑本地状态阶段，也可以使用旧入口：

```bash
python -m app.main \
  --project-root ../demo_java_order_system \
  --max-depth 8
```

这个入口只负责生成本地状态，不执行 LLM 步骤。

### 5.5 运行旧版示例问答

```bash
python -m app.run_sample_questions \
  --project-root .
```

默认会读取 [examples/sample_questions.md](examples/sample_questions.md)，并输出到 `outputs/sample_answers.md`。

## 6. 输出物说明

`outputs/` 目录用于保存中间状态和最终结果。

- `project_tree.*`
  项目目录树
- `directory_index.*`
  目录索引和规则分类结果
- `folder_semantics.*`
  目录语义解释
- `tool_registry.*`
  本地抽取出的工具类和方法签名
- `tool_registry_enhanced.*`
  LLM 增强后的工具类语义信息
- `tool_reuse_recommendation.*`
  针对具体需求的工具复用建议
- `sample_answers.md`
  早期问答原型输出

## 7. Prompt 体系

当前 prompt 资源按职责分层组织：

- `app/prompts/shared/`
  通用 system prompt 和 JSON 输出约束
- `app/prompts/tool_registry/`
  工具类语义增强 prompt
- `app/prompts/tool_reuse/`
  工具复用推荐 prompt

对应的 prompt 加载逻辑在：

- `app/services/prompt_loader.py`

## 8. 目录结构

```text
app/
  run_pipeline.py                  # 当前推荐入口
  main.py                          # 本地状态旧入口
  run_sample_questions.py          # 早期问答原型入口
  tools/
    build_project_tree_state.py
    build_directory_index_state.py
    build_folder_semantics_state.py
    build_tool_registry_state.py
    enhance_tool_registry_with_llm.py
    recommend_tool_reuse.py
    detect_stack.py
    find_key_files.py
    summarize_file.py
    answer_question.py
  services/
    prompt_loader.py
    llm_client.py
  prompts/
    shared/
    tool_registry/
    tool_reuse/
outputs/                           # 生成的 JSON / Markdown 结果
examples/                          # 示例问题
```

## 9. 当前限制

这个项目已经能跑出一条完整链路，但目前还有一些明确边界：

- 当前主线更偏向 Java 项目，不是完整的多语言通用分析器。
- 工具注册表抽取主要依赖目录分类和正则解析，不是 AST 级解析。
- 目录语义规则对常见 Java 分层目录较友好，但对非典型结构支持有限。
- LLM 输出目前主要通过 prompt 约束和 JSON 解析做控制，结构化校验还可以继续加强。
- 一些 `services/`、`models/`、`state/` 下的模块仍是占位或待扩展状态。
- 测试文件目前还比较薄，回归保护不够完整。

## 10. 非目标

当前阶段，这个项目不追求：

- 自动修改代码
- 自动生成补丁
- 复杂多 Agent 编排
- 全量代码索引系统
- IDE 插件集成

## 11. 后续可演进方向

如果继续往前推进，比较自然的下一步包括：

- 用 AST 或更稳健的解析方式替代部分正则抽取
- 把工具注册表增强和复用推荐接入更严格的 schema 校验
- 把早期规则问答链路和当前状态链路统一起来
- 为不同项目分别管理 `outputs/`，避免不同样例互相覆盖
- 增加真实测试样例和回归测试

## 12. 一句话总结

这是一个“先用本地规则把项目结构化，再用 LLM 做语义增强和复用决策”的代码分析原型；当前最成熟的部分，是 Java 项目结构分析、工具类注册表构建，以及基于增强注册表的工具复用推荐。
