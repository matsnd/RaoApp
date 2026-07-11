from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class AdditionalServiceListItem(BaseModel):
    id: int
    name: str
    default_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None
    is_archival: bool = False
    fakturownia_product_id: int | None = None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class AdditionalServiceDetail(BaseModel):
    id: int
    name: str
    default_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None
    notes: str | None
    is_archival: bool = False
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class AdditionalServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    default_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    is_archival: bool = False
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None


class AdditionalServiceUpdate(BaseModel):
    """Partial update — only fields explicitly sent are applied."""
    name: str | None = Field(None, min_length=1, max_length=200)
    default_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    is_archival: bool | None = None
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
