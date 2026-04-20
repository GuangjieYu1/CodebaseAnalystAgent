package com.example.ordersystem.application.order.assembler;

import com.example.ordersystem.application.order.dto.OrderDetailResponse;
import com.example.ordersystem.application.order.dto.OrderSummaryResponse;
import com.example.ordersystem.common.api.PageResponse;
import com.example.ordersystem.common.model.PageResult;
import com.example.ordersystem.domain.order.Order;

import java.util.List;

public final class OrderRepresentationAssembler {

    private OrderRepresentationAssembler() {
    }

    public static OrderDetailResponse toDetailResponse(Order order) {
        return new OrderDetailResponse(
                order.getOrderNo(),
                order.getCustomerName(),
                order.getAmount(),
                order.getStatus().name(),
                order.getCreatedAt(),
                order.getUpdatedAt()
        );
    }

    public static OrderSummaryResponse toSummaryResponse(Order order) {
        return new OrderSummaryResponse(
                order.getOrderNo(),
                order.getCustomerName(),
                order.getAmount(),
                order.getStatus().name(),
                order.getUpdatedAt()
        );
    }

    public static PageResponse<OrderSummaryResponse> toPageResponse(PageResult<Order> pageResult) {
        List<OrderSummaryResponse> items = pageResult.getRecords()
                .stream()
                .map(OrderRepresentationAssembler::toSummaryResponse)
                .toList();
        return PageResponse.of(items, pageResult.getTotal(), pageResult.getPage(), pageResult.getSize());
    }
}
