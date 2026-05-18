package com.example.brats.model;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Entity
@Table(name = "scans", indexes = @Index(name = "idx_scans_case_id", columnList = "case_id", unique = true))
public class Scan {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "case_id", nullable = false, unique = true)
    private String caseId;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false)
    private String status = "uploaded";

    @Column(name = "upload_prefix", nullable = false)
    private String uploadPrefix;

    @Column(name = "result_path")
    private String resultPath;

    @Column(columnDefinition = "text")
    private String metrics;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @PrePersist
    void prePersist() {
        OffsetDateTime now = OffsetDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void preUpdate() {
        updatedAt = OffsetDateTime.now();
    }
}
