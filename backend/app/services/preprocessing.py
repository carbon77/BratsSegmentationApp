import nibabel as nib
import numpy as np
import torch
import cv2

IMG_SIZE = 128
VOLUME_SLICES = 96
VOLUME_START_AT = 24

def load_nifti(file):
    return nib.load(file).get_fdata()

def preprocess_case(files_dict):
    data = [load_nifti(f) for f in files_dict.values()]
    X = np.zeros((VOLUME_SLICES, IMG_SIZE, IMG_SIZE, 4))

    for j in range(VOLUME_SLICES):
        slice_pos = j + VOLUME_START_AT
        for k in range(4):
            X[j, :, :, k] = cv2.resize(
                data[k][:, :, slice_pos],
                (IMG_SIZE, IMG_SIZE),
            )
    X /= np.max(X)
    X = torch.FloatTensor(X).permute(3, 0, 1, 2).unsqueeze(0)
    return X


def preprocess_true_mask(mask_path):
    mask = load_nifti(mask_path)
    y = np.zeros((VOLUME_SLICES, IMG_SIZE, IMG_SIZE), dtype=np.int32)

    for j in range(VOLUME_SLICES):
        slice_pos = j + VOLUME_START_AT
        y[j, :, :] = cv2.resize(
            mask[:, :, slice_pos],
            (IMG_SIZE, IMG_SIZE),
            interpolation=cv2.INTER_NEAREST,
        )

    return y
