"""
RAO-P2-058 / RAO-P1-100: seed syntetycznych produktów Fakturownia do lokalnego cache.

Uruchamiany PO migrate.py. Wypełnia:
- fakturownia_settings (enabled=True, token z .env zaszyfrowany)
- fakturownia_products_cache (produkty odpowiadające artykułom RAO)

Nie wysyła danych do prawdziwego API Fakturownia — dane są lokalne,
umożliwiające testy endpointu /integrations/fakturownia/products/search
oraz mapowania artykuł ↔ fakturownia_product_id.

Użycie:
    cd backend && .venv\Scripts\python seed_fakturownia_synthetic.py
"""
import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, Base
from config import settings as app_settings

# Import modeli — ładują metadane
import auth.models  # noqa
import contractors.models  # noqa
import machines.models  # noqa
import services.models  # noqa
import additional_services.models  # noqa
import contracts.models  # noqa
import settings.models  # noqa
import categories.models  # noqa
import settlements.models  # noqa
import archive.models  # noqa
import audit.models  # noqa
import contract_costs.models  # noqa
import deliveries.models  # noqa
import reservations.models  # noqa
import integrations.fakturownia.models  # noqa
import integrations.models  # noqa

from machines.models import Machine
from integrations.fakturownia.crypto import encrypt_token, mask_token
from integrations.fakturownia.models import FakturowniaProductCache, FakturowniaSettings
from integrations.fakturownia.schemas import FakturowniaProductOut


# Syntetyczny katalog produktów FA odwzorowujący artykuły RAO.
# product_id to 13-cyfrowe ID zgodnie z konwencją użytą w seed_demo_data.py.
SYNTHETIC_PRODUCTS = [
    FakturowniaProductOut(id=8845156432567, name="Koparka kołowa 15t z łyżką", code="KOP001", price_net=Decimal("450.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156432568, name="Koparka kołowa 20t z łyżką", code="KOP002", price_net=Decimal("520.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156436442, name="Ładowarka teleskopowa 17m", code="LAD001", price_net=Decimal("380.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156436443, name="Podnośnik nożycowy 16m", code="POD001", price_net=Decimal("300.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156436444, name="Spycharka gąsienicowa", code="SPY001", price_net=Decimal("600.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156436446, name="Zagęszczarka wibracyjna", code="ZAG001", price_net=Decimal("120.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156432587, name="Transport maszyny", code="TRA001", price_net=Decimal("250.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="49.41.12.0"),
    FakturowniaProductOut(id=8845156432589, name="Czyszczenie maszyny myjką ciśnieniową", code="CZY001", price_net=Decimal("180.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="45.20.11.0"),
    FakturowniaProductOut(id=8845156436448, name="Czyszczenie maszyny ręczne", code="CZY002", price_net=Decimal("120.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="45.20.11.0"),
    FakturowniaProductOut(id=8845156432620, name="Tankowanie ON do pełna", code="TAN001", price_net=Decimal("6.50"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="25.50.21.0"),
    FakturowniaProductOut(id=8845156436449, name="Deklarowany przestój", code="PZT001", price_net=Decimal("350.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156436450, name="Serwis maszyny", code="SER001", price_net=Decimal("300.00"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
    FakturowniaProductOut(id=8845156436451, name="Praca operatora (niezmapowana)", code="OPR001", price_net=Decimal("650.41"), currency="PLN", tax="23", gtu_code="GTU_01", pkwiu="43.99.20.0"),
]


async def seed_fakturownia_settings(db: AsyncSession) -> FakturowniaSettings:
    """Wstawia / aktualizuje wiersz fakturownia_settings z danymi z .env."""
    token = (
        os.environ.get("FA_TOKEN")
        or os.environ.get("FAKTUROWNIA_API_TOKEN")
        or app_settings.RAO_FAKTUROWNIA_API_TOKEN
        or ""
    )
    domain = os.environ.get("FA_DOMAIN") or app_settings.RAO_FAKTUROWNIA_DOMAIN_SUBDOMAIN or "matsnd"

    if not token:
        print("  WARN: brak tokenu Fakturownia w env — używam dummy tokenu (niedziała z FA API, ale wystarczy do cache).")
        token = "DEMO_FAKTUROWNIA_TOKEN_NOT_FOR_API"

    # Szukamy istniejącego wiersza
    result = await db.execute(select(FakturowniaSettings).limit(1))
    obj = result.scalars().first()

    ciphertext = encrypt_token(token)
    preview = mask_token(token)

    if obj is None:
        obj = FakturowniaSettings(
            id=1,
            enabled=True,
            api_token_ciphertext=ciphertext,
            api_token_preview=preview,
            domain_subdomain=domain,
            api_token_updated_at=datetime.utcnow(),
            api_token_updated_by=1,
        )
        db.add(obj)
    else:
        obj.enabled = True
        obj.api_token_ciphertext = ciphertext
        obj.api_token_preview = preview
        obj.domain_subdomain = domain
        obj.api_token_updated_at = datetime.utcnow()
        obj.api_token_updated_by = 1

    await db.commit()
    await db.refresh(obj)
    print(f"  FA settings: enabled={obj.enabled}, domain={obj.domain_subdomain}, token_preview={obj.api_token_preview}")
    return obj


async def seed_fakturownia_products(db: AsyncSession) -> int:
    """Upsertuje syntetyczne produkty do fakturownia_products_cache."""
    count = 0
    for p in SYNTHETIC_PRODUCTS:
        result = await db.execute(
            select(FakturowniaProductCache).where(FakturowniaProductCache.product_id == p.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.code = p.code
            existing.name = p.name
            existing.price_net = p.price_net
            existing.currency = p.currency or "PLN"
            existing.tax_rate = p.tax
            existing.gtu_code = p.gtu_code
            existing.pkwiu = p.pkwiu
            existing.synced_at = datetime.utcnow()
        else:
            db.add(FakturowniaProductCache(
                product_id=p.id,
                code=p.code,
                name=p.name,
                price_net=p.price_net,
                currency=p.currency or "PLN",
                tax_rate=p.tax,
                gtu_code=p.gtu_code,
                pkwiu=p.pkwiu,
                synced_at=datetime.utcnow(),
            ))
        count += 1

    await db.commit()
    print(f"  FA products cache: {count} products")
    return count


async def link_machines_to_fa_products(db: AsyncSession) -> int:
    """Mapuje maszyny RAO na syntetyczne produkty FA po kluczowych słowach w nazwie."""
    mapping = [
        ("kopark", 8845156432567),
        ("ładowark", 8845156436442),
        ("podnośnik", 8845156436443),
        ("spychark", 8845156436444),
        ("zagęszczark", 8845156436446),
        ("transport", 8845156432587),
        ("czyszcz", 8845156432589),
        ("tank", 8845156432620),
        ("przestój", 8845156436449),
        ("serwis", 8845156436450),
        ("operator", 8845156436451),
    ]
    linked = 0
    result = await db.execute(select(Machine.id, Machine.name))
    rows = result.all()

    from sqlalchemy import text
    for mach_id, name in rows:
        matched_fa_id = None
        for keyword, fa_id in mapping:
            if keyword in (name or "").lower():
                matched_fa_id = fa_id
                break
        if matched_fa_id:
            await db.execute(
                text("UPDATE machines SET fakturownia_product_id = :fa_id WHERE id = :mach_id"),
                {"fa_id": matched_fa_id, "mach_id": mach_id},
            )
            linked += 1

    await db.commit()
    print(f"  Linked {linked} machines to FA products")
    return linked


async def main():
    print("Seeding syntetycznych danych Fakturownia...")
    async with AsyncSessionLocal() as db:
        await seed_fakturownia_settings(db)
        await seed_fakturownia_products(db)
        await link_machines_to_fa_products(db)
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
