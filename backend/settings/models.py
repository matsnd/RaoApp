from sqlalchemy import Boolean, Column, ForeignKey, Integer, LargeBinary, Numeric, String, Text
from sqlalchemy.orm import relationship
from database import Base


class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=True)
    name_short = Column(String(100), nullable=True)
    nip = Column(String(20), nullable=True)
    regon = Column(String(20), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(50), nullable=True)
    street = Column(String(50), nullable=True)
    header_text = Column(Text, nullable=True)
    logo = Column(LargeBinary, nullable=True)
    bank_name = Column(String(200), nullable=True)
    bank_account = Column(String(40), nullable=True)
    numbering_start = Column(Integer, nullable=True, default=1)
    increment_step = Column(Numeric(18, 2), nullable=True, default=50)
    report_folder = Column(String(200), nullable=True)
    protocol_folder = Column(String(200), nullable=True)
    app_version = Column(String(20), nullable=True)


class FeePresetGroup(Base):
    __tablename__ = "fee_preset_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False, default=1)
    name = Column(String(200), nullable=False)
    contract_type = Column(String(1), nullable=False)
    description = Column(String(400), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)

    templates = relationship("ServiceFeeTemplate", back_populates="preset_group", cascade="all, delete-orphan")


class ServiceFeeTemplate(Base):
    __tablename__ = "service_fee_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False, default=1)
    preset_id = Column(Integer, ForeignKey("fee_preset_groups.id", ondelete="CASCADE"), nullable=True)
    contract_type = Column(String(1), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    name = Column(String(200), nullable=False)
    amount_from = Column(Numeric(18, 2), nullable=True)
    amount_to = Column(Numeric(18, 2), nullable=True)
    unit = Column(String(50), nullable=True)
    description = Column(String(400), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    preset_group = relationship("FeePresetGroup", back_populates="templates")


class Salesperson(Base):
    __tablename__ = "salespeople"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class RateType(Base):
    __tablename__ = "rate_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(400), nullable=False)
    description = Column(String(800), nullable=True)
    is_dependent = Column(Boolean, nullable=True, default=False)


class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    address = Column(String(200), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    street = Column(String(100), nullable=True)
    created_at = Column(String(30), nullable=True)
