package com.example.brats.service;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import com.example.brats.config.BratsProperties;

@Service
public class PreprocessingService {
    public static final int IMG_SIZE = 128;
    public static final int VOLUME_SLICES = 96;
    public static final int VOLUME_START_AT = 24;
    public static final List<String> MODALITIES = List.of("t1", "t1ce", "t2", "flair");

    private static final int TENSOR_MAGIC = 0x54454E53;
    private static final int VOLUME_MAGIC = 0x564F4C31;
    private static final int SLICE_MAGIC = 0x534C4331;

    private final RestClient niftiClient;

    public PreprocessingService(BratsProperties properties) {
        this.niftiClient = RestClient.builder()
                .baseUrl(properties.getNiftiServiceUrl())
                .build();
    }

    public float[][][][][] preprocessCase(Map<String, Path> files) throws IOException {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        for (String modality : MODALITIES) {
            body.add(modality, new FileSystemResource(files.get(modality)));
        }
        byte[] response = niftiClient.post()
                .uri("/preprocess/case")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body)
                .retrieve()
                .body(byte[].class);
        return decodeTensor(response);
    }

    public Volume preprocessTrueMask(Path maskPath) throws IOException {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("true_mask", new FileSystemResource(maskPath));
        byte[] response = niftiClient.post()
                .uri("/preprocess/mask")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body)
                .retrieve()
                .body(byte[].class);
        return decodeVolume(response);
    }

    public double[][] preprocessModalitySlice(Path modalityPath, int sliceIdx) throws IOException {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("modality", new FileSystemResource(modalityPath));
        try {
            byte[] response = niftiClient.post()
                    .uri(uriBuilder -> uriBuilder.path("/preprocess/slice").queryParam("slice_idx", sliceIdx).build())
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(body)
                    .retrieve()
                    .body(byte[].class);
            return decodeSlice(response);
        } catch (RestClientResponseException exc) {
            throw new IndexOutOfBoundsException("Slice index out of range");
        }
    }

    private float[][][][][] decodeTensor(byte[] bytes) throws IOException {
        try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes))) {
            expectMagic(in, TENSOR_MAGIC, "tensor");
            int batch = in.readInt();
            int channels = in.readInt();
            int depth = in.readInt();
            int height = in.readInt();
            int width = in.readInt();
            float[][][][][] tensor = new float[batch][channels][depth][height][width];
            for (int b = 0; b < batch; b++) {
                for (int c = 0; c < channels; c++) {
                    for (int z = 0; z < depth; z++) {
                        for (int y = 0; y < height; y++) {
                            for (int x = 0; x < width; x++) {
                                tensor[b][c][z][y][x] = in.readFloat();
                            }
                        }
                    }
                }
            }
            return tensor;
        }
    }

    private Volume decodeVolume(byte[] bytes) throws IOException {
        try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes))) {
            expectMagic(in, VOLUME_MAGIC, "volume");
            Volume volume = new Volume(in.readInt(), in.readInt(), in.readInt());
            for (int i = 0; i < volume.size(); i++) {
                volume.data()[i] = in.readUnsignedByte();
            }
            return volume;
        }
    }

    private double[][] decodeSlice(byte[] bytes) throws IOException {
        try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes))) {
            expectMagic(in, SLICE_MAGIC, "slice");
            int height = in.readInt();
            int width = in.readInt();
            double[][] image = new double[height][width];
            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    image[y][x] = in.readFloat();
                }
            }
            return image;
        }
    }

    private void expectMagic(DataInputStream in, int expectedMagic, String payloadName) throws IOException {
        int magic = in.readInt();
        if (magic != expectedMagic) {
            throw new IOException("Unexpected NIfTI service " + payloadName + " payload");
        }
    }
}
