import io

import matplotlib.pyplot as plt
import numpy as np

CLASS_LABELS = {
    0: 'background',
    1: 'necrotic',
    2: 'edema',
    3: 'enhancing',
}


def compute_metrics(prediction: np.ndarray) -> dict:
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

    return {
        'total_voxels': total_voxels,
        'classes': classes,
    }


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
