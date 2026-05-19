"""RAO-P3-005: Model dostaw (deliveries).

Tabela `deliveries` rejestruje pojedyncze zlecenia dostawy / odbioru maszyny
w ramach umowy. Powiązana z `contracts` (CASCADE) oraz opcjonalnie z konkretną
pozycją `contract_positions` (SET NULL).
"""
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func

from database import Base


class Delivery(Base):
    __tablename__ = "deliveries"

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
    delivery_type = Column(
        Enum("deliver", "collect", name="delivery_type_enum"),
        nullable=False,
        default="deliver",
    )
    scheduled_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    address = Column(String(500), nullable=True)
    driver = Column(String(200), nullable=True)
    note = Column(String(500), nullable=True)
    status = Column(
        Enum("pending", "done", "cancelled", name="delivery_status_enum"),
        nullable=False,
        default="pending",
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
