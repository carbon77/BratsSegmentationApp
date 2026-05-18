package com.example.brats.config;

import java.net.URI;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

@Configuration
@EnableConfigurationProperties(BratsProperties.class)
public class AppConfig {
    @Bean
    S3Client s3Client(BratsProperties properties) {
        BratsProperties.S3 s3 = properties.getS3();
        var builder = S3Client.builder()
                .region(Region.of(s3.getRegion()))
                .endpointOverride(URI.create(s3.getEndpointUrl()))
                .forcePathStyle(true);
        if (!s3.getAccessKey().isBlank() || !s3.getSecretKey().isBlank()) {
            builder.credentialsProvider(StaticCredentialsProvider.create(
                    AwsBasicCredentials.create(s3.getAccessKey(), s3.getSecretKey())));
        }
        return builder.build();
    }
}
