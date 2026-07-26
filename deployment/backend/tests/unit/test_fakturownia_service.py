"""Unit tests for backend/integrations/fakturownia/service._resolve_invoice — RAO-P2-012 QA.

Tests 1:N entity mapping semantics (RAO articles split: machines / services / additional_services):
- 1 FA product → 1 RAO machine  (normal case)
- 1 FA product → N RAO machines (each RAO machine gets full line.total_net; mapped_total = total_net × N)
- 1 FA product → 0 RAO entities (unmapped — counted, contributes 0 to mapped_total)
- Mixed mapping across machines, services, and additional_services
"""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from integrations.fakturownia.schemas import InvoiceLine, InvoiceOut
from integrations.fakturownia.service import _resolve_invoice


def _make_db(machine_rows=None, service_rows=None, additional_service_rows=None, cache_rows=None):
    """Build a mock AsyncSession whose execute() returns rows iterable via .all().

    RAO articles split: _resolve_invoice now makes 4 DB calls when product_ids exist:
    1st → machine rows (id, name, fakturownia_product_id)
    2nd → service rows (id, name, fakturownia_product_id)
    3rd → additional_service rows (id, name, fakturownia_product_id)
    4th → cache rows (product_id, name) from fakturownia_products_cache
    Uses side_effect to return them in order.
    """
    db = MagicMock()
    mach_result = MagicMock()
    mach_result.all.return_value = machine_rows or []
    svc_result = MagicMock()
    svc_result.all.return_value = service_rows or []
    addsvc_result = MagicMock()
    addsvc_result.all.return_value = additional_service_rows or []
    cache_result = MagicMock()
    cache_result.all.return_value = cache_rows or []
    db.execute = AsyncMock(side_effect=[mach_result, svc_result, addsvc_result, cache_result])
    return db


def _row(entity_id: int, name: str, fakturownia_product_id: int):
    """Mimic a SQLAlchemy Row with named attribute access."""
    return SimpleNamespace(
        id=entity_id,
        name=name,
        fakturownia_product_id=fakturownia_product_id,
    )


def _cache_row(product_id: int, name: str):
    """Mimic a SQLAlchemy Row from fakturownia_products_cache (product_id, name)."""
    return SimpleNamespace(product_id=product_id, name=name)


def _line(pid: int, name: str = "Mlotowiertarka", total_net: str = "1000.00"):
    return InvoiceLine(
        fakturownia_product_id=pid,
        fakturownia_product_name=name,
        quantity=Decimal("1"),
        price_net=Decimal(total_net),
        total_net=Decimal(total_net),
        invoice_number="FV/1/2025",
    )


# ── 1:1 mapping (machine) ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_1to1_mapping():
    """1 FA product (id=100) → 1 RAO machine (id=42)."""
    db = _make_db(machine_rows=[_row(42, "Mlotowiertarka Hilti", 100)])

    invoice = InvoiceOut(
        invoice_number="FV/1/2025",
        lines=[_line(100)],
        total_net=Decimal("1000.00"),
    )

    out = await _resolve_invoice(db, invoice)

    assert out.invoice_number == "FV/1/2025"
    assert len(out.lines) == 1
    assert len(out.lines[0].rao_machines) == 1
    assert out.lines[0].rao_machines[0].id == 42
    assert out.lines[0].rao_machines[0].name == "Mlotowiertarka Hilti"
    assert out.unmapped_count == 0
    # 1000 × 1 machine = 1000
    assert out.mapped_total_net == Decimal("1000.00")


# ── 1:N mapping (machines) ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_1toN_mapping():
    """1 FA product (id=100) → 3 RAO machines → mapped_total = total_net × 3 (per spec)."""
    db = _make_db([
        _row(42, "Mlotowiertarka A", 100),
        _row(43, "Mlotowiertarka B", 100),
        _row(44, "Mlotowiertarka C", 100),
    ])

    invoice = InvoiceOut(
        invoice_number="FV/1/2025",
        lines=[_line(100, total_net="1000.00")],
        total_net=Decimal("1000.00"),
    )

    out = await _resolve_invoice(db, invoice)

    assert len(out.lines[0].rao_machines) == 3
    machine_ids = {m.id for m in out.lines[0].rao_machines}
    assert machine_ids == {42, 43, 44}
    assert out.unmapped_count == 0
    # Per spec: line gets full total_net × N mapped machines
    assert out.mapped_total_net == Decimal("3000.00")


# ── 1:0 mapping (unmapped) ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_zero_mapping():
    """1 FA product (id=999) → 0 RAO entities → unmapped_count=1, mapped_total=0."""
    db = _make_db()  # no matching entities

    invoice = InvoiceOut(
        invoice_number="FV/1/2025",
        lines=[_line(999, name="Nieznany produkt", total_net="500.00")],
        total_net=Decimal("500.00"),
    )

    out = await _resolve_invoice(db, invoice)

    assert len(out.lines) == 1
    assert out.lines[0].rao_machines == []
    assert out.lines[0].rao_services == []
    assert out.lines[0].rao_additional_services == []
    assert out.lines[0].fakturownia_product_id == 999
    assert out.lines[0].fakturownia_product_name == "Nieznany produkt"
    assert out.unmapped_count == 1
    assert out.mapped_total_net == Decimal("0.00")
    # Total_net of invoice is untouched
    assert out.total_net == Decimal("500.00")


# ── Mixed: some mapped, some unmapped ────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_mixed_mapping():
    """Mix of 1:1, 1:N, 1:0 in single invoice."""
    db = _make_db([
        _row(10, "Art A", 100),  # 1:1 → product 100
        _row(20, "Art B1", 200), # 1:N → product 200
        _row(21, "Art B2", 200),
        # product 300 has zero matches
    ])

    invoice = InvoiceOut(
        invoice_number="FV/2/2025",
        lines=[
            _line(100, total_net="100.00"),
            _line(200, total_net="200.00"),
            _line(300, total_net="50.00"),
        ],
        total_net=Decimal("350.00"),
    )

    out = await _resolve_invoice(db, invoice)

    assert len(out.lines) == 3
    assert len(out.lines[0].rao_machines) == 1  # 1:1
    assert len(out.lines[1].rao_machines) == 2  # 1:N
    assert len(out.lines[2].rao_machines) == 0  # unmapped
    assert out.unmapped_count == 1
    # 100*1 + 200*2 + 50*0 = 500
    assert out.mapped_total_net == Decimal("500.00")


# ── Cross-entity mapping: machines + services + additional_services ──────────

@pytest.mark.asyncio
async def test_resolve_invoice_cross_entity_mapping():
    """1 FA product (id=100) → 1 machine + 1 service + 1 additional_service → mapped_total = total_net × 3."""
    db = _make_db(
        machine_rows=[_row(1, "Koparka", 100)],
        service_rows=[_row(2, "Transport", 100)],
        additional_service_rows=[_row(3, "Ubezpieczenie", 100)],
    )

    invoice = InvoiceOut(
        invoice_number="FV/7/2025",
        lines=[_line(100, total_net="500.00")],
        total_net=Decimal("500.00"),
    )

    out = await _resolve_invoice(db, invoice)

    assert len(out.lines[0].rao_machines) == 1
    assert len(out.lines[0].rao_services) == 1
    assert len(out.lines[0].rao_additional_services) == 1
    assert out.unmapped_count == 0
    # 500 × 3 entities = 1500
    assert out.mapped_total_net == Decimal("1500.00")


# ── Empty invoice ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_no_lines():
    """Invoice with zero lines should not crash."""
    db = _make_db()
    invoice = InvoiceOut(
        invoice_number="FV/3/2025",
        lines=[],
        total_net=Decimal("0.00"),
    )
    out = await _resolve_invoice(db, invoice)
    assert out.lines == []
    assert out.unmapped_count == 0
    assert out.mapped_total_net == Decimal("0.00")
    # When no product_ids → DB should NOT be queried
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_invoice_decimal_precision():
    """Decimal arithmetic preserves precision (no float weirdness)."""
    db = _make_db([
        _row(1, "A", 100),
        _row(2, "B", 100),
    ])
    invoice = InvoiceOut(
        invoice_number="FV/4/2025",
        lines=[_line(100, total_net="0.10")],  # tricky decimal
        total_net=Decimal("0.10"),
    )
    out = await _resolve_invoice(db, invoice)
    # 0.10 × 2 = 0.20 exact (not 0.2000000001)
    assert out.mapped_total_net == Decimal("0.20")


# ── P0-014: empty product name fallback ──────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_empty_name_fallback_to_cache():
    """P0-014: FA position with empty name → fallback to fakturownia_products_cache."""
    db = _make_db(
        machine_rows=[_row(42, "Koparka RAO", 100)],
        cache_rows=[_cache_row(100, "Koparka JCB 8035 (z cache)")],
    )
    line = InvoiceLine(
        fakturownia_product_id=100,
        fakturownia_product_name="",  # puste name z FA API
        quantity=Decimal("1"),
        price_net=Decimal("800.00"),
        total_net=Decimal("800.00"),
        invoice_number="FV/5/2026",
    )
    invoice = InvoiceOut(
        invoice_number="FV/5/2026",
        lines=[line],
        total_net=Decimal("800.00"),
    )
    out = await _resolve_invoice(db, invoice)
    assert out.lines[0].fakturownia_product_name == "Koparka JCB 8035 (z cache)"


@pytest.mark.asyncio
async def test_resolve_invoice_empty_name_no_cache_placeholder():
    """P0-014: empty name + no cache → placeholder 'Produkt FA #{pid}'."""
    db = _make_db()
    line = InvoiceLine(
        fakturownia_product_id=999,
        fakturownia_product_name="",
        quantity=Decimal("1"),
        price_net=Decimal("150.00"),
        total_net=Decimal("150.00"),
        invoice_number="FV/6/2026",
    )
    invoice = InvoiceOut(
        invoice_number="FV/6/2026",
        lines=[line],
        total_net=Decimal("150.00"),
    )
    out = await _resolve_invoice(db, invoice)
    assert out.lines[0].fakturownia_product_name == "Produkt FA #999"
    assert out.unmapped_count == 1
