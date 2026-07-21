"""P1-205 Faza 1: Schemas dla read-only kalendarza dostaw (źródło: umowy)."""
from pydantic import BaseModel
from datetime import date
from typing import Optional


class DeliveryCalendarEvent(BaseModel):
    """Event dostawy na kalendarzu — pochodzi z umów (read-only, brak osobnej tabeli)."""

    source: str  # zawsze "contract" (jedyny source)
    source_id: int  # contract_id
    contract_number: str
    contract_type: str  # "S" | "U"
    machine_id: Optional[int] = None  # z pozycji (LEFT JOIN), NULL dla umów U bez machine
    machine_name: Optional[str] = None
    internal_number: Optional[str] = None
    contractor_id: int
    contractor_name: str
    delivery_date: date  # Contract.date_from
    delivery_address: Optional[str] = None
    city: Optional[str] = None
    salesperson_id: Optional[int] = None
    salesperson_name: Optional[str] = None
    model_config = {"from_attributes": True}
