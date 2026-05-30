from datetime import datetime, timezone
from types import SimpleNamespace

import nibabel as nib
import pytest

import numpy as np

from app.services.dicom import _build_slice_dataset, send_nifti_to_orthanc


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


@pytest.mark.anyio
async def test_send_nifti_to_orthanc_posts_each_dicom_slice(monkeypatch, tmp_path):
    nifti_path = tmp_path / "case.nii"
    image = nib.Nifti1Image(np.ones((2, 2, 3), dtype=np.float32), affine=np.eye(4))
    nib.save(image, nifti_path)

    posts = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ID": f"instance-{len(posts)}"}

    class FakeClient:
        def __init__(self, *, timeout, auth):
            self.timeout = timeout
            self.auth = auth

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, *, content, headers):
            posts.append(SimpleNamespace(url=url, content=content, headers=headers, auth=self.auth))
            return FakeResponse()

    monkeypatch.setenv("ORTHANC_USERNAME", "orthanc")
    monkeypatch.setenv("ORTHANC_PASSWORD", "orthanc")
    monkeypatch.setattr("app.services.dicom.httpx.AsyncClient", FakeClient)

    result = await send_nifti_to_orthanc(
        str(nifti_path),
        case_id="case-1",
        modality="t1",
        orthanc_url="http://orthanc.example",
    )

    assert result["instances_uploaded"] == 3
    assert len(posts) == 3
    assert all(post.url == "http://orthanc.example/instances" for post in posts)
    assert all(post.headers == {"Content-Type": "application/dicom"} for post in posts)
    assert all(post.auth == ("orthanc", "orthanc") for post in posts)
    assert all(post.content.startswith(b"\x00" * 128 + b"DICM") for post in posts)
