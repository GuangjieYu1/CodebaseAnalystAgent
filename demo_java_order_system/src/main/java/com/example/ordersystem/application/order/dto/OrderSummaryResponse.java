package com.example.ordersystem.application.order.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class OrderSummaryResponse {

    private final String orderNo;
    private final String customerName;
    private final BigDecimal amount;
    private final String status;
    private final LocalDateTime updatedAt;

    public OrderSummaryResponse(
            String orderNo,
            String customerName,
            BigDecimal amount,
            String status,
            LocalDateTime updatedAt
    ) {
        this.orderNo = orderNo;
        this.customerName = customerName;
        this.amount = amount;
        this.status = status;
        this.updatedAt = updatedAt;
    }

    public String getOrderNo() {
        return orderNo;
    }

    public String getCustomerName() {
        return customerName;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public String getStatus() {
        return status;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}
