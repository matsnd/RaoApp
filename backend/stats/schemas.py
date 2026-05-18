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
