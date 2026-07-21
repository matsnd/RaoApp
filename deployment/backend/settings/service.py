from datetime import datetime
import re
import unicodedata
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload
from settings.models import (
    Company, FeePresetGroup, ServiceFeeTemplate, Salesperson, RateType, Branch,
    MachineRatePreset, MachineRatePresetItem,
)
from settings.schemas import (
    CompanyUpdate, FeePresetGroupCreate, ServiceFeeTemplateCreate, SalespersonCreate,
    CategoryCreate, BranchCreate, RateTypeCreate,
    MachineRatePresetCreate, MachineRatePresetUpdate,
    MachineRatePresetItemCreate, MachineRatePresetItemUpdate,
)
from categories.models import Category
from shared.exceptions import not_found, conflict


def _normalize_category_name(name: str) -> str:
    """RAO-P0-054: Normalizacja nazwy kategorii — trim + collapse whitespace.
    Zachowuje polskie znaki (DB ma utf8mb4_polish_ci), ale usuwa podwójne spacje
    i leading/trailing whitespace. Nie usuwa diakrytyków (to robi tylko migrate.py
    do porównania, nie do przechowywania).
    """
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip())


def _normalize_category_key(name: str) -> str:
    """RAO-P0-054: Klucz normalizacji do porównania (NFD + usuwanie Mn + ł→l + lower).
    Używane do wykrywania duplikatów (np. 'Koparki' vs 'koparki ' vs 'Koparki  ').
    """
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", name.strip())
    no_dia = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    no_dia = no_dia.replace("\u0142", "l").replace("\u0141", "L")
    return re.sub(r"\s+", " ", no_dia.lower()).strip()


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
            ("Transport",                                    400.00, 400.00,  None),
            ("Czyszczenie (zabrudzenia drobne)",             150.00, 400.00,  None),
            ("Czyszczenie (zabrudzenia trudnościeralne)",    400.00, 1500.00, None),
            ("Usługa tankowania",                            200.00, None,    "plus koszt paliwa"),
            ("Ponadnormatywny przestój transportu",          200.00, 300.00,  None),
            ("Nieuzasadnione wezwanie serwisowe",            280.00, None,    "plus transport"),
        ]
        from decimal import Decimal
        count = 0
        for contract_type in ("S", "U"):
            for i, (name, amt_from, amt_to, desc) in enumerate(DEFAULT_FEES):
                db.add(ServiceFeeTemplate(
                    company_id=1,
                    contract_type=contract_type,
                    sort_order=i,
                    name=name,
                    amount_from=Decimal(str(amt_from)) if amt_from else None,
                    amount_to=Decimal(str(amt_to)) if amt_to else None,
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
        payload = data.model_dump()
        # RAO-P1-011: jeśli wybrano usługę dodatkową, synchronizuj nazwę (snapshot do `name`)
        await self._resolve_additional_service_name(db, payload)
        t = ServiceFeeTemplate(**payload, company_id=1, sort_order=next_order)
        db.add(t)
        await db.commit()
        await db.refresh(t)
        return t

    async def _resolve_additional_service_name(self, db: AsyncSession, payload: dict) -> None:
        """RAO-P1-011: jeśli payload zawiera additional_service_id, ustaw `name` na additional_services.name."""
        additional_service_id = payload.get("additional_service_id")
        if not additional_service_id:
            return
        from additional_services.models import AdditionalService
        result = await db.execute(select(AdditionalService).where(AdditionalService.id == additional_service_id))
        art = result.scalar_one_or_none()
        if art is None:
            raise not_found("Usługa dodatkowa")
        # Snapshot nazwy usługi dodatkowej do `name` (zachowuje display name nawet po ON DELETE SET NULL)
        payload["name"] = art.name

    async def update_fee_template(self, db: AsyncSession, template_id: int, data: ServiceFeeTemplateCreate) -> ServiceFeeTemplate:
        result = await db.execute(select(ServiceFeeTemplate).where(ServiceFeeTemplate.id == template_id))
        t = result.scalar_one_or_none()
        if not t:
            raise not_found("Szablon")
        payload = data.model_dump()
        await self._resolve_additional_service_name(db, payload)
        for field, value in payload.items():
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

    async def list_fee_preset_groups(self, db: AsyncSession):
        result = await db.execute(
            select(FeePresetGroup)
            .options(selectinload(FeePresetGroup.templates))
            .order_by(FeePresetGroup.contract_type, FeePresetGroup.sort_order)
        )
        return result.scalars().all()

    async def get_fee_preset_group(self, db: AsyncSession, preset_id: int) -> FeePresetGroup:
        result = await db.execute(
            select(FeePresetGroup)
            .options(selectinload(FeePresetGroup.templates))
            .where(FeePresetGroup.id == preset_id)
        )
        grp = result.scalar_one_or_none()
        if not grp:
            raise not_found("Zestaw usług")
        return grp

    async def create_fee_preset_group(self, db: AsyncSession, data: FeePresetGroupCreate) -> FeePresetGroup:
        max_order = await db.execute(
            select(func.max(FeePresetGroup.sort_order))
            .where(FeePresetGroup.contract_type == data.contract_type)
        )
        next_order = (max_order.scalar_one_or_none() or 0) + 1
        grp = FeePresetGroup(**data.model_dump(), company_id=1, sort_order=next_order)
        db.add(grp)
        await db.commit()
        await db.refresh(grp)
        return await self.get_fee_preset_group(db, grp.id)

    async def update_fee_preset_group(self, db: AsyncSession, preset_id: int, data: FeePresetGroupCreate) -> FeePresetGroup:
        grp = await self.get_fee_preset_group(db, preset_id)
        for field, value in data.model_dump().items():
            setattr(grp, field, value)
        await db.commit()
        return await self.get_fee_preset_group(db, preset_id)

    async def delete_fee_preset_group(self, db: AsyncSession, preset_id: int):
        await db.execute(delete(FeePresetGroup).where(FeePresetGroup.id == preset_id))
        await db.commit()

    async def add_template_to_preset(self, db: AsyncSession, preset_id: int, data: ServiceFeeTemplateCreate) -> ServiceFeeTemplate:
        grp = await self.get_fee_preset_group(db, preset_id)
        max_order = await db.execute(
            select(func.max(ServiceFeeTemplate.sort_order)).where(ServiceFeeTemplate.preset_id == preset_id)
        )
        next_order = (max_order.scalar_one_or_none() or 0) + 1
        # RAO-P1-011: jeśli additional_service_id ustawiony, snapshot name z additional_services.name
        name = data.name
        if data.additional_service_id:
            from additional_services.models import AdditionalService
            art = (await db.execute(select(AdditionalService).where(AdditionalService.id == data.additional_service_id))).scalar_one_or_none()
            if art is None:
                raise not_found("Usługa dodatkowa")
            name = art.name
        t = ServiceFeeTemplate(
            company_id=1,
            preset_id=preset_id,
            contract_type=grp.contract_type,
            sort_order=next_order,
            additional_service_id=data.additional_service_id,
            name=name,
            amount_from=data.amount_from,
            amount_to=data.amount_to,
            description=data.description,
            is_active=data.is_active,
        )
        db.add(t)
        await db.commit()
        await db.refresh(t)
        return t

    async def update_preset_template(self, db: AsyncSession, template_id: int, data: ServiceFeeTemplateCreate) -> ServiceFeeTemplate:
        result = await db.execute(select(ServiceFeeTemplate).where(ServiceFeeTemplate.id == template_id))
        t = result.scalar_one_or_none()
        if not t:
            raise not_found("Szablon")
        # RAO-P1-011: jeśli additional_service_id ustawiony, snapshot name z additional_services.name
        new_name = data.name
        if data.additional_service_id:
            from additional_services.models import AdditionalService
            art = (await db.execute(select(AdditionalService).where(AdditionalService.id == data.additional_service_id))).scalar_one_or_none()
            if art is None:
                raise not_found("Usługa dodatkowa")
            new_name = art.name
        t.additional_service_id = data.additional_service_id
        t.name = new_name
        for field in ("amount_from", "amount_to", "description", "is_active"):
            setattr(t, field, getattr(data, field))
        await db.commit()
        await db.refresh(t)
        return t

    async def delete_preset_template(self, db: AsyncSession, template_id: int):
        await db.execute(delete(ServiceFeeTemplate).where(ServiceFeeTemplate.id == template_id))
        await db.commit()

    async def reorder_preset_templates(self, db: AsyncSession, preset_id: int, order_list) -> None:
        """RAO-P3-001: aktualizuje sort_order dla szablonów danego presetu."""
        for item in order_list:
            await db.execute(
                update(ServiceFeeTemplate)
                .where(ServiceFeeTemplate.id == item.id, ServiceFeeTemplate.preset_id == preset_id)
                .values(sort_order=item.sort_order)
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

    async def list_categories_tree(self, db: AsyncSession):
        """Zwraca kategorie główne z zagnieżdżonymi children (do 3 poziomów)."""
        result = await db.execute(
            select(Category)
            .where(Category.parent_id == None)
            .options(
                selectinload(Category.children)
                .selectinload(Category.children)
                .selectinload(Category.children)
            )
            .order_by(Category.name)
        )
        return result.scalars().all()

    async def create_category(self, db: AsyncSession, data: CategoryCreate) -> Category:
        # RAO-P0-054: Normalizacja nazwy + wykrywanie duplikatów (case/diakrytyki-insensitive)
        payload = data.model_dump()
        payload["name"] = _normalize_category_name(payload.get("name", ""))
        if not payload["name"]:
            raise conflict("Nazwa kategorii nie może być pusta")
        # Sprawdź duplikat w tej samej hierarchii (parent_id) po znormalizowanej nazwie
        new_key = _normalize_category_key(payload["name"])
        existing = await db.execute(
            select(Category).where(Category.parent_id == payload.get("parent_id"))
        )
        for cat in existing.scalars().all():
            if _normalize_category_key(cat.name) == new_key:
                raise conflict(f"Kategoria '{cat.name}' już istnieje w tej hierarchii")
        cat = Category(**payload)
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return cat

    async def update_category(self, db: AsyncSession, cat_id: int, data: CategoryCreate) -> Category:
        result = await db.execute(select(Category).where(Category.id == cat_id))
        cat = result.scalar_one_or_none()
        if not cat:
            raise not_found("Kategoria")
        # RAO-P0-054: Normalizacja nazwy + wykrywanie duplikatów
        payload = data.model_dump()
        payload["name"] = _normalize_category_name(payload.get("name", ""))
        if not payload["name"]:
            raise conflict("Nazwa kategorii nie może być pusta")
        new_key = _normalize_category_key(payload["name"])
        new_parent = payload.get("parent_id")
        dup_check = await db.execute(
            select(Category).where(
                Category.parent_id == new_parent,
                Category.id != cat_id,
            )
        )
        for other in dup_check.scalars().all():
            if _normalize_category_key(other.name) == new_key:
                raise conflict(f"Kategoria '{other.name}' już istnieje w tej hierarchii")
        for field, value in payload.items():
            setattr(cat, field, value)
        await db.commit()
        await db.refresh(cat)
        return cat

    async def delete_category(self, db: AsyncSession, cat_id: int):
        result = await db.execute(select(Category).where(Category.id == cat_id))
        cat = result.scalar_one_or_none()
        if not cat:
            raise not_found("Kategoria")
        # Sprawdź czy ma podkategorie
        children_result = await db.execute(
            select(Category.id).where(Category.parent_id == cat_id).limit(1)
        )
        if children_result.scalar_one_or_none() is not None:
            raise conflict("Kategoria ma podkategorie — usuń je najpierw")
        try:
            await db.execute(delete(Category).where(Category.id == cat_id))
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise conflict("Kategoria jest używana przez artykuły i nie może zostać usunięta")

    async def list_branches(self, db: AsyncSession):
        result = await db.execute(select(Branch).order_by(Branch.id))
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

    # ------------------------------------------------------------------
    # RAO-P1-001: Predefiniowane cenniki warunków rozliczenia maszyn
    # ------------------------------------------------------------------

    async def list_machine_rate_presets(self, db: AsyncSession, machine_id: int) -> list[MachineRatePreset]:
        result = await db.execute(
            select(MachineRatePreset)
            .options(selectinload(MachineRatePreset.items))
            .where(MachineRatePreset.machine_id == machine_id)
            .order_by(MachineRatePreset.sort_order, MachineRatePreset.id)
        )
        return list(result.scalars().all())

    async def get_machine_rate_preset(self, db: AsyncSession, preset_id: int) -> MachineRatePreset:
        result = await db.execute(
            select(MachineRatePreset)
            .options(selectinload(MachineRatePreset.items))
            .where(MachineRatePreset.id == preset_id)
        )
        preset = result.scalar_one_or_none()
        if not preset:
            raise not_found("Cennik")
        return preset

    async def create_machine_rate_preset(
        self, db: AsyncSession, machine_id: int, data: MachineRatePresetCreate
    ) -> MachineRatePreset:
        # Walidacja FK: maszyna musi istnieć
        from machines.models import Machine
        art = await db.get(Machine, machine_id)
        if art is None:
            raise not_found("Maszyna")

        max_order = await db.execute(
            select(func.max(MachineRatePreset.sort_order))
            .where(MachineRatePreset.machine_id == machine_id)
        )
        next_order = (max_order.scalar_one_or_none() or 0) + 1

        preset = MachineRatePreset(
            company_id=1,
            machine_id=machine_id,
            name=data.name,
            description=data.description,
            is_default=False,  # ustawione niżej jeśli data.is_default
            sort_order=next_order,
            updated_at=datetime.utcnow(),
        )
        db.add(preset)
        await db.flush()  # potrzebne preset.id dla items

        for i, item in enumerate(data.items):
            db.add(MachineRatePresetItem(
                preset_id=preset.id,
                sort_order=i,
                rate_type_id=item.rate_type_id,
                description=item.description,
                rate1=item.rate1,
                rate2=item.rate2,
                billing_label=item.billing_label,
                period_count=item.period_count,
                minimum=item.minimum,
            ))

        if data.is_default:
            # unset innych presetów tej maszyny, ustaw ten
            await db.execute(
                update(MachineRatePreset)
                .where(MachineRatePreset.machine_id == machine_id, MachineRatePreset.id != preset.id)
                .values(is_default=False)
            )
            preset.is_default = True

        await db.commit()
        return await self.get_machine_rate_preset(db, preset.id)

    async def update_machine_rate_preset(
        self, db: AsyncSession, preset_id: int, data: MachineRatePresetUpdate
    ) -> MachineRatePreset:
        preset = await self.get_machine_rate_preset(db, preset_id)
        update_data = data.model_dump(exclude_unset=True)
        new_is_default = update_data.pop("is_default", None)
        for field, value in update_data.items():
            setattr(preset, field, value)
        preset.updated_at = datetime.utcnow()

        if new_is_default is True:
            await db.execute(
                update(MachineRatePreset)
                .where(MachineRatePreset.machine_id == preset.machine_id, MachineRatePreset.id != preset_id)
                .values(is_default=False)
            )
            preset.is_default = True
        elif new_is_default is False:
            preset.is_default = False

        await db.commit()
        return await self.get_machine_rate_preset(db, preset_id)

    async def delete_machine_rate_preset(self, db: AsyncSession, preset_id: int) -> None:
        preset = await self.get_machine_rate_preset(db, preset_id)
        await db.execute(delete(MachineRatePreset).where(MachineRatePreset.id == preset_id))
        await db.commit()

    async def set_default_preset(self, db: AsyncSession, preset_id: int) -> MachineRatePreset:
        """Atomowo ustawia dany preset jako domyślny dla swojej maszyny.

        1. UPDATE machine_rate_presets SET is_default=0 WHERE machine_id=:mid AND id<>:pid
        2. UPDATE machine_rate_presets SET is_default=1 WHERE id=:pid
        """
        preset = await self.get_machine_rate_preset(db, preset_id)
        await db.execute(
            update(MachineRatePreset)
            .where(MachineRatePreset.machine_id == preset.machine_id, MachineRatePreset.id != preset_id)
            .values(is_default=False)
        )
        await db.execute(
            update(MachineRatePreset)
            .where(MachineRatePreset.id == preset_id)
            .values(is_default=True, updated_at=datetime.utcnow())
        )
        await db.commit()
        return await self.get_machine_rate_preset(db, preset_id)

    async def get_default_preset(self, db: AsyncSession, machine_id: int) -> MachineRatePreset | None:
        result = await db.execute(
            select(MachineRatePreset)
            .options(selectinload(MachineRatePreset.items))
            .where(MachineRatePreset.machine_id == machine_id, MachineRatePreset.is_default == True)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def add_preset_item(
        self, db: AsyncSession, preset_id: int, data: MachineRatePresetItemCreate
    ) -> MachineRatePresetItem:
        preset = await self.get_machine_rate_preset(db, preset_id)
        max_order = await db.execute(
            select(func.max(MachineRatePresetItem.sort_order))
            .where(MachineRatePresetItem.preset_id == preset_id)
        )
        next_order = (max_order.scalar_one_or_none() or 0) + 1
        item = MachineRatePresetItem(
            preset_id=preset_id,
            sort_order=next_order,
            rate_type_id=data.rate_type_id,
            description=data.description,
            rate1=data.rate1,
            rate2=data.rate2,
            billing_label=data.billing_label,
            period_count=data.period_count,
            minimum=data.minimum,
        )
        db.add(item)
        # bump updated_at na presercie
        preset.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(item)
        return item

    async def update_preset_item(
        self, db: AsyncSession, item_id: int, data: MachineRatePresetItemUpdate
    ) -> MachineRatePresetItem:
        result = await db.execute(
            select(MachineRatePresetItem).where(MachineRatePresetItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise not_found("Warunek cennika")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        # bump updated_at na presercie
        preset_result = await db.execute(
            select(MachineRatePreset).where(MachineRatePreset.id == item.preset_id)
        )
        preset = preset_result.scalar_one_or_none()
        if preset:
            preset.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(item)
        return item

    async def delete_preset_item(self, db: AsyncSession, item_id: int) -> None:
        result = await db.execute(
            select(MachineRatePresetItem).where(MachineRatePresetItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise not_found("Warunek cennika")
        preset_id = item.preset_id
        await db.execute(delete(MachineRatePresetItem).where(MachineRatePresetItem.id == item_id))
        # bump updated_at na presercie
        preset_result = await db.execute(
            select(MachineRatePreset).where(MachineRatePreset.id == preset_id)
        )
        preset = preset_result.scalar_one_or_none()
        if preset:
            preset.updated_at = datetime.utcnow()
        await db.commit()


settings_service = SettingsService()
