package com.example.ordersystem.service.impl;

import com.example.ordersystem.domain.Order;
import com.example.ordersystem.dto.CreateOrderRequest;
import com.example.ordersystem.repository.OrderRepository;
import com.example.ordersystem.service.OrderService;
import com.example.ordersystem.util.OrderUtils;
import com.example.ordersystem.vo.OrderVO;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.Collections;

@Service
public class OrderServiceImpl implements OrderService {

    private final OrderRepository orderRepository;

    public OrderServiceImpl(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Override
    public OrderVO createOrder(CreateOrderRequest request) {
        String orderNo = OrderUtils.generateOrderNo("ORD");
        BigDecimal totalAmount = OrderUtils.calculateTotalAmount(
                Collections.singletonList(request.getAmount())
        );

        Order order = new Order();
        order.setOrderNo(orderNo);
        order.setCustomerName(request.getCustomerName());
        order.setAmount(totalAmount);
        order.setStatus("CREATED");

        orderRepository.save(order);

        return new OrderVO(orderNo, request.getCustomerName(), totalAmount, "CREATED");
    }

    @Override
    public OrderVO getOrder(String orderNo) {
        Order order = orderRepository.findByOrderNo(orderNo);
        if (order == null) {
            return null;
        }
        return new OrderVO(
                order.getOrderNo(),
                order.getCustomerName(),
                order.getAmount(),
                order.getStatus()
        );
    }
}
