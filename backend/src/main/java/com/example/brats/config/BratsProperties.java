package com.example.brats.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Data;

@Data
@ConfigurationProperties(prefix = "brats")
public class BratsProperties {
    private String modelPath = "/app/model.onnx";
    private String uploadStagingDir = "/tmp/brats-upload-staging";
    private String segmentationTopic = "segmentation-tasks";
    private String niftiServiceUrl = "http://localhost:8010";
    private final S3 s3 = new S3();

    @Data
    public static class S3 {
        private String bucket = "brats";
        private String region = "ru-central1";
        private String endpointUrl = "https://storage.yandexcloud.net";
        private String accessKey = "";
        private String secretKey = "";
    }
}
