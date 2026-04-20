package com.example.ordersystem.common.api;

import com.example.ordersystem.common.tracing.TraceIdHolder;

import java.time.OffsetDateTime;

public class ApiResponse<T> {

    private final String code;
    private final String message;
    private final T data;
    private final String traceId;
    private final OffsetDateTime timestamp;

    private ApiResponse(String code, String message, T data, String traceId, OffsetDateTime timestamp) {
        this.code = code;
        this.message = message;
        this.data = data;
        this.traceId = traceId;
        this.timestamp = timestamp;
    }

    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(
                "SUCCESS",
                "Request completed successfully",
                data,
                TraceIdHolder.getOrCreateTraceId(),
                OffsetDateTime.now()
        );
    }

    public static <T> ApiResponse<T> failure(String code, String message) {
        return new ApiResponse<>(
                code,
                message,
                null,
                TraceIdHolder.getOrCreateTraceId(),
                OffsetDateTime.now()
        );
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }

    public T getData() {
        return data;
    }

    public String getTraceId() {
        return traceId;
    }

    public OffsetDateTime getTimestamp() {
        return timestamp;
    }
}
