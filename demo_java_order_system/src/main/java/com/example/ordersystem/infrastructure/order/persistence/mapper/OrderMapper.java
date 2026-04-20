package com.example.ordersystem.infrastructure.order.persistence.mapper;

import com.example.ordersystem.infrastructure.order.persistence.po.OrderPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface OrderMapper {

    int insert(OrderPO orderPO);

    OrderPO selectByOrderNo(@Param("orderNo") String orderNo);

    List<OrderPO> selectPage(
            @Param("offset") int offset,
            @Param("limit") int limit,
            @Param("status") String status,
            @Param("customerName") String customerName
    );

    long countPage(
            @Param("status") String status,
            @Param("customerName") String customerName
    );

    int updateStatusByOrderNo(
            @Param("orderNo") String orderNo,
            @Param("status") String status,
            @Param("updatedAt") LocalDateTime updatedAt
    );
}
