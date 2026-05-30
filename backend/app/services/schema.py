from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


SCAN_OPTIONAL_COLUMNS = {
    'user_id': 'INTEGER',
    'dicom_patient_name': 'VARCHAR',
    'dicom_patient_id': 'VARCHAR',
    'dicom_patient_birth_date': 'VARCHAR',
    'dicom_patient_sex': 'VARCHAR',
    'dicom_accession_number': 'VARCHAR',
    'dicom_study_id': 'VARCHAR',
    'dicom_study_date': 'VARCHAR',
    'dicom_study_description': 'VARCHAR',
    'dicom_series_description': 'VARCHAR',
    'dicom_institution_name': 'VARCHAR',
    'dicom_referring_physician_name': 'VARCHAR',
}


def ensure_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if 'scans' not in inspector.get_table_names():
        return

    scan_columns = {column['name'] for column in inspector.get_columns('scans')}
    missing_columns = {
        column_name: column_type
        for column_name, column_type in SCAN_OPTIONAL_COLUMNS.items()
        if column_name not in scan_columns
    }

    if missing_columns:
        with engine.begin() as connection:
            for column_name, column_type in missing_columns.items():
                connection.execute(text(f'ALTER TABLE scans ADD COLUMN {column_name} {column_type}'))
            if 'user_id' in missing_columns:
                connection.execute(text('CREATE INDEX IF NOT EXISTS ix_scans_user_id ON scans (user_id)'))
