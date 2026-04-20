package com.example.ordersystem.integration;

import com.jayway.jsonpath.JsonPath;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import javax.sql.DataSource;

import org.flywaydb.core.Flyway;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Testcontainers(disabledWithoutDocker = true)
class OrderSystemIntegrationTest {

    @Container
    static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.0.39")
            .withDatabaseName("demo_order_system_integration")
            .withUsername("demo")
            .withPassword("demo123");

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private DataSource dataSource;

    @DynamicPropertySource
    static void registerMysqlProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);
    }

    @BeforeEach
    void resetDatabase() {
        Flyway flyway = Flyway.configure()
                .cleanDisabled(false)
                .dataSource(dataSource)
                .locations("classpath:db/migration")
                .load();
        flyway.clean();
        flyway.migrate();
    }

    @Test
    void shouldRunCreateQueryAndStatusChangeFlow() throws Exception {
        mockMvc.perform(post("/api/v1/orders")
                        .contentType("application/json")
                        .content("""
                                {
                                  "customerName": "Alice",
                                  "amount": 99.99
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(header().exists("X-Trace-Id"))
                .andExpect(jsonPath("$.data.orderNo").exists())
                .andExpect(jsonPath("$.data.status").value("CREATED"));

        String orderNo = mockMvc.perform(get("/api/v1/orders"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.total").value(1))
                .andReturn()
                .getResponse()
                .getContentAsString();
        String extractedOrderNo = JsonPath.read(orderNo, "$.data.items[0].orderNo");

        mockMvc.perform(patch("/api/v1/orders/" + extractedOrderNo + "/status")
                        .contentType("application/json")
                        .content("""
                                {
                                  "targetStatus": "PAID"
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.status").value("PAID"));
    }
}
