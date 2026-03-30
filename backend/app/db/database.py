import os

from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg://postgres:postgres@localhost:5432/brats')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
