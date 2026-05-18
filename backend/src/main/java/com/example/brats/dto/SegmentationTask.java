package com.example.brats.dto;

import java.util.Map;

public record SegmentationTask(String caseId, String uploadPrefix, Map<String, String> stagedFiles) {}
