from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from database import Base


class Contractor(Base):
    __tablename__ = "contractors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(400), nullable=False)
    name_short = Column(String(200), nullable=True)
    nip = Column(String(20), nullable=True)
    regon = Column(String(20), nullable=True)
    pesel = Column(String(20), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(50), nullable=True)
    street = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_supplier = Column(Boolean, nullable=False, default=False)
    email = Column(String(100), nullable=True)
    contact_person1 = Column(String(100), nullable=True)
    phone1 = Column(String(100), nullable=True)
    contact_person2 = Column(String(100), nullable=True)
    phone2 = Column(String(100), nullable=True)
    landline_phone = Column(String(20), nullable=True)
    website = Column(String(100), nullable=True)
    files_folder = Column(String(100), nullable=True)
    gus_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    addresses = relationship("ContractorAddress", back_populates="contractor", cascade="all, delete-orphan")


class ContractorAddress(Base):
    __tablename__ = "contractor_addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=True)
    country_code = Column(String(3), nullable=True, default="PL")
    postal_code = Column(String(20), nullable=True)
    city = Column(String(50), nullable=True)
    street = Column(String(50), nullable=True)
    notes = Column(String(200), nullable=True)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(20), nullable=True)
    is_default_delivery = Column(Boolean, nullable=False, default=False)
    is_headquarters = Column(Boolean, nullable=False, default=False)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    created_at = Column(DateTime, nullable=False)

    contractor = relationship("Contractor", back_populates="addresses")
