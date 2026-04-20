package com.example.ordersystem.infrastructure.order.persistence.repository;

import com.example.ordersystem.common.model.PageResult;
import com.example.ordersystem.domain.order.Order;
import com.example.ordersystem.domain.order.OrderStatus;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mybatis.spring.boot.test.autoconfigure.MybatisTest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

@MybatisTest
@Import(MybatisOrderRepository.class)
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers(disabledWithoutDocker = true)
class MybatisOrderRepositoryTest {

    @Container
    static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.0.39")
            .withDatabaseName("demo_order_system_test")
            .withUsername("demo")
            .withPassword("demo123");

    @Autowired
    private MybatisOrderRepository repository;

    @DynamicPropertySource
    static void registerMysqlProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);
        registry.add("spring.flyway.enabled", () -> false);
    }

    @BeforeEach
    void setUpSchema() {
        Flyway flyway = Flyway.configure()
                .cleanDisabled(false)
                .dataSource(MYSQL.getJdbcUrl(), MYSQL.getUsername(), MYSQL.getPassword())
                .locations("classpath:db/migration")
                .load();
        flyway.clean();
        flyway.migrate();
    }

    @Test
    void shouldPersistAndQueryOrders() {
        Order order = Order.newCreated(
                "ORD-PERSIST-001",
                "Alice",
                new BigDecimal("99.99"),
                LocalDateTime.of(2026, 4, 21, 10, 0)
        );

        Order savedOrder = repository.save(order);
        PageResult<Order> pageResult = repository.findPage(0, 10, OrderStatus.CREATED, "Ali");

        assertThat(savedOrder.getId()).isNotNull();
        assertThat(repository.findByOrderNo("ORD-PERSIST-001")).isPresent();
        assertThat(pageResult.getTotal()).isEqualTo(1);
    }

    @Test
    void shouldUpdateOrderStatus() {
        Order order = repository.save(Order.newCreated(
                "ORD-PERSIST-002",
                "Bob",
                new BigDecimal("199.99"),
                LocalDateTime.of(2026, 4, 21, 10, 0)
        ));
        order.changeStatus(OrderStatus.PAID, LocalDateTime.of(2026, 4, 21, 11, 0));

        repository.update(order);

        assertThat(repository.findByOrderNo("ORD-PERSIST-002"))
                .get()
                .extracting(Order::getStatus)
                .isEqualTo(OrderStatus.PAID);
    }
}
