package com.example.ordersystem.controller.request;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public class CreateOrderRequest {

    @NotBlank(message = "must not be blank")
    @Size(max = 64, message = "length must be less than or equal to 64")
    private String customerName;

    @NotNull(message = "must not be null")
    @DecimalMin(value = "0.01", message = "must be greater than 0")
    @Digits(integer = 12, fraction = 2, message = "must be a valid monetary amount")
    private BigDecimal amount;

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = customerName;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }
}
