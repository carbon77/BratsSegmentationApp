from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    scan_columns = {column['name'] for column in inspector.get_columns('scans')} if inspector.has_table('scans') else set()
    if 'scans' in inspector.get_table_names() and 'user_id' not in scan_columns:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE scans ADD COLUMN user_id INTEGER'))
            connection.execute(text('CREATE INDEX IF NOT EXISTS ix_scans_user_id ON scans (user_id)'))
