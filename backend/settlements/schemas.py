from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


class ContractSettlementResponse(BaseModel):
    id: int
    contract_id: int
    position_id: Optional[int] = None
    service_fee_id: Optional[int] = None  # RAO-P2-012
    service_fee_name: Optional[str] = None  # RAO-P2-012: nazwa usługi dodatkowej dla UI
    cost_client: Optional[Decimal] = None
    cost_company: Optional[Decimal] = None
    margin: Optional[Decimal] = None
    notes: Optional[str] = None
    # RAO Faza 2a (opcja E): pola unmapped settlements z Fakturownia
    article_name_snapshot: Optional[str] = None
    fakturownia_product_id: Optional[int] = None
    fakturownia_invoice_number: Optional[str] = None
    source: Optional[str] = None
    settled_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractSettlementCreate(BaseModel):
    contract_id: int
    position_id: Optional[int] = None
    service_fee_id: Optional[int] = None  # RAO-P2-012
    cost_client: Optional[Decimal] = Field(None, ge=0)
    cost_company: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=2000)


class ContractSettlementUpdate(BaseModel):
    cost_client: Optional[Decimal] = Field(None, ge=0)
    cost_company: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=2000)