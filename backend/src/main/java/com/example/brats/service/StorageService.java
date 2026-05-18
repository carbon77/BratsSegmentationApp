package com.example.brats.service;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.example.brats.config.BratsProperties;
import com.example.brats.model.Scan;

import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.Delete;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.ObjectIdentifier;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

@Service
public class StorageService {
    private static final Logger log = LoggerFactory.getLogger(StorageService.class);
    private static final int RESULT_MAGIC = 0x42524154;

    private final BratsProperties properties;
    private final S3Client s3;

    public StorageService(BratsProperties properties, S3Client s3) {
        this.properties = properties;
        this.s3 = s3;
    }

    public StagedUpload stageUploadedFiles(Map<String, MultipartFile> files) throws IOException {
        String caseId = UUID.randomUUID().toString();
        String uploadPrefix = "uploads/" + caseId;
        Path caseDir = caseStagingDir(caseId);
        Files.createDirectories(caseDir);
        Map<String, String> stagedFiles = new HashMap<>();
        for (Map.Entry<String, MultipartFile> entry : files.entrySet()) {
            Path localPath = caseDir.resolve(entry.getKey() + ".nii");
            entry.getValue().transferTo(localPath);
            stagedFiles.put(entry.getKey(), localPath.toString());
        }
        return new StagedUpload(caseId, uploadPrefix, stagedFiles);
    }

    public Map<String, String> uploadStagedFiles(Map<String, String> stagedFiles, String uploadPrefix) {
        Map<String, String> s3Uris = new HashMap<>();
        for (Map.Entry<String, String> entry : stagedFiles.entrySet()) {
            String key = uploadPrefix + "/" + entry.getKey() + ".nii";
            log.info("Uploading file key={}", key);
            s3.putObject(PutObjectRequest.builder().bucket(bucket()).key(key).build(), RequestBody.fromFile(Path.of(entry.getValue())));
            s3Uris.put(entry.getKey(), toS3Uri(key));
        }
        return s3Uris;
    }

    public Map<String, Path> downloadFiles(Map<String, String> s3Uris) throws IOException {
        Path tempDir = Files.createTempDirectory("brats-case-");
        Map<String, Path> localPaths = new HashMap<>();
        for (Map.Entry<String, String> entry : s3Uris.entrySet()) {
            String key = fromS3Uri(entry.getValue());
            Path localPath = tempDir.resolve(entry.getKey() + ".nii");
            log.info("Downloading file key={}", key);
            s3.getObject(GetObjectRequest.builder().bucket(bucket()).key(key).build(), localPath);
            localPaths.put(entry.getKey(), localPath);
        }
        return localPaths;
    }

    public String uploadedFileUri(String uploadPrefix, String name) {
        return toS3Uri(uploadPrefix + "/" + name + ".nii");
    }

    public String saveResult(String caseId, Volume prediction) throws IOException {
        String key = "results/" + caseId + ".bratsbin";
        Path tempFile = Files.createTempFile("brats-result-", ".bin");
        try (DataOutputStream out = new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(tempFile)))) {
            out.writeInt(RESULT_MAGIC);
            out.writeInt(prediction.depth());
            out.writeInt(prediction.height());
            out.writeInt(prediction.width());
            for (int value : prediction.data()) {
                out.writeByte(value);
            }
        }
        s3.putObject(PutObjectRequest.builder().bucket(bucket()).key(key).build(), RequestBody.fromFile(tempFile));
        Files.deleteIfExists(tempFile);
        return toS3Uri(key);
    }

    public Volume loadResult(String resultUri) throws IOException {
        Path tempFile = Files.createTempFile("brats-result-", ".bin");
        s3.getObject(GetObjectRequest.builder().bucket(bucket()).key(fromS3Uri(resultUri)).build(), tempFile);
        try (DataInputStream in = new DataInputStream(new BufferedInputStream(Files.newInputStream(tempFile)))) {
            if (in.readInt() != RESULT_MAGIC) {
                throw new IOException("Unsupported result format");
            }
            Volume volume = new Volume(in.readInt(), in.readInt(), in.readInt());
            for (int i = 0; i < volume.size(); i++) {
                volume.data()[i] = in.readUnsignedByte();
            }
            return volume;
        } finally {
            Files.deleteIfExists(tempFile);
        }
    }

    public void deleteScanFiles(Scan scan) {
        deleteStagedFiles(scan.getCaseId());
        List<ObjectIdentifier> objects = new java.util.ArrayList<>();
        for (String name : List.of("t1", "t1ce", "t2", "flair", "true_mask")) {
            objects.add(ObjectIdentifier.builder().key(scan.getUploadPrefix() + "/" + name + ".nii").build());
        }
        if (scan.getResultPath() != null) {
            objects.add(ObjectIdentifier.builder().key(fromS3Uri(scan.getResultPath())).build());
        }
        if (!objects.isEmpty()) {
            s3.deleteObjects(builder -> builder.bucket(bucket()).delete(Delete.builder().objects(objects).build()));
        }
    }

    public void deleteStagedFiles(String caseId) {
        deleteRecursively(caseStagingDir(caseId));
    }

    public void cleanupDownloadedFiles(Map<String, Path> localPaths) {
        localPaths.values().stream().findFirst().map(Path::getParent).ifPresent(this::deleteRecursively);
    }

    private void deleteRecursively(Path path) {
        if (!Files.exists(path)) {
            return;
        }
        try (var paths = Files.walk(path)) {
            paths.sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
                try { Files.deleteIfExists(p); } catch (IOException ignored) { }
            });
        } catch (IOException ignored) {
        }
    }

    private Path caseStagingDir(String caseId) {
        return Path.of(properties.getUploadStagingDir(), caseId);
    }

    private String bucket() {
        return properties.getS3().getBucket();
    }

    private String toS3Uri(String key) {
        return "s3://" + bucket() + "/" + key;
    }

    private String fromS3Uri(String uri) {
        String prefix = "s3://" + bucket() + "/";
        if (!uri.startsWith(prefix)) {
            throw new IllegalArgumentException("Invalid S3 URI: " + uri);
        }
        return uri.substring(prefix.length());
    }

    public record StagedUpload(String caseId, String uploadPrefix, Map<String, String> stagedFiles) {}
}
