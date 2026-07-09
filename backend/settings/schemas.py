from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


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
    logo_url: str | None = None  # RAO-P3-002: URL do logo firmy (mapuje logo_path z modelu)

    class Config:
        from_attributes = True
        populate_by_name = True

    @model_validator(mode='before')
    @classmethod
    def map_logo_path(cls, data):
        if hasattr(data, '__dict__'):
            # ORM object
            if 'logo_url' not in (data.__dict__ or {}) and hasattr(data, 'logo_path'):
                data.__dict__['logo_url'] = data.logo_path
        elif isinstance(data, dict) and 'logo_url' not in data and 'logo_path' in data:
            data['logo_url'] = data['logo_path']
        return data


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
    name: str
    amount_from: Decimal | None
    amount_to: Decimal | None
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ServiceFeeTemplateCreate(BaseModel):
    contract_type: Literal["S", "U"]
    preset_id: int | None = None
    # RAO-P1-011: opcjonalna referencja do artykułu (gdy ustawiona, nazwa derive z articles)
    article_id: int | None = None
    name: str = Field(..., max_length=200)
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
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


class CategoryTreeNode(BaseModel):
    id: int
    name: str
    level: str
    code: str | None = None
    parent_id: int | None = None
    children: list['CategoryTreeNode'] = []

    class Config:
        from_attributes = True


CategoryTreeNode.model_rebuild()  # wymagane dla self-referential Pydantic v2


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    code: str | None = Field(None, max_length=40)
    description: str | None = Field(None, max_length=400)
    parent_id: int | None = None
    level: str = Field("main", pattern="^(main|sub1|sub2|sub3)$")


class CategoryResponse(BaseModel):
    id: int
    name: str
    code: str | None = None
    description: str | None = None
    parent_id: int | None = None
    level: str = "main"

    class Config:
        from_attributes = True


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


# RAO-P1-001: Predefiniowane cenniki warunków rozliczenia maszyn

class ArticleRatePresetItemCreate(BaseModel):
    rate_type_id: int | None = None
    description: str | None = Field(None, max_length=400)
    rate1: Decimal | None = None
    rate2: Decimal | None = None
    billing_label: str | None = Field(None, max_length=20)
    period_count: int | None = None
    minimum: int | None = None


class ArticleRatePresetItemUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied."""
    rate_type_id: int | None = None
    description: str | None = Field(None, max_length=400)
    rate1: Decimal | None = None
    rate2: Decimal | None = None
    billing_label: str | None = Field(None, max_length=20)
    period_count: int | None = None
    minimum: int | None = None


class ArticleRatePresetItemResponse(ArticleRatePresetItemCreate):
    id: int
    preset_id: int
    sort_order: int

    class Config:
        from_attributes = True


class ArticleRatePresetCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = Field(None, max_length=400)
    is_default: bool = False
    items: list[ArticleRatePresetItemCreate] = []


class ArticleRatePresetUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied."""
    name: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=400)
    is_default: bool | None = None


class ArticleRatePresetResponse(BaseModel):
    id: int
    article_id: int
    name: str
    description: str | None
    is_default: bool
    sort_order: int
    items: list[ArticleRatePresetItemResponse] = []

    class Config:
        from_attributes = True
