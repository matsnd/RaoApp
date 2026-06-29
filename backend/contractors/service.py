from datetime import datetime
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from contractors.models import Contractor, ContractorAddress
from contractors.schemas import ContractorCreate, AddressCreate
from shared.exceptions import conflict, not_found


class ContractorService:
    async def list_contractors(
        self, db: AsyncSession,
        search: str | None = None,
        supplier: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ):
        stmt = select(Contractor)
        if search:
            stmt = stmt.where(
                (Contractor.name.ilike(f"%{search}%")) |
                (Contractor.nip.ilike(f"%{search}%"))
            )
        if supplier is not None:
            stmt = stmt.where(Contractor.is_supplier == supplier)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Contractor.name).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        contractors = result.scalars().all()

        from contracts.models import Contract

        # RAO-P0-035: Batch-fetch active contract numbers to eliminate N+1
        contractor_ids = [c.id for c in contractors]
        active_map = {}
        if contractor_ids:
            today = datetime.utcnow().date()
            active_result = await db.execute(
                select(Contract.contractor_id, Contract.number)
                .where(Contract.contractor_id.in_(contractor_ids))
                .where(Contract.date_to >= today)
                .order_by(Contract.date_to.desc())
            )
            for cid, num in active_result.all():
                if cid not in active_map:
                    active_map[cid] = num

        items = []
        for c in contractors:
            active_num = active_map.get(c.id)

            from contractors.schemas import ContractorListItem
            items.append(ContractorListItem(
                id=c.id, name=c.name, name_short=c.name_short,
                nip=c.nip, city=c.city, street=c.street,
                is_supplier=c.is_supplier, phone1=c.phone1, email=c.email,
                active_contract_number=active_num,
                created_at=c.created_at, updated_at=c.updated_at,
            ))
        return items, total

    async def get_contractor(self, db: AsyncSession, contractor_id: int) -> Contractor:
        result = await db.execute(
            select(Contractor)
            .options(selectinload(Contractor.addresses))
            .where(Contractor.id == contractor_id)
        )
        contractor = result.scalar_one_or_none()
        if not contractor:
            raise not_found("Kontrahent")
        return contractor

    async def create_contractor(self, db: AsyncSession, data: ContractorCreate) -> Contractor:
        if data.nip:
            existing = await db.execute(
                select(Contractor).where(Contractor.nip == data.nip)
            )
            if existing.scalar_one_or_none():
                raise conflict("Kontrahent z tym NIP-em już istnieje")

        contractor = Contractor(
            **data.model_dump(),
            created_at=datetime.utcnow(),
        )
        db.add(contractor)
        await db.commit()
        return await self.get_contractor(db, contractor.id)

    async def update_contractor(
        self, db: AsyncSession, contractor_id: int, data: ContractorCreate
    ) -> Contractor:
        contractor = await self.get_contractor(db, contractor_id)
        if data.nip and data.nip != contractor.nip:
            existing = await db.execute(
                select(Contractor).where(
                    Contractor.nip == data.nip, Contractor.id != contractor_id
                )
            )
            if existing.scalar_one_or_none():
                raise conflict("Kontrahent z tym NIP-em już istnieje")

        for field, value in data.model_dump().items():
            setattr(contractor, field, value)
        contractor.updated_at = datetime.utcnow()
        await db.commit()
        return await self.get_contractor(db, contractor_id)

    async def delete_contractor(self, db: AsyncSession, contractor_id: int):
        from contracts.models import Contract
        from datetime import date
        active = await db.execute(
            select(func.count()).select_from(Contract)
            .where(Contract.contractor_id == contractor_id)
            .where(Contract.date_to >= date.today())
        )
        if active.scalar_one() > 0:
            raise conflict("Nie można usunąć — kontrahent ma aktywne umowy")
        contractor = await self.get_contractor(db, contractor_id)
        await db.delete(contractor)
        await db.commit()

    async def list_addresses(self, db: AsyncSession, contractor_id: int):
        result = await db.execute(
            select(ContractorAddress).where(ContractorAddress.contractor_id == contractor_id)
        )
        return result.scalars().all()

    async def create_address(
        self, db: AsyncSession, contractor_id: int, data: AddressCreate
    ) -> ContractorAddress:
        addr = ContractorAddress(
            **data.model_dump(),
            contractor_id=contractor_id,
            created_at=datetime.utcnow(),
        )
        db.add(addr)
        await db.commit()
        await db.refresh(addr)
        return addr

    async def update_address(
        self, db: AsyncSession, contractor_id: int, address_id: int, data: AddressCreate
    ) -> ContractorAddress:
        result = await db.execute(
            select(ContractorAddress).where(
                ContractorAddress.id == address_id,
                ContractorAddress.contractor_id == contractor_id,
            )
        )
        addr = result.scalar_one_or_none()
        if not addr:
            raise not_found("Adres")
        for field, value in data.model_dump().items():
            setattr(addr, field, value)
        await db.commit()
        await db.refresh(addr)
        return addr

    async def delete_address(self, db: AsyncSession, contractor_id: int, address_id: int):
        result = await db.execute(
            select(ContractorAddress).where(
                ContractorAddress.id == address_id,
                ContractorAddress.contractor_id == contractor_id,
            )
        )
        addr = result.scalar_one_or_none()
        if not addr:
            raise not_found("Adres")
        await db.delete(addr)
        await db.commit()


def validate_nip_checksum(nip: str) -> bool:
    """
    Validate Polish NIP (Tax Identification Number) checksum.

    Algorithm:
    1. Remove spaces and hyphens
    2. Check if it has exactly 10 digits
    3. Multiply digits by weights [6, 5, 7, 2, 3, 4, 5, 6, 7]
    4. Sum the results
    5. Sum modulo 11 should equal the last digit (if result is 10, use 0)

    Returns True if checksum is valid, False otherwise.
    """
    if not nip:
        return False

    # Remove spaces and hyphens
    nip_clean = nip.replace(" ", "").replace("-", "")

    # Check if it has exactly 10 digits
    if len(nip_clean) != 10 or not nip_clean.isdigit():
        return False

    # Weights for first 9 digits
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]

    # Calculate weighted sum
    total = sum(int(nip_clean[i]) * weights[i] for i in range(9))

    # Checksum: sum modulo 11 should equal last digit
    # Special case: if checksum is 10, it should be compared to 0
    checksum = total % 11
    expected_last_digit = 0 if checksum == 10 else checksum
    return expected_last_digit == int(nip_clean[9])


contractor_service = ContractorService()
