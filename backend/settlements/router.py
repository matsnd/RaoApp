from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.dependencies import get_current_user
from .schemas import (
    ContractSettlementResponse,
    ContractSettlementCreate,
    ContractSettlementUpdate,
)
from .service import SettlementService

router = APIRouter(prefix="/settlements", tags=["settlements"])
service = SettlementService()


@router.get("/contract/{contract_id}", response_model=list[ContractSettlementResponse])
async def get_contract_settlements(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Pobierz wszystkie rozliczenia dla umowy."""
    return await service.get_settlements_by_contract(db, contract_id)


@router.get("/{settlement_id}", response_model=ContractSettlementResponse)
async def get_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Pobierz pojedyncze rozliczenie."""
    settlement = await service.get_settlement(db, settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Rozliczenie nie znalezione")
    return settlement


@router.post("", response_model=ContractSettlementResponse)
async def create_settlement(
    data: ContractSettlementCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Utwórz nowe rozliczenie."""
    return await service.create_settlement(db, data)


@router.put("/{settlement_id}", response_model=ContractSettlementResponse)
async def update_settlement(
    settlement_id: int,
    data: ContractSettlementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Zaktualizuj rozliczenie."""
    settlement = await service.update_settlement(db, settlement_id, data)
    if not settlement:
        raise HTTPException(status_code=404, detail="Rozliczenie nie znalezione")
    return settlement


@router.delete("/{settlement_id}")
async def delete_settlement(
    settlement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Usuń rozliczenie."""
    deleted = await service.delete_settlement(db, settlement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rozliczenie nie znalezione")
    return {"message": "Rozliczenie usunięte"}