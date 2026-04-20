package com.example.ordersystem.infrastructure.order.support;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class TimestampOrderNumberGeneratorTest {

    private final TimestampOrderNumberGenerator generator = new TimestampOrderNumberGenerator();

    @Test
    void shouldGenerateOrderNumberWithExpectedPrefix() {
        String orderNo = generator.nextOrderNo();

        assertThat(orderNo).startsWith("ORD-");
        assertThat(orderNo).matches("ORD-\\d{14}-[0-9a-f]{8}");
    }
}
