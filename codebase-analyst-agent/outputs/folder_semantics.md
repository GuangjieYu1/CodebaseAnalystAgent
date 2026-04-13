# Folder Semantics

- Root: `/Users/guangjieyu/VibeCodingProject/AgentDevelopment/CodebaseAnalystAgent/demo_java_order_system`
- Source Directory Index JSON: `outputs/directory_index.json`
- Generated At: `2026-04-13T14:41:40`
- Semantic Count: `22`

## Folder Semantics

### src

- Category: `unknown`
- Semantic Type: `unknown`
- Parent Path: `/`
- Contains Java Files: `no`
- Reason: 未命中已知目录分类规则
- Description: 当前目录尚未命中明确的语义规则，后续可结合项目上下文进一步细化。

### src/main

- Category: `unknown`
- Semantic Type: `unknown`
- Parent Path: `src`
- Contains Java Files: `no`
- Reason: 未命中已知目录分类规则
- Description: 当前目录尚未命中明确的语义规则，后续可结合项目上下文进一步细化。

### src/main/java

- Category: `java_source_root`
- Semantic Type: `java_source_root`
- Parent Path: `src/main`
- Contains Java Files: `no`
- Reason: 目录为 src/main/java
- Description: 该目录是 Java 主源码根路径，用于组织生产代码包结构。
- Recommended Contents:
  - 主源码包路径
  - 业务代码目录
- Downstream Dependencies:
  - controller
  - service
  - repository
  - domain
  - dto
  - vo
  - config
  - util

### src/main/java/com

- Category: `java_source_root`
- Semantic Type: `java_source_root`
- Parent Path: `src/main/java`
- Contains Java Files: `no`
- Reason: 路径位于 src/main/java 下
- Description: 该目录是 Java 主源码根路径，用于组织生产代码包结构。
- Recommended Contents:
  - 主源码包路径
  - 业务代码目录
- Downstream Dependencies:
  - controller
  - service
  - repository
  - domain
  - dto
  - vo
  - config
  - util

### src/main/java/com/example

- Category: `java_source_root`
- Semantic Type: `java_source_root`
- Parent Path: `src/main/java/com`
- Contains Java Files: `no`
- Reason: 路径位于 src/main/java 下
- Description: 该目录是 Java 主源码根路径，用于组织生产代码包结构。
- Recommended Contents:
  - 主源码包路径
  - 业务代码目录
- Downstream Dependencies:
  - controller
  - service
  - repository
  - domain
  - dto
  - vo
  - config
  - util

### src/main/java/com/example/ordersystem

- Category: `java_source_root`
- Semantic Type: `java_source_root`
- Parent Path: `src/main/java/com/example`
- Contains Java Files: `yes`
- Reason: 路径位于 src/main/java 下
- Description: 该目录是 Java 主源码根路径，用于组织生产代码包结构。
- Recommended Contents:
  - 主源码包路径
  - 业务代码目录
- Downstream Dependencies:
  - controller
  - service
  - repository
  - domain
  - dto
  - vo
  - config
  - util

### src/main/java/com/example/ordersystem/config

- Category: `config`
- Semantic Type: `config_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 config
- Description: 该目录通常负责项目配置相关内容，例如 Bean 配置、序列化配置或基础框架配置。
- Recommended Contents:
  - 配置类
  - Bean 定义
  - 框架初始化配置

### src/main/java/com/example/ordersystem/controller

- Category: `controller`
- Semantic Type: `controller_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 controller
- Description: 该目录通常作为接口入口层，负责接收请求、参数转换，并调用 service 层完成业务处理。
- Recommended Contents:
  - Controller 类
  - 接口路由定义
  - 简单参数校验
- Downstream Dependencies:
  - service
  - dto
  - vo

### src/main/java/com/example/ordersystem/domain

- Category: `domain`
- Semantic Type: `domain_model_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 domain
- Description: 该目录通常存放核心领域模型，表达业务中的主要对象和状态。
- Recommended Contents:
  - 领域模型
  - 核心实体对象
  - 业务状态对象
- Upstream Dependencies:
  - service
  - repository

### src/main/java/com/example/ordersystem/dto

- Category: `dto`
- Semantic Type: `dto_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 dto
- Description: 该目录通常存放数据传输对象，用于接口入参或跨层传递数据。
- Recommended Contents:
  - 请求 DTO
  - 传输对象
  - 输入参数模型
- Upstream Dependencies:
  - controller
  - service

### src/main/java/com/example/ordersystem/repository

- Category: `repository`
- Semantic Type: `repository_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 repository
- Description: 该目录通常负责数据访问逻辑，与数据库、缓存或外部存储交互。
- Recommended Contents:
  - Repository 类
  - DAO
  - 数据查询与保存逻辑
- Upstream Dependencies:
  - service
- Downstream Dependencies:
  - domain
  - entity

### src/main/java/com/example/ordersystem/service

- Category: `service`
- Semantic Type: `service_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 service
- Description: 该目录通常承载业务逻辑实现，负责协调领域对象、工具类和数据访问层。
- Recommended Contents:
  - Service 接口
  - Service 实现类
  - 业务流程编排
- Upstream Dependencies:
  - controller
- Downstream Dependencies:
  - repository
  - domain
  - util
  - dto
  - vo

### src/main/java/com/example/ordersystem/service/impl

- Category: `service`
- Semantic Type: `service_layer`
- Parent Path: `src/main/java/com/example/ordersystem/service`
- Contains Java Files: `yes`
- Reason: 路径中包含 service
- Description: 该目录通常承载业务逻辑实现，负责协调领域对象、工具类和数据访问层。
- Recommended Contents:
  - Service 接口
  - Service 实现类
  - 业务流程编排
- Upstream Dependencies:
  - controller
- Downstream Dependencies:
  - repository
  - domain
  - util
  - dto
  - vo

### src/main/java/com/example/ordersystem/util

- Category: `util`
- Semantic Type: `utility_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 util
- Description: 该目录通常存放通用工具类，提供可复用的独立辅助能力。
- Recommended Contents:
  - 工具类
  - 静态辅助方法
  - 格式化/校验/转换逻辑
- Upstream Dependencies:
  - controller
  - service
  - repository

### src/main/java/com/example/ordersystem/vo

- Category: `vo`
- Semantic Type: `vo_layer`
- Parent Path: `src/main/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 目录名为 vo
- Description: 该目录通常存放视图对象或返回对象，用于接口输出和展示层封装。
- Recommended Contents:
  - 返回 VO
  - 展示对象
  - 接口响应模型
- Upstream Dependencies:
  - controller
  - service

### src/main/resources

- Category: `resources`
- Semantic Type: `resource_layer`
- Parent Path: `src/main`
- Contains Java Files: `no`
- Reason: 路径位于 resources 目录下
- Description: 该目录通常存放配置文件、模板文件或静态资源，是项目的资源与配置承载位置。
- Recommended Contents:
  - application.yml
  - 配置文件
  - 模板或静态资源

### src/test

- Category: `test`
- Semantic Type: `unknown`
- Parent Path: `src`
- Contains Java Files: `no`
- Reason: 目录名为 test
- Description: 当前目录尚未命中明确的语义规则，后续可结合项目上下文进一步细化。

### src/test/java

- Category: `java_test_root`
- Semantic Type: `java_test_root`
- Parent Path: `src/test`
- Contains Java Files: `no`
- Reason: 路径位于 src/test/java 下
- Description: 该目录是 Java 测试源码根路径，用于组织测试代码和测试上下文。
- Recommended Contents:
  - 测试类
  - 测试上下文
  - 测试辅助代码

### src/test/java/com

- Category: `java_test_root`
- Semantic Type: `java_test_root`
- Parent Path: `src/test/java`
- Contains Java Files: `no`
- Reason: 路径位于 src/test/java 下
- Description: 该目录是 Java 测试源码根路径，用于组织测试代码和测试上下文。
- Recommended Contents:
  - 测试类
  - 测试上下文
  - 测试辅助代码

### src/test/java/com/example

- Category: `java_test_root`
- Semantic Type: `java_test_root`
- Parent Path: `src/test/java/com`
- Contains Java Files: `no`
- Reason: 路径位于 src/test/java 下
- Description: 该目录是 Java 测试源码根路径，用于组织测试代码和测试上下文。
- Recommended Contents:
  - 测试类
  - 测试上下文
  - 测试辅助代码

### src/test/java/com/example/ordersystem

- Category: `java_test_root`
- Semantic Type: `java_test_root`
- Parent Path: `src/test/java/com/example`
- Contains Java Files: `no`
- Reason: 路径位于 src/test/java 下
- Description: 该目录是 Java 测试源码根路径，用于组织测试代码和测试上下文。
- Recommended Contents:
  - 测试类
  - 测试上下文
  - 测试辅助代码

### src/test/java/com/example/ordersystem/service

- Category: `service`
- Semantic Type: `test_service_context`
- Parent Path: `src/test/java/com/example/ordersystem`
- Contains Java Files: `yes`
- Reason: 测试源码目录下的 service 语境
- Description: 该目录位于测试源码路径下，主要用于组织 service 相关测试类，而不是生产业务实现。
- Recommended Contents:
  - Service 测试类
  - 业务测试上下文
  - Mock/Stub 测试辅助逻辑
- Downstream Dependencies:
  - repository
  - domain
  - dto
  - vo
  - util
