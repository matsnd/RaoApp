from datetime import datetime
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from settings.models import Company, ServiceFeeTemplate, Salesperson, RateType, Branch
from settings.schemas import CompanyUpdate, ServiceFeeTemplateCreate, SalespersonCreate, CategoryCreate, BranchCreate, RateTypeCreate
from categories.models import Category
from shared.exceptions import not_found, conflict


class SettingsService:
    async def get_company(self, db: AsyncSession) -> Company:
        result = await db.execute(select(Company).where(Company.id == 1))
        company = result.scalar_one_or_none()
        if not company:
            company = Company(id=1, name="RAO")
            db.add(company)
            await db.commit()
            await db.refresh(company)
        return company

    async def update_company(self, db: AsyncSession, data: CompanyUpdate) -> Company:
        company = await self.get_company(db)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(company, field, value)
        await db.commit()
        await db.refresh(company)
        return company

    async def seed_fee_templates(self, db: AsyncSession, force: bool = False) -> int:
        if not force:
            existing = await db.execute(select(func.count()).select_from(ServiceFeeTemplate))
            if existing.scalar_one() > 0:
                return 0
        DEFAULT_FEES = [
            ("Transport",                                    400.00, 400.00,  "dostawa/odbiór", None),
            ("Czyszczenie (zabrudzenia drobne)",             150.00, 400.00,  None,              None),
            ("Czyszczenie (zabrudzenia trudnościeralne)",    400.00, 1500.00, None,              None),
            ("Usługa tankowania",                            200.00, None,    None,              "plus koszt paliwa"),
            ("Ponadnormatywny przestój transportu",          200.00, 300.00,  "h",               None),
            ("Nieuzasadnione wezwanie serwisowe",            280.00, None,    None,              "plus transport"),
        ]
        from decimal import Decimal
        count = 0
        for contract_type in ("S", "U"):
            for i, (name, amt_from, amt_to, unit, desc) in enumerate(DEFAULT_FEES):
                db.add(ServiceFeeTemplate(
                    company_id=1,
                    contract_type=contract_type,
                    sort_order=i,
                    name=name,
                    amount_from=Decimal(str(amt_from)) if amt_from else None,
                    amount_to=Decimal(str(amt_to)) if amt_to else None,
                    unit=unit,
                    description=desc,
                    is_active=True,
                ))
                count += 1
        await db.commit()
        return count

    async def list_fee_templates(self, db: AsyncSession):
        result = await db.execute(
            select(ServiceFeeTemplate)
            .order_by(ServiceFeeTemplate.contract_type, ServiceFeeTemplate.sort_order)
        )
        return result.scalars().all()

    async def create_fee_template(self, db: AsyncSession, data: ServiceFeeTemplateCreate) -> ServiceFeeTemplate:
        max_order = await db.execute(
            select(func.max(ServiceFeeTemplate.sort_order))
            .where(ServiceFeeTemplate.contract_type == data.contract_type)
        )
        next_order = (max_order.scalar_one_or_none() or 0) + 1
        t = ServiceFeeTemplate(**data.model_dump(), company_id=1, sort_order=next_order)
        db.add(t)
        await db.commit()
        await db.refresh(t)
        return t

    async def update_fee_template(self, db: AsyncSession, template_id: int, data: ServiceFeeTemplateCreate) -> ServiceFeeTemplate:
        result = await db.execute(select(ServiceFeeTemplate).where(ServiceFeeTemplate.id == template_id))
        t = result.scalar_one_or_none()
        if not t:
            raise not_found("Szablon")
        for field, value in data.model_dump().items():
            setattr(t, field, value)
        await db.commit()
        await db.refresh(t)
        return t

    async def delete_fee_template(self, db: AsyncSession, template_id: int):
        await db.execute(delete(ServiceFeeTemplate).where(ServiceFeeTemplate.id == template_id))
        await db.commit()

    async def reorder_fee_templates(self, db: AsyncSession, ids: list[int]):
        for i, tid in enumerate(ids):
            await db.execute(
                update(ServiceFeeTemplate).where(ServiceFeeTemplate.id == tid).values(sort_order=i)
            )
        await db.commit()

    async def list_salespeople(self, db: AsyncSession):
        result = await db.execute(select(Salesperson).order_by(Salesperson.name))
        return result.scalars().all()

    async def create_salesperson(self, db: AsyncSession, data: SalespersonCreate) -> Salesperson:
        sp = Salesperson(**data.model_dump())
        db.add(sp)
        await db.commit()
        await db.refresh(sp)
        return sp

    async def update_salesperson(self, db: AsyncSession, sp_id: int, data: SalespersonCreate) -> Salesperson:
        result = await db.execute(select(Salesperson).where(Salesperson.id == sp_id))
        sp = result.scalar_one_or_none()
        if not sp:
            raise not_found("Handlowiec")
        for field, value in data.model_dump().items():
            setattr(sp, field, value)
        await db.commit()
        await db.refresh(sp)
        return sp

    async def toggle_salesperson(self, db: AsyncSession, sp_id: int) -> Salesperson:
        result = await db.execute(select(Salesperson).where(Salesperson.id == sp_id))
        sp = result.scalar_one_or_none()
        if not sp:
            raise not_found("Handlowiec")
        sp.is_active = not sp.is_active
        await db.commit()
        await db.refresh(sp)
        return sp

    async def list_categories(self, db: AsyncSession):
        result = await db.execute(select(Category).order_by(Category.name))
        return result.scalars().all()

    async def create_category(self, db: AsyncSession, data: CategoryCreate) -> Category:
        cat = Category(**data.model_dump())
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return cat

    async def update_category(self, db: AsyncSession, cat_id: int, data: CategoryCreate) -> Category:
        result = await db.execute(select(Category).where(Category.id == cat_id))
        cat = result.scalar_one_or_none()
        if not cat:
            raise not_found("Kategoria")
        for field, value in data.model_dump().items():
            setattr(cat, field, value)
        await db.commit()
        await db.refresh(cat)
        return cat

    async def delete_category(self, db: AsyncSession, cat_id: int):
        result = await db.execute(select(Category).where(Category.id == cat_id))
        if not result.scalar_one_or_none():
            raise not_found("Kategoria")
        try:
            await db.execute(delete(Category).where(Category.id == cat_id))
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise conflict("Kategoria jest używana przez artykuły i nie może zostać usunięta")

    async def list_branches(self, db: AsyncSession):
        result = await db.execute(select(Branch).order_by(Branch.name))
        return result.scalars().all()

    async def create_branch(self, db: AsyncSession, data: BranchCreate) -> Branch:
        b = Branch(**data.model_dump(), created_at=datetime.utcnow().isoformat())
        db.add(b)
        await db.commit()
        await db.refresh(b)
        return b

    async def list_rate_types(self, db: AsyncSession):
        result = await db.execute(select(RateType).order_by(RateType.name))
        return result.scalars().all()

    async def create_rate_type(self, db: AsyncSession, data: RateTypeCreate) -> RateType:
        rt = RateType(**data.model_dump())
        db.add(rt)
        await db.commit()
        await db.refresh(rt)
        return rt

    async def update_rate_type(self, db: AsyncSession, rt_id: int, data: RateTypeCreate) -> RateType:
        result = await db.execute(select(RateType).where(RateType.id == rt_id))
        rt = result.scalar_one_or_none()
        if not rt:
            raise not_found("Typ stawki")
        for field, value in data.model_dump().items():
            setattr(rt, field, value)
        await db.commit()
        await db.refresh(rt)
        return rt

    async def delete_rate_type(self, db: AsyncSession, rt_id: int):
        result = await db.execute(select(RateType).where(RateType.id == rt_id))
        if not result.scalar_one_or_none():
            raise not_found("Typ stawki")
        try:
            await db.execute(delete(RateType).where(RateType.id == rt_id))
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise conflict("Typ stawki jest używany i nie może zostać usunięty")

    async def delete_salesperson(self, db: AsyncSession, sp_id: int):
        result = await db.execute(select(Salesperson).where(Salesperson.id == sp_id))
        if not result.scalar_one_or_none():
            raise not_found("Handlowiec")
        try:
            await db.execute(delete(Salesperson).where(Salesperson.id == sp_id))
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise conflict("Handlowiec jest przypisany do umów i nie może zostać usunięty")


settings_service = SettingsService()
