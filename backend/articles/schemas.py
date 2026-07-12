from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

# RAO: typ zasilania maszyny — dopuszczalne wartości (kolumna articles.power_type)
PowerType = Literal["diesel", "electric", "other"]


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
    is_external: bool = False  # RAO-P1-027
    owner_name: str | None
    notes: str | None
    active_contract_number: str | None
    # RAO-P2-012: Fakturownia product mapping (1:N global)
    fakturownia_product_id: int | None = None
    # RAO-P2-058: snapshot metadanych z FA
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
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
    is_external: bool = False  # RAO-P1-027
    # RAO-P1-026: dane techniczne
    zasieg_m: Decimal | None = None
    udzwig_t: Decimal | None = None
    dodatki: str | None = None
    # RAO-P2-012: Fakturownia product mapping (1:N global)
    fakturownia_product_id: int | None = None
    # RAO-P2-058: snapshot metadanych z FA
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    # RAO: typ zasilania maszyny (backward compat — default 'other')
    power_type: str = "other"
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ArticleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_service: bool = False
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
    # RAO-P2-058: snapshot metadanych z FA
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    # RAO: typ zasilania maszyny
    power_type: PowerType = "other"


class ArticleUpdate(BaseModel):
    """RAO: Partial update — only fields explicitly sent are applied.

    Używana z model_dump(exclude_unset=True) w ArticleService.update_article
    (zgodnie ze wzorcem RAO-P0-034 jak ContractUpdate/ConditionUpdate).
    """
    name: str | None = Field(None, min_length=1, max_length=200)
    is_service: bool | None = None
    is_external: bool | None = None
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
    zasieg_m: Decimal | None = None
    udzwig_t: Decimal | None = None
    dodatki: str | None = None
    fakturownia_product_id: int | None = None
    fakturownia_tax_rate: str | None = None
    fakturownia_gtu_code: str | None = None
    fakturownia_pkwiu: str | None = None
    # RAO: typ zasilania maszyny (opcjonalny przy partial update)
    power_type: PowerType | None = None


class AvailabilityConflict(BaseModel):
    contract_id: int
    contract_number: str
    date_from: date | None
    date_to: date | None
    contractor_name: str


class AvailabilityReservationConflict(BaseModel):
    """RAO-P2-066: konflikt z ręczną rezerwacją maszyny (article_reservations)."""
    reservation_id: int
    reserved_from: date
    reserved_to: date
    note: str | None = None
    # Data, od której maszyna będzie dostępna (= reserved_to + 1 dzień)
    available_from: date | None = None
    # RAO-L-Phase2: powiązanie z kontrahentem (JOIN contractors)
    contractor_id: int | None = None
    contractor_name: str | None = None


class AvailabilityResponse(BaseModel):
    is_available: bool
    conflicting_contracts: list[AvailabilityConflict]
    # RAO-P2-066: konflikty z rezerwacjami (article_reservations)
    conflicting_reservations: list[AvailabilityReservationConflict] = []
