package com.example.ordersystem.domain.order;

import com.example.ordersystem.common.model.PageResult;

import java.util.Optional;

public interface OrderRepository {

    Order save(Order order);

    Optional<Order> findByOrderNo(String orderNo);

    PageResult<Order> findPage(int page, int size, OrderStatus status, String customerName);

    void update(Order order);
}
