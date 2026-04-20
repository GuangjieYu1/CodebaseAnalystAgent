package com.example.ordersystem.application.order.command;

import java.math.BigDecimal;

public class CreateOrderCommand {

    private final String customerName;
    private final BigDecimal amount;

    public CreateOrderCommand(String customerName, BigDecimal amount) {
        this.customerName = customerName;
        this.amount = amount;
    }

    public String getCustomerName() {
        return customerName;
    }

    public BigDecimal getAmount() {
        return amount;
    }
}
