import io
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import httpx

import nibabel as nib
import numpy as np
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, MRImageStorage, generate_uid


DICOM_MIME_TYPE = 'application/zip'
DEFAULT_ORTHANC_URL = 'http://orthanc:8042'


class OrthancUploadError(RuntimeError):
    pass


def _dicom_date(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace('-', '')


def _first_metadata_value(metadata: dict | None, key: str, fallback: str) -> str:
    if not metadata:
        return fallback
    value = metadata.get(key)
    return str(value) if value else fallback


def _load_volume(nifti_path: str) -> tuple[np.ndarray, tuple[float, float, float]]:
    image = nib.load(nifti_path)
    data = np.asarray(image.get_fdata(dtype=np.float32))

    if data.ndim == 4:
        data = np.squeeze(data)
    if data.ndim != 3:
        raise ValueError('Only 3D NIfTI volumes can be converted to DICOM')

    zooms = image.header.get_zooms()[:3]
    spacing = tuple(float(zoom) for zoom in zooms)
    return data, spacing


def _normalize_to_uint16(volume: np.ndarray) -> np.ndarray:
    finite = np.nan_to_num(volume, nan=0.0, posinf=0.0, neginf=0.0)
    min_value = float(np.min(finite))
    max_value = float(np.max(finite))

    if max_value <= min_value:
        return np.zeros(finite.shape, dtype=np.uint16)

    scaled = (finite - min_value) / (max_value - min_value)
    return np.rint(scaled * np.iinfo(np.uint16).max).astype(np.uint16)


def _build_slice_dataset(
    slice_pixels: np.ndarray,
    *,
    case_id: str,
    modality: str,
    slice_index: int,
    total_slices: int,
    study_uid: str,
    series_uid: str,
    frame_uid: str,
    spacing: tuple[float, float, float],
    created_at: datetime,
    dicom_metadata: dict | None,
) -> FileDataset:
    sop_instance_uid = generate_uid()
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = MRImageStorage
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    dataset = FileDataset('', {}, file_meta=file_meta, preamble=b'\0' * 128)
    dataset.is_little_endian = True
    dataset.is_implicit_VR = False

    dataset.SpecificCharacterSet = 'ISO_IR 192'
    dataset.SOPClassUID = MRImageStorage
    dataset.SOPInstanceUID = sop_instance_uid
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid
    dataset.FrameOfReferenceUID = frame_uid

    dataset.PatientName = _first_metadata_value(dicom_metadata, 'patient_name', f'BRATS^{case_id}')
    dataset.PatientID = _first_metadata_value(dicom_metadata, 'patient_id', case_id)
    if dicom_metadata:
        if dicom_metadata.get('patient_birth_date'):
            dataset.PatientBirthDate = _dicom_date(dicom_metadata['patient_birth_date'])
        if dicom_metadata.get('patient_sex'):
            dataset.PatientSex = dicom_metadata['patient_sex']
        if dicom_metadata.get('accession_number'):
            dataset.AccessionNumber = dicom_metadata['accession_number']
        if dicom_metadata.get('study_id'):
            dataset.StudyID = dicom_metadata['study_id']
        if dicom_metadata.get('institution_name'):
            dataset.InstitutionName = dicom_metadata['institution_name']
        if dicom_metadata.get('referring_physician_name'):
            dataset.ReferringPhysicianName = dicom_metadata['referring_physician_name']
    dataset.Modality = 'MR'
    dataset.BodyPartExamined = 'BRAIN'
    dataset.StudyDescription = _first_metadata_value(dicom_metadata, 'study_description', 'BraTS MRI scan')
    dataset.SeriesDescription = _first_metadata_value(
        dicom_metadata,
        'series_description',
        f'{modality.upper()} converted from NIfTI',
    )
    dataset.Manufacturer = 'BratsSegmentationApp'

    dataset.StudyDate = _dicom_date(dicom_metadata.get('study_date')) if dicom_metadata else None
    dataset.StudyDate = dataset.StudyDate or created_at.strftime('%Y%m%d')
    dataset.StudyTime = created_at.strftime('%H%M%S')
    dataset.SeriesDate = dataset.StudyDate
    dataset.SeriesTime = dataset.StudyTime
    dataset.ContentDate = dataset.StudyDate
    dataset.ContentTime = dataset.StudyTime

    dataset.InstanceNumber = slice_index + 1
    dataset.ImagesInAcquisition = total_slices
    dataset.Rows = int(slice_pixels.shape[0])
    dataset.Columns = int(slice_pixels.shape[1])
    dataset.PixelSpacing = [str(spacing[0]), str(spacing[1])]
    dataset.SliceThickness = str(spacing[2])
    dataset.SpacingBetweenSlices = str(spacing[2])
    dataset.ImagePositionPatient = ['0', '0', str(slice_index * spacing[2])]
    dataset.ImageOrientationPatient = ['1', '0', '0', '0', '1', '0']

    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = 'MONOCHROME2'
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.SmallestImagePixelValue = int(slice_pixels.min())
    dataset.LargestImagePixelValue = int(slice_pixels.max())
    dataset.PixelData = np.ascontiguousarray(slice_pixels).tobytes()

    return dataset


def iter_nifti_dicom_instances(
    nifti_path: str,
    *,
    case_id: str,
    modality: str,
    dicom_metadata: dict | None = None,
):
    volume, spacing = _load_volume(nifti_path)
    pixel_volume = _normalize_to_uint16(volume)
    study_uid = generate_uid()
    series_uid = generate_uid()
    created_at = datetime.now(timezone.utc)
    frame_uid = generate_uid()
    total_slices = int(pixel_volume.shape[2])

    for slice_index in range(total_slices):
        dataset = _build_slice_dataset(
            pixel_volume[:, :, slice_index],
            case_id=case_id,
            modality=modality,
            slice_index=slice_index,
            total_slices=total_slices,
            study_uid=study_uid,
            series_uid=series_uid,
            frame_uid=frame_uid,
            spacing=spacing,
            created_at=created_at,
            dicom_metadata=dicom_metadata,
        )
        slice_buffer = io.BytesIO()
        dataset.save_as(slice_buffer, write_like_original=False)
        filename = Path(f'{case_id}-{modality}-slice-{slice_index + 1:04d}.dcm')
        yield str(filename), slice_buffer.getvalue()


def convert_nifti_to_dicom_zip(
    nifti_path: str,
    *,
    case_id: str,
    modality: str,
    dicom_metadata: dict | None = None,
) -> io.BytesIO:
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for filename, instance in iter_nifti_dicom_instances(
            nifti_path,
            case_id=case_id,
            modality=modality,
            dicom_metadata=dicom_metadata,
        ):
            zip_file.writestr(filename, instance)

    archive.seek(0)
    return archive


async def send_nifti_to_orthanc(
    nifti_path: str,
    *,
    case_id: str,
    modality: str,
    dicom_metadata: dict | None = None,
    orthanc_url: str | None = None,
) -> dict:
    target_base_url = orthanc_url or os.getenv('ORTHANC_URL', DEFAULT_ORTHANC_URL)
    target_url = urljoin(target_base_url.rstrip('/') + '/', 'instances')
    username = os.getenv('ORTHANC_USERNAME')
    password = os.getenv('ORTHANC_PASSWORD')
    timeout = float(os.getenv('ORTHANC_UPLOAD_TIMEOUT_SECONDS', '30'))
    auth = (username, password) if username and password else None

    uploaded_instances = []
    try:
        async with httpx.AsyncClient(timeout=timeout, auth=auth) as client:
            for filename, instance in iter_nifti_dicom_instances(
                nifti_path,
                case_id=case_id,
                modality=modality,
                dicom_metadata=dicom_metadata,
            ):
                response = await client.post(
                    target_url,
                    content=instance,
                    headers={'Content-Type': 'application/dicom'},
                )
                response.raise_for_status()
                uploaded_instances.append({'filename': filename, 'orthanc': response.json()})
    except httpx.HTTPError as exc:
        raise OrthancUploadError(f'Could not upload DICOM instances to Orthanc at {target_url}') from exc

    return {
        'orthanc_url': target_url,
        'case_id': case_id,
        'modality': modality,
        'instances_uploaded': len(uploaded_instances),
        'instances': uploaded_instances,
    }
