Codebase Analyst Agent
│
├── 状态构建层
│   ├── build_project_tree_state.py
│   ├── build_directory_index_state.py
│   ├── build_folder_semantics_state.py
│   └── build_tool_registry_state.py
│
├── Prompt 层
│   ├── shared/
│   │   ├── system_base.txt
│   │   └── output_json_rules.txt
│   └── tool_registry/
│       ├── enhance_tool_registry_system.txt
│       └── enhance_tool_registry_user.txt
│
├── 服务层
│   ├── prompt_loader.py
│   └── llm_client.py
│       ├── generate_with_ollama()
│       └── generate_with_deepseek()
│
├── 增强层
│   ├── enhance_tool_registry_with_llm.py
│   └── enhance_tool_registry.py
│
└── 输出层
    ├── tool_registry.json
    ├── tool_registry_enhanced.json
    └── tool_registry_enhanced.md