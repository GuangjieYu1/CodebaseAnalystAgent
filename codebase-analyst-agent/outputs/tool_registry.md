# Tool Registry

- Root: `/Users/guangjieyu/VibeCodingProject/AgentDevelopment/CodebaseAnalystAgent/demo_java_order_system`
- Source Directory Index JSON: `outputs/directory_index.json`
- Generated At: `2026-04-14T15:02:25`
- Tool Class Count: `1`
- Method Count: `6`

## Tool Classes

### OrderUtils

- Package: `com.example.ordersystem.util`
- File Path: `src/main/java/com/example/ordersystem/util/OrderUtils.java`
- Method Count: `6`

| Method | Visibility | Static | Return Type | Parameters |
| --- | --- | --- | --- | --- |
| generateOrderNo | public | yes | String | String prefix |
| randomMethod | public | yes | String | String filePath |
| buildNormalizedOrderSnapshot | public | yes | String | String rawCustomerName, String rawOrderNo, String rawStatus, java.math.BigDecimal rawAmount, java.math.BigDecimal discountAmount, java.util.List<String> rawTags, boolean strictMode |
| normalizeAndExtractStillDuplicatedItems | public | yes | List<String> | List<String> rawItems |
| calculateTotalAmount | public | yes | BigDecimal | List<BigDecimal> items |
| isValidOrderStatus | public | yes | boolean | String status |
