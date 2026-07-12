from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

PowerType = Literal["diesel", "electric", "other"]


class MachineListItem(BaseModel):
    id: int
    name: str
    internal_number: str | None
    registration_no: str | None
    serial_no: str | None
    brand: str | None
    model: str | None
    replacement_value: Decimal | None = Field(None, ge=0, decimal_places=2)
    category_name: str | None
    category_main: str | None = None
    is_external: bool = False
    owner_name: str | None
    notes: str | None
    active_contract_number: str | None
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    created_at: datetime
    updated_at: datetime | None
    conditions_count: int

    class Config:
        from_attributes = True


class MachineDetail(BaseModel):
    id: int
    name: str
    internal_number: str | None
    registration_no: str | None
    serial_no: str | None
    brand: str | None
    model: str | None
    replacement_value: Decimal | None = Field(None, ge=0, decimal_places=2)
    category_id: int | None
    category_name: str | None
    category_main: str | None = None
    category_sub1: str | None = None
    category_sub2: str | None = None
    category_sub3: str | None = None
    owner_id: int | None
    owner_name: str | None
    branch_id: int | None
    description: str | None
    notes: str | None
    rental_days: int | None
    is_external: bool = False
    reach_m: Decimal | None = None
    capacity_t: Decimal | None = None
    accessories: str | None = None
    technical_attributes: dict | None = None
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    power_type: str = "other"
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class MachineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_external: bool = False
    internal_number: str | None = Field(None, max_length=50)
    registration_no: str | None = Field(None, max_length=40)
    serial_no: str | None = Field(None, max_length=40)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    replacement_value: Decimal | None = Field(None, ge=0, decimal_places=2)
    category_id: int | None = None
    owner_id: int | None = None
    branch_id: int | None = None
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    rental_days: int | None = None
    reach_m: Decimal | None = None
    capacity_t: Decimal | None = None
    accessories: str | None = None
    technical_attributes: dict | None = None
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    power_type: PowerType = "other"


class MachineUpdate(BaseModel):
    """Partial update — only fields explicitly sent are applied."""
    name: str | None = Field(None, min_length=1, max_length=200)
    is_external: bool | None = None
    internal_number: str | None = Field(None, max_length=50)
    registration_no: str | None = Field(None, max_length=40)
    serial_no: str | None = Field(None, max_length=40)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    replacement_value: Decimal | None = Field(None, ge=0, decimal_places=2)
    category_id: int | None = None
    owner_id: int | None = None
    branch_id: int | None = None
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    rental_days: int | None = None
    reach_m: Decimal | None = None
    capacity_t: Decimal | None = None
    accessories: str | None = None
    technical_attributes: dict | None = None
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    power_type: PowerType | None = None


class AvailabilityConflict(BaseModel):
    contract_id: int
    contract_number: str
    date_from: date | None
    date_to: date | None
    contractor_name: str


class AvailabilityReservationConflict(BaseModel):
    reservation_id: int
    reserved_from: date
    reserved_to: date
    note: str | None = None
    available_from: date | None = None
    contractor_id: int | None = None
    contractor_name: str | None = None


class AvailabilityResponse(BaseModel):
    is_available: bool
    conflicting_contracts: list[AvailabilityConflict]
    conflicting_reservations: list[AvailabilityReservationConflict] = []
