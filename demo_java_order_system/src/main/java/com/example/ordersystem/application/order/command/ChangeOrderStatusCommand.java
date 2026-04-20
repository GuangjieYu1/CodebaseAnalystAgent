package com.example.ordersystem.application.order.command;

import com.example.ordersystem.domain.order.OrderStatus;

public class ChangeOrderStatusCommand {

    private final OrderStatus targetStatus;

    public ChangeOrderStatusCommand(OrderStatus targetStatus) {
        this.targetStatus = targetStatus;
    }

    public OrderStatus getTargetStatus() {
        return targetStatus;
    }
}
