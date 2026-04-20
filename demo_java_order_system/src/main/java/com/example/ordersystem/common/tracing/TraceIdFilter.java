package com.example.ordersystem.common.tracing;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

@Component
public class TraceIdFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(TraceIdFilter.class);

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String headerTraceId = request.getHeader(TraceIdHolder.TRACE_ID_HEADER);
        String traceId = StringUtils.hasText(headerTraceId) ? headerTraceId : UUID.randomUUID().toString();
        long startAt = System.currentTimeMillis();

        MDC.put(TraceIdHolder.TRACE_ID_MDC_KEY, traceId);
        response.setHeader(TraceIdHolder.TRACE_ID_HEADER, traceId);

        try {
            filterChain.doFilter(request, response);
        } finally {
            log.info("{} {} -> {} ({} ms)",
                    request.getMethod(),
                    request.getRequestURI(),
                    response.getStatus(),
                    System.currentTimeMillis() - startAt);
            MDC.remove(TraceIdHolder.TRACE_ID_MDC_KEY);
        }
    }
}
