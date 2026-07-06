from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .models import ContractSettlement
from .schemas import ContractSettlementCreate, ContractSettlementUpdate, ContractSettlementResponse


class SettlementService:
    async def get_settlements_by_contract(self, db: AsyncSession, contract_id: int):
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(ContractSettlement)
            .options(selectinload(ContractSettlement.service_fee))
            .where(ContractSettlement.contract_id == contract_id)
            .order_by(ContractSettlement.id)
        )
        settlements = result.scalars().all()

        # RAO-P2-012: ręcznie mapuj na Pydantic response z service_fee_name
        # (property nie jest automatycznie serializowane przez Pydantic from_attributes)
        return [
            ContractSettlementResponse.model_validate({
                **{k: v for k, v in s.__dict__.items() if not k.startswith('_')},
                'service_fee_name': s.service_fee_name  # z property modelu
            })
            for s in settlements
        ]

    async def get_settlement(self, db: AsyncSession, settlement_id: int):
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(ContractSettlement)
            .options(selectinload(ContractSettlement.service_fee))
            .where(ContractSettlement.id == settlement_id)
        )
        return result.scalar_one_or_none()

    async def create_settlement(self, db: AsyncSession, data: ContractSettlementCreate):
        settlement = ContractSettlement(**data.model_dump())
        db.add(settlement)
        await db.commit()
        await db.refresh(settlement)
        return settlement

    async def update_settlement(
        self, db: AsyncSession, settlement_id: int, data: ContractSettlementUpdate
    ):
        result = await db.execute(
            select(ContractSettlement).where(ContractSettlement.id == settlement_id)
        )
        settlement = result.scalar_one_or_none()
        if not settlement:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(settlement, field, value)

        await db.commit()
        await db.refresh(settlement)
        return settlement

    async def delete_settlement(self, db: AsyncSession, settlement_id: int):
        result = await db.execute(
            select(ContractSettlement).where(ContractSettlement.id == settlement_id)
        )
        settlement = result.scalar_one_or_none()
        if not settlement:
            return False

        await db.delete(settlement)
        await db.commit()
        return True

    async def clear_settlements_by_contract(self, db: AsyncSession, contract_id: int) -> int:
        """P0-013: Usuń wszystkie rozliczenia dla umowy.

        Bulk DELETE (bez SELECT + pętli) — zwraca liczbę usuniętych rekordów.
        """
        result = await db.execute(
            delete(ContractSettlement).where(
                ContractSettlement.contract_id == contract_id
            )
        )
        await db.commit()
        return result.rowcount or 0

    async def auto_create_settlements_for_contract(
        self, db: AsyncSession, contract_id: int, position_ids: list[int]
    ):
        """
        RAO-P1-012: Auto-create settlement records for all contract positions.
        Called after contract creation.
        """
        for position_id in position_ids:
            existing = await db.execute(
                select(ContractSettlement).where(
                    ContractSettlement.contract_id == contract_id,
                    ContractSettlement.position_id == position_id,
                )
            )
            if not existing.scalar_one_or_none():
                settlement = ContractSettlement(
                    contract_id=contract_id,
                    position_id=position_id,
                    cost_client=None,
                    cost_company=None,
                    notes=None,
                )
                db.add(settlement)
        await db.commit()