from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
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