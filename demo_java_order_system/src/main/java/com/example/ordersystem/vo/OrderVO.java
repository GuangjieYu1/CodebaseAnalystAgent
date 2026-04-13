package com.example.ordersystem.vo;

import java.math.BigDecimal;

public class OrderVO {

    private String orderNo;
    private String customerName;
    private BigDecimal amount;
    private String status;

    public OrderVO(String orderNo, String customerName, BigDecimal amount, String status) {
        this.orderNo = orderNo;
        this.customerName = customerName;
        this.amount = amount;
        this.status = status;
    }

    public String getOrderNo() {
        return orderNo;
    }

    public String getCustomerName() {
        return customerName;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public String getStatus() {
        return status;
    }
}
