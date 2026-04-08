from datetime import datetime, date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class ConditionResponse(BaseModel):
    id: int
    position_id: int
    rate_type_id: int | None
    rate_type_name: str | None
    description: str | None
    rate1: Decimal | None
    rate2: Decimal | None
    billing_label: str | None
    period_count: int | None
    minimum: int | None

    class Config:
        from_attributes = True


class ConditionCreate(BaseModel):
    rate_type_id: int | None = None
    description: str | None = Field(None, max_length=400)
    rate1: Decimal | None = None
    rate2: Decimal | None = None
    billing_label: str | None = None
    period_count: int | None = None
    minimum: int | None = None


class PositionResponse(BaseModel):
    id: int
    contract_id: int
    article_id: int
    article_name: str | None
    rental_type: str | None
    description: str | None
    rental_days: int | None
    quantity: int | None
    unit_price: Decimal | None
    costs: Decimal | None
    rate_type_id: int | None
    rate_type_name: str | None
    billing_frequency: str | None
    billing_unit: str | None
    supplier_id: int | None
    supplier_name: str | None
    delivery_date: date | None
    conditions_count: int
    conditions: list[ConditionResponse] = []

    class Config:
        from_attributes = True


class PositionCreate(BaseModel):
    article_id: int
    rental_type: str | None = None
    description: str | None = Field(None, max_length=400)
    rental_days: int | None = None
    quantity: int = 1
    unit_price: Decimal | None = None
    costs: Decimal | None = None
    rate_type_id: int | None = None
    billing_frequency: str | None = None
    billing_unit: str | None = None
    supplier_id: int | None = None
    delivery_date: date | None = None


class ContractServiceFeeResponse(BaseModel):
    id: int
    sort_order: int
    name: str
    amount_from: Decimal | None
    amount_to: Decimal | None
    unit: str | None
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ContractServiceFeeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
    unit: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=400)
    is_active: bool = True


class ContractServiceFeeReorder(BaseModel):
    ids: list[int]


class ContractListItem(BaseModel):
    id: int
    contractor_id: int
    contractor_name: str
    number: str
    contract_type: str
    type_label: str
    delivery_address: str | None
    date_from: date | None
    date_to: date | None
    total_value: Decimal | None
    prepayment_amount: Decimal | None
    invoice_amount: Decimal | None
    notes: str | None
    email: str | None
    contact_person1: str | None = None
    contact_phone1: str | None = None
    phone: str | None = None
    salesperson_name: str | None
    print_date: datetime | None
    is_print_current: bool
    duration_days: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ContractDetail(BaseModel):
    id: int
    contractor_id: int
    contractor_name: str | None
    branch_id: int | None
    salesperson_id: int | None
    number: str
    auto_number: int | None
    contract_type: str
    delivery_address: str | None
    date_from: date | None
    date_to: date | None
    total_value: Decimal | None
    prepayment_amount: Decimal | None
    prepayment_document: str | None
    invoice_amount: Decimal | None
    invoice_document: str | None
    notes: str | None
    contact_person1: str | None
    contact_phone1: str | None
    show_person1: bool
    contact_person2: str | None
    contact_phone2: str | None
    show_person2: bool
    email: str | None
    phone: str | None
    report_without_data: bool
    working_days_per_week: int | None
    print_date: datetime | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ContractCreate(BaseModel):
    contractor_id: int
    branch_id: int | None = None
    salesperson_id: int | None = None
    contract_type: Literal["S", "U"] = "S"
    delivery_address: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    total_value: Decimal = Decimal("0.00")
    prepayment_amount: Decimal = Decimal("0.00")
    prepayment_document: str | None = None
    invoice_amount: Decimal = Decimal("0.00")
    invoice_document: str | None = None
    notes: str | None = None
    contact_person1: str | None = None
    contact_phone1: str | None = None
    show_person1: bool = True
    contact_person2: str | None = None
    contact_phone2: str | None = None
    show_person2: bool = True
    email: str | None = None
    phone: str | None = None
    contractor_name: str | None = None
    working_days_per_week: int = 6
    report_without_data: bool = False


class ServiceHourResponse(BaseModel):
    id: int
    position_id: int
    work_date: date
    time_from: str | None
    time_to: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceHourCreate(BaseModel):
    work_date: date
    time_from: str | None = Field(None, max_length=10)
    time_to: str | None = Field(None, max_length=10)
    notes: str | None = Field(None, max_length=200)
