package com.example.ordersystem.domain.order;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class OrderStatusTest {

    @Test
    void shouldAllowCreatedToTransitToPaidOrCancelled() {
        assertThat(OrderStatus.CREATED.canTransitTo(OrderStatus.PAID)).isTrue();
        assertThat(OrderStatus.CREATED.canTransitTo(OrderStatus.CANCELLED)).isTrue();
    }

    @Test
    void shouldRejectUnsupportedTransitions() {
        assertThat(OrderStatus.PAID.canTransitTo(OrderStatus.CANCELLED)).isFalse();
        assertThat(OrderStatus.CANCELLED.canTransitTo(OrderStatus.PAID)).isFalse();
        assertThat(OrderStatus.CREATED.canTransitTo(OrderStatus.CREATED)).isFalse();
    }

    @Test
    void shouldUpdateOrderStatusWhenTransitionIsValid() {
        Order order = Order.newCreated(
                "ORD-001",
                "Alice",
                new BigDecimal("99.99"),
                LocalDateTime.of(2026, 4, 21, 10, 0)
        );

        order.changeStatus(OrderStatus.PAID, LocalDateTime.of(2026, 4, 21, 11, 0));

        assertThat(order.getStatus()).isEqualTo(OrderStatus.PAID);
        assertThat(order.getUpdatedAt()).isEqualTo(LocalDateTime.of(2026, 4, 21, 11, 0));
    }

    @Test
    void shouldThrowWhenTransitionIsInvalid() {
        Order order = Order.newCreated(
                "ORD-001",
                "Alice",
                new BigDecimal("99.99"),
                LocalDateTime.of(2026, 4, 21, 10, 0)
        );
        order.changeStatus(OrderStatus.PAID, LocalDateTime.of(2026, 4, 21, 11, 0));

        assertThatThrownBy(() -> order.changeStatus(OrderStatus.CANCELLED, LocalDateTime.of(2026, 4, 21, 12, 0)))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Unsupported order status transition");
    }
}
