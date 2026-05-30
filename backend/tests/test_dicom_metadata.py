from datetime import datetime, timezone

import numpy as np

from app.services.dicom import _build_slice_dataset


def test_build_slice_dataset_embeds_optional_dicom_metadata():
    dataset = _build_slice_dataset(
        np.zeros((2, 3), dtype=np.uint16),
        case_id="case-1",
        modality="t1",
        slice_index=0,
        total_slices=1,
        study_uid="1.2.3",
        series_uid="1.2.4",
        frame_uid="1.2.5",
        spacing=(1.0, 1.0, 2.0),
        created_at=datetime(2026, 5, 30, 12, 0, tzinfo=timezone.utc),
        dicom_metadata={
            "patient_name": "Doe^Jane",
            "patient_id": "P-42",
            "patient_birth_date": "1980-01-02",
            "patient_sex": "F",
            "accession_number": "ACC-7",
            "study_id": "ST-9",
            "study_date": "2026-05-01",
            "study_description": "Brain MRI",
            "series_description": "T1 source",
            "institution_name": "General Hospital",
            "referring_physician_name": "Smith^John",
        },
    )

    assert str(dataset.PatientName) == "Doe^Jane"
    assert dataset.PatientID == "P-42"
    assert dataset.PatientBirthDate == "19800102"
    assert dataset.PatientSex == "F"
    assert dataset.AccessionNumber == "ACC-7"
    assert dataset.StudyID == "ST-9"
    assert dataset.StudyDate == "20260501"
    assert dataset.StudyDescription == "Brain MRI"
    assert dataset.SeriesDescription == "T1 source"
    assert dataset.InstitutionName == "General Hospital"
    assert str(dataset.ReferringPhysicianName) == "Smith^John"
