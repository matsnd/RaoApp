from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from contracts.schemas import (
    ConditionCreate, ConditionResponse, ContractCreate, ContractDetail,
    ContractListItem, ContractServiceFeeCreate, ContractServiceFeeReorder,
    ContractServiceFeeResponse, PositionCreate, PositionResponse,
)
from contracts.service import contract_service
from database import get_db
from shared.pagination import PaginatedResponse


async def _cond_response(db, cond):
    from settings.models import RateType
    rt_name = None
    if cond.rate_type_id:
        rt = await db.get(RateType, cond.rate_type_id)
        rt_name = rt.name if rt else None
    return ConditionResponse(
        id=cond.id, position_id=cond.position_id,
        rate_type_id=cond.rate_type_id, rate_type_name=rt_name,
        description=cond.description, rate1=cond.rate1, rate2=cond.rate2,
        billing_label=cond.billing_label, period_count=cond.period_count,
        minimum=cond.minimum,
    )

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=PaginatedResponse[ContractListItem])
async def list_contracts(
    search: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    contract_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await contract_service.list_contracts(db, search, date_from, date_to, contract_type, page, per_page)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = await contract_service.get_contract(db, contract_id)
    return ContractDetail.model_validate(c)


@router.post("", response_model=ContractDetail, status_code=201)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = await contract_service.create_contract(db, data)
    return ContractDetail.model_validate(c)


@router.put("/{contract_id}", response_model=ContractDetail)
async def update_contract(
    contract_id: int,
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = await contract_service.update_contract(db, contract_id, data)
    return ContractDetail.model_validate(c)


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await contract_service.delete_contract(db, contract_id)


@router.get("/{contract_id}/positions", response_model=list[PositionResponse])
async def list_positions(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await contract_service.list_positions(db, contract_id)


@router.post("/{contract_id}/positions", response_model=PositionResponse, status_code=201)
async def create_position(
    contract_id: int,
    data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pos = await contract_service.create_position(db, contract_id, data)
    from contracts.schemas import PositionResponse as PR
    return PR(
        id=pos.id, contract_id=pos.contract_id, article_id=pos.article_id,
        article_name=pos.article_name, rental_type=pos.rental_type,
        description=pos.description, rental_days=pos.rental_days,
        quantity=pos.quantity, unit_price=pos.unit_price, costs=pos.costs,
        rate_type_id=pos.rate_type_id, rate_type_name=None,
        billing_frequency=pos.billing_frequency, billing_unit=pos.billing_unit,
        supplier_id=pos.supplier_id, supplier_name=None,
        delivery_date=pos.delivery_date, conditions_count=0, conditions=[],
    )


@router.put("/{contract_id}/positions/{pos_id}", response_model=PositionResponse)
async def update_position(
    contract_id: int,
    pos_id: int,
    data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pos = await contract_service.update_position(db, pos_id, data)
    from contracts.schemas import PositionResponse as PR
    return PR(
        id=pos.id, contract_id=pos.contract_id, article_id=pos.article_id,
        article_name=pos.article_name, rental_type=pos.rental_type,
        description=pos.description, rental_days=pos.rental_days,
        quantity=pos.quantity, unit_price=pos.unit_price, costs=pos.costs,
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
    _: User = Depends(get_current_user),
):
    await contract_service.delete_position(db, contract_id, pos_id)


@router.get("/{contract_id}/positions/{pos_id}/conditions", response_model=list[ConditionResponse])
async def list_conditions(
    contract_id: int,
    pos_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from settings.models import RateType
    conds = await contract_service.list_conditions(db, pos_id)
    result = []
    for c in conds:
        rt_name = None
        if c.rate_type_id:
            rt = await db.get(RateType, c.rate_type_id)
            rt_name = rt.name if rt else None
        result.append(ConditionResponse(
            id=c.id, position_id=c.position_id,
            rate_type_id=c.rate_type_id, rate_type_name=rt_name,
            description=c.description, rate1=c.rate1, rate2=c.rate2,
            billing_label=c.billing_label, period_count=c.period_count,
            minimum=c.minimum,
        ))
    return result


@router.post("/{contract_id}/positions/{pos_id}/conditions", response_model=ConditionResponse, status_code=201)
async def create_condition(
    contract_id: int,
    pos_id: int,
    data: ConditionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cond = await contract_service.create_condition(db, pos_id, data)
    return await _cond_response(db, cond)


@router.put("/{contract_id}/positions/{pos_id}/conditions/{cond_id}", response_model=ConditionResponse)
async def update_condition(
    contract_id: int,
    pos_id: int,
    cond_id: int,
    data: ConditionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cond = await contract_service.update_condition(db, cond_id, data)
    return await _cond_response(db, cond)


@router.delete("/{contract_id}/positions/{pos_id}/conditions/{cond_id}", status_code=204)
async def delete_condition(
    contract_id: int,
    pos_id: int,
    cond_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await contract_service.delete_condition(db, cond_id)


@router.get("/{contract_id}/service-fees", response_model=list[ContractServiceFeeResponse])
async def list_service_fees(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    fees = await contract_service.list_service_fees(db, contract_id)
    return [ContractServiceFeeResponse.model_validate(f) for f in fees]


@router.post("/{contract_id}/service-fees", response_model=ContractServiceFeeResponse, status_code=201)
async def create_service_fee(
    contract_id: int,
    data: ContractServiceFeeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    fee = await contract_service.create_service_fee(db, contract_id, data)
    return ContractServiceFeeResponse.model_validate(fee)


@router.put("/{contract_id}/service-fees/{fee_id}", response_model=ContractServiceFeeResponse)
async def update_service_fee(
    contract_id: int,
    fee_id: int,
    data: ContractServiceFeeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    fee = await contract_service.update_service_fee(db, fee_id, data)
    return ContractServiceFeeResponse.model_validate(fee)


@router.delete("/{contract_id}/service-fees/{fee_id}", status_code=204)
async def delete_service_fee(
    contract_id: int,
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await contract_service.delete_service_fee(db, fee_id)


@router.post("/{contract_id}/service-fees/reorder", status_code=200)
async def reorder_service_fees(
    contract_id: int,
    data: ContractServiceFeeReorder,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await contract_service.reorder_service_fees(db, contract_id, data.ids)
    return {"message": "Kolejność zaktualizowana"}


@router.post("/{contract_id}/service-fees/reset", status_code=200)
async def reset_service_fees(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await contract_service.reset_service_fees(db, contract_id)
    return {"message": "Usługi zresetowane do szablonu"}


@router.post("/{contract_id}/recalculate", status_code=200)
async def recalculate_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total = await contract_service.recalculate_total(db, contract_id)
    return {"total_value": total}
