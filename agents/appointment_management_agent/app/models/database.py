"""Database models for the appointment management service."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Appointment(Base):
    """SQLAlchemy model for appointments."""
    __tablename__ = 'appointments'

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    service_type = Column(String, nullable=False)
    status = Column(String, nullable=False)  # confirmed, cancelled, completed
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
