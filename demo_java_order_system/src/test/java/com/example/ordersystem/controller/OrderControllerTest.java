package com.example.ordersystem.controller;

import com.example.ordersystem.application.order.OrderApplicationService;
import com.example.ordersystem.application.order.dto.OrderDetailResponse;
import com.example.ordersystem.application.order.dto.OrderSummaryResponse;
import com.example.ordersystem.common.api.PageResponse;
import com.example.ordersystem.common.exception.BusinessException;
import com.example.ordersystem.common.exception.ErrorCode;
import com.example.ordersystem.common.exception.GlobalExceptionHandler;
import com.example.ordersystem.common.tracing.TraceIdFilter;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.ImportAutoConfiguration;
import org.springframework.boot.autoconfigure.validation.ValidationAutoConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(OrderController.class)
@Import({GlobalExceptionHandler.class, TraceIdFilter.class})
@ImportAutoConfiguration(ValidationAutoConfiguration.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private OrderApplicationService orderApplicationService;

    @Test
    void shouldCreateOrderSuccessfully() throws Exception {
        OrderDetailResponse response = new OrderDetailResponse(
                "ORD-202604210001",
                "Alice",
                new BigDecimal("99.99"),
                "CREATED",
                LocalDateTime.of(2026, 4, 21, 10, 0),
                LocalDateTime.of(2026, 4, 21, 10, 0)
        );
        given(orderApplicationService.createOrder(any())).willReturn(response);

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new RequestBodyFixture("Alice", new BigDecimal("99.99")))))
                .andExpect(status().isCreated())
                .andExpect(header().exists("X-Trace-Id"))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.data.orderNo").value("ORD-202604210001"));
    }

    @Test
    void shouldRejectInvalidCreateRequest() throws Exception {
        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new RequestBodyFixture("", BigDecimal.ZERO))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_REQUEST"));
    }

    @Test
    void shouldReturnNotFoundWhenOrderDoesNotExist() throws Exception {
        given(orderApplicationService.getOrder("ORD-MISSING")).willThrow(
                new BusinessException(ErrorCode.ORDER_NOT_FOUND, HttpStatus.NOT_FOUND, "Order not found: ORD-MISSING")
        );

        mockMvc.perform(get("/api/v1/orders/ORD-MISSING"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("ORDER_NOT_FOUND"));
    }

    @Test
    void shouldReturnConflictForInvalidStatusTransition() throws Exception {
        given(orderApplicationService.changeOrderStatus(eq("ORD-001"), any())).willThrow(
                new BusinessException(
                        ErrorCode.INVALID_ORDER_STATUS,
                        HttpStatus.CONFLICT,
                        "Unsupported order status transition from PAID to CANCELLED"
                )
        );

        mockMvc.perform(patch("/api/v1/orders/ORD-001/status")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"targetStatus\":\"CANCELLED\"}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("INVALID_ORDER_STATUS"));
    }

    @Test
    void shouldReturnPagedOrders() throws Exception {
        PageResponse<OrderSummaryResponse> pageResponse = PageResponse.of(
                List.of(new OrderSummaryResponse(
                        "ORD-001",
                        "Alice",
                        new BigDecimal("99.99"),
                        "CREATED",
                        LocalDateTime.of(2026, 4, 21, 10, 0)
                )),
                1,
                0,
                20
        );
        given(orderApplicationService.listOrders(0, 20, null, null)).willReturn(pageResponse);

        mockMvc.perform(get("/api/v1/orders"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.total").value(1))
                .andExpect(jsonPath("$.data.items[0].orderNo").value("ORD-001"));
    }

    private record RequestBodyFixture(String customerName, BigDecimal amount) {
    }
}
