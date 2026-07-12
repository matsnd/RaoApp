from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


class ServiceListItem(BaseModel):
    id: int
    name: str
    description: str | None
    fakturownia_product_id: int | None = None
    created_at: datetime
    updated_at: datetime | None
    # P1-126: fields to align shape with MachineListItem so the frontend
    # article picker can use the same table for both contracts types (S/U).
    is_service: bool = True
    brand: str | None = None
    registration_no: str | None = None
    is_external: bool = False

    class Config:
        from_attributes = True


class ServiceDetail(BaseModel):
    id: int
    name: str
    description: str | None
    notes: str | None
    replacement_value: Decimal | None = Field(None, ge=0, decimal_places=2)
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    replacement_value: Decimal | None = Field(None, ge=0, decimal_places=2)
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None


class ServiceUpdate(BaseModel):
    """Partial update — only fields explicitly sent are applied."""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    replacement_value: Decimal | None = Field(None, ge=0, decimal_places=2)
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
