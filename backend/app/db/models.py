from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    status = Column(String, default='uploaded')
    result_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))