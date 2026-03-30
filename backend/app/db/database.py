import os

from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

DATABASE_URL = os.environ['DATABASE_URL']

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)