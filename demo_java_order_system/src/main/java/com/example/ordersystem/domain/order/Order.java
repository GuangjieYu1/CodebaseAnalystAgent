package com.example.ordersystem.domain.order;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Objects;

public class Order {

    private Long id;
    private String orderNo;
    private String customerName;
    private BigDecimal amount;
    private OrderStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static Order newCreated(String orderNo, String customerName, BigDecimal amount, LocalDateTime now) {
        Order order = new Order();
        order.setOrderNo(orderNo);
        order.setCustomerName(customerName);
        order.setAmount(amount);
        order.setStatus(OrderStatus.CREATED);
        order.setCreatedAt(now);
        order.setUpdatedAt(now);
        return order;
    }

    public void changeStatus(OrderStatus targetStatus, LocalDateTime now) {
        Objects.requireNonNull(targetStatus, "targetStatus must not be null");
        Objects.requireNonNull(now, "updatedAt must not be null");
        if (!status.canTransitTo(targetStatus)) {
            throw new IllegalArgumentException(
                    "Unsupported order status transition from " + status + " to " + targetStatus
            );
        }
        this.status = targetStatus;
        this.updatedAt = now;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getOrderNo() {
        return orderNo;
    }

    public void setOrderNo(String orderNo) {
        this.orderNo = orderNo;
    }

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = customerName;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public OrderStatus getStatus() {
        return status;
    }

    public void setStatus(OrderStatus status) {
        this.status = status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
