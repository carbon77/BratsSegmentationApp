package com.example.brats.service;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;

import javax.imageio.ImageIO;

import org.springframework.stereotype.Service;

@Service
public class ResultsService {
    private static final Map<Integer, String> CLASS_LABELS = classLabels();
    private static final Color[] CLASS_COLORS = {
            new Color(68, 1, 84),
            new Color(59, 82, 139),
            new Color(33, 145, 140),
            new Color(253, 231, 37)
    };

    private static Map<Integer, String> classLabels() {
        Map<Integer, String> labels = new LinkedHashMap<>();
        labels.put(0, "background");
        labels.put(1, "necrotic");
        labels.put(2, "edema");
        labels.put(3, "enhancing");
        return labels;
    }

    public Map<String, Object> computeMetrics(Volume prediction, Volume trueMask) {
        int totalVoxels = prediction.size();
        Map<String, Object> classes = new LinkedHashMap<>();
        for (Map.Entry<Integer, String> entry : CLASS_LABELS.entrySet()) {
            int classId = entry.getKey();
            int voxels = 0;
            for (int value : prediction.data()) {
                if (value == classId) {
                    voxels++;
                }
            }
            classes.put(entry.getValue(), Map.of(
                    "class_id", classId,
                    "ratio", totalVoxels == 0 ? 0.0 : (double) voxels / totalVoxels,
                    "voxels", voxels));
        }

        Map<String, Object> metrics = new LinkedHashMap<>();
        metrics.put("total_voxels", totalVoxels);
        metrics.put("classes", classes);
        if (trueMask != null) {
            metrics.put("overlap", computeOverlap(prediction, trueMask));
        }
        return metrics;
    }

    public byte[] renderSlicePng(Volume prediction, int sliceIdx, double[][] background, String modality) throws IOException {
        int scale = 4;
        int legendWidth = 190;
        int titleHeight = 44;
        int w = prediction.width() * scale;
        int h = prediction.height() * scale;
        BufferedImage image = new BufferedImage(w + legendWidth, h + titleHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(Color.WHITE);
        g.fillRect(0, 0, image.getWidth(), image.getHeight());

        double min = 0;
        double max = 1;
        if (background != null) {
            min = Double.POSITIVE_INFINITY;
            max = Double.NEGATIVE_INFINITY;
            for (double[] row : background) {
                for (double value : row) {
                    min = Math.min(min, value);
                    max = Math.max(max, value);
                }
            }
        }

        for (int y = 0; y < prediction.height(); y++) {
            for (int x = 0; x < prediction.width(); x++) {
                int cls = prediction.get(sliceIdx, y, x);
                Color color;
                if (background == null) {
                    color = CLASS_COLORS[Math.max(0, Math.min(cls, CLASS_COLORS.length - 1))];
                } else {
                    int gray = normalize(background[y][x], min, max);
                    Color base = new Color(gray, gray, gray);
                    color = cls == 0 ? base : blend(base, CLASS_COLORS[Math.min(cls, CLASS_COLORS.length - 1)], 0.65);
                }
                g.setColor(color);
                g.fillRect(x * scale, y * scale + titleHeight, scale, scale);
            }
        }

        g.setColor(Color.BLACK);
        g.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 18));
        String title = background == null
                ? "Segmentation mask - slice " + sliceIdx
                : "Segmentation on " + modality.toUpperCase() + " - slice " + sliceIdx;
        g.drawString(title, 12, 28);
        drawLegend(g, w + 18, titleHeight + 24);
        g.dispose();

        ByteArrayOutputStream output = new ByteArrayOutputStream();
        ImageIO.write(image, "png", output);
        return output.toByteArray();
    }

    private Map<String, Object> computeOverlap(Volume prediction, Volume trueMask) {
        Map<String, Object> overlap = new LinkedHashMap<>();
        for (Map.Entry<Integer, String> entry : CLASS_LABELS.entrySet()) {
            int cls = entry.getKey();
            boolean includeClass = cls != 0;
            int predSum = 0;
            int trueSum = 0;
            int intersection = 0;
            int union = 0;
            for (int i = 0; i < prediction.size(); i++) {
                boolean pred = includeClass ? prediction.data()[i] == cls : prediction.data()[i] == 0;
                boolean truth = includeClass ? trueMask.data()[i] == cls : trueMask.data()[i] == 0;
                if (pred) predSum++;
                if (truth) trueSum++;
                if (pred && truth) intersection++;
                if (pred || truth) union++;
            }
            double dice = predSum + trueSum == 0 ? 1.0 : (2.0 * intersection) / (predSum + trueSum);
            double jaccard = union == 0 ? 1.0 : (double) intersection / union;
            overlap.put(entry.getValue(), Map.of("dice", dice, "jaccard", jaccard));
        }
        return overlap;
    }

    private int normalize(double value, double min, double max) {
        if (max <= min) {
            return 0;
        }
        return Math.max(0, Math.min(255, (int) Math.round(255 * (value - min) / (max - min))));
    }

    private Color blend(Color base, Color overlay, double alpha) {
        return new Color(
                (int) (base.getRed() * (1 - alpha) + overlay.getRed() * alpha),
                (int) (base.getGreen() * (1 - alpha) + overlay.getGreen() * alpha),
                (int) (base.getBlue() * (1 - alpha) + overlay.getBlue() * alpha));
    }

    private void drawLegend(Graphics2D g, int x, int y) {
        g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 14));
        g.setStroke(new BasicStroke(1));
        for (Map.Entry<Integer, String> entry : CLASS_LABELS.entrySet()) {
            int classId = entry.getKey();
            g.setColor(CLASS_COLORS[classId]);
            g.fillRect(x, y + classId * 30, 22, 22);
            g.setColor(Color.BLACK);
            g.drawRect(x, y + classId * 30, 22, 22);
            g.drawString(classId + " - " + entry.getValue(), x + 32, y + 17 + classId * 30);
        }
    }
}
