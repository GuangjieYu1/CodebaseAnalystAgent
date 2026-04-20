# 方法执行路径说明：buildNormalizedOrderSnapshot

## 1. 基本信息

- 类名：`OrderUtils`
- 文件：`src/main/java/com/example/ordersystem/util/OrderUtils.java`
- 方法签名：

```java
public static String buildNormalizedOrderSnapshot(
            String rawCustomerName,
            String rawOrderNo,
            String rawStatus,
            java.math.BigDecimal rawAmount,
            java.math.BigDecimal discountAmount,
            java.util.List<String> rawTags,
            boolean strictMode
    )
```

## 2. 最终执行总结

方法 buildNormalizedOrderSnapshot 的主流程可以概括为：先处理“条件校验与分支判断”，产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换；接着处理“条件校验与分支判断”，产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换；接着处理“条件校验与分支判断”，产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换；接着处理“规则判断”，产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换；接着处理“数值计算处理”，得到新的金额结果、阈值判断结论或修正后的数值状态；接着处理“集合内容校验与去重”，更新后的问题项集合，用于后续风险判断、兜底处理或最终输出；接着处理“规则判断”，产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换；最后处理“条件校验与分支判断”，产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

## 3. 主流程业务步骤

### 步骤 1：条件校验与分支判断

- 代码行范围：`47 - 47`
- 步骤总结：该步骤检查输入或当前候选值是否有效，并决定是提前返回、跳过当前项，还是继续进入后续处理。
- 步骤输入：当前方法参数、已生成的中间变量，以及用于判断是否继续执行的条件状态。
- 步骤输出：产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

### 步骤 2：条件校验与分支判断

- 代码行范围：`53 - 58`
- 步骤总结：该步骤检查输入或当前候选值是否有效，并决定是提前返回、跳过当前项，还是继续进入后续处理。
- 步骤输入：当前方法参数、已生成的中间变量，以及用于判断是否继续执行的条件状态。
- 步骤输出：产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

### 步骤 3：条件校验与分支判断

- 代码行范围：`80 - 88`
- 步骤总结：该步骤检查输入或当前候选值是否有效，并决定是提前返回、跳过当前项，还是继续进入后续处理。
- 步骤输入：当前方法参数、已生成的中间变量，以及用于判断是否继续执行的条件状态。
- 步骤输出：产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

### 步骤 4：规则判断

- 代码行范围：`104 - 104`
- 步骤总结：该步骤主要围绕 compareTo 等调用展开，集中处理 规则判断，代码范围约在第 104 到 104 行。
- 步骤输入：当前方法参数、已生成的中间变量，以及用于判断是否继续执行的条件状态。
- 步骤输出：产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

### 步骤 5：数值计算处理

- 代码行范围：`108 - 109`
- 步骤总结：该步骤主要围绕 compareTo、subtract 等调用展开，集中处理 数值计算处理，代码范围约在第 108 到 109 行。
- 步骤输入：金额、折扣、阈值等数值型中间状态，以及前置判断结果。
- 步骤输出：得到新的金额结果、阈值判断结论或修正后的数值状态。

### 步骤 6：集合内容校验与去重

- 代码行范围：`113 - 118`
- 步骤总结：该步骤主要围绕 compareTo、contains、isEmpty 等调用展开，集中处理 集合内容校验与去重，代码范围约在第 113 到 118 行。
- 步骤输入：前面校验阶段得到的异常标记、缺失字段信息或非法状态判断结果。
- 步骤输出：更新后的问题项集合，用于后续风险判断、兜底处理或最终输出。

### 步骤 7：规则判断

- 代码行范围：`127 - 131`
- 步骤总结：该步骤主要围绕 compareTo 等调用展开，集中处理 规则判断，代码范围约在第 127 到 131 行。
- 步骤输入：当前方法参数、已生成的中间变量，以及用于判断是否继续执行的条件状态。
- 步骤输出：产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

### 步骤 8：条件校验与分支判断

- 代码行范围：`139 - 139`
- 步骤总结：该步骤检查输入或当前候选值是否有效，并决定是提前返回、跳过当前项，还是继续进入后续处理。
- 步骤输入：当前方法参数、已生成的中间变量，以及用于判断是否继续执行的条件状态。
- 步骤输出：产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

## 4. 标准输入模拟

### 标准输入

- `rawCustomerName` (String): `Alice`
- `rawOrderNo` (String): `ORD-20260417-001`
- `rawStatus` (String): `paid`
- `rawAmount` (BigDecimal): `12000`
- `discountAmount` (BigDecimal): `1000`
- `rawTags` (List<String>): `[vip, urgent]`
- `strictMode` (boolean): `false`

### 预期执行摘要

- 步骤 1：条件校验与分支判断 → 产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。
- 步骤 2：条件校验与分支判断 → 产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。
- 步骤 3：条件校验与分支判断 → 产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。
- 步骤 4：规则判断 → 产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。
- 步骤 5：数值计算处理 → 得到新的金额结果、阈值判断结论或修正后的数值状态。
- 步骤 6：集合内容校验与去重 → 更新后的问题项集合，用于后续风险判断、兜底处理或最终输出。
- 步骤 7：规则判断 → 产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。
- 步骤 8：条件校验与分支判断 → 产出是否继续后续流程的判断结论，必要时触发提前返回或分支切换。

### 预期输出

- `按当前源码推断，该方法存在多条返回路径：提前结束时可能返回当前分支拼装出的固定格式字符串；主路径最终返回组装完成的字符串结果。`

## 5. 调试附录

### 业务流程 Mermaid 图

```mermaid
flowchart TD
    BM0["buildNormalizedOrderSnapshot 业务流程"]
    BS1["1. 条件校验与分支判断"]
    BM0 --> BS1
    BS2["2. 条件校验与分支判断"]
    BS3["3. 条件校验与分支判断"]
    BS4["4. 规则判断"]
    BS5["5. 数值计算处理"]
    BS6["6. 集合内容校验与去重"]
    BS7["7. 规则判断"]
    BS8["8. 条件校验与分支判断"]
    BS1 --> BS2
    BS2 --> BS3
    BS3 --> BS4
    BS4 --> BS5
    BS5 --> BS6
    BS6 --> BS7
    BS7 --> BS8
    BS8 --> BME
    BME(["End"])
```

### 分支执行 Mermaid 图

```mermaid
flowchart TD
    M0["buildNormalizedOrderSnapshot()"]
    S1["步骤 1: 条件校验与分支判断 (47-47)"]
    M0 --> S1
    B3{"if @L47: (!normalizedTag.isEmpty() && !tags.contains(normalizedTag))"}
    S1 --> B3
    B3_Y["进入分支"]
    B3_N["跳过分支"]
    B3 -->|Y| B3_Y
    B3 -->|N| B3_N
    S2["步骤 2: 条件校验与分支判断 (53-58)"]
    S1 --> S2
    S3["步骤 3: 条件校验与分支判断 (80-88)"]
    S2 --> S3
    B10{"if @L80: (strictMode && !issues.isEmpty())"}
    S3 --> B10
    B10_Y["进入分支"]
    B10_N["跳过分支"]
    B10 -->|Y| B10_Y
    B10 -->|N| B10_N
    B11["return @L81: return 'ORDER_SNAPSHOT(valid=false,mode=strict,issues=' + issues..."]
    B10_Y --> B11
    T1(["RETURN @L81"])
    B11 --> T1
    B12{"if @L84: (customerName.isEmpty())"}
    B12_Y["进入分支"]
    B12_N["跳过分支"]
    B12 -->|Y| B12_Y
    B12 -->|N| B12_N
    B13{"if @L88: (orderNo.isEmpty())"}
    B12_Y --> B13
    B13_Y["进入分支"]
    B13_N["跳过分支"]
    B13 -->|Y| B13_Y
    B13 -->|N| B13_N
    S4["步骤 4: 规则判断 (104-104)"]
    S3 --> S4
    B17{"if @L104: (discount.compareTo(amount) ＞ 0)"}
    S4 --> B17
    B17_Y["进入分支"]
    B17_N["跳过分支"]
    B17 -->|Y| B17_Y
    B17 -->|N| B17_N
    S5["步骤 5: 数值计算处理 (108-109)"]
    S4 --> S5
    B18{"if @L109: (payableAmount.compareTo(java.math.BigDecimal.ZERO) ＜ 0)"}
    S5 --> B18
    B18_Y["进入分支"]
    B18_N["跳过分支"]
    B18 -->|Y| B18_Y
    B18 -->|N| B18_N
    S6["步骤 6: 集合内容校验与去重 (113-118)"]
    S5 --> S6
    B19{"if @L118: (manualReview && payableAmount.compareTo(new java.math.BigDecimal('..."}
    S6 --> B19
    B19_Y["进入分支"]
    B19_N["跳过分支"]
    B19 -->|Y| B19_Y
    B19 -->|N| B19_N
    S7["步骤 7: 规则判断 (127-131)"]
    S6 --> S7
    B21{"if @L127: (vip && payableAmount.compareTo(new java.math.BigDecimal('5000')) ＞..."}
    S7 --> B21
    B21_Y["进入分支"]
    B21_N["跳过分支"]
    B21 -->|Y| B21_Y
    B21 -->|N| B21_N
    B22{"if @L129: (vip)"}
    B21_Y --> B22
    B22_Y["进入分支"]
    B22_N["跳过分支"]
    B22 -->|Y| B22_Y
    B22 -->|N| B22_N
    B23{"if @L131: (payableAmount.compareTo(new java.math.BigDecimal('3000')) ＞= 0)"}
    B22_Y --> B23
    B23_Y["进入分支"]
    B23_N["跳过分支"]
    B23 -->|Y| B23_Y
    B23 -->|N| B23_N
    S8["步骤 8: 条件校验与分支判断 (139-139)"]
    S7 --> S8
    U0["未归组分支"]
    M0 --> U0
    UB1{"if @L41: (rawTags != null)"}
    U0 --> UB1
    UB1_Y["进入分支"]
    UB1_N["跳过分支"]
    UB1 -->|Y| UB1_Y
    UB1 -->|N| UB1_N
    UB2{"if @L43: (tag == null)"}
    UB1_Y --> UB2
    UB2_Y["进入分支"]
    UB2_N["跳过分支"]
    UB2 -->|Y| UB2_Y
    UB2 -->|N| UB2_N
    UB4{"if @L61: (missingCustomer)"}
    UB2_Y --> UB4
    UB4_Y["进入分支"]
    UB4_N["跳过分支"]
    UB4 -->|Y| UB4_Y
    UB4 -->|N| UB4_N
    UB5{"if @L64: (missingOrderNo)"}
    UB4_Y --> UB5
    UB5_Y["进入分支"]
    UB5_N["跳过分支"]
    UB5 -->|Y| UB5_Y
    UB5 -->|N| UB5_N
    UB6{"if @L67: (invalidStatus)"}
    UB5_Y --> UB6
    UB6_Y["进入分支"]
    UB6_N["跳过分支"]
    UB6 -->|Y| UB6_Y
    UB6 -->|N| UB6_N
    UB7{"if @L70: (negativeAmount)"}
    UB6_Y --> UB7
    UB7_Y["进入分支"]
    UB7_N["跳过分支"]
    UB7 -->|Y| UB7_Y
    UB7 -->|N| UB7_N
    UB8{"if @L73: (negativeDiscount)"}
    UB7_Y --> UB8
    UB8_Y["进入分支"]
    UB8_N["跳过分支"]
    UB8 -->|Y| UB8_Y
    UB8 -->|N| UB8_N
    UB9{"if @L76: (discountTooLarge)"}
    UB8_Y --> UB9
    UB9_Y["进入分支"]
    UB9_N["跳过分支"]
    UB9 -->|Y| UB9_Y
    UB9 -->|N| UB9_N
    UB14{"if @L92: (invalidStatus)"}
    UB9_Y --> UB14
    UB14_Y["进入分支"]
    UB14_N["跳过分支"]
    UB14 -->|Y| UB14_Y
    UB14 -->|N| UB14_N
    UB15{"if @L96: (negativeAmount)"}
    UB14_Y --> UB15
    UB15_Y["进入分支"]
    UB15_N["跳过分支"]
    UB15 -->|Y| UB15_Y
    UB15 -->|N| UB15_N
    UB16{"if @L100: (negativeDiscount)"}
    UB15_Y --> UB16
    UB16_Y["进入分支"]
    UB16_N["跳过分支"]
    UB16 -->|Y| UB16_Y
    UB16 -->|N| UB16_N
    UB20{"if @L120: (manualReview // urgent)"}
    UB16_Y --> UB20
    UB20_Y["进入分支"]
    UB20_N["跳过分支"]
    UB20 -->|Y| UB20_Y
    UB20 -->|N| UB20_N
    UB24["return @L155: return snapshot.toString()"]
    UB20_Y --> UB24
    T2(["RETURN @L155"])
    UB24 --> T2
```

### 主流程调用明细

- [1] `normalizedTag.isEmpty()` | type=`library_value_method` | line=`47`
- [2] `tags.contains(normalizedTag)` | type=`library_value_method` | line=`47`
- [3] `customerName.isEmpty()` | type=`library_value_method` | line=`53`
- [4] `orderNo.isEmpty()` | type=`library_value_method` | line=`54`
- [5] `"CREATED".equals(status)` | type=`library_value_method` | line=`55`
- [6] `"PAID".equals(status)` | type=`library_value_method` | line=`55`
- [7] `"CANCELLED".equals(status)` | type=`library_value_method` | line=`55`
- [8] `amount.compareTo(java.math.BigDecimal.ZERO)` | type=`library_value_method` | line=`56`
- [9] `discount.compareTo(java.math.BigDecimal.ZERO)` | type=`library_value_method` | line=`57`
- [10] `discount.compareTo(amount)` | type=`library_value_method` | line=`58`
- [11] `issues.isEmpty()` | type=`library_value_method` | line=`80`
- [12] `customerName.isEmpty()` | type=`library_value_method` | line=`84`
- [13] `orderNo.isEmpty()` | type=`library_value_method` | line=`88`
- [14] `discount.compareTo(amount)` | type=`library_value_method` | line=`104`
- [15] `amount.subtract(discount)` | type=`library_value_method` | line=`108`
- [16] `payableAmount.compareTo(java.math.BigDecimal.ZERO)` | type=`library_value_method` | line=`109`
- [17] `tags.contains("vip")` | type=`library_value_method` | line=`113`
- [18] `tags.contains("urgent")` | type=`library_value_method` | line=`114`
- [19] `tags.contains("manual-review")` | type=`library_value_method` | line=`115`
- [20] `issues.isEmpty()` | type=`library_value_method` | line=`115`
- [21] `payableAmount.compareTo(new java.math.BigDecimal("10000"))` | type=`library_value_method` | line=`118`
- [22] `payableAmount.compareTo(new java.math.BigDecimal("5000"))` | type=`library_value_method` | line=`127`
- [23] `payableAmount.compareTo(new java.math.BigDecimal("3000"))` | type=`library_value_method` | line=`131`
- [24] `issues.isEmpty()` | type=`library_value_method` | line=`139`

### 分支信息

- [1] `if` | line=`41` | (rawTags != null)
- [2] `if` | line=`43` | (tag == null)
- [3] `if` | line=`47` | (!normalizedTag.isEmpty() && !tags.contains(normalizedTag))
- [4] `if` | line=`61` | (missingCustomer)
- [5] `if` | line=`64` | (missingOrderNo)
- [6] `if` | line=`67` | (invalidStatus)
- [7] `if` | line=`70` | (negativeAmount)
- [8] `if` | line=`73` | (negativeDiscount)
- [9] `if` | line=`76` | (discountTooLarge)
- [10] `if` | line=`80` | (strictMode && !issues.isEmpty())
- [11] `return` | line=`81` | return "ORDER_SNAPSHOT{valid=false,mode=strict,issues=" + issues + "}";
- [12] `if` | line=`84` | (customerName.isEmpty())
- [13] `if` | line=`88` | (orderNo.isEmpty())
- [14] `if` | line=`92` | (invalidStatus)
- [15] `if` | line=`96` | (negativeAmount)
- [16] `if` | line=`100` | (negativeDiscount)
- [17] `if` | line=`104` | (discount.compareTo(amount) > 0)
- [18] `if` | line=`109` | (payableAmount.compareTo(java.math.BigDecimal.ZERO) < 0)
- [19] `if` | line=`118` | (manualReview && payableAmount.compareTo(new java.math.BigDecimal("10000")) > 0)
- [20] `if` | line=`120` | (manualReview || urgent)
- [21] `if` | line=`127` | (vip && payableAmount.compareTo(new java.math.BigDecimal("5000")) >= 0)
- [22] `if` | line=`129` | (vip)
- [23] `if` | line=`131` | (payableAmount.compareTo(new java.math.BigDecimal("3000")) >= 0)
- [24] `return` | line=`155` | return snapshot.toString();

### 方法源码

```java
public static String buildNormalizedOrderSnapshot(
            String rawCustomerName,
            String rawOrderNo,
            String rawStatus,
            java.math.BigDecimal rawAmount,
            java.math.BigDecimal discountAmount,
            java.util.List<String> rawTags,
            boolean strictMode
    ) {
        String customerName = rawCustomerName == null ? "" : rawCustomerName.trim();
        String orderNo = rawOrderNo == null ? "" : rawOrderNo.trim();
        String status = rawStatus == null ? "" : rawStatus.trim().toUpperCase();

        java.math.BigDecimal amount = rawAmount == null ? java.math.BigDecimal.ZERO : rawAmount;
        java.math.BigDecimal discount = discountAmount == null ? java.math.BigDecimal.ZERO : discountAmount;

        java.util.List<String> tags = new java.util.ArrayList<>();
        if (rawTags != null) {
            for (String tag : rawTags) {
                if (tag == null) {
                    continue;
                }
                String normalizedTag = tag.trim().toLowerCase();
                if (!normalizedTag.isEmpty() && !tags.contains(normalizedTag)) {
                    tags.add(normalizedTag);
                }
            }
        }

        boolean missingCustomer = customerName.isEmpty();
        boolean missingOrderNo = orderNo.isEmpty();
        boolean invalidStatus = !("CREATED".equals(status) || "PAID".equals(status) || "CANCELLED".equals(status));
        boolean negativeAmount = amount.compareTo(java.math.BigDecimal.ZERO) < 0;
        boolean negativeDiscount = discount.compareTo(java.math.BigDecimal.ZERO) < 0;
        boolean discountTooLarge = discount.compareTo(amount) > 0;

        java.util.List<String> issues = new java.util.ArrayList<>();
        if (missingCustomer) {
            issues.add("missing_customer");
        }
        if (missingOrderNo) {
            issues.add("missing_order_no");
        }
        if (invalidStatus) {
            issues.add("invalid_status");
        }
        if (negativeAmount) {
            issues.add("negative_amount");
        }
        if (negativeDiscount) {
            issues.add("negative_discount");
        }
        if (discountTooLarge) {
            issues.add("discount_too_large");
        }

        if (strictMode && !issues.isEmpty()) {
            return "ORDER_SNAPSHOT{valid=false,mode=strict,issues=" + issues + "}";
        }

        if (customerName.isEmpty()) {
            customerName = "UNKNOWN_CUSTOMER";
        }

        if (orderNo.isEmpty()) {
            orderNo = "NO_ORDER_NO";
        }

        if (invalidStatus) {
            status = "CREATED";
        }

        if (negativeAmount) {
            amount = java.math.BigDecimal.ZERO;
        }

        if (negativeDiscount) {
            discount = java.math.BigDecimal.ZERO;
        }

        if (discount.compareTo(amount) > 0) {
            discount = amount;
        }

        java.math.BigDecimal payableAmount = amount.subtract(discount);
        if (payableAmount.compareTo(java.math.BigDecimal.ZERO) < 0) {
            payableAmount = java.math.BigDecimal.ZERO;
        }

        boolean vip = tags.contains("vip");
        boolean urgent = tags.contains("urgent");
        boolean manualReview = tags.contains("manual-review") || !issues.isEmpty();

        String riskLevel;
        if (manualReview && payableAmount.compareTo(new java.math.BigDecimal("10000")) > 0) {
            riskLevel = "HIGH";
        } else if (manualReview || urgent) {
            riskLevel = "MEDIUM";
        } else {
            riskLevel = "LOW";
        }

        String customerSegment;
        if (vip && payableAmount.compareTo(new java.math.BigDecimal("5000")) >= 0) {
            customerSegment = "VIP_HIGH_VALUE";
        } else if (vip) {
            customerSegment = "VIP";
        } else if (payableAmount.compareTo(new java.math.BigDecimal("3000")) >= 0) {
            customerSegment = "HIGH_VALUE";
        } else {
            customerSegment = "NORMAL";
        }

        StringBuilder snapshot = new StringBuilder();
        snapshot.append("ORDER_SNAPSHOT{");
        snapshot.append("valid=").append(issues.isEmpty());
        snapshot.append(",customer=").append(customerName);
        snapshot.append(",orderNo=").append(orderNo);
        snapshot.append(",status=").append(status);
        snapshot.append(",amount=").append(amount);
        snapshot.append(",discount=").append(discount);
        snapshot.append(",payable=").append(payableAmount);
        snapshot.append(",segment=").append(customerSegment);
        snapshot.append(",risk=").append(riskLevel);
        snapshot.append(",vip=").append(vip);
        snapshot.append(",urgent=").append(urgent);
        snapshot.append(",manualReview=").append(manualReview);
        snapshot.append(",tags=").append(tags);
        snapshot.append(",issues=").append(issues);
        snapshot.append("}");

        return snapshot.toString();
    }
```
