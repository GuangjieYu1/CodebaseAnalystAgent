package com.example.ordersystem.service;

import com.example.ordersystem.dto.CreateOrderRequest;
import com.example.ordersystem.vo.OrderVO;

public interface OrderService {

    OrderVO createOrder(CreateOrderRequest request);

    OrderVO getOrder(String orderNo);
}
