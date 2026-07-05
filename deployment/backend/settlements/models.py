from sqlalchemy import Column, Integer, BigInteger, String, Text, DECIMAL, DateTime, Date, ForeignKey, UniqueConstraint, Computed
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class ContractSettlement(Base):
    __tablename__ = "contract_settlements"
    __table_args__ = (
        # RAO-P2-032: idempotentny import rozliczenie — UNIQUE zapobiega duplikatom mapped settlements
        UniqueConstraint("contract_id", "position_id", "service_fee_id", "settled_at",
                         name="uq_settlements_contract_pos_fee_date"),
        # RAO Faza 2a (opcja E): idempotentność unmapped — UNIQUE na generated unmapped_key
        UniqueConstraint("unmapped_key", name="uq_settlements_unmapped_key"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    position_id = Column(Integer, ForeignKey("contract_positions.id", ondelete="CASCADE"), nullable=True)
    service_fee_id = Column(Integer, ForeignKey("contract_service_fees.id", ondelete="CASCADE"), nullable=True)
    cost_client = Column(DECIMAL(18, 2), nullable=True)
    cost_company = Column(DECIMAL(18, 2), nullable=True)
    notes = Column(Text, nullable=True)
    settled_at = Column(Date, nullable=True, comment="Data rozliczenia (legacy/Fakturownia)")
    source = Column(String(20), nullable=True, server_default="manual",
                    comment="Źródło: legacy/fakturownia/manual/fa_unmapped")
    # RAO Faza 2a (opcja E): unmapped settlements z Fakturownia
    article_name_snapshot = Column(String(255), nullable=True,
                                   comment="Snapshot nazwy pozycji z FA (gdy position_id=NULL)")
    fakturownia_product_id = Column(BigInteger, nullable=True,
                                    comment="ID produktu FA (grupowanie w analytics, duplikaty)")
    fakturownia_invoice_number = Column(String(50), nullable=True,
                                        comment="Numer faktury FA (wydzielony z notes dla query)")
    unmapped_key = Column(
        String(100),
        Computed(
            "CASE WHEN position_id IS NULL AND service_fee_id IS NULL "
            "THEN CONCAT('unmapped:', IFNULL(fakturownia_product_id,0), ':', IFNULL(fakturownia_invoice_number,'')) "
            "ELSE NULL END",
            persisted=True,
        ),
        nullable=True,
        comment="Klucz deduplikacji unmapped (NULL dla mapped)",
    )
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