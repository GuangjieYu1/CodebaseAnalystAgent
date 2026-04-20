package com.example.ordersystem.application.order;

import com.example.ordersystem.application.order.assembler.OrderRepresentationAssembler;
import com.example.ordersystem.application.order.command.ChangeOrderStatusCommand;
import com.example.ordersystem.application.order.command.CreateOrderCommand;
import com.example.ordersystem.application.order.dto.OrderDetailResponse;
import com.example.ordersystem.application.order.dto.OrderSummaryResponse;
import com.example.ordersystem.common.api.PageResponse;
import com.example.ordersystem.common.exception.BusinessException;
import com.example.ordersystem.common.exception.ErrorCode;
import com.example.ordersystem.common.model.PageResult;
import com.example.ordersystem.domain.order.Order;
import com.example.ordersystem.domain.order.OrderNumberGenerator;
import com.example.ordersystem.domain.order.OrderRepository;
import com.example.ordersystem.domain.order.OrderStatus;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Service
@Transactional(readOnly = true)
public class OrderApplicationService {

    private final OrderRepository orderRepository;
    private final OrderNumberGenerator orderNumberGenerator;

    public OrderApplicationService(OrderRepository orderRepository, OrderNumberGenerator orderNumberGenerator) {
        this.orderRepository = orderRepository;
        this.orderNumberGenerator = orderNumberGenerator;
    }

    @Transactional
    public OrderDetailResponse createOrder(CreateOrderCommand command) {
        validateCustomerName(command.getCustomerName());
        validateAmount(command.getAmount());
        LocalDateTime now = LocalDateTime.now();
        Order order = Order.newCreated(
                orderNumberGenerator.nextOrderNo(),
                command.getCustomerName().trim(),
                command.getAmount(),
                now
        );
        Order savedOrder = orderRepository.save(order);
        return OrderRepresentationAssembler.toDetailResponse(savedOrder);
    }

    public OrderDetailResponse getOrder(String orderNo) {
        return OrderRepresentationAssembler.toDetailResponse(loadOrder(orderNo));
    }

    public PageResponse<OrderSummaryResponse> listOrders(int page, int size, OrderStatus status, String customerName) {
        PageResult<Order> pageResult = orderRepository.findPage(page, size, status, normalize(customerName));
        return OrderRepresentationAssembler.toPageResponse(pageResult);
    }

    @Transactional
    public OrderDetailResponse changeOrderStatus(String orderNo, ChangeOrderStatusCommand command) {
        Order order = loadOrder(orderNo);
        try {
            order.changeStatus(command.getTargetStatus(), LocalDateTime.now());
        } catch (IllegalArgumentException exception) {
            throw new BusinessException(
                    ErrorCode.INVALID_ORDER_STATUS,
                    HttpStatus.CONFLICT,
                    exception.getMessage()
            );
        }
        orderRepository.update(order);
        return OrderRepresentationAssembler.toDetailResponse(order);
    }

    private Order loadOrder(String orderNo) {
        return orderRepository.findByOrderNo(orderNo)
                .orElseThrow(() -> new BusinessException(
                        ErrorCode.ORDER_NOT_FOUND,
                        HttpStatus.NOT_FOUND,
                        "Order not found: " + orderNo
                ));
    }

    private String normalize(String customerName) {
        if (!StringUtils.hasText(customerName)) {
            return null;
        }
        return customerName.trim();
    }

    private void validateAmount(BigDecimal amount) {
        if (amount == null || amount.signum() <= 0) {
            throw new BusinessException(
                    ErrorCode.INVALID_REQUEST,
                    HttpStatus.BAD_REQUEST,
                    "amount must be greater than 0"
            );
        }
    }

    private void validateCustomerName(String customerName) {
        if (!StringUtils.hasText(customerName)) {
            throw new BusinessException(
                    ErrorCode.INVALID_REQUEST,
                    HttpStatus.BAD_REQUEST,
                    "customerName must not be blank"
            );
        }
    }
}
