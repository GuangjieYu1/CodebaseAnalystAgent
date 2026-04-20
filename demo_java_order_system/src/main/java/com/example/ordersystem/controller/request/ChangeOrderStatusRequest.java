package com.example.ordersystem.controller.request;

import com.example.ordersystem.domain.order.OrderStatus;
import jakarta.validation.constraints.NotNull;

public class ChangeOrderStatusRequest {

    @NotNull(message = "must not be null")
    private OrderStatus targetStatus;

    public OrderStatus getTargetStatus() {
        return targetStatus;
    }

    public void setTargetStatus(OrderStatus targetStatus) {
        this.targetStatus = targetStatus;
    }
}
