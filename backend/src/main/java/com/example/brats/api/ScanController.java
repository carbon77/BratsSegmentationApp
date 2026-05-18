package com.example.brats.api;

import java.io.IOException;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.springframework.web.server.ResponseStatusException;

import com.example.brats.config.BratsProperties;
import com.example.brats.dto.MetricsResponse;
import com.example.brats.dto.PatchScanRequest;
import com.example.brats.dto.ScanResponse;
import com.example.brats.dto.SegmentationTask;
import com.example.brats.model.Scan;
import com.example.brats.repository.ScanRepository;
import com.example.brats.service.PreprocessingService;
import com.example.brats.service.ResultsService;
import com.example.brats.service.StorageService;
import com.example.brats.service.Volume;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequiredArgsConstructor
public class ScanController {
    private final ScanRepository scanRepository;
    private final StorageService storageService;
    private final PreprocessingService preprocessingService;
    private final ResultsService resultsService;
    private final KafkaTemplate<String, SegmentationTask> kafkaTemplate;
    private final BratsProperties properties;
    private final ObjectMapper objectMapper;

    @PostMapping(path = "/predict", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Transactional
    public ResponseEntity<ScanResponse> predict(
            @RequestPart("t1") MultipartFile t1,
            @RequestPart("t1ce") MultipartFile t1ce,
            @RequestPart("t2") MultipartFile t2,
            @RequestPart("flair") MultipartFile flair,
            @RequestPart(value = "true_mask", required = false) MultipartFile trueMask) throws IOException {
        Map<String, MultipartFile> files = new LinkedHashMap<>();
        files.put("t1", t1);
        files.put("t1ce", t1ce);
        files.put("t2", t2);
        files.put("flair", flair);
        if (trueMask != null && !trueMask.isEmpty()) {
            files.put("true_mask", trueMask);
        }

        StorageService.StagedUpload staged = storageService.stageUploadedFiles(files);
        Scan scan = new Scan();
        scan.setCaseId(staged.caseId());
        scan.setTitle(staged.caseId());
        scan.setUploadPrefix(staged.uploadPrefix());
        scan.setStatus("uploading");
        scanRepository.save(scan);

        SegmentationTask task = new SegmentationTask(staged.caseId(), staged.uploadPrefix(), staged.stagedFiles());
        kafkaTemplate.send(properties.getSegmentationTopic(), staged.caseId(), task);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(ScanResponse.from(scan));
    }

    @GetMapping("/scans")
    public List<ScanResponse> scans() {
        return scanRepository.findAllByOrderByCreatedAtDesc().stream().map(ScanResponse::from).toList();
    }

    @GetMapping("/scans/events")
    public SseEmitter scanEvents() {
        SseEmitter emitter = new SseEmitter(0L);
        Thread.startVirtualThread(() -> {
            String lastPayload = null;
            try {
                while (true) {
                    String payload = objectMapper.writeValueAsString(scans());
                    if (!payload.equals(lastPayload)) {
                        emitter.send(SseEmitter.event().name("scans").data(payload));
                        lastPayload = payload;
                    }
                    Thread.sleep(2000);
                }
            } catch (Exception exc) {
                emitter.complete();
            }
        });
        return emitter;
    }

    @GetMapping("/scans/{caseId}/result/metrics")
    public MetricsResponse metrics(@PathVariable String caseId) throws IOException {
        Scan scan = getScan(caseId);
        if (!"completed".equals(scan.getStatus()) || scan.getMetrics() == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Scan results not ready");
        }
        JsonNode metrics = objectMapper.readTree(scan.getMetrics());
        return new MetricsResponse(caseId, metrics);
    }

    @GetMapping(value = "/scans/{caseId}/result/images", produces = MediaType.IMAGE_PNG_VALUE)
    public byte[] resultImages(
            @PathVariable String caseId,
            @RequestParam(name = "slice_idx", defaultValue = "1") int sliceIdx,
            @RequestParam(name = "overlay_modality", required = false) String overlayModality) throws IOException {
        Scan scan = getScan(caseId);
        if (!"completed".equals(scan.getStatus()) || scan.getResultPath() == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Scan result not ready");
        }
        if (overlayModality != null && !PreprocessingService.MODALITIES.contains(overlayModality)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "overlay_modality must be one of: t1, t1ce, t2, flair");
        }

        Volume prediction = storageService.loadResult(scan.getResultPath());
        if (sliceIdx < 0 || sliceIdx >= prediction.depth()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "slice_idx must be between 0 and " + (prediction.depth() - 1));
        }

        double[][] background = null;
        if (overlayModality != null) {
            String uri = storageService.uploadedFileUri(scan.getUploadPrefix(), overlayModality);
            Map<String, Path> localPaths = storageService.downloadFiles(Map.of(overlayModality, uri));
            try {
                background = preprocessingService.preprocessModalitySlice(localPaths.get(overlayModality), sliceIdx);
            } catch (IndexOutOfBoundsException exc) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "slice_idx is outside the uploaded MRI volume", exc);
            } finally {
                storageService.cleanupDownloadedFiles(localPaths);
            }
        }
        return resultsService.renderSlicePng(prediction, sliceIdx, background, overlayModality);
    }

    @DeleteMapping("/scans/{caseId}")
    @Transactional
    public ResponseEntity<Void> deleteScan(@PathVariable String caseId) {
        scanRepository.findByCaseId(caseId).ifPresent(scan -> {
            storageService.deleteScanFiles(scan);
            scanRepository.delete(scan);
        });
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/scans/{caseId}")
    @Transactional
    public ResponseEntity<Void> patchScan(@PathVariable String caseId, @org.springframework.web.bind.annotation.RequestBody PatchScanRequest request) {
        Scan scan = getScan(caseId);
        scan.setTitle(request.title());
        scanRepository.save(scan);
        return ResponseEntity.noContent().build();
    }

    private Scan getScan(String caseId) {
        return scanRepository.findByCaseId(caseId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "scan not found"));
    }

    @ExceptionHandler(ResponseStatusException.class)
    ResponseEntity<Map<String, String>> responseStatus(ResponseStatusException exc) {
        return ResponseEntity.status(exc.getStatusCode()).body(Map.of("detail", exc.getReason()));
    }
}
