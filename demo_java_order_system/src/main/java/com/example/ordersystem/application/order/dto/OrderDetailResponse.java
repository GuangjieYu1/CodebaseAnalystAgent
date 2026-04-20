package com.example.ordersystem.application.order.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class OrderDetailResponse {

    private final String orderNo;
    private final String customerName;
    private final BigDecimal amount;
    private final String status;
    private final LocalDateTime createdAt;
    private final LocalDateTime updatedAt;

    public OrderDetailResponse(
            String orderNo,
            String customerName,
            BigDecimal amount,
            String status,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {
        this.orderNo = orderNo;
        this.customerName = customerName;
        this.amount = amount;
        this.status = status;
        this.createdAt = createdAt;
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

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}
