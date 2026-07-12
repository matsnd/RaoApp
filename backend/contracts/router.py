from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from contracts.schemas import (
    ConditionCreate, ConditionResponse, ConditionUpdate, ContractCreate, ContractDetail,
    ContractListItem, ContractServiceFeeCreate, ContractServiceFeeUpdate,
    ContractServiceFeeReorder, ContractServiceFeeResponse, ContractUpdate, PositionCreate,
    PositionResponse, PositionUpdate,
    SettleContractRequest,
)
from contracts.service import contract_service
from database import get_db
from shared.pagination import PaginatedResponse


async def _cond_response(db, cond):
    return ConditionResponse(
        id=cond.id, position_id=cond.position_id,
        rate1=cond.rate1, rate2=cond.rate2,
        billing_label=cond.billing_label, period_count=cond.period_count,
        period_from=cond.period_from, period_to=cond.period_to,  # RAO-P1-005
    )

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=PaginatedResponse[ContractListItem])
async def list_contracts(
    search: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    contract_type: str | None = Query(None, pattern="^[SU]$"),
    is_settled: bool | None = Query(None, description="None=wszystkie, false=aktywne, true=rozliczone"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = await contract_service.list_contracts(
        db, user, search, date_from, date_to, contract_type, is_settled, page, per_page
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/overdue", response_model=PaginatedResponse[ContractListItem])
async def list_overdue_contracts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista przeterminowanych (zamkniętych) umów - date_to < dzisiaj i is_settled = false"""
    items, total = await contract_service.list_overdue_contracts(db, user, page, per_page)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = await contract_service.verify_contract_access(db, contract_id, user)
    detail = ContractDetail.model_validate(c)
    detail.suggested_preset = await contract_service.suggest_preset(db, c.id)
    return detail


@router.post("", response_model=ContractDetail, status_code=201)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = await contract_service.create_contract(db, data, user)
    detail = ContractDetail.model_validate(c)
    detail.suggested_preset = await contract_service.suggest_preset(db, c.id)
    return detail


@router.put("/{contract_id}", response_model=ContractDetail)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = await contract_service.update_contract(db, contract_id, data, user)
    return ContractDetail.model_validate(c)


@router.patch("/{contract_id}/settle", response_model=ContractDetail)
async def settle_contract(
    contract_id: int,
    data: SettleContractRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """RAO-P2-022: oznacz umowę jako rozliczoną lub cofnij rozliczenie."""
    c = await contract_service.settle_contract(db, contract_id, data.is_settled, user)
    return ContractDetail.model_validate(c)


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await contract_service.delete_contract(db, contract_id, user)


@router.get("/{contract_id}/positions", response_model=list[PositionResponse])
async def list_positions(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await contract_service.list_positions(db, contract_id, user)


@router.post("/{contract_id}/positions", response_model=PositionResponse, status_code=201)
async def create_position(
    contract_id: int,
    data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pos = await contract_service.create_position(db, contract_id, data, user)
    from contracts.schemas import PositionResponse as PR
    return PR(
        id=pos.id, contract_id=pos.contract_id, machine_id=pos.machine_id,
        service_id=pos.service_id,
        article_name=pos.article_name,
        description=pos.description, rental_days=pos.rental_days,
        quantity=pos.quantity, unit_price=pos.unit_price,
        rate_type_id=pos.rate_type_id, rate_type_name=None,
        billing_frequency=pos.billing_frequency, billing_unit=pos.billing_unit,
        supplier_id=pos.supplier_id, supplier_name=None,
        delivery_date=pos.delivery_date, conditions_count=0, conditions=[],
    )


@router.put("/{contract_id}/positions/{pos_id}", response_model=PositionResponse)
async def update_position(
    contract_id: int,
    pos_id: int,
    data: PositionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pos = await contract_service.update_position(db, pos_id, data, user)
    from contracts.schemas import PositionResponse as PR
    return PR(
        id=pos.id, contract_id=pos.contract_id, machine_id=pos.machine_id,
        service_id=pos.service_id,
        article_name=pos.article_name,
        description=pos.description, rental_days=pos.rental_days,
        quantity=pos.quantity, unit_price=pos.unit_price,
        rate_type_id=pos.rate_type_id, rate_type_name=None,
        billing_frequency=pos.billing_frequency, billing_unit=pos.billing_unit,
        supplier_id=pos.supplier_id, supplier_name=None,
        delivery_date=pos.delivery_date, conditions_count=0, conditions=[],
    )


@router.delete("/{contract_id}/positions/{pos_id}", status_code=204)
async def delete_position(
    contract_id: int,
    pos_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await contract_service.delete_position(db, contract_id, pos_id, user)


@router.get("/{contract_id}/positions/{pos_id}/conditions", response_model=list[ConditionResponse])
async def list_conditions(
    contract_id: int,
    pos_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conds = await contract_service.list_conditions(db, pos_id, user)
    return [
        ConditionResponse(
            id=c.id, position_id=c.position_id,
            rate1=c.rate1, rate2=c.rate2,
            billing_label=c.billing_label, period_count=c.period_count,
            period_from=c.period_from, period_to=c.period_to,  # RAO-P1-005
        )
        for c in conds
    ]


@router.post("/{contract_id}/positions/{pos_id}/conditions", response_model=ConditionResponse, status_code=201)
async def create_condition(
    contract_id: int,
    pos_id: int,
    data: ConditionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        cond = await contract_service.create_condition(db, pos_id, data, user)
        return await _cond_response(db, cond)
    except Exception as e:
        # IntegrityError (FK constraint) — nie crashuj serwera, zwróć 422
        if 'IntegrityError' in type(e).__name__ or 'foreign key' in str(e).lower():
            await db.rollback()
            raise HTTPException(
                status_code=422,
                detail="Nieprawidłowy billing_label lub inny błąd FK.",
            )
        raise


@router.put("/{contract_id}/positions/{pos_id}/conditions/{cond_id}", response_model=ConditionResponse)
async def update_condition(
    contract_id: int,
    pos_id: int,
    cond_id: int,
    data: ConditionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cond = await contract_service.update_condition(db, cond_id, data, user)
    return await _cond_response(db, cond)


@router.delete("/{contract_id}/positions/{pos_id}/conditions/{cond_id}", status_code=204)
async def delete_condition(
    contract_id: int,
    pos_id: int,
    cond_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await contract_service.delete_condition(db, cond_id, user)


@router.get("/{contract_id}/service-fees", response_model=list[ContractServiceFeeResponse])
async def list_service_fees(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fees = await contract_service.list_service_fees(db, contract_id, user)
    return [ContractServiceFeeResponse.model_validate(f) for f in fees]


@router.post("/{contract_id}/service-fees", response_model=ContractServiceFeeResponse, status_code=201)
async def create_service_fee(
    contract_id: int,
    data: ContractServiceFeeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fee = await contract_service.create_service_fee(db, contract_id, data, user)
    return ContractServiceFeeResponse.model_validate(fee)


@router.put("/{contract_id}/service-fees/{fee_id}", response_model=ContractServiceFeeResponse)
async def update_service_fee(
    contract_id: int,
    fee_id: int,
    data: ContractServiceFeeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fee = await contract_service.update_service_fee(db, fee_id, data, user)
    return ContractServiceFeeResponse.model_validate(fee)


@router.delete("/{contract_id}/service-fees/{fee_id}", status_code=204)
async def delete_service_fee(
    contract_id: int,
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await contract_service.delete_service_fee(db, fee_id, user)


@router.post("/{contract_id}/service-fees/reorder", status_code=200)
async def reorder_service_fees(
    contract_id: int,
    data: ContractServiceFeeReorder,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await contract_service.reorder_service_fees(db, contract_id, data.ids, user)
    return {"message": "Kolejność zaktualizowana"}


@router.post("/{contract_id}/service-fees/reset", status_code=200)
async def reset_service_fees(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await contract_service.reset_service_fees(db, contract_id, user)
    return {"message": "Usługi zresetowane do szablonu"}


@router.post("/{contract_id}/service-fees/apply-preset", status_code=200)
async def apply_fee_preset(
    contract_id: int,
    preset_id: int = Query(...),
    replace: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await contract_service.verify_contract_access(db, contract_id, user, allow_mutation=True)
    from contracts.service import apply_preset_to_contract
    await apply_preset_to_contract(db, contract_id, preset_id, replace)
    return {"message": "Zestaw zastosowany"}


@router.post("/{contract_id}/recalculate", status_code=200)
async def recalculate_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total = await contract_service.recalculate_total(db, contract_id, user)
    return {"total_value": total}


# ----------------------------------------------------------------------
# RAO-P1-001: Apply predefiniowany cennik do pozycji umowy (snapshot)
# ----------------------------------------------------------------------

class ApplyRatePresetRequest(BaseModel):
    preset_id: int
    replace: bool = True


class ApplyRatePresetResponse(BaseModel):
    applied_count: int
    conditions: list[ConditionResponse]


@router.post(
    "/{contract_id}/positions/{pos_id}/conditions/apply-preset",
    response_model=ApplyRatePresetResponse,
    status_code=200,
)
async def apply_rate_preset_to_position(
    contract_id: int,
    pos_id: int,
    data: ApplyRatePresetRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Kopiuje warunki z cennika (MachineRatePreset) do PositionCondition jako snapshot."""
    conds = await contract_service.apply_rate_preset_to_position(
        db, pos_id, data.preset_id, user, data.replace
    )
    resp_conds = [await _cond_response(db, c) for c in conds]
    return ApplyRatePresetResponse(applied_count=len(resp_conds), conditions=resp_conds)
