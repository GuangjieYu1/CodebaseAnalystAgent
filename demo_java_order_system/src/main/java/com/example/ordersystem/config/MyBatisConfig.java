package com.example.ordersystem.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@MapperScan("com.example.ordersystem.infrastructure.order.persistence.mapper")
public class MyBatisConfig {
}
