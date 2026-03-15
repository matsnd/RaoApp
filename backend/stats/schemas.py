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
