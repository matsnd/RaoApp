import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from articles.models import Article
from auth.models import User
from config import settings
from contracts.models import Contract

from .client import FakturowniaClient
from .crypto import decrypt_token, encrypt_token, mask_token
from .models import FakturowniaSettings
from .schemas import (
    FakturowniaProductOut,
    FakturowniaSettingsIn,
    InvoiceOut,
    RaoArticleRef,
    ResolvedInvoiceLine,
    ResolvedInvoiceOut,
)

logger = logging.getLogger(__name__)


async def get_settings(db: AsyncSession) -> Optional[FakturowniaSettings]:
    result = await db.execute(
        select(FakturowniaSettings).where(FakturowniaSettings.id == 1)
    )
    return result.scalar_one_or_none()


async def get_or_create_settings(db: AsyncSession) -> FakturowniaSettings:
    obj = await get_settings(db)
    if obj is None:
        obj = FakturowniaSettings(id=1, enabled=False)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
    return obj


async def update_settings(
    db: AsyncSession,
    payload: FakturowniaSettingsIn,
    user: User,
) -> FakturowniaSettings:
    obj = await get_or_create_settings(db)
    obj.enabled = payload.enabled

    if payload.domain_subdomain is not None:
        obj.domain_subdomain = payload.domain_subdomain

    if payload.api_token is not None:
        enc_key = settings.RAO_FAKTUROWNIA_ENC_KEY
        if not enc_key:
            raise HTTPException(
                status_code=500,
                detail="Brak klucza szyfrujacego RAO_FAKTUROWNIA_ENC_KEY na serwerze",
            )
        try:
            obj.api_token_ciphertext = encrypt_token(payload.api_token, enc_key)
        except Exception as exc:
            logger.error("Fakturownia token encryption failed: %s", type(exc).__name__)
            raise HTTPException(status_code=500, detail="Blad szyfrowania tokenu")
        obj.api_token_preview = mask_token(payload.api_token)
        obj.api_token_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        obj.api_token_updated_by = user.id

    await db.commit()
    await db.refresh(obj)
    return obj


def _build_client(obj: FakturowniaSettings) -> FakturowniaClient:
    if not obj.enabled:
        raise HTTPException(status_code=503, detail="Integracja Fakturownia jest wylaczona")
    if not obj.domain_subdomain:
        raise HTTPException(status_code=503, detail="Brak konfiguracji domeny Fakturownia")
    if not obj.api_token_ciphertext:
        raise HTTPException(status_code=503, detail="Brak tokenu API Fakturownia")

    enc_key = settings.RAO_FAKTUROWNIA_ENC_KEY
    if not enc_key:
        raise HTTPException(status_code=500, detail="Brak klucza szyfrujacego RAO_FAKTUROWNIA_ENC_KEY")

    try:
        api_token = decrypt_token(obj.api_token_ciphertext, enc_key)
    except ValueError:
        raise HTTPException(status_code=500, detail="Blad deszyfrowania tokenu Fakturownia")

    try:
        return FakturowniaClient(domain_subdomain=obj.domain_subdomain, api_token=api_token)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


async def fetch_products(db: AsyncSession) -> List[FakturowniaProductOut]:
    obj = await get_or_create_settings(db)
    client = _build_client(obj)
    return await client.get_products()


async def fetch_invoices_for_contract(
    db: AsyncSession,
    contract_id: int,
    user: User,
) -> List[ResolvedInvoiceOut]:
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=404, detail="Umowa nie znaleziona")

    if user.role != "admin" and user.branch_id is not None:
        if contract.branch_id != user.branch_id:
            raise HTTPException(status_code=403, detail="Brak dostepu do tej umowy")

    oid = contract.oid
    if not oid:
        raise HTTPException(status_code=422, detail="Umowa nie posiada numeru OID (zamówienia Fakturownia)")

    obj = await get_or_create_settings(db)
    client = _build_client(obj)

    raw_invoices: List[InvoiceOut] = await client.get_invoices_by_oid(oid)
    resolved: List[ResolvedInvoiceOut] = []
    for invoice in raw_invoices:
        resolved.append(await _resolve_invoice(db, invoice))
    return resolved


async def _resolve_invoice(db: AsyncSession, invoice: InvoiceOut) -> ResolvedInvoiceOut:
    product_ids = {
        line.fakturownia_product_id
        for line in invoice.lines
        if line.fakturownia_product_id
    }

    pid_to_articles: dict = {}
    if product_ids:
        art_rows = await db.execute(
            select(Article.id, Article.name, Article.fakturownia_product_id)
            .where(Article.fakturownia_product_id.in_(product_ids))
        )
        for row in art_rows.all():
            pid = int(row.fakturownia_product_id)
            pid_to_articles.setdefault(pid, []).append(
                RaoArticleRef(id=row.id, name=row.name)
            )

    resolved_lines: List[ResolvedInvoiceLine] = []
    mapped_total = Decimal("0.00")
    unmapped_count = 0

    for line in invoice.lines:
        pid = line.fakturownia_product_id
        rao_articles = pid_to_articles.get(pid, [])

        resolved_lines.append(
            ResolvedInvoiceLine(
                fakturownia_product_id=pid,
                fakturownia_product_name=line.fakturownia_product_name,
                quantity=line.quantity,
                price_net=line.price_net,
                total_net=line.total_net,
                invoice_number=line.invoice_number or invoice.invoice_number,
                rao_articles=rao_articles,
            )
        )

        if rao_articles:
            mapped_total += line.total_net * len(rao_articles)
        else:
            unmapped_count += 1

    return ResolvedInvoiceOut(
        invoice_number=invoice.invoice_number,
        lines=resolved_lines,
        total_net=invoice.total_net,
        mapped_total_net=mapped_total,
        unmapped_count=unmapped_count,
    )
