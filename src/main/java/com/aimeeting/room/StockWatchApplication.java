package com.aimeeting.room;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.aimeeting.room.dao")
public class StockWatchApplication {

    public static void main(String[] args) {
        SpringApplication.run(StockWatchApplication.class, args);
    }
}
