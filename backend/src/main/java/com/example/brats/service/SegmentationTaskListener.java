package com.example.brats.service;

import lombok.RequiredArgsConstructor;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.example.brats.dto.SegmentationTask;
import com.example.brats.model.Scan;
import com.example.brats.repository.ScanRepository;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
@RequiredArgsConstructor
public class SegmentationTaskListener {
    private static final Logger log = LoggerFactory.getLogger(SegmentationTaskListener.class);

    private final StorageService storageService;
    private final SegmentationService segmentationService;
    private final ScanRepository scanRepository;
    private final ObjectMapper objectMapper;

    @KafkaListener(topics = "${brats.segmentation-topic}")
    @Transactional
    public void handle(SegmentationTask task, Acknowledgment acknowledgment) {
        log.info("Starting segmentation task caseId={}", task.caseId());
        try {
            MapStatus marker = new MapStatus();
            scanRepository.findByCaseId(task.caseId()).ifPresent(scan -> {
                scan.setStatus("uploading");
                scanRepository.save(scan);
                marker.found = true;
            });
            if (!marker.found) {
                acknowledgment.acknowledge();
                return;
            }

            var s3Paths = storageService.uploadStagedFiles(task.stagedFiles(), task.uploadPrefix());
            scanRepository.findByCaseId(task.caseId()).ifPresent(scan -> {
                scan.setStatus("processing");
                scanRepository.save(scan);
            });

            var result = segmentationService.process(task.caseId(), s3Paths);
            Scan scan = scanRepository.findByCaseId(task.caseId()).orElseThrow();
            scan.setStatus("completed");
            scan.setResultPath(result.resultPath());
            scan.setMetrics(objectMapper.writeValueAsString(result.metrics()));
            scanRepository.save(scan);
            log.info("Segmentation task completed caseId={}", task.caseId());
        } catch (Exception exc) {
            log.error("Segmentation task failed caseId={}", task.caseId(), exc);
            scanRepository.findByCaseId(task.caseId()).ifPresent(scan -> {
                scan.setStatus("failed");
                scanRepository.save(scan);
            });
        } finally {
            storageService.deleteStagedFiles(task.caseId());
            acknowledgment.acknowledge();
        }
    }

    private static class MapStatus { boolean found; }
}
