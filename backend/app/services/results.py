import io

import matplotlib.pyplot as plt
import numpy as np

CLASS_LABELS = {
    0: 'background',
    1: 'necrotic',
    2: 'edema',
    3: 'enhancing',
}

SEGMENTATION_CMAP = plt.get_cmap('viridis', len(CLASS_LABELS))


def _overlap_metrics(pred_binary: np.ndarray, true_binary: np.ndarray) -> dict:
    pred_sum = int(np.count_nonzero(pred_binary))
    true_sum = int(np.count_nonzero(true_binary))
    intersection = int(np.count_nonzero(pred_binary & true_binary))
    union = int(np.count_nonzero(pred_binary | true_binary))

    dice_denominator = pred_sum + true_sum
    dice = float((2 * intersection) / dice_denominator) if dice_denominator else 1.0
    jaccard = float(intersection / union) if union else 1.0

    return {
        'dice': dice,
        'jaccard': jaccard,
    }


def compute_metrics(prediction: np.ndarray, true_mask: np.ndarray | None = None) -> dict:
    volume = prediction[0] if prediction.ndim == 4 else prediction
    total_voxels = int(volume.size)

    classes = {}
    for class_id, label in CLASS_LABELS.items():
        voxels = int(np.count_nonzero(volume == class_id))
        ratio = float(voxels / total_voxels) if total_voxels else 0.0
        classes[label] = {
            'class_id': class_id,
            'ratio': ratio,
            'voxels': voxels,
        }

    metrics = {
        'total_voxels': total_voxels,
        'classes': classes,
    }

    if true_mask is not None:
        true_volume = true_mask[0] if true_mask.ndim == 4 else true_mask
        pred_tumor = volume > 0
        true_tumor = true_volume > 0

        overlaps = {
            'whole_tumor': _overlap_metrics(pred_tumor, true_tumor),
            'by_class': {},
        }
        for class_id, label in CLASS_LABELS.items():
            if class_id == 0:
                continue
            overlaps['by_class'][label] = _overlap_metrics(volume == class_id, true_volume == class_id)

        metrics['segmentation'] = overlaps

    return metrics


def _normalize_background(background_slice: np.ndarray) -> np.ndarray:
    background = background_slice.astype(np.float32)
    lower, upper = np.percentile(background, [1, 99])
    if upper > lower:
        background = np.clip(background, lower, upper)

    min_value = float(np.min(background))
    max_value = float(np.max(background))
    if max_value > min_value:
        background = (background - min_value) / (max_value - min_value)
    return background


def _class_rgb_colors() -> dict[int, np.ndarray]:
    return {
        class_id: np.array(SEGMENTATION_CMAP(class_id)[:3], dtype=np.float32)
        for class_id in CLASS_LABELS
    }


def _encode_png(image: np.ndarray):
    import cv2

    success, encoded = cv2.imencode('.png', image)
    if not success:
        raise ValueError('Could not encode slice image as PNG')
    return io.BytesIO(encoded.tobytes())


def get_slice_plot(
    prediction: np.ndarray,
    slice_idx: int,
    background_slice: np.ndarray | None = None,
    modality: str | None = None,
    include_mask: bool = True,
):
    volume = prediction[0] if prediction.ndim == 4 else prediction
    mask_slice = volume[slice_idx, :, :]

    if background_slice is not None:
        background = (_normalize_background(background_slice) * 255).astype(np.uint8)
        image = np.repeat(background[:, :, np.newaxis], 3, axis=2)
    else:
        image = np.zeros((*mask_slice.shape, 3), dtype=np.uint8)

    if include_mask:
        colors = _class_rgb_colors()
        mask_rgb = np.zeros_like(image, dtype=np.float32)
        for class_id, color in colors.items():
            mask_rgb[mask_slice == class_id] = color * 255

        if background_slice is None:
            image = mask_rgb.astype(np.uint8)
        else:
            foreground = mask_slice > 0
            blended = (image.astype(np.float32) * 0.35) + (mask_rgb * 0.65)
            image[foreground] = blended[foreground].astype(np.uint8)

    return _encode_png(image)
