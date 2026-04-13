package com.example.ordersystem.repository;

import com.example.ordersystem.domain.Order;
import org.springframework.stereotype.Repository;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class OrderRepository {

    private final Map<String, Order> store = new ConcurrentHashMap<>();

    public void save(Order order) {
        store.put(order.getOrderNo(), order);
    }

    public Order findByOrderNo(String orderNo) {
        return store.get(orderNo);
    }
}
