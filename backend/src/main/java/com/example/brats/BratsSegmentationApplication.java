package com.example.brats;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

@EnableKafka
@SpringBootApplication
public class BratsSegmentationApplication {
    public static void main(String[] args) {
        SpringApplication.run(BratsSegmentationApplication.class, args);
    }
}
