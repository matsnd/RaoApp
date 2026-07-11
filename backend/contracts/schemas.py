from datetime import datetime, date, time
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

SafeName = Annotated[str, Field(
    min_length=1,
    max_length=200,
    pattern=r"^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 \-\_\(\)\[\]\.\,\!\?\:\/\\&\+\=%$#@\'\"]+$",
)]

SafeDescription = Annotated[str | None, Field(
    max_length=400,
    pattern=r"^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 \-\_\(\)\[\]\.\,\!\?\:\/\\&\+\=%$#@\'\"\n\r\t\*\;\(\)]+$",
)]


class ConditionResponse(BaseModel):
    id: int
    position_id: int
    rate1: Decimal | None
    rate2: Decimal | None
    billing_label: str | None
    period_count: int | None  # RAO-P1-005: backward compatibility
    period_from: int | None  # RAO-P1-005: elastyczne widełki (od)
    period_to: int | None    # RAO-P1-005: elastyczne widełki (do)
    is_flat_rate: bool = True  # P1-101: ryczałt (kwota całkowita) vs stawka (per jednostka)

    class Config:
        from_attributes = True


class ConditionCreate(BaseModel):
    rate1: Decimal | None = Field(None, ge=0, decimal_places=2)
    rate2: Decimal | None = Field(None, ge=0, decimal_places=2)
    billing_label: SafeName | None = None
    period_count: int | None = Field(None, ge=0)  # RAO-P1-005: backward compatibility
    period_from: int | None = Field(None, ge=0)  # RAO-P1-005: elastyczne widełki (od)
    period_to: int | None = Field(None, ge=0)    # RAO-P1-005: elastyczne widełki (do)
    is_flat_rate: bool = True  # P1-101: ryczałt=TRUE (kwota całkowita), stawka=FALSE (per jednostka)

    @model_validator(mode='after')
    def check_condition(self):
        # Przynajmniej jedna stawka ustawiona
        if not (self.rate1 is not None or self.rate2 is not None):
            raise ValueError("Przynajmniej jedna stawka (rate1 lub rate2) jest wymagana.")
        if self.rate1 is not None and self.rate2 is not None:
            if self.rate1 == 0 and self.rate2 == 0:
                raise ValueError("Przynajmniej jedna stawka musi być większa od zera.")
        # RAO-P1-005: backward compatibility — period_count maps to 1..period_count
        if self.period_count is not None and self.period_from is None and self.period_to is None:
            self.period_from = 1
            self.period_to = self.period_count
        # period_to >= period_from (allow single-day: pf=1, pt=1 = "1 dzień")
        if self.period_from is not None and self.period_to is not None and self.period_to < self.period_from:
            raise ValueError("period_to musi być większe lub równe period_from.")
        return self


class ConditionUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied."""
    rate1: Decimal | None = Field(None, ge=0, decimal_places=2)
    rate2: Decimal | None = Field(None, ge=0, decimal_places=2)
    billing_label: SafeName | None = None
    period_count: int | None = Field(None, ge=0)  # RAO-P1-005: backward compatibility
    period_from: int | None = Field(None, ge=0)  # RAO-P1-005: elastyczne widełki (od)
    period_to: int | None = Field(None, ge=0)    # RAO-P1-005: elastyczne widełki (do)
    is_flat_rate: bool | None = None  # P1-101: ryczałt=TRUE, stawka=FALSE

    @model_validator(mode='after')
    def check_condition(self):
        # Przynajmniej jedna stawka ustawiona wśród przesłanych wartości
        if self.rate1 is not None or self.rate2 is not None:
            if self.rate1 == 0 and self.rate2 == 0:
                raise ValueError("Przynajmniej jedna stawka musi być większa od zera.")
        # RAO-P1-005: backward compatibility — period_count maps to 1..period_count
        if self.period_count is not None and self.period_from is None and self.period_to is None:
            self.period_from = 1
            self.period_to = self.period_count
        if self.period_from is not None and self.period_to is not None and self.period_to < self.period_from:
            raise ValueError("period_to musi być większe lub równe period_from.")
        return self


class PositionResponse(BaseModel):
    id: int
    contract_id: int
    machine_id: int | None = None
    service_id: int | None = None
    article_name: str | None
    description: str | None
    rental_days: int | None
    quantity: int | None
    unit_price: Decimal | None
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
    machine_id: int | None = None
    service_id: int | None = None
    description: SafeDescription = None
    rental_days: int | None = Field(None, ge=0)
    quantity: int = Field(1, ge=1)
    unit_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    rate_type_id: int | None = None
    billing_frequency: str | None = None
    billing_unit: str | None = None
    supplier_id: int | None = None
    delivery_date: date | None = None

    @model_validator(mode='after')
    def validate_xor(self) -> "PositionCreate":
        if (self.machine_id is None) == (self.service_id is None):
            raise ValueError("Dokładnie jeden z machine_id / service_id musi być ustawiony.")
        return self


class PositionUpdate(BaseModel):
    """Partial update — only fields explicitly sent are applied.
    XOR invariant (machine_id XOR service_id) validated in service layer
    on the final state after applying partial fields."""
    machine_id: int | None = None
    service_id: int | None = None
    description: SafeDescription = None
    rental_days: int | None = Field(None, ge=0)
    quantity: int | None = Field(None, ge=1)
    unit_price: Decimal | None = Field(None, ge=0, decimal_places=2)
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
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ContractServiceFeeCreate(BaseModel):
    name: SafeName
    amount_from: Decimal | None = Field(None, ge=0, decimal_places=2)
    amount_to: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: SafeDescription = None
    is_active: bool = True

    @model_validator(mode='after')
    def check_and_fill_description(self):
        if self.amount_from is not None and self.amount_to is not None:
            if self.amount_to < self.amount_from:
                raise ValueError("amount_to nie może być mniejsze od amount_from.")
        # RAO-P1-100: KISS — "Tekst na umowie" zawsze wypełniony (fallback do nazwy)
        if not self.description or not self.description.strip():
            self.description = self.name
        return self


class ContractServiceFeeUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied."""
    name: SafeName | None = None
    amount_from: Decimal | None = Field(None, ge=0, decimal_places=2)
    amount_to: Decimal | None = Field(None, ge=0, decimal_places=2)
    description: SafeDescription = None
    is_active: bool | None = None

    @model_validator(mode='after')
    def check_amounts(self):
        if self.amount_from is not None and self.amount_to is not None:
            if self.amount_to < self.amount_from:
                raise ValueError("amount_to nie może być mniejsze od amount_from.")
        return self


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
    # RAO: pre-selekcja zestawu opłat — sugestia na podstawie power_type
    # pierwszej pozycji (diesel/electric). NIGDY auto-apply — operator wybiera.
    suggested_preset: str | None = None
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
    delivery_address: str | None = Field(None, max_length=255)
    postal_code: PostalCode | None = None
    city: CityName | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    date_from: date | None = None
    date_to: date | None = None
    # RAO-P1-021/P2-033: total_value usunięte
    prepayment_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    prepayment_document: str | None = Field(None, max_length=200)
    notes: SafeDescription = None
    contact_person1: SafeName | None = None
    contact_phone1: str | None = Field(None, max_length=100)
    show_person1: bool = True
    contact_person2: SafeName | None = None
    contact_phone2: str | None = Field(None, max_length=100)
    show_person2: bool = True
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=100)
    contractor_name: SafeName | None = None
    working_days_per_week: int = Field(6, ge=1, le=7)
    report_without_data: bool = False
    hide_delivery_address: bool = False
    signatures_on_page1: bool = False

    @model_validator(mode="after")
    def _validate_dates_and_amounts(self):
        # RAO-QA-002: date_from required — without it, downstream code crashes with 500
        if not self.date_from:
            raise ValueError("Data rozpoczęcia (date_from) jest wymagana.")
        # RAO-P1-039: date_from must not be after date_to
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Data rozpoczęcia (date_from) nie może być po dacie zakończenia (date_to).")
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
    delivery_address: str | None = Field(None, max_length=255)
    postal_code: PostalCode | None = None
    city: CityName | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    date_from: date | None = None
    date_to: date | None = None
    # RAO-P1-021/P2-033: total_value usunięte
    prepayment_amount: Decimal | None = Field(None, ge=0, decimal_places=2)
    prepayment_document: str | None = Field(None, max_length=200)
    notes: SafeDescription = None
    contact_person1: SafeName | None = None
    contact_phone1: str | None = Field(None, max_length=100)
    show_person1: bool | None = None
    contact_person2: SafeName | None = None
    contact_phone2: str | None = Field(None, max_length=100)
    show_person2: bool | None = None
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=100)
    contractor_name: SafeName | None = None
    working_days_per_week: int | None = Field(None, ge=1, le=7)
    report_without_data: bool | None = None
    hide_delivery_address: bool | None = None
    signatures_on_page1: bool | None = None

    @model_validator(mode="after")
    def _validate_dates_and_amounts(self):
        # RAO-P1-039: same validation as ContractCreate (partial — only check set fields)
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Data rozpoczęcia (date_from) nie może być po dacie zakończenia (date_to).")
        return self


class ServiceHourResponse(BaseModel):
    id: int
    position_id: int
    service_date: date
    time_from: time | None
    time_to: time | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ServiceHourCreate(BaseModel):
    service_date: date
    time_from: time | None = None
    time_to: time | None = None
    notes: str | None = Field(None, max_length=500)


class ServiceHourUpdate(BaseModel):
    service_date: date | None = None
    time_from: time | None = None
    time_to: time | None = None
    notes: str | None = Field(None, max_length=500)
