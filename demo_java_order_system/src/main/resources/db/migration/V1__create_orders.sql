CREATE TABLE IF NOT EXISTS orders (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(64) NOT NULL,
    customer_name VARCHAR(64) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT uk_orders_order_no UNIQUE (order_no),
    INDEX idx_orders_status (status),
    INDEX idx_orders_customer_name (customer_name),
    INDEX idx_orders_updated_at (updated_at)
);
