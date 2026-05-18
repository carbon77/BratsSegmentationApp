package com.example.brats.service;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Service;

@Service
public class PreprocessingService {
    public static final int IMG_SIZE = 128;
    public static final int VOLUME_SLICES = 96;
    public static final int VOLUME_START_AT = 24;
    public static final List<String> MODALITIES = List.of("t1", "t1ce", "t2", "flair");

    private final NiftiReader niftiReader;

    public PreprocessingService(NiftiReader niftiReader) {
        this.niftiReader = niftiReader;
    }

    public float[][][][][] preprocessCase(Map<String, Path> files) throws IOException {
        NiftiImage[] images = new NiftiImage[MODALITIES.size()];
        for (int i = 0; i < MODALITIES.size(); i++) {
            images[i] = niftiReader.read(files.get(MODALITIES.get(i)));
        }

        float[][][][][] tensor = new float[1][MODALITIES.size()][VOLUME_SLICES][IMG_SIZE][IMG_SIZE];
        double max = 0.0;
        for (int z = 0; z < VOLUME_SLICES; z++) {
            int sourceZ = z + VOLUME_START_AT;
            for (int channel = 0; channel < images.length; channel++) {
                double[][] resized = resizeLinear(images[channel], sourceZ, IMG_SIZE, IMG_SIZE);
                for (int y = 0; y < IMG_SIZE; y++) {
                    for (int x = 0; x < IMG_SIZE; x++) {
                        float value = (float) resized[y][x];
                        tensor[0][channel][z][y][x] = value;
                        max = Math.max(max, Math.abs(value));
                    }
                }
            }
        }
        if (max > 0) {
            for (int c = 0; c < MODALITIES.size(); c++) {
                for (int z = 0; z < VOLUME_SLICES; z++) {
                    for (int y = 0; y < IMG_SIZE; y++) {
                        for (int x = 0; x < IMG_SIZE; x++) {
                            tensor[0][c][z][y][x] /= (float) max;
                        }
                    }
                }
            }
        }
        return tensor;
    }

    public Volume preprocessTrueMask(Path maskPath) throws IOException {
        NiftiImage mask = niftiReader.read(maskPath);
        Volume volume = new Volume(VOLUME_SLICES, IMG_SIZE, IMG_SIZE);
        for (int z = 0; z < VOLUME_SLICES; z++) {
            double[][] resized = resizeNearest(mask, z + VOLUME_START_AT, IMG_SIZE, IMG_SIZE);
            for (int y = 0; y < IMG_SIZE; y++) {
                for (int x = 0; x < IMG_SIZE; x++) {
                    volume.set(z, y, x, (int) Math.round(resized[y][x]));
                }
            }
        }
        return volume;
    }

    public double[][] preprocessModalitySlice(Path modalityPath, int sliceIdx) throws IOException {
        NiftiImage image = niftiReader.read(modalityPath);
        int sourceZ = sliceIdx + VOLUME_START_AT;
        if (sliceIdx < 0 || sourceZ >= image.depth()) {
            throw new IndexOutOfBoundsException("Slice index out of range");
        }
        return resizeLinear(image, sourceZ, IMG_SIZE, IMG_SIZE);
    }

    private double[][] resizeLinear(NiftiImage image, int z, int outW, int outH) {
        ensureSlice(image, z);
        double[][] out = new double[outH][outW];
        double scaleX = (double) image.width() / outW;
        double scaleY = (double) image.height() / outH;
        for (int y = 0; y < outH; y++) {
            double sy = (y + 0.5) * scaleY - 0.5;
            int y0 = clamp((int) Math.floor(sy), 0, image.height() - 1);
            int y1 = clamp(y0 + 1, 0, image.height() - 1);
            double wy = sy - Math.floor(sy);
            for (int x = 0; x < outW; x++) {
                double sx = (x + 0.5) * scaleX - 0.5;
                int x0 = clamp((int) Math.floor(sx), 0, image.width() - 1);
                int x1 = clamp(x0 + 1, 0, image.width() - 1);
                double wx = sx - Math.floor(sx);
                double top = image.voxel(x0, y0, z) * (1 - wx) + image.voxel(x1, y0, z) * wx;
                double bottom = image.voxel(x0, y1, z) * (1 - wx) + image.voxel(x1, y1, z) * wx;
                out[y][x] = top * (1 - wy) + bottom * wy;
            }
        }
        return out;
    }

    private double[][] resizeNearest(NiftiImage image, int z, int outW, int outH) {
        ensureSlice(image, z);
        double[][] out = new double[outH][outW];
        for (int y = 0; y < outH; y++) {
            int sy = clamp((int) Math.floor((double) y * image.height() / outH), 0, image.height() - 1);
            for (int x = 0; x < outW; x++) {
                int sx = clamp((int) Math.floor((double) x * image.width() / outW), 0, image.width() - 1);
                out[y][x] = image.voxel(sx, sy, z);
            }
        }
        return out;
    }

    private void ensureSlice(NiftiImage image, int z) {
        if (z < 0 || z >= image.depth()) {
            throw new IndexOutOfBoundsException("Slice index out of range");
        }
    }

    private int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }
}
