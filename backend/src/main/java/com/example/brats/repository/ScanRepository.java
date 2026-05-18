package com.example.brats.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.brats.model.Scan;

public interface ScanRepository extends JpaRepository<Scan, Integer> {
    Optional<Scan> findByCaseId(String caseId);
    List<Scan> findAllByOrderByCreatedAtDesc();
}
