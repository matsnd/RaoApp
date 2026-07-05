from datetime import datetime, date
from decimal import Decimal
from typing import Literal, Annotated, Optional
from pydantic import BaseModel, Field, model_validator

# RAO-P2-058: OID validation pattern (Fakturownia order ID)
OidStr = Annotated[str, Field(pattern=r"^[A-Za-z0-9\-/_]+$", max_length=40)]


PostalCode = Annotated[str, Field(
    pattern=r"^\d{2}-\d{3}$",
    min_length=6,
    max_length=6,
    examples=["00-001"],
)]

CityName = Annotated[str, Field(
    min_length=1,
    max_length=100,
    pattern=r"^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 \-\.\']+$",
)]


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


class ConditionUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied."""
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


class PositionUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied."""
    article_id: int | None = None
    rental_type: str | None = None
    description: str | None = Field(None, max_length=400)
    rental_days: int | None = None
    quantity: int | None = None
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
    article_id: int | None = None  # RAO-P1-011
    default_price: Decimal | None = None  # RAO-P1-011

    class Config:
        from_attributes = True


class ContractServiceFeeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
    unit: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=400)
    is_active: bool = True
    article_id: int | None = None  # RAO-P2-059: link do artykułu usługi
    default_price: Decimal | None = None  # RAO-P2-059: snapshot ceny z artykułu


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
    postal_code: str | None
    city: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    date_from: date | None
    date_to: date | None
    # RAO-P1-021/P2-033: total_value usunięte (martwe pole, 100% NULL)
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
    is_settled: bool = False          # RAO-P2-022
    settled_at: datetime | None = None  # RAO-P2-022
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
    oid: str | None = None  # RAO-P2-058: Fakturownia order ID (hybrydowe: oid or number)
    contract_type: str
    delivery_address: str | None
    postal_code: str | None
    city: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    date_from: date | None
    date_to: date | None
    # RAO-P1-021/P2-033: total_value usunięte
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
    hide_delivery_address: bool
    signatures_on_page1: bool
    working_days_per_week: int | None
    print_date: datetime | None
    is_settled: bool = False          # RAO-P2-022
    settled_at: datetime | None = None  # RAO-P2-022
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class SettleContractRequest(BaseModel):
    """RAO-P2-022: zmiana statusu rozliczenia umowy."""
    is_settled: bool


class ContractCreate(BaseModel):
    contractor_id: int
    branch_id: int = 1  # RAO-P1-022: domyślnie Warszawa (id=1)
    salesperson_id: int | None = None
    contract_type: Literal["S", "U"] = "S"
    oid: Optional[OidStr] = None  # RAO-P2-058: Fakturownia OID (puste = użyj number)
    delivery_address: str | None = None
    postal_code: PostalCode | None = None
    city: CityName | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    date_from: date | None = None
    date_to: date | None = None
    # RAO-P1-021/P2-033: total_value usunięte
    prepayment_amount: Decimal | None = None
    prepayment_document: str | None = None
    invoice_amount: Decimal | None = None
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
    hide_delivery_address: bool = False
    signatures_on_page1: bool = False

    @model_validator(mode="after")
    def _validate_dates_and_amounts(self):
        # RAO-P1-039: date_from must not be after date_to
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Data rozpoczęcia (date_from) nie może być po dacie zakończenia (date_to).")
        # RAO-P1-039: monetary fields must be non-negative
        # RAO-P1-021/P2-033: total_value usunięte z walidacji
        for field in ("prepayment_amount", "invoice_amount"):
            v = getattr(self, field)
            if v is not None and v < 0:
                raise ValueError(f"{field} nie może być ujemne.")
        return self


class ContractUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied.

    Fixes lost-data bug where PUT with partial body reset unspecified fields
    to ContractCreate defaults (e.g. working_days_per_week=6, contract_type='S').
    Used with model_dump(exclude_unset=True) in update_contract.
    """
    contractor_id: int | None = None
    branch_id: int | None = None
    salesperson_id: int | None = None
    contract_type: Literal["S", "U"] | None = None
    oid: Optional[OidStr] = None  # RAO-P2-058: Fakturownia OID (puste = użyj number)
    delivery_address: str | None = None
    postal_code: PostalCode | None = None
    city: CityName | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    date_from: date | None = None
    date_to: date | None = None
    # RAO-P1-021/P2-033: total_value usunięte
    prepayment_amount: Decimal | None = None
    prepayment_document: str | None = None
    invoice_amount: Decimal | None = None
    invoice_document: str | None = None
    notes: str | None = None
    contact_person1: str | None = None
    contact_phone1: str | None = None
    show_person1: bool | None = None
    contact_person2: str | None = None
    contact_phone2: str | None = None
    show_person2: bool | None = None
    email: str | None = None
    phone: str | None = None
    contractor_name: str | None = None
    working_days_per_week: int | None = None
    report_without_data: bool | None = None
    hide_delivery_address: bool | None = None
    signatures_on_page1: bool | None = None

    @model_validator(mode="after")
    def _validate_dates_and_amounts(self):
        # RAO-P1-039: same validation as ContractCreate (partial — only check set fields)
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Data rozpoczęcia (date_from) nie może być po dacie zakończenia (date_to).")
        for field in ("prepayment_amount", "invoice_amount"):
            v = getattr(self, field)
            if v is not None and v < 0:
                raise ValueError(f"{field} nie może być ujemne.")
        return self

