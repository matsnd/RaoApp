from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from database import Base


class MachineReservation(Base):
    __tablename__ = "machine_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(
        Integer,
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reserved_from = Column(Date, nullable=False, index=True)
    reserved_to = Column(Date, nullable=False, index=True)
    note = Column(String(300), nullable=True)
    # RAO-L-Phase1: rezerwacja może być dla kontrahenta (contractor_id) lub bez (NULL)
    contractor_id = Column(
        Integer,
        ForeignKey("contractors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # RAO-L-Phase1: status rezerwacji — usunięty (uproszczenie, wszystkie potwierdzone)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # P1-119: opcjonalny handlowiec powiązany z rezerwacją
    salesperson_id = Column(
        Integer,
        ForeignKey("salespeople.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
