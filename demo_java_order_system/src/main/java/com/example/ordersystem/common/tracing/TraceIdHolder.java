package com.example.ordersystem.common.tracing;

import org.slf4j.MDC;

import java.util.UUID;

public final class TraceIdHolder {

    public static final String TRACE_ID_HEADER = "X-Trace-Id";
    public static final String TRACE_ID_MDC_KEY = "traceId";

    private TraceIdHolder() {
    }

    public static String currentTraceId() {
        return MDC.get(TRACE_ID_MDC_KEY);
    }

    public static String getOrCreateTraceId() {
        String traceId = currentTraceId();
        if (traceId == null || traceId.isBlank()) {
            traceId = UUID.randomUUID().toString();
            MDC.put(TRACE_ID_MDC_KEY, traceId);
        }
        return traceId;
    }
}
