import os
import uuid
import numpy as np

UPLOAD_DIR = 'data/uploads'
RESULT_DIR = 'data/results'

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

def save_uploaded_files(files):
    case_id = str(uuid.uuid4())
    case_dir = os.path.join(UPLOAD_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)

    paths = {}
    for name, file in files.items():
        path = os.path.join(case_dir, f"{name}.nii")
        with open(path, 'wb') as f:
            f.write(file.file.read())
        paths[name] = path
    return case_id, paths

def save_result(case_id, prediction):
    path = os.path.join(RESULT_DIR, f'{case_id}.npy')
    np.save(path, prediction)
    return path