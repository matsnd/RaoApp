from pydantic import BaseModel
from decimal import Decimal
from datetime import date


class FleetSummary(BaseModel):
    total_rented: int
    total_machines: int
    utilization_pct: float
    period_revenue: Decimal
    top_machine_name: str | None
    top_machine_revenue: Decimal | None
    contracts_in_period: int
    # RAO-P2-032: breakdown po źródłach przychodu (actual/estimate_lookup/estimate_tiered)
    revenue_actual: Decimal | None = None
    revenue_estimate: Decimal | None = None
    revenue_source_label: str | None = None  # "rzeczywiste" | "szacunek" | "mieszane"


class TopMachineItem(BaseModel):
    article_id: int
    name: str
    internal_number: str | None
    revenue: Decimal
    rented_days: int
    contracts_count: int


class CurrentlyRentedItem(BaseModel):
    article_id: int
    name: str
    internal_number: str | None
    category_main: str | None   # RAO-P1-017: kategoria główna maszyny
    contract_number: str
    contractor_name: str | None
    return_date: date | None


class CurrentlyRentedResponse(BaseModel):
    total_rented: int
    total_machines: int
    utilization_pct: float
    items: list[CurrentlyRentedItem]


class MachineRoiResponse(BaseModel):
    article_id: int
    name: str
    internal_number: str | None
    category_main: str | None   # RAO-P1-017: kategoria główna maszyny
    replacement_value: Decimal | None
    total_rented_days: int
    estimated_revenue: Decimal
    contracts_count: int
    roi_pct: float | None


class ServiceFeeItem(BaseModel):
    article_id: int
    service_name: str
    total_revenue: Decimal
    times_billed: int


class AdditionalFeesResponse(BaseModel):
    date_from: date
    date_to: date
    total_services_revenue: Decimal
    breakdown: list[ServiceFeeItem]


class LocationStatItem(BaseModel):
    city: str
    postal_code: str | None = None  # RAO-P2-028: grupowanie po PNA
    gmina: str | None = None        # RAO-P2-028: rollup z postal_codes (LEFT JOIN)
    powiat: str | None = None       # RAO-P2-028: rollup z postal_codes (LEFT JOIN)
    wojewodztwo: str | None = None  # RAO-P2-028: rollup z postal_codes (LEFT JOIN)
    rentals_count: int
    total_revenue: Decimal


class ExpiringContractItem(BaseModel):
    id: int
    number: str
    contractor_name: str | None
    date_from: date | None
    date_to: date | None
    days_left: int
    delivery_address: str | None
    contact_person1: str | None
    contact_phone1: str | None
    salesperson_name: str | None


class OverdueContractItem(BaseModel):
    id: int
    number: str
    contractor_name: str | None
    date_from: date | None
    date_to: date | None
    days_overdue: int
    delivery_address: str | None
    contact_person1: str | None
    contact_phone1: str | None


class DeliveryTodayItem(BaseModel):
    contract_id: int
    contract_number: str
    contractor_name: str | None
    article_name: str | None
    delivery_date: date | None
    delivery_address: str | None
    contact_person1: str | None
    contact_phone1: str | None


class UnprintedContractItem(BaseModel):
    id: int
    number: str
    contractor_name: str | None
    date_from: date | None
    date_to: date | None
    created_at: str | None


class StalePrintContractItem(BaseModel):
    id: int
    number: str
    contractor_name: str | None
    date_from: date | None
    date_to: date | None
    print_date: str | None
    updated_at: str | None


class SalespersonCommissionItem(BaseModel):
    salesperson_id: int
    salesperson_name: str
    commission_rate: Decimal | None
    contracts_count: int
    total_revenue: Decimal
    commission_amount: Decimal


class CommissionReportResponse(BaseModel):
    date_from: date
    date_to: date
    items: list[SalespersonCommissionItem]
    grand_total_revenue: Decimal
    grand_total_commission: Decimal


# ── RAO-P1-017: Statystyki po kategoriach ─────────────────────────────────────

class CategoryStatItem(BaseModel):
    """Statystyki wynajmu zagregowane dla jednej kategorii."""
    category_name: str
    articles_count: int     # ile unikalnych maszyn wynajętych w okresie
    rented_days: int        # suma dni wynajmu (z zakresu dat)
    revenue: Decimal        # suma przychodu z kategorii
    contracts_count: int    # ile unikalnych umów


class CategoryStatsResponse(BaseModel):
    """Odpowiedź endpointu GET /stats/by-category."""
    date_from: date
    date_to: date
    level: str              # "main" | "sub1"
    total_revenue: Decimal
    items: list[CategoryStatItem]


# ── RAO-P2-010: Statystyki pozycji z filtrem typu ────────────────────────────────

class PositionStatItem(BaseModel):
    """Jedna pozycja zagregowana per article w okresie [date_from, date_to]."""
    article_id: int
    article_name: str
    internal_number: str | None
    is_service: bool                  # ← klucz filtra type
    category_main: str | None         # spójność z RAO-P1-017
    revenue: Decimal
    rented_days: int                  # 0 dla usług o billing_frequency != "DAILY"
    contracts_count: int
    times_billed: int                 # liczba pozycji = ile razy wystąpiła w umowach


class PositionStatsResponse(BaseModel):
    """Odpowiedź endpointu GET /stats/positions."""
    date_from: date
    date_to: date
    type: str                         # "machines" | "services" | "all"
    total_revenue: Decimal
    total_machines_revenue: Decimal   # podsumowanie per typ (zawsze, niezależnie od filtra)
    total_services_revenue: Decimal   # ↑ pozwala FE pokazać "Z czego usługi: X zł"
    items: list[PositionStatItem]


# ── RAO-P1-026: Statystyki po okresach i lista kategorii ─────────────────────

class ByPeriodItem(BaseModel):
    """Wiersz agregatu per (period, category_name) — RAO-P1-026."""
    period: str             # "2024-03" (month) lub "2024" (year)
    category_name: str      # "__all__" gdy bez filtra kategorii
    revenue: Decimal
    contracts_count: int
    rented_days: int


class ByPeriodResponse(BaseModel):
    """Odpowiedź endpointu GET /stats/by-period — RAO-P1-026."""
    date_from: date
    date_to: date
    granularity: str        # "month" | "year"
    items: list[ByPeriodItem]


class CategoriesListNode(BaseModel):
    """Węzeł drzewa kategorii z liczbą artykułów — RAO-P1-026."""
    id: int
    name: str
    level: str
    articles_count: int = 0
    children: list["CategoriesListNode"] = []

    model_config = {"from_attributes": True}


CategoriesListNode.model_rebuild()
