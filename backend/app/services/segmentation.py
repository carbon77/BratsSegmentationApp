from app.services.inference import run_inference
from app.services.preprocessing import preprocess_case, preprocess_true_mask
from app.services.results import compute_metrics
from app.services.storage import local_paths_for_case, save_result

MODALITIES = ('t1', 't1ce', 't2', 'flair')


def process_segmentation(case_id: str, s3_paths: dict[str, str]) -> tuple[str, dict]:
    with local_paths_for_case(s3_paths) as local_paths:
        modality_paths = {modality: local_paths[modality] for modality in MODALITIES}
        tensor = preprocess_case(modality_paths)
        true_mask_volume = preprocess_true_mask(local_paths['true_mask']) if 'true_mask' in local_paths else None

    prediction = run_inference(tensor)
    metrics = compute_metrics(prediction, true_mask_volume)
    result_path = save_result(case_id, prediction)

    return result_path, metrics
