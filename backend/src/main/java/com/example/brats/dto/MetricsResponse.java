package com.example.brats.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record MetricsResponse(String case_id, JsonNode metrics) {}
