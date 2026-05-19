from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class CompanyResponse(BaseModel):
    id: int
    name: str | None
    name_short: str | None
    nip: str | None
    regon: str | None
    postal_code: str | None
    city: str | None
    street: str | None
    header_text: str | None
    bank_name: str | None
    bank_account: str | None
    numbering_start: int | None
    increment_step: Decimal | None
    report_folder: str | None
    protocol_folder: str | None

    class Config:
        from_attributes = True


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    name_short: str | None = Field(None, max_length=100)
    nip: str | None = Field(None, max_length=20)
    regon: str | None = Field(None, max_length=20)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=50)
    street: str | None = Field(None, max_length=50)
    header_text: str | None = None
    bank_name: str | None = Field(None, max_length=200)
    bank_account: str | None = Field(None, max_length=40)
    numbering_start: int | None = None
    increment_step: Decimal | None = None
    report_folder: str | None = Field(None, max_length=200)
    protocol_folder: str | None = Field(None, max_length=200)


class ServiceFeeTemplateResponse(BaseModel):
    id: int
    preset_id: int | None
    contract_type: str
    sort_order: int
    # RAO-P1-011: FK do articles + nazwa z articles (jeśli article_id ustawiony)
    article_id: int | None = None
    article_name: str | None = None
    default_price: Decimal | None = None
    name: str
    amount_from: Decimal | None
    amount_to: Decimal | None
    unit: str | None
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ServiceFeeTemplateCreate(BaseModel):
    contract_type: Literal["S", "U"]
    preset_id: int | None = None
    # RAO-P1-011: opcjonalna referencja do artykułu (gdy ustawiona, nazwa derive z articles)
    article_id: int | None = None
    default_price: Decimal | None = None
    name: str = Field(..., max_length=200)
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
    unit: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=400)
    is_active: bool = True


class ServiceFeeTemplateReorder(BaseModel):
    ids: list[int]


class FeePresetGroupCreate(BaseModel):
    name: str = Field(..., max_length=200)
    contract_type: Literal["S", "U"]
    description: str | None = Field(None, max_length=400)
    is_default: bool = False


class FeePresetGroupResponse(BaseModel):
    id: int
    name: str
    contract_type: str
    description: str | None
    is_default: bool
    sort_order: int
    templates: list[ServiceFeeTemplateResponse] = []

    class Config:
        from_attributes = True


class SalespersonResponse(BaseModel):
    id: int
    name: str
    phone: str | None
    is_active: bool
    commission_rate: Decimal | None

    class Config:
        from_attributes = True


class SalespersonCreate(BaseModel):
    name: str = Field(..., max_length=200)
    phone: str | None = Field(None, max_length=100)
    commission_rate: Decimal | None = Field(None, ge=0, le=100, description="Prowizja w % (0-100)")


class CategoryResponse(BaseModel):
    id: int
    name: str
    code: str | None
    description: str | None

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    code: str | None = Field(None, max_length=40)
    description: str | None = Field(None, max_length=400)


class BranchResponse(BaseModel):
    id: int
    name: str
    address: str | None
    postal_code: str | None
    city: str | None
    street: str | None

    class Config:
        from_attributes = True


class BranchCreate(BaseModel):
    name: str = Field(..., max_length=200)
    address: str | None = Field(None, max_length=200)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=100)
    street: str | None = Field(None, max_length=100)


class RateTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_dependent: bool

    class Config:
        from_attributes = True


class RateTypeCreate(BaseModel):
    name: str = Field(..., max_length=400)
    description: str | None = Field(None, max_length=800)
    is_dependent: bool = False


# RAO-P3-001: reorder szablonów opłat
class ReorderItem(BaseModel):
    id: int
    sort_order: int


class ReorderRequest(BaseModel):
    order: list[ReorderItem]
