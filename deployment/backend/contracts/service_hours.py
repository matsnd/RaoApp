"""Service hours model for tracking operator work hours in service contracts"""

from datetime import datetime, date, time
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class ServiceHour(Base):
    """Service hours for operator work tracking in service contracts"""
    __tablename__ = "service_hours"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("contract_positions.id", ondelete="CASCADE"), nullable=False)
    service_date = Column(Date, nullable=False, comment="Data wykonania usługi")
    time_from = Column(Time, nullable=True, comment="Godzina rozpoczęcia")
    time_to = Column(Time, nullable=True, comment="Godzina zakończenia")
    notes = Column(String(500), nullable=True, comment="Uwagi")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    position = relationship("ContractPosition", back_populates="service_hours")
