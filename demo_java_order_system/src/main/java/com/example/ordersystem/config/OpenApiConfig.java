package com.example.ordersystem.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI orderSystemOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("Demo Java Order System API")
                        .description("Enterprise-style order service demo")
                        .version("v1")
                        .contact(new Contact().name("Demo Team").email("demo@example.com")));
    }
}
