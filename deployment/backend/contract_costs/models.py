"""RAO-P3-005: Model kosztów dodatkowych umowy (contract_costs).

Tabela `contract_costs` przechowuje koszty dodatkowe naliczane do umowy
(transport, paliwo, naprawy itd.) — powiązane z umową (CASCADE) i opcjonalnie
z konkretną pozycją (SET NULL).
"""
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from database import Base


class ContractCost(Base):
    __tablename__ = "contract_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position_id = Column(
        Integer,
        ForeignKey("contract_positions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cost_type = Column(String(100), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String(500), nullable=True)
    cost_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
