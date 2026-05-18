package com.example.brats.dto;

import com.example.brats.model.Scan;

public record ScanResponse(String case_id, String title, String status) {
    public static ScanResponse from(Scan scan) {
        return new ScanResponse(scan.getCaseId(), scan.getTitle(), scan.getStatus());
    }
}
