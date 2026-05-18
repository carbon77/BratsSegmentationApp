package com.example.brats.service;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;

import org.springframework.stereotype.Component;

@Component
public class NiftiReader {
    public NiftiImage read(Path path) throws IOException {
        byte[] bytes = Files.readAllBytes(path);
        if (bytes.length < 352) {
            throw new IllegalArgumentException("NIfTI file is too small: " + path);
        }

        ByteBuffer header = ByteBuffer.wrap(bytes, 0, 348).order(ByteOrder.LITTLE_ENDIAN);
        int sizeofHdr = header.getInt(0);
        if (sizeofHdr != 348) {
            header.order(ByteOrder.BIG_ENDIAN);
            sizeofHdr = header.getInt(0);
        }
        if (sizeofHdr != 348) {
            throw new IllegalArgumentException("Unsupported NIfTI header size in " + path);
        }

        short nx = header.getShort(42);
        short ny = header.getShort(44);
        short nz = header.getShort(46);
        short datatype = header.getShort(70);
        short bitpix = header.getShort(72);
        int offset = Math.max(352, Math.round(header.getFloat(108)));
        int voxelCount = nx * ny * nz;
        int bytesPerVoxel = bitpix / 8;
        if (nx <= 0 || ny <= 0 || nz <= 0 || offset + voxelCount * bytesPerVoxel > bytes.length) {
            throw new IllegalArgumentException("Invalid or truncated NIfTI volume: " + path);
        }

        ByteBuffer data = ByteBuffer.wrap(bytes, offset, bytes.length - offset).order(header.order());
        double[] voxels = new double[voxelCount];
        for (int i = 0; i < voxelCount; i++) {
            voxels[i] = switch (datatype) {
                case 2 -> Byte.toUnsignedInt(data.get());
                case 4 -> data.getShort();
                case 8 -> data.getInt();
                case 16 -> data.getFloat();
                case 64 -> data.getDouble();
                case 256 -> data.get();
                case 512 -> Short.toUnsignedInt(data.getShort());
                case 768 -> Integer.toUnsignedLong(data.getInt());
                default -> throw new IllegalArgumentException("Unsupported NIfTI datatype " + datatype + " in " + path);
            };
        }
        return new NiftiImage(nx, ny, nz, voxels);
    }
}
