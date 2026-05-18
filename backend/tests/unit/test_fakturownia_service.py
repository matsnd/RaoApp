"""Unit tests for backend/integrations/fakturownia/service._resolve_invoice — RAO-P2-012 QA.

Tests 1:N article mapping semantics:
- 1 FA product → 1 RAO article  (normal case)
- 1 FA product → N RAO articles (each RAO article gets full line.total_net; mapped_total = total_net × N)
- 1 FA product → 0 RAO articles (unmapped — counted, contributes 0 to mapped_total)
"""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from integrations.fakturownia.schemas import InvoiceLine, InvoiceOut
from integrations.fakturownia.service import _resolve_invoice


def _make_db(article_rows):
    """Build a mock AsyncSession whose execute() returns rows iterable via .all()."""
    db = MagicMock()
    rows_result = MagicMock()
    rows_result.all.return_value = article_rows
    db.execute = AsyncMock(return_value=rows_result)
    return db


def _row(article_id: int, name: str, fakturownia_product_id: int):
    """Mimic a SQLAlchemy Row with named attribute access."""
    return SimpleNamespace(
        id=article_id,
        name=name,
        fakturownia_product_id=fakturownia_product_id,
    )


def _line(pid: int, name: str = "Mlotowiertarka", total_net: str = "1000.00"):
    return InvoiceLine(
        fakturownia_product_id=pid,
        fakturownia_product_name=name,
        quantity=Decimal("1"),
        price_net=Decimal(total_net),
        total_net=Decimal(total_net),
        invoice_number="FV/1/2025",
    )


# ── 1:1 mapping ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_1to1_mapping():
    """1 FA product (id=100) → 1 RAO article (id=42)."""
    db = _make_db([_row(42, "Mlotowiertarka Hilti", 100)])

    invoice = InvoiceOut(
        invoice_number="FV/1/2025",
        lines=[_line(100)],
        total_net=Decimal("1000.00"),
    )

    out = await _resolve_invoice(db, invoice)

    assert out.invoice_number == "FV/1/2025"
    assert len(out.lines) == 1
    assert len(out.lines[0].rao_articles) == 1
    assert out.lines[0].rao_articles[0].id == 42
    assert out.lines[0].rao_articles[0].name == "Mlotowiertarka Hilti"
    assert out.unmapped_count == 0
    # 1000 × 1 article = 1000
    assert out.mapped_total_net == Decimal("1000.00")


# ── 1:N mapping ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_1toN_mapping():
    """1 FA product (id=100) → 3 RAO articles → mapped_total = total_net × 3 (per spec)."""
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

    assert len(out.lines[0].rao_articles) == 3
    article_ids = {a.id for a in out.lines[0].rao_articles}
    assert article_ids == {42, 43, 44}
    assert out.unmapped_count == 0
    # Per spec: line gets full total_net × N mapped articles
    assert out.mapped_total_net == Decimal("3000.00")


# ── 1:0 mapping (unmapped) ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_zero_mapping():
    """1 FA product (id=999) → 0 RAO articles → unmapped_count=1, mapped_total=0."""
    db = _make_db([])  # no matching articles

    invoice = InvoiceOut(
        invoice_number="FV/1/2025",
        lines=[_line(999, name="Nieznany produkt", total_net="500.00")],
        total_net=Decimal("500.00"),
    )

    out = await _resolve_invoice(db, invoice)

    assert len(out.lines) == 1
    assert out.lines[0].rao_articles == []
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
    assert len(out.lines[0].rao_articles) == 1  # 1:1
    assert len(out.lines[1].rao_articles) == 2  # 1:N
    assert len(out.lines[2].rao_articles) == 0  # unmapped
    assert out.unmapped_count == 1
    # 100*1 + 200*2 + 50*0 = 500
    assert out.mapped_total_net == Decimal("500.00")


# ── Empty invoice ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_invoice_no_lines():
    """Invoice with zero lines should not crash."""
    db = _make_db([])
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
