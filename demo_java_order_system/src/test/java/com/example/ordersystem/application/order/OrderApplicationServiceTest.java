package com.example.ordersystem.application.order;

import com.example.ordersystem.application.order.command.ChangeOrderStatusCommand;
import com.example.ordersystem.application.order.command.CreateOrderCommand;
import com.example.ordersystem.application.order.dto.OrderDetailResponse;
import com.example.ordersystem.common.api.PageResponse;
import com.example.ordersystem.common.exception.BusinessException;
import com.example.ordersystem.common.model.PageResult;
import com.example.ordersystem.domain.order.Order;
import com.example.ordersystem.domain.order.OrderNumberGenerator;
import com.example.ordersystem.domain.order.OrderRepository;
import com.example.ordersystem.domain.order.OrderStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class OrderApplicationServiceTest {

    private OrderApplicationService service;

    @BeforeEach
    void setUp() {
        service = new OrderApplicationService(new InMemoryOrderRepository(), new FixedOrderNumberGenerator());
    }

    @Test
    void shouldCreateOrderSuccessfully() {
        OrderDetailResponse response = service.createOrder(new CreateOrderCommand("Alice", new BigDecimal("99.99")));

        assertThat(response.getOrderNo()).isEqualTo("ORD-TEST-0001");
        assertThat(response.getCustomerName()).isEqualTo("Alice");
        assertThat(response.getStatus()).isEqualTo(OrderStatus.CREATED.name());
    }

    @Test
    void shouldGetOrderByOrderNo() {
        service.createOrder(new CreateOrderCommand("Alice", new BigDecimal("99.99")));

        OrderDetailResponse response = service.getOrder("ORD-TEST-0001");

        assertThat(response.getCustomerName()).isEqualTo("Alice");
    }

    @Test
    void shouldChangeOrderStatus() {
        service.createOrder(new CreateOrderCommand("Alice", new BigDecimal("99.99")));

        OrderDetailResponse response = service.changeOrderStatus(
                "ORD-TEST-0001",
                new ChangeOrderStatusCommand(OrderStatus.PAID)
        );

        assertThat(response.getStatus()).isEqualTo(OrderStatus.PAID.name());
    }

    @Test
    void shouldReturnPagedOrders() {
        service.createOrder(new CreateOrderCommand("Alice", new BigDecimal("99.99")));
        service.createOrder(new CreateOrderCommand("Bob", new BigDecimal("199.99")));

        PageResponse<?> pageResponse = service.listOrders(0, 10, null, "A");

        assertThat(pageResponse.getTotal()).isEqualTo(1);
        assertThat(pageResponse.getItems()).hasSize(1);
    }

    @Test
    void shouldThrowNotFoundWhenOrderIsMissing() {
        assertThatThrownBy(() -> service.getOrder("ORD-NOT-EXIST"))
                .isInstanceOf(BusinessException.class)
                .satisfies(exception -> {
                    BusinessException businessException = (BusinessException) exception;
                    assertThat(businessException.getHttpStatus()).isEqualTo(HttpStatus.NOT_FOUND);
                });
    }

    @Test
    void shouldThrowConflictWhenTransitionIsInvalid() {
        service.createOrder(new CreateOrderCommand("Alice", new BigDecimal("99.99")));
        service.changeOrderStatus("ORD-TEST-0001", new ChangeOrderStatusCommand(OrderStatus.PAID));

        assertThatThrownBy(() -> service.changeOrderStatus(
                "ORD-TEST-0001",
                new ChangeOrderStatusCommand(OrderStatus.CANCELLED)
        )).isInstanceOf(BusinessException.class)
                .satisfies(exception -> {
                    BusinessException businessException = (BusinessException) exception;
                    assertThat(businessException.getHttpStatus()).isEqualTo(HttpStatus.CONFLICT);
                });
    }

    private static class FixedOrderNumberGenerator implements OrderNumberGenerator {

        private int sequence = 1;

        @Override
        public String nextOrderNo() {
            return "ORD-TEST-" + String.format("%04d", sequence++);
        }
    }

    private static class InMemoryOrderRepository implements OrderRepository {

        private final Map<String, Order> store = new LinkedHashMap<>();
        private long nextId = 1L;

        @Override
        public Order save(Order order) {
            order.setId(nextId++);
            store.put(order.getOrderNo(), order);
            return order;
        }

        @Override
        public Optional<Order> findByOrderNo(String orderNo) {
            return Optional.ofNullable(store.get(orderNo));
        }

        @Override
        public PageResult<Order> findPage(int page, int size, OrderStatus status, String customerName) {
            List<Order> matched = new ArrayList<>(store.values()).stream()
                    .filter(order -> status == null || order.getStatus() == status)
                    .filter(order -> customerName == null || order.getCustomerName().contains(customerName))
                    .sorted(Comparator.comparing(Order::getOrderNo))
                    .toList();
            return new PageResult<>(matched, matched.size(), page, size);
        }

        @Override
        public void update(Order order) {
            order.setUpdatedAt(LocalDateTime.now());
            store.put(order.getOrderNo(), order);
        }
    }
}
