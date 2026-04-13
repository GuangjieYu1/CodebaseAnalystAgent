from app.services.prompt_loader import load_prompt, load_and_render_prompt, build_system_prompt


def main():
    system_prompt = build_system_prompt(
        "shared/system_base.txt",
        "shared/output_json_rules.txt",
        "tool_registry/enhance_tool_registry_system.txt",
    )

    user_prompt = load_and_render_prompt(
        "tool_registry/enhance_tool_registry_user.txt",
        {
            "class_name": "OrderUtils",
            "package_name": "com.example.ordersystem.util",
            "file_path": "src/main/java/com/example/ordersystem/util/OrderUtils.java",
            "methods_json": '[{"method_name":"generateOrderNo","return_type":"String"}]',
            "java_source": "public class OrderUtils { public static String generateOrderNo(String prefix) { return prefix; } }",
        },
    )

    print("=== SYSTEM PROMPT ===")
    print(system_prompt)
    print("\n=== USER PROMPT ===")
    print(user_prompt)


if __name__ == "__main__":
    main()