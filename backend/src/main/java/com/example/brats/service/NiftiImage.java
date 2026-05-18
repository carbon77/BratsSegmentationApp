package com.example.brats.service;

public record NiftiImage(int width, int height, int depth, double[] data) {
    public double voxel(int x, int y, int z) {
        return data[x + width * (y + height * z)];
    }
}
