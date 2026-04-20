package com.example.ordersystem.common.exception;

public enum ErrorCode {
    INVALID_REQUEST("INVALID_REQUEST", "The request parameters are invalid"),
    ORDER_NOT_FOUND("ORDER_NOT_FOUND", "The order does not exist"),
    INVALID_ORDER_STATUS("INVALID_ORDER_STATUS", "The order status is invalid"),
    INTERNAL_ERROR("INTERNAL_ERROR", "Internal server error");

    private final String code;
    private final String defaultMessage;

    ErrorCode(String code, String defaultMessage) {
        this.code = code;
        this.defaultMessage = defaultMessage;
    }

    public String getCode() {
        return code;
    }

    public String getDefaultMessage() {
        return defaultMessage;
    }
}
