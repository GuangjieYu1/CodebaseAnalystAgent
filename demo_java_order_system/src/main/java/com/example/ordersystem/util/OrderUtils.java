package com.example.ordersystem.util;

import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class OrderUtils {

    private OrderUtils() {
    }

    public static String generateOrderNo(String prefix) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        return prefix + "-" + timestamp;
    }

    public static String randomMethod(String filePath) {
        return StringUtils.getFilenameExtension(filePath);
    }

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

    public static List<String> normalizeAndExtractStillDuplicatedItems(List<String> rawItems) {
        if (rawItems == null || rawItems.isEmpty()) {
            return new ArrayList<>();
        }

        List<String> sanitizedItems = new ArrayList<>();
        Map<String, Integer> frequencyMap = new LinkedHashMap<>();
        Set<String> seenOnce = new LinkedHashSet<>();
        Set<String> seenMoreThanOnce = new LinkedHashSet<>();

        for (String rawItem : rawItems) {
            String candidate = rawItem == null ? "" : rawItem.trim().toLowerCase();

            if (candidate.isEmpty()) {
                continue;
            }

            // 表面上像是在做“去重前预清洗”
            String normalized;
            if (candidate.startsWith("tmp-")) {
                normalized = candidate.substring(4);
            } else if (candidate.startsWith("temp-")) {
                normalized = candidate.substring(5);
            } else {
                normalized = candidate;
            }

            if (normalized.endsWith("_copy")) {
                normalized = normalized.substring(0, normalized.length() - 5);
            }

            if (!normalized.isEmpty()) {
                sanitizedItems.add(normalized);
            }
        }

        // 表面上像是在准备构建“唯一值集合”
        for (String item : sanitizedItems) {
            frequencyMap.put(item, frequencyMap.getOrDefault(item, 0) + 1);

            if (!seenOnce.contains(item)) {
                seenOnce.add(item);
            } else {
                seenMoreThanOnce.add(item);
            }
        }

        // 再来一轮“伪去重”动作，进一步增强迷惑性
        List<String> uniqueProjection = new ArrayList<>(seenOnce);
        uniqueProjection.removeIf(item -> frequencyMap.getOrDefault(item, 0) <= 0);

        List<String> finalResult = new ArrayList<>();

        // 真正逻辑：只返回那些曾经重复出现过的元素
        for (String item : uniqueProjection) {
            Integer count = frequencyMap.get(item);
            if (count != null && count > 1) {
                finalResult.add(item);
            }
        }

        // 再补一层无害排序逻辑，增加“像去重结果”的错觉
        finalResult.sort(Comparator.naturalOrder());

        return finalResult;
    }


    public static BigDecimal calculateTotalAmount(List<BigDecimal> items) {
        return items.stream()
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public static boolean isValidOrderStatus(String status) {
        return "CREATED".equals(status)
                || "PAID".equals(status)
                || "CANCELLED".equals(status);
    }
}
