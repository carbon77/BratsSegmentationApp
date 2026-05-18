package com.example.brats.service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.example.brats.config.BratsProperties;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;

@Service
public class InferenceService implements AutoCloseable {
    private static final Logger log = LoggerFactory.getLogger(InferenceService.class);

    private final BratsProperties properties;
    private OrtEnvironment environment;
    private OrtSession session;
    private String inputName;

    public InferenceService(BratsProperties properties) {
        this.properties = properties;
    }

    public synchronized Volume runInference(float[][][][][] tensor) throws OrtException {
        ensureSession();
        try (OnnxTensor input = OnnxTensor.createTensor(environment, tensor);
             OrtSession.Result result = session.run(Map.of(inputName, input))) {
            Object output = result.get(0).getValue();
            float[][][][][] logits = castLogits(output);
            int classes = logits[0].length;
            int depth = logits[0][0].length;
            int height = logits[0][0][0].length;
            int width = logits[0][0][0][0].length;
            Volume prediction = new Volume(depth, height, width);
            for (int z = 0; z < depth; z++) {
                for (int y = 0; y < height; y++) {
                    for (int x = 0; x < width; x++) {
                        int bestClass = 0;
                        float best = logits[0][0][z][y][x];
                        for (int cls = 1; cls < classes; cls++) {
                            float value = logits[0][cls][z][y][x];
                            if (value > best) {
                                best = value;
                                bestClass = cls;
                            }
                        }
                        prediction.set(z, y, x, bestClass);
                    }
                }
            }
            return prediction;
        }
    }

    private void ensureSession() throws OrtException {
        if (session != null) {
            return;
        }
        Path modelPath = Path.of(properties.getModelPath());
        if (!Files.exists(modelPath)) {
            throw new IllegalStateException("ONNX model not found at " + modelPath
                    + ". Run scripts/convert_model_to_onnx.py and set ONNX_MODEL_PATH if needed.");
        }
        environment = OrtEnvironment.getEnvironment();
        session = environment.createSession(modelPath.toString(), new OrtSession.SessionOptions());
        inputName = session.getInputNames().iterator().next();
        log.info("Loaded ONNX model from {} with input {}", modelPath, inputName);
    }

    private float[][][][][] castLogits(Object output) {
        if (output instanceof float[][][][][] logits) {
            return logits;
        }
        throw new IllegalStateException("Expected ONNX output shape [1, classes, depth, height, width]");
    }

    @Override
    public void close() throws OrtException {
        if (session != null) {
            session.close();
        }
    }
}
