from typing import Any

from pydantic import BaseModel, field_validator


class AuthRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if '@' not in normalized:
            raise ValueError('Valid email is required')
        return normalized


class RegisterRequest(AuthRequest):
    name: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError('Name is required')
        return normalized


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: dict


class DicomMetadata(BaseModel):
    patient_name: str | None = None
    patient_id: str | None = None
    patient_birth_date: str | None = None
    patient_sex: str | None = None
    accession_number: str | None = None
    study_id: str | None = None
    study_date: str | None = None
    study_description: str | None = None
    series_description: str | None = None
    institution_name: str | None = None
    referring_physician_name: str | None = None

    @field_validator('*', mode='before')
    @classmethod
    def empty_strings_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value


class PatchScanRequest(BaseModel):
    title: str | None = None
    dicom_metadata: DicomMetadata | None = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            raise ValueError('Title is required')
        return normalized
