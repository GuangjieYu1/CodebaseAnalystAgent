# Demo Java Order System

一个按“公司级单体项目”思路改造的 Spring Boot 订单服务示例，保留单模块 Maven 结构，但补齐了企业项目常见的工程能力。

## 技术栈

- Java 17
- Spring Boot 3.3.5
- MyBatis + XML Mapper
- MySQL 8 + Flyway
- Spring Validation
- Spring Boot Actuator
- springdoc OpenAPI / Swagger UI
- Testcontainers + MockMvc

## 项目结构

```text
src/main/java/com/example/ordersystem
├─ application       # 应用服务、命令对象、DTO 组装
├─ common            # 统一响应、异常、分页、traceId
├─ config            # Jackson、MyBatis、OpenAPI 配置
├─ controller        # HTTP API 和请求对象
├─ domain            # 订单领域模型、状态、仓储接口
└─ infrastructure    # MyBatis Mapper、PO、仓储实现、订单号生成器
```

## 主要能力

- `POST /api/v1/orders` 创建订单
- `GET /api/v1/orders/{orderNo}` 查询订单详情
- `GET /api/v1/orders` 分页查询订单
- `PATCH /api/v1/orders/{orderNo}/status` 修改订单状态
- 统一响应 `ApiResponse<T>`
- 参数校验和统一异常处理
- `X-Trace-Id` 透传与请求日志
- Flyway 自动建表
- OpenAPI 文档与 Actuator 健康检查

## 本地启动

### 1. 启动数据库

```bash
docker-compose up -d mysql
```

### 2. 启动应用

Linux / macOS:

```bash
./mvnw spring-boot:run
```

Windows PowerShell:

```powershell
.\mvnw.cmd spring-boot:run
```

默认连接信息：

- DB Host: `localhost`
- DB Port: `3306`
- DB Name: `demo_order_system`
- DB Username: `demo`
- DB Password: `demo123`

如需覆盖，可通过环境变量设置：

```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=demo_order_system
DB_USERNAME=demo
DB_PASSWORD=demo123
SPRING_PROFILES_ACTIVE=local
```

## Docker 方式运行

```bash
docker-compose up --build
```

应用启动后可访问：

- Swagger UI: `http://localhost:8080/swagger-ui.html`
- OpenAPI JSON: `http://localhost:8080/api-docs`
- Actuator Health: `http://localhost:8080/actuator/health`

## API 示例

### 创建订单

```bash
curl -X POST "http://localhost:8080/api/v1/orders" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: demo-trace-id" \
  -d '{
    "customerName": "Alice",
    "amount": 99.99
  }'
```

### 查询订单

```bash
curl "http://localhost:8080/api/v1/orders/ORD-20260421101010-1a2b3c4d"
```

### 分页查询

```bash
curl "http://localhost:8080/api/v1/orders?page=0&size=20&status=CREATED&customerName=Ali"
```

### 状态流转

```bash
curl -X PATCH "http://localhost:8080/api/v1/orders/ORD-20260421101010-1a2b3c4d/status" \
  -H "Content-Type: application/json" \
  -d '{
    "targetStatus": "PAID"
  }'
```

允许的状态流转：

- `CREATED -> PAID`
- `CREATED -> CANCELLED`

## 测试

运行全部测试：

```bash
./mvnw test
```

测试覆盖面：

- 领域规则与订单号生成
- 应用服务主路径和异常路径
- Web 层参数校验和统一错误响应
- MyBatis + MySQL 持久化测试
- 基于 MockMvc 的端到端集成测试

说明：

- 持久化测试和集成测试使用 Testcontainers MySQL。
- 若本机没有 Docker，这两类测试会自动跳过。

## 生产化改造点

- 从内存仓储升级为 MyBatis + MySQL
- 新增 Flyway 数据迁移
- 统一 API 响应和错误码
- 新增配置分环境和健康检查
- 引入 OpenAPI 文档和请求 traceId
- 提供 Dockerfile、docker-compose 和 CI 骨架
