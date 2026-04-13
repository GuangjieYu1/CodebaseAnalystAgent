package com.example.ordersystem.controller;

import com.example.ordersystem.dto.CreateOrderRequest;
import com.example.ordersystem.service.OrderService;
import com.example.ordersystem.vo.OrderVO;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public OrderVO createOrder(@RequestBody CreateOrderRequest request) {
        return orderService.createOrder(request);
    }

    @GetMapping("/{orderNo}")
    public OrderVO getOrder(@PathVariable String orderNo) {
        return orderService.getOrder(orderNo);
    }
}
