import io

import matplotlib.pyplot as plt
import numpy as np

CLASS_LABELS = {
    0: 'background',
    1: 'necrotic',
    2: 'edema',
    3: 'enhancing',
}


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


def get_slice_plot(prediction: np.ndarray, slice_idx: int):
    y = prediction[:, slice_idx, :, :].squeeze(0)

    fig, ax = plt.subplots()
    im = ax.imshow(y)
    plt.title(f'Slice {slice_idx}')
    plt.colorbar(im, ax=ax)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    return buf
