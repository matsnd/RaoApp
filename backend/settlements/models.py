from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class ContractSettlement(Base):
    __tablename__ = "contract_settlements"
    __table_args__ = (
        # RAO-P2-032: idempotentny import rozliczenie — UNIQUE zapobiega duplikatom
        UniqueConstraint("contract_id", "position_id", "service_fee_id", "settled_at",
                         name="uq_settlements_contract_pos_fee_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    position_id = Column(Integer, ForeignKey("contract_positions.id", ondelete="CASCADE"), nullable=True)
    service_fee_id = Column(Integer, ForeignKey("contract_service_fees.id", ondelete="CASCADE"), nullable=True)
    cost_client = Column(DECIMAL(18, 2), nullable=True)
    cost_company = Column(DECIMAL(18, 2), nullable=True)
    notes = Column(Text, nullable=True)
    # RAO-P2-032: data rozliczenia (z rozliczenie.data lub data importu z Fakturownia)
    settled_at = Column(Date, nullable=True, comment="Data rozliczenia (z legacy rozliczenie.data lub Fakturownia)")
    # RAO-P2-032: źródło danych — 'legacy' (import z rozliczenie), 'fakturownia', 'manual'
    source = Column(String(20), nullable=True, server_default="manual",
                    comment="Źródło: legacy/fakturownia/manual")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    contract = relationship("Contract", lazy="selectin")
    position = relationship("ContractPosition", lazy="selectin")
    service_fee = relationship("ContractServiceFee", lazy="selectin")

    @property
    def margin(self):
        """Marża = cost_client - cost_company"""
        if self.cost_client is None or self.cost_company is None:
            return None
        return self.cost_client - self.cost_company

    @property
    def service_fee_name(self) -> str | None:
        """Nazwa usługi dodatkowej (dla wyświetlania w UI)"""
        if self.service_fee:
            return self.service_fee.name
        return None