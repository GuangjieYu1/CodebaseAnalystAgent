package com.example.ordersystem.infrastructure.order.support;

import com.example.ordersystem.domain.order.OrderNumberGenerator;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

@Component
public class TimestampOrderNumberGenerator implements OrderNumberGenerator {

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

    @Override
    public String nextOrderNo() {
        return "ORD-" + LocalDateTime.now().format(FORMATTER) + "-" + UUID.randomUUID().toString().substring(0, 8);
    }
}
