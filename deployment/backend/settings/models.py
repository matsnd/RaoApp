from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
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
    bank_name = Column(String(200), nullable=True)
    bank_account = Column(String(40), nullable=True)
    numbering_start = Column(Integer, nullable=True, default=1)
    increment_step = Column(Numeric(18, 2), nullable=True, default=50)
    logo_path = Column(String(500), nullable=True)  # RAO-P3-002: ścieżka do logo


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
    # FK do additional_services (usługi dodatkowe: transport, tankowanie, etc.)
    additional_service_id = Column(Integer, ForeignKey("additional_services.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    amount_from = Column(Numeric(18, 2), nullable=True)
    amount_to = Column(Numeric(18, 2), nullable=True)
    description = Column(String(400), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    preset_group = relationship("FeePresetGroup", back_populates="templates")
    additional_service = relationship("AdditionalService", lazy="selectin", foreign_keys=[additional_service_id])

    @property
    def article_name(self) -> str | None:
        return self.additional_service.name if self.additional_service else None


class Salesperson(Base):
    __tablename__ = "salespeople"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    commission_rate = Column(Numeric(5, 2), nullable=True, default=0)


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
    created_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())


class MachineRatePreset(Base):
    """Predefiniowany cennik rozliczenia dla konkretnej maszyny.

    Scope: per-machine (machine_id NOT NULL). Jedna maszyna może mieć wiele
    presetów (np. "Standard", "Promo Q1", "Długoterminowy"), z czego jeden
    is_default. Po zastosowaniu w umowie warunki są kopiowane (snapshot) do
    position_conditions — edycja cennika NIE wpływa na istniejące umowy.
    """
    __tablename__ = "machine_rate_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False, default=1)
    machine_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(400), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=True)

    items = relationship(
        "MachineRatePresetItem",
        back_populates="preset",
        cascade="all, delete-orphan",
        order_by="MachineRatePresetItem.sort_order",
    )
    machine = relationship("Machine", lazy="selectin")


class MachineRatePresetItem(Base):
    """Pojedynczy warunek (prog) w presercie — 1:1 z PositionCondition.

    Identyczne pola jak PositionCondition (rate_type_id, rate1, rate2,
    billing_label, period_count, minimum) — apply = bulk copy do position_conditions.
    """
    __tablename__ = "machine_rate_preset_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    preset_id = Column(Integer, ForeignKey("machine_rate_presets.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0)
    rate_type_id = Column(Integer, ForeignKey("rate_types.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(400), nullable=True)
    rate1 = Column(Numeric(18, 2), nullable=True)
    rate2 = Column(Numeric(18, 2), nullable=True)
    billing_label = Column(String(20), nullable=True)
    period_count = Column(Integer, nullable=True)
    minimum = Column(Integer, nullable=True)

    preset = relationship("MachineRatePreset", back_populates="items")
