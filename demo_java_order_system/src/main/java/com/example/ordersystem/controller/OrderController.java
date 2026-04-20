package com.example.ordersystem.controller;

import com.example.ordersystem.application.order.OrderApplicationService;
import com.example.ordersystem.application.order.command.ChangeOrderStatusCommand;
import com.example.ordersystem.application.order.command.CreateOrderCommand;
import com.example.ordersystem.application.order.dto.OrderDetailResponse;
import com.example.ordersystem.application.order.dto.OrderSummaryResponse;
import com.example.ordersystem.common.api.ApiResponse;
import com.example.ordersystem.common.api.PageResponse;
import com.example.ordersystem.controller.request.ChangeOrderStatusRequest;
import com.example.ordersystem.controller.request.CreateOrderRequest;
import com.example.ordersystem.domain.order.OrderStatus;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderApplicationService orderApplicationService;

    public OrderController(OrderApplicationService orderApplicationService) {
        this.orderApplicationService = orderApplicationService;
    }

    @Operation(summary = "Create an order")
    @PostMapping
    public ResponseEntity<ApiResponse<OrderDetailResponse>> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        OrderDetailResponse response = orderApplicationService.createOrder(
                new CreateOrderCommand(request.getCustomerName(), request.getAmount())
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.success(response));
    }

    @Operation(summary = "Get an order by order number")
    @GetMapping("/{orderNo}")
    public ApiResponse<OrderDetailResponse> getOrder(@PathVariable @NotBlank String orderNo) {
        return ApiResponse.success(orderApplicationService.getOrder(orderNo));
    }

    @Operation(summary = "List orders")
    @GetMapping
    public ApiResponse<PageResponse<OrderSummaryResponse>> listOrders(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            @RequestParam(required = false) OrderStatus status,
            @RequestParam(required = false) String customerName
    ) {
        return ApiResponse.success(orderApplicationService.listOrders(page, size, status, customerName));
    }

    @Operation(summary = "Change order status")
    @PatchMapping("/{orderNo}/status")
    public ApiResponse<OrderDetailResponse> changeOrderStatus(
            @PathVariable @NotBlank String orderNo,
            @Valid @RequestBody ChangeOrderStatusRequest request
    ) {
        return ApiResponse.success(orderApplicationService.changeOrderStatus(
                orderNo,
                new ChangeOrderStatusCommand(request.getTargetStatus())
        ));
    }
}
