package com.example.ordersystem.common.exception;

import org.springframework.http.HttpStatus;

public class BusinessException extends RuntimeException {

    private final ErrorCode errorCode;
    private final HttpStatus httpStatus;

    public BusinessException(ErrorCode errorCode, HttpStatus httpStatus, String message) {
        super(message);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }

    public HttpStatus getHttpStatus() {
        return httpStatus;
    }
}
