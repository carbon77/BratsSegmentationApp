package com.example.brats.service;

public class Volume {
    private final int depth;
    private final int height;
    private final int width;
    private final int[] data;

    public Volume(int depth, int height, int width) {
        this.depth = depth;
        this.height = height;
        this.width = width;
        this.data = new int[depth * height * width];
    }

    public int depth() { return depth; }
    public int height() { return height; }
    public int width() { return width; }
    public int[] data() { return data; }
    public int size() { return data.length; }

    public int get(int z, int y, int x) {
        return data[(z * height + y) * width + x];
    }

    public void set(int z, int y, int x, int value) {
        data[(z * height + y) * width + x] = value;
    }
}
