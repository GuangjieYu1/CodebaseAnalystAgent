package com.example.ordersystem.domain.order;

public enum OrderStatus {
    CREATED,
    PAID,
    CANCELLED;

    public boolean canTransitTo(OrderStatus targetStatus) {
        if (targetStatus == null || this == targetStatus) {
            return false;
        }
        return this == CREATED && (targetStatus == PAID || targetStatus == CANCELLED);
    }
}
