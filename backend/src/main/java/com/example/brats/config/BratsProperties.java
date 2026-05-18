package com.example.brats.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "brats")
public class BratsProperties {
    private String modelPath = "/app/model.onnx";
    private String uploadStagingDir = "/tmp/brats-upload-staging";
    private String segmentationTopic = "segmentation-tasks";
    private final S3 s3 = new S3();

    public String getModelPath() { return modelPath; }
    public void setModelPath(String modelPath) { this.modelPath = modelPath; }
    public String getUploadStagingDir() { return uploadStagingDir; }
    public void setUploadStagingDir(String uploadStagingDir) { this.uploadStagingDir = uploadStagingDir; }
    public String getSegmentationTopic() { return segmentationTopic; }
    public void setSegmentationTopic(String segmentationTopic) { this.segmentationTopic = segmentationTopic; }
    public S3 getS3() { return s3; }

    public static class S3 {
        private String bucket = "brats";
        private String region = "ru-central1";
        private String endpointUrl = "https://storage.yandexcloud.net";
        private String accessKey = "";
        private String secretKey = "";

        public String getBucket() { return bucket; }
        public void setBucket(String bucket) { this.bucket = bucket; }
        public String getRegion() { return region; }
        public void setRegion(String region) { this.region = region; }
        public String getEndpointUrl() { return endpointUrl; }
        public void setEndpointUrl(String endpointUrl) { this.endpointUrl = endpointUrl; }
        public String getAccessKey() { return accessKey; }
        public void setAccessKey(String accessKey) { this.accessKey = accessKey; }
        public String getSecretKey() { return secretKey; }
        public void setSecretKey(String secretKey) { this.secretKey = secretKey; }
    }
}
