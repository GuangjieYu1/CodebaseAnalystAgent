package com.example.ordersystem.common.exception;

import com.example.ordersystem.common.api.ApiResponse;
import jakarta.validation.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusinessException(BusinessException exception) {
        return ResponseEntity
                .status(exception.getHttpStatus())
                .body(ApiResponse.failure(exception.getErrorCode().getCode(), exception.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(MethodArgumentNotValidException exception) {
        String message = exception.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(this::formatFieldError)
                .collect(Collectors.joining("; "));
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.failure(ErrorCode.INVALID_REQUEST.getCode(), message));
    }

    @ExceptionHandler({
            ConstraintViolationException.class,
            MethodArgumentTypeMismatchException.class,
            HttpMessageNotReadableException.class,
            IllegalArgumentException.class
    })
    public ResponseEntity<ApiResponse<Void>> handleBadRequest(Exception exception) {
        String message = exception.getMessage() == null
                ? ErrorCode.INVALID_REQUEST.getDefaultMessage()
                : exception.getMessage();
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.failure(ErrorCode.INVALID_REQUEST.getCode(), message));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(Exception exception) {
        log.error("Unhandled exception", exception);
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.failure(ErrorCode.INTERNAL_ERROR.getCode(), ErrorCode.INTERNAL_ERROR.getDefaultMessage()));
    }

    private String formatFieldError(FieldError fieldError) {
        return fieldError.getField() + " " + fieldError.getDefaultMessage();
    }
}
