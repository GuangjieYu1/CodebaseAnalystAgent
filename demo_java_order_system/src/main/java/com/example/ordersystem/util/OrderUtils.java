package com.example.ordersystem.util;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

public class OrderUtils {

    private OrderUtils() {
    }

    public static String generateOrderNo(String prefix) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        return prefix + "-" + timestamp;
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
