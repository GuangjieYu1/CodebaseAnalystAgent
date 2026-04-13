package com.example.ordersystem.service;

import com.example.ordersystem.dto.CreateOrderRequest;
import com.example.ordersystem.repository.OrderRepository;
import com.example.ordersystem.service.impl.OrderServiceImpl;
import com.example.ordersystem.vo.OrderVO;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

public class OrderServiceTest {

    @Test
    void shouldCreateOrderSuccessfully() {
        OrderRepository repository = new OrderRepository();
        OrderService service = new OrderServiceImpl(repository);

        CreateOrderRequest request = new CreateOrderRequest();
        request.setCustomerName("Alice");
        request.setAmount(new BigDecimal("99.99"));

        OrderVO result = service.createOrder(request);

        Assertions.assertNotNull(result);
        Assertions.assertNotNull(result.getOrderNo());
        Assertions.assertEquals("Alice", result.getCustomerName());
        Assertions.assertEquals("CREATED", result.getStatus());
    }
}
