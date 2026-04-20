package com.example.ordersystem.infrastructure.order.persistence.repository;

import com.example.ordersystem.common.model.PageResult;
import com.example.ordersystem.domain.order.Order;
import com.example.ordersystem.domain.order.OrderRepository;
import com.example.ordersystem.domain.order.OrderStatus;
import com.example.ordersystem.infrastructure.order.persistence.mapper.OrderMapper;
import com.example.ordersystem.infrastructure.order.persistence.po.OrderPO;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public class MybatisOrderRepository implements OrderRepository {

    private final OrderMapper orderMapper;

    public MybatisOrderRepository(OrderMapper orderMapper) {
        this.orderMapper = orderMapper;
    }

    @Override
    public Order save(Order order) {
        OrderPO orderPO = toPersistence(order);
        orderMapper.insert(orderPO);
        return toDomain(orderPO);
    }

    @Override
    public Optional<Order> findByOrderNo(String orderNo) {
        return Optional.ofNullable(orderMapper.selectByOrderNo(orderNo))
                .map(this::toDomain);
    }

    @Override
    public PageResult<Order> findPage(int page, int size, OrderStatus status, String customerName) {
        int offset = page * size;
        List<Order> orders = orderMapper.selectPage(offset, size, status == null ? null : status.name(), customerName)
                .stream()
                .map(this::toDomain)
                .toList();
        long total = orderMapper.countPage(status == null ? null : status.name(), customerName);
        return new PageResult<>(orders, total, page, size);
    }

    @Override
    public void update(Order order) {
        orderMapper.updateStatusByOrderNo(order.getOrderNo(), order.getStatus().name(), order.getUpdatedAt());
    }

    private Order toDomain(OrderPO orderPO) {
        Order order = new Order();
        order.setId(orderPO.getId());
        order.setOrderNo(orderPO.getOrderNo());
        order.setCustomerName(orderPO.getCustomerName());
        order.setAmount(orderPO.getAmount());
        order.setStatus(OrderStatus.valueOf(orderPO.getStatus()));
        order.setCreatedAt(orderPO.getCreatedAt());
        order.setUpdatedAt(orderPO.getUpdatedAt());
        return order;
    }

    private OrderPO toPersistence(Order order) {
        OrderPO orderPO = new OrderPO();
        orderPO.setId(order.getId());
        orderPO.setOrderNo(order.getOrderNo());
        orderPO.setCustomerName(order.getCustomerName());
        orderPO.setAmount(order.getAmount());
        orderPO.setStatus(order.getStatus().name());
        orderPO.setCreatedAt(order.getCreatedAt());
        orderPO.setUpdatedAt(order.getUpdatedAt());
        return orderPO;
    }
}
