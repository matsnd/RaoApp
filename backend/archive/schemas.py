"""RAO-P2-062 Faza 1 - Pydantic v2 schemas dla archiwum.

Mirror schematow contracts/articles/categories ale BEZ is_legacy.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from shared.pagination import PaginatedResponse


# ── Kategorie archiwum (CRUD - mirror settings.schemas.Category*) ────────────

class ArchiveCategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    code: str | None = Field(None, max_length=40)
    description: str | None = Field(None, max_length=400)
    parent_id: int | None = None
    level: str = Field("main", pattern="^(main|sub1|sub2|sub3)$")


class ArchiveCategoryResponse(BaseModel):
    id: int
    name: str
    code: str | None = None
    description: str | None = None
    parent_id: int | None = None
    level: str = "main"

    class Config:
        from_attributes = True


class ArchiveCategoryTreeNode(BaseModel):
    id: int
    name: str
    level: str
    code: str | None = None
    parent_id: int | None = None
    children: list["ArchiveCategoryTreeNode"] = []

    class Config:
        from_attributes = True


ArchiveCategoryTreeNode.model_rebuild()


# ── Artykuly archiwum (read + PATCH category_id) ─────────────────────────────

class ArchiveArticleResponse(BaseModel):
    id: int
    name: str
    is_service: bool
    internal_number: str | None = None
    registration_no: str | None = None
    serial_no: str | None = None
    brand: str | None = None
    model: str | None = None
    replacement_value: Decimal | None = None
    category_id: int | None = None
    owner_id: int | None = None
    branch_id: int | None = None
    description: str | None = None
    notes: str | None = None
    rental_days: int | None = None
    article_type: str | None = None
    category_main: str | None = None
    category_sub1: str | None = None
    category_sub2: str | None = None
    category_sub3: str | None = None
    is_archival: bool = False
    is_external: bool = False
    zasieg_m: Decimal | None = None
    udzwig_t: Decimal | None = None
    dodatki: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ArchiveArticleCategoryUpdate(BaseModel):
    """Jedyny write na archive_articles - zmiana kategorii (PATCH)."""
    category_id: int | None = None


# ── Pozycje / warunki / oplaty / rozliczenia ─────────────────────────────────

class ArchiveConditionResponse(BaseModel):
    id: int
    position_id: int
    rate_type_id: int | None = None
    rate_type_name: str | None = None
    description: str | None = None
    rate1: Decimal | None = None
    rate2: Decimal | None = None
    billing_label: str | None = None
    period_count: int | None = None
    minimum: int | None = None

    class Config:
        from_attributes = True


class ArchivePositionResponse(BaseModel):
    id: int
    contract_id: int
    article_id: int
    article_name: str | None = None
    rental_type: str | None = None
    description: str | None = None
    rental_days: int | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None
    costs: Decimal | None = None
    rate_type_id: int | None = None
    rate_type_name: str | None = None
    billing_frequency: str | None = None
    billing_unit: str | None = None
    supplier_id: int | None = None
    delivery_date: date | None = None
    conditions: list[ArchiveConditionResponse] = []

    class Config:
        from_attributes = True


class ArchiveServiceFeeResponse(BaseModel):
    id: int
    contract_id: int
    sort_order: int
    name: str
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
    description: str | None = None
    is_active: bool
    article_id: int | None = None
    default_price: Decimal | None = None

    class Config:
        from_attributes = True


class ArchiveSettlementResponse(BaseModel):
    id: int
    contract_id: int
    position_id: int | None = None
    service_fee_id: int | None = None
    cost_client: Decimal | None = None
    cost_company: Decimal | None = None
    notes: str | None = None
    settled_at: date | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# ── Umowy archiwum ───────────────────────────────────────────────────────────

class ArchiveContractListItem(BaseModel):
    id: int
    contractor_id: int
    contractor_name: str | None
    number: str
    contract_type: str
    type_label: str
    delivery_address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    prepayment_amount: Decimal | None = None
    notes: str | None = None
    email: str | None = None
    contact_person1: str | None = None
    contact_phone1: str | None = None
    phone: str | None = None
    is_settled: bool = False
    settled_at: datetime | None = None
    position_count: int | None = None
    duration_days: int | None = None
    revenue_estimate: Decimal = Decimal("0.00")
    created_at: datetime

    class Config:
        from_attributes = True


class ArchiveContractDetail(BaseModel):
    id: int
    contractor_id: int
    contractor_name: str | None = None
    branch_id: int | None = None
    salesperson_id: int | None = None
    number: str
    auto_number: int | None = None
    contract_type: str
    delivery_address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    date_from: date | None = None
    date_to: date | None = None
    prepayment_amount: Decimal | None = None
    prepayment_document: str | None = None
    notes: str | None = None
    contact_person1: str | None = None
    contact_phone1: str | None = None
    show_person1: bool = True
    contact_person2: str | None = None
    contact_phone2: str | None = None
    show_person2: bool = True
    email: str | None = None
    phone: str | None = None
    report_without_data: bool = False
    hide_delivery_address: bool = False
    signatures_on_page1: bool = False
    working_days_per_week: int | None = None
    print_date: datetime | None = None
    is_settled: bool = False
    settled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    positions: list[ArchivePositionResponse] = []
    service_fees: list[ArchiveServiceFeeResponse] = []
    settlements: list[ArchiveSettlementResponse] = []

    class Config:
        from_attributes = True


# ── Stats ────────────────────────────────────────────────────────────────────

class ArchiveStatsSummary(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    contracts_count: int = 0
    positions_count: int = 0
    revenue_estimate: Decimal = Decimal("0.00")


class ArchiveTopMachineItem(BaseModel):
    article_id: int
    article_name: str
    internal_number: str | None = None
    contracts_count: int
    rented_days: int = 0
    revenue_estimate: Decimal = Decimal("0.00")


class ArchiveCategoryStatItem(BaseModel):
    category_id: int | None = None
    category_name: str
    contracts_count: int = 0
    positions_count: int = 0
    revenue_estimate: Decimal = Decimal("0.00")


class ArchiveMachineRoiResponse(BaseModel):
    article_id: int
    name: str
    internal_number: str | None = None
    replacement_value: Decimal | None = None
    revenue_estimate: Decimal = Decimal("0.00")
    contracts_count: int = 0
    rented_days: int = 0
    roi_pct: float | None = None


class ArchiveCityStatItem(BaseModel):
    city: str
    contracts_count: int = 0
    positions_count: int = 0
    revenue_estimate: Decimal = Decimal("0.00")
    postal_codes_count: int = 0


# Re-eksport dla wygody routerow
__all__ = [
    "PaginatedResponse",
    "ArchiveCategoryCreate",
    "ArchiveCategoryResponse",
    "ArchiveCategoryTreeNode",
    "ArchiveArticleResponse",
    "ArchiveArticleCategoryUpdate",
    "ArchiveConditionResponse",
    "ArchivePositionResponse",
    "ArchiveServiceFeeResponse",
    "ArchiveSettlementResponse",
    "ArchiveContractListItem",
    "ArchiveContractDetail",
    "ArchiveStatsSummary",
    "ArchiveTopMachineItem",
    "ArchiveCategoryStatItem",
    "ArchiveMachineRoiResponse",
    "ArchiveCityStatItem",
]
