from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


class ArticleListItem(BaseModel):
    id: int
    name: str
    is_service: bool
    internal_number: str | None
    registration_no: str | None
    serial_no: str | None
    brand: str | None
    model: str | None
    replacement_value: Decimal | None
    category_name: str | None
    # RAO-P1-026: kategoria hierarchiczna (do filtrów statystyk)
    category_main: str | None = None
    is_archival: bool = False
    is_external: bool = False  # RAO-P1-027
    owner_name: str | None
    notes: str | None
    active_contract_number: str | None
    # RAO-P2-012: Fakturownia product mapping (1:N global)
    fakturownia_product_id: int | None = None
    created_at: datetime
    updated_at: datetime | None
    conditions_count: int

    class Config:
        from_attributes = True


class ArticleDetail(BaseModel):
    id: int
    name: str
    is_service: bool
    internal_number: str | None
    registration_no: str | None
    serial_no: str | None
    brand: str | None
    model: str | None
    replacement_value: Decimal | None
    category_id: int | None
    category_name: str | None
    # RAO-P1-026: hierarchia kategorii
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
    article_type: str | None
    is_archival: bool = False
    is_external: bool = False  # RAO-P1-027
    # RAO-P1-026: dane techniczne
    zasieg_m: Decimal | None = None
    udzwig_t: Decimal | None = None
    dodatki: str | None = None
    # RAO-P2-012: Fakturownia product mapping (1:N global)
    fakturownia_product_id: int | None = None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ArticleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_service: bool = False
    is_archival: bool = False
    is_external: bool = False  # RAO-P1-027
    internal_number: str | None = Field(None, max_length=50)
    registration_no: str | None = Field(None, max_length=40)
    serial_no: str | None = Field(None, max_length=40)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    replacement_value: Decimal | None = None
    category_id: int | None = None
    owner_id: int | None = None
    branch_id: int | None = None
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    article_type: str | None = Field(None, max_length=20)
    # RAO-P1-026: dane techniczne
    zasieg_m: Decimal | None = None
    udzwig_t: Decimal | None = None
    dodatki: str | None = None
    # RAO-P2-012: Fakturownia product mapping (1:N global)
    fakturownia_product_id: int | None = None


class AvailabilityConflict(BaseModel):
    contract_id: int
    contract_number: str
    date_from: date | None
    date_to: date | None
    contractor_name: str


class AvailabilityResponse(BaseModel):
    is_available: bool
    conflicting_contracts: list[AvailabilityConflict]
