package com.example.brats.service;

import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Service;

@Service
public class SegmentationService {
    private final StorageService storageService;
    private final PreprocessingService preprocessingService;
    private final InferenceService inferenceService;
    private final ResultsService resultsService;

    public SegmentationService(
            StorageService storageService,
            PreprocessingService preprocessingService,
            InferenceService inferenceService,
            ResultsService resultsService) {
        this.storageService = storageService;
        this.preprocessingService = preprocessingService;
        this.inferenceService = inferenceService;
        this.resultsService = resultsService;
    }

    public SegmentationResult process(String caseId, Map<String, String> s3Paths) throws Exception {
        Map<String, Path> localPaths = storageService.downloadFiles(s3Paths);
        try {
            Map<String, Path> modalityPaths = new HashMap<>();
            for (String modality : PreprocessingService.MODALITIES) {
                modalityPaths.put(modality, localPaths.get(modality));
            }
            float[][][][][] tensor = preprocessingService.preprocessCase(modalityPaths);
            Volume trueMask = localPaths.containsKey("true_mask")
                    ? preprocessingService.preprocessTrueMask(localPaths.get("true_mask"))
                    : null;
            Volume prediction = inferenceService.runInference(tensor);
            Map<String, Object> metrics = resultsService.computeMetrics(prediction, trueMask);
            String resultPath = storageService.saveResult(caseId, prediction);
            return new SegmentationResult(resultPath, metrics);
        } finally {
            storageService.cleanupDownloadedFiles(localPaths);
        }
    }

    public record SegmentationResult(String resultPath, Map<String, Object> metrics) {}
}
