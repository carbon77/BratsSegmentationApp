from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Scan(Base):
    __tablename__ = 'scans'

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, unique=False, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=True)
    status = Column(String, default='uploaded', nullable=False)
    upload_prefix = Column(String, nullable=False)
    result_path = Column(String, nullable=True)
    metrics = Column(JSON, nullable=True)
    dicom_patient_name = Column(String, nullable=True)
    dicom_patient_id = Column(String, nullable=True)
    dicom_patient_birth_date = Column(String, nullable=True)
    dicom_patient_sex = Column(String, nullable=True)
    dicom_accession_number = Column(String, nullable=True)
    dicom_study_id = Column(String, nullable=True)
    dicom_study_date = Column(String, nullable=True)
    dicom_study_description = Column(String, nullable=True)
    dicom_series_description = Column(String, nullable=True)
    dicom_institution_name = Column(String, nullable=True)
    dicom_referring_physician_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
