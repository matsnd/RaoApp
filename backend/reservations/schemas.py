from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import Optional


class ReservationCreate(BaseModel):
    machine_id: int
    reserved_from: date
    reserved_to: date
    note: Optional[str] = Field(None, max_length=300)
    contractor_id: Optional[int] = None
    status: str = Field("confirmed", pattern="^(confirmed|provisional)$")

    @model_validator(mode="after")
    def validate_dates(self) -> "ReservationCreate":
        if self.reserved_from > self.reserved_to:
            raise ValueError("reserved_from must be <= reserved_to")
        return self


class ReservationUpdate(BaseModel):
    reserved_from: Optional[date] = None
    reserved_to: Optional[date] = None
    note: Optional[str] = Field(None, max_length=300)
    # RAO-L-Phase2: edycja powiązania z kontrahentem
    contractor_id: Optional[int] = None
    # RAO-L-Phase2: edycja statusu rezerwacji
    status: Optional[str] = Field(None, pattern="^(confirmed|provisional)$")
    # P2-003: zmiana maszyny (z walidacją is_external w service.update)
    machine_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ReservationUpdate":
        if (
            self.reserved_from is not None
            and self.reserved_to is not None
            and self.reserved_from > self.reserved_to
        ):
            raise ValueError("reserved_from must be <= reserved_to")
        return self


class ReservationResponse(BaseModel):
    id: int
    machine_id: int
    reserved_from: date
    reserved_to: date
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    contractor_id: Optional[int] = None
    status: str = "confirmed"
    model_config = {"from_attributes": True}


class ReservationWithMachineResponse(BaseModel):
    id: int
    machine_id: int
    machine_name: Optional[str] = None
    internal_number: Optional[str] = None
    reserved_from: date
    reserved_to: date
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    model_config = {"from_attributes": True}
    contractor_id: Optional[int] = None
    contractor_name: Optional[str] = None
    status: str = "confirmed"


class CalendarEvent(BaseModel):
    """Event na kalendarzu rezerwacji — z rezerwacji lub umowy."""
    source: str  # "reservation" | "contract"
    source_id: int  # reservation_id lub contract_id
    machine_id: Optional[int] = None  # None dla pozycji umowy bez machine_id (usługi)
    machine_name: Optional[str] = None
    internal_number: Optional[str] = None
    contractor_id: Optional[int] = None
    contractor_name: Optional[str] = None
    date_from: date
    date_to: Optional[date] = None  # umowa może nie mieć date_to
    note: Optional[str] = None  # note z rezerwacji lub number umowy
    status: Optional[str] = None  # tylko dla rezerwacji
