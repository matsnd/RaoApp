from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    salesperson_id = Column(Integer, ForeignKey("salespeople.id", ondelete="SET NULL"), nullable=True)
    number = Column(String(40), nullable=False, unique=True)  # RAO-P0-030: UNIQUE constraint (DB index uq_contracts_number już istnieje w main.py)
    oid = Column(String(40), nullable=True, comment="Numer zamówienia w Fakturownia (dla integracji RAO-P2-012)")
    auto_number = Column(Integer, nullable=True)
    contract_type = Column(String(1), nullable=False, default="S")
    delivery_address = Column(Text, nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code_id = Column(Integer, ForeignKey("postal_codes.id", ondelete="SET NULL"), nullable=True, index=True, comment="RAO-P2-028: FK do postal_codes (deterministyczna lokalizacja)")
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    date_from = Column(Date, nullable=True)
    date_to = Column(Date, nullable=True)
    # RAO-P1-021/P2-033: total_value usunięte (martwe pole, 100% NULL)
    prepayment_amount = Column(Numeric(18, 2), nullable=True, default=0)
    prepayment_document = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    contact_person1 = Column(String(100), nullable=True)
    contact_phone1 = Column(String(100), nullable=True)
    show_person1 = Column(Boolean, nullable=False, default=True)
    contact_person2 = Column(String(100), nullable=True)
    contact_phone2 = Column(String(100), nullable=True)
    show_person2 = Column(Boolean, nullable=False, default=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(40), nullable=True)
    contractor_name = Column(String(200), nullable=True)
    print_path = Column(String(100), nullable=True)
    print_date = Column(DateTime, nullable=True)
    report_without_data = Column(Boolean, nullable=False, default=False)
    hide_delivery_address = Column(Boolean, nullable=False, default=False)
    signatures_on_page1 = Column(Boolean, nullable=False, default=False)
    working_days_per_week = Column(Integer, nullable=True, default=6)
    position_count = Column(Integer, nullable=True, default=0)
    is_settled = Column(Boolean, nullable=False, default=False)  # RAO-P2-022: umowa rozliczona
    settled_at = Column(DateTime, nullable=True)                  # RAO-P2-022: kiedy rozliczona
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    positions = relationship("ContractPosition", back_populates="contract", cascade="all, delete-orphan")
    service_fees = relationship("ContractServiceFee", back_populates="contract", cascade="all, delete-orphan")
    postal_code_ref = relationship("PostalCode", lazy="selectin")  # RAO-P2-028: JOIN do słownika PNA


class ContractPosition(Base):
    __tablename__ = "contract_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    description = Column(String(400), nullable=True)
    rental_days = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True, default=1)
    unit_price = Column(Numeric(18, 2), nullable=True)
    rate_type_id = Column(Integer, ForeignKey("rate_types.id", ondelete="SET NULL"), nullable=True)
    billing_frequency = Column(String(20), nullable=True)
    billing_unit = Column(String(20), nullable=True)
    supplier_id = Column(Integer, ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True)
    delivery_date = Column(Date, nullable=True)
    article_name = Column(String(400), nullable=True)

    contract = relationship("Contract", back_populates="positions")
    conditions = relationship("PositionCondition", back_populates="position", cascade="all, delete-orphan")
    machine = relationship("Machine", lazy="selectin")
    service = relationship("Service", lazy="selectin")


class PositionCondition(Base):
    __tablename__ = "position_conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(Integer, ForeignKey("contract_positions.id", ondelete="CASCADE"), nullable=False)
    rate1 = Column(Numeric(18, 2), nullable=True)
    rate2 = Column(Numeric(18, 2), nullable=True)
    billing_label = Column(String(20), nullable=True)
    period_count = Column(Integer, nullable=True)  # RAO-P1-005: backward compatibility
    period_from = Column(Integer, nullable=True)  # RAO-P1-005: elastyczne widełki (od)
    period_to = Column(Integer, nullable=True)    # RAO-P1-005: elastyczne widełki (do)

    position = relationship("ContractPosition", back_populates="conditions")


class ContractServiceFee(Base):
    __tablename__ = "contract_service_fees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    # P1-120: FK do additional_services (mapowanie dla statystyk/Fakturowni)
    additional_service_id = Column(
        Integer,
        ForeignKey("additional_services.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(200), nullable=False)
    amount_from = Column(Numeric(18, 2), nullable=True)
    amount_to = Column(Numeric(18, 2), nullable=True)
    description = Column(String(400), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    contract = relationship("Contract", back_populates="service_fees")
    additional_service = relationship("AdditionalService", lazy="selectin", foreign_keys=[additional_service_id])
