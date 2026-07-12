"""RAO Faza 2a (opcja E) — testy unit dla unmapped settlements z Fakturownia.

Pokrycie:
  1. unmapped pozycja FA → settlement utworzony z position_id=None, source='fa_unmapped',
     article_name_snapshot ustawione (source inspection + mock DB)
  2. idempotentność — drugi import NIE duplikuje (UNIQUE unmapped_key chroni — sprawdzamy
     że router odpytuje existing przed insert)
  3. pozycja FA bez fakturownia_product_id (pid=0) → NIE tworzy unmapped settlement
  4. korekta FA (total_net ujemny) → settlement z cost_client ujemny (brak walidacji ge=0
     w import path)
  5. source='fakturownia' ustawione dla mapped settlements (bug fix bonus — source inspection)
  6. settled_at ustawione z invoice.issue_date (bug fix bonus — source inspection)
  7. compute_position_revenues uwzględnia unmapped settlement w revenue (mock DB)
  8. umowa bez pozycji, tylko unmapped → wynik niepusty (mock DB)
  9. agregacje calc.py obsługują unmapped (is_service=None, article_id=None) — pure function
  10. stats/router.py: top_machines bucket "(niezmapowane z FA)", machine_roi/positions skip
"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from stats.calc import (
    aggregate_by_category,
    aggregate_by_period,
    aggregate_by_contract_type,
    aggregate_by_branch,
)


# ── Helper: source inspection ────────────────────────────────────────────────

def _read_router_source() -> str:
    with open(
        "C:/projects/repos/RaoApp_new/backend/settlements/router.py",
        encoding="utf-8",
    ) as f:
        return f.read()


def _read_stats_router_source() -> str:
    with open(
        "C:/projects/repos/RaoApp_new/backend/stats/router.py",
        encoding="utf-8",
    ) as f:
        return f.read()


# ── Test 1 + 3 + 4: router source inspection — unmapped block presence ───────

def test_router_has_unmapped_block_with_source_fa_unmapped():
    """Test 1: router zawiera blok unmapped z source='fa_unmapped' i snapshot nazwy."""
    src = _read_router_source()
    assert 'source="fa_unmapped"' in src
    assert "article_name_snapshot=line.fakturownia_product_name" in src
    assert "position_id=None" in src
    assert "fakturownia_product_id=pid" in src


def test_router_skips_unmapped_when_pid_is_none_or_zero():
    """Test 3: pozycja FA bez fakturownia_product_id (pid=0/None) → NIE unmapped."""
    src = _read_router_source()
    assert "pid is not None and pid != 0" in src


def test_router_uses_float_line_total_net_for_cost_client():
    """Test 4: cost_client = float(line.total_net) — pozwala na wartości ujemne (korekty)."""
    src = _read_router_source()
    assert "cost_client=float(line.total_net)" in src


# ── Test 2: idempotentność — existing check przed insert ─────────────────────

def test_router_checks_existing_unmapped_before_insert():
    """Test 2: router odpytuje existing unmapped settlement przed insert (idempotentność)."""
    src = _read_router_source()
    assert "ContractSettlement.position_id.is_(None)" in src
    assert "ContractSettlement.service_fee_id.is_(None)" in src
    assert "ContractSettlement.fakturownia_product_id == pid" in src
    assert "ContractSettlement.fakturownia_invoice_number == line.invoice_number" in src
    assert "if not existing.scalar_one_or_none()" in src


# ── Test 5 + 6: bug fix bonus — source/settled_at dla mapped ─────────────────

def test_router_sets_source_fakturownia_for_mapped_settlements():
    """Test 5: mapped settlements dostają source='fakturownia' (nie domyślne 'manual')."""
    src = _read_router_source()
    # 4 ścieżki mapped (positions update+create, fees update+create) używają "fakturownia"
    # Update: existing_settlement.source = "fakturownia"
    # Create: source="fakturownia" w konstruktorze
    assert src.count('"fakturownia"') >= 4


def test_router_sets_settled_at_from_invoice_issue_date():
    """Test 6: settled_at ustawione z invoice.issue_date dla mapped i unmapped."""
    src = _read_router_source()
    assert "settled_at=invoice.issue_date" in src


def test_router_propagates_fakturownia_invoice_number_to_settlement():
    """Bonus: fakturownia_invoice_number zapisane na settlement (dla query/analytics)."""
    src = _read_router_source()
    assert "fakturownia_invoice_number=line.invoice_number" in src


# ── Test 7 + 8: compute_position_revenues — unmapped synthetic rows ──────────

def _make_unmapped_db(positions_rows, unmapped_rows):
    """Mock AsyncSession z dynamiczną sekwencją execute():
    - positions query (zawsze 1. wywołanie) → positions_rows
    - conditions query (gdy pos_ids niepuste) → []
    - settlements query (gdy pos_ids niepuste) → []
    - unmapped query (ostatnie wywołanie) → unmapped_rows
    """
    db = MagicMock()
    call_count = {"n": 0}
    has_positions = bool(positions_rows)

    async def mock_execute(stmt):
        call_count["n"] += 1
        result = MagicMock()
        result.all.return_value = []
        if call_count["n"] == 1:
            result.all.return_value = positions_rows
        else:
            # Ostatnie wywołanie = unmapped query
            # Gdy has_positions: sekwencja to 1=positions, 2=conditions, 3=settlements, 4=unmapped
            # Gdy brak positions: 1=positions, 2=unmapped
            expected_unmapped_call = 4 if has_positions else 2
            if call_count["n"] == expected_unmapped_call:
                result.all.return_value = unmapped_rows
        return result

    db.execute = mock_execute
    return db


@pytest.mark.asyncio
async def test_compute_position_revenues_includes_unmapped_in_revenue():
    """Test 7: unmapped settlement uwzględniony w results z revenue=cost_client."""
    from shared.revenue import compute_position_revenues

    unmapped_row = (
        999, 5, "Transport specjalny", 888, Decimal("1500.00"),
        date(2026, 6, 15), "S001/2026", "Firma XYZ", 10,
        date(2026, 6, 1), date(2026, 6, 30), "Gdańsk", "S", 3,
    )
    db = _make_unmapped_db(positions_rows=[], unmapped_rows=[unmapped_row])

    results = await compute_position_revenues(
        db, date(2026, 1, 1), date(2026, 12, 31),
    )

    assert len(results) == 1
    r = results[0]
    assert r["position_id"] is None
    assert r["machine_id"] is None  # was article_id (articles split)
    assert r["is_service"] is None
    assert r["article_name"] == "Transport specjalny"
    assert r["revenue"] == Decimal("1500.00")
    assert r["revenue_source"] == "actual"
    assert r["revenue_actual"] == Decimal("1500.00")
    assert r["category_main"] is None
    assert r["contract_id"] == 5
    assert r["contract_type"] == "S"
    assert r["branch_id"] == 3
    assert r["city"] == "Gdańsk"


@pytest.mark.asyncio
async def test_compute_position_revenues_unmapped_only_no_positions():
    """Test 8: umowa bez pozycji, tylko unmapped → wynik niepusty (nie early-return)."""
    from shared.revenue import compute_position_revenues

    unmapped_row = (
        100, 7, "Nieznany produkt FA", 555, Decimal("500.00"),
        date(2026, 3, 10), "U002/2026", "ABC Sp z o.o.", 20,
        date(2026, 3, 1), date(2026, 3, 15), "Warszawa", "U", None,
    )
    db = _make_unmapped_db(positions_rows=[], unmapped_rows=[unmapped_row])

    results = await compute_position_revenues(
        db, date(2026, 1, 1), date(2026, 12, 31),
    )

    assert len(results) == 1
    assert results[0]["machine_id"] is None  # was article_id (articles split)
    assert results[0]["revenue"] == Decimal("500.00")
    assert results[0]["contract_type"] == "U"


@pytest.mark.asyncio
async def test_compute_position_revenues_unmapped_uses_snapshot_name_or_fallback():
    """article_name_snapshot=None → fallback '(niezmapowane z FA)'."""
    from shared.revenue import compute_position_revenues

    unmapped_row = (
        200, 8, None, 777, Decimal("300.00"),
        date(2026, 5, 1), "S003/2026", "Firma Q", 30,
        date(2026, 5, 1), date(2026, 5, 10), "Poznań", "S", 1,
    )
    db = _make_unmapped_db(positions_rows=[], unmapped_rows=[unmapped_row])

    results = await compute_position_revenues(
        db, date(2026, 1, 1), date(2026, 12, 31),
    )

    assert results[0]["article_name"] == "(niezmapowane z FA)"


@pytest.mark.asyncio
async def test_compute_position_revenues_unmapped_negative_cost_client():
    """Test 4 (revenue side): korekta FA (cost_client ujemny) → revenue ujemne."""
    from shared.revenue import compute_position_revenues

    unmapped_row = (
        300, 9, "Korekta transportu", 999, Decimal("-200.00"),
        date(2026, 7, 1), "FK/2026", "Firma R", 40,
        date(2026, 7, 1), date(2026, 7, 5), "Łódź", "S", 2,
    )
    db = _make_unmapped_db(positions_rows=[], unmapped_rows=[unmapped_row])

    results = await compute_position_revenues(
        db, date(2026, 1, 1), date(2026, 12, 31),
    )

    assert results[0]["revenue"] == Decimal("-200.00")
    assert results[0]["revenue_actual"] == Decimal("-200.00")


# ── Test 9: calc.py agregacje z unmapped (is_service=None, article_id=None) ──

def _mk_unmapped_pos(contract_id, revenue, contract_type="S", branch_id=None,
                     category_main=None, clamped_days=0, contract_date_from=None):
    return {
        "position_id": None,
        "article_id": None,
        "contract_id": contract_id,
        "revenue": Decimal(str(revenue)),
        # RAO Faza 2a (opcja E): unmapped ma clamped_days=0 (nie zaburza utilization)
        "clamped_days": clamped_days,
        "is_service": None,
        "category_main": category_main,
        "category_sub1": None,
        "category_sub2": None,
        "category_sub3": None,
        "contract_type": contract_type,
        "branch_id": branch_id,
        "contract_date_from": contract_date_from or date(2026, 6, 1),
    }


def _mk_machine_pos(contract_id, article_id, revenue, clamped_days=5,
                    category_main="Koparki", contract_type="S", branch_id=1):
    return {
        "position_id": 1,
        "article_id": article_id,
        "contract_id": contract_id,
        "revenue": Decimal(str(revenue)),
        "clamped_days": clamped_days,
        "is_service": False,
        "category_main": category_main,
        "category_sub1": None,
        "category_sub2": None,
        "category_sub3": None,
        "contract_type": contract_type,
        "branch_id": branch_id,
        "contract_date_from": date(2026, 6, 1),
    }


def test_aggregate_by_category_unmapped_goes_to_bez_kategorii():
    """Test 9a: unmapped (category_main=None) → bucket '(bez kategorii)'."""
    positions = [
        _mk_machine_pos(1, 100, 1000, category_main="Koparki"),
        _mk_unmapped_pos(1, 500, category_main=None),
    ]
    result = aggregate_by_category(positions, level="main")
    cats = {r["category_name"]: r for r in result}
    assert "(bez kategorii)" in cats
    assert cats["(bez kategorii)"]["revenue"] == Decimal("500")
    assert cats["(bez kategorii)"]["articles_count"] == 0
    assert cats["(bez kategorii)"]["rented_days"] == 0
    assert cats["Koparki"]["revenue"] == Decimal("1000")
    assert cats["Koparki"]["rented_days"] == 5


def test_aggregate_by_period_unmapped_included_in_revenue():
    """Test 9b: unmapped doda się do sumy okresu (revenue), ale nie do rented_days
    (clamped_days=0 dla unmapped)."""
    positions = [
        _mk_machine_pos(1, 100, 1000, clamped_days=10),
        _mk_unmapped_pos(1, 500, clamped_days=0, contract_date_from=date(2026, 6, 1)),
    ]
    result = aggregate_by_period(positions, granularity="month")
    assert len(result) == 1
    assert result[0]["period"] == "2026-06"
    assert result[0]["revenue"] == Decimal("1500")
    assert result[0]["rented_days"] == 10  # tylko maszyna (unmapped clamped_days=0)


def test_aggregate_by_contract_type_unmapped_inherits_contract_type():
    """Test 9c: unmapped dziedziczy contract_type po Contract."""
    positions = [
        _mk_machine_pos(1, 100, 1000, contract_type="S"),
        _mk_unmapped_pos(2, 500, contract_type="U"),
    ]
    result = aggregate_by_contract_type(positions)
    types = {r["contract_type"]: r for r in result}
    assert types["S"]["revenue"] == Decimal("1000")
    assert types["S"]["articles_count"] == 1
    assert types["U"]["revenue"] == Decimal("500")
    assert types["U"]["articles_count"] == 0


def test_aggregate_by_branch_unmapped_inherits_branch():
    """Test 9d: unmapped dziedziczy branch_id po Contract."""
    positions = [
        _mk_machine_pos(1, 100, 1000, branch_id=3),
        _mk_unmapped_pos(2, 500, branch_id=4),
    ]
    branches = [{"id": 3, "name": "Warszawa"}, {"id": 4, "name": "Gdańsk"}]
    result = aggregate_by_branch(positions, branches=branches)
    by_branch = {r["branch_id"]: r for r in result}
    assert by_branch[3]["revenue"] == Decimal("1000")
    assert by_branch[3]["articles_count"] == 1
    assert by_branch[4]["revenue"] == Decimal("500")
    assert by_branch[4]["articles_count"] == 0


# ── Test 10: stats/router.py — top_machines bucket, machine_roi/positions skip ──

def test_stats_top_machines_has_unmapped_bucket():
    """Test 10a: top_machines zawiera bucket 'Inne (niezmapowane z FA)'."""
    src = _read_stats_router_source()
    assert "Inne (niezmapowane z FA)" in src
    assert "__unmapped__" in src


def test_stats_machine_roi_skips_unmapped():
    """Test 10b: machine_roi pomija unmapped (article_id=None)."""
    src = _read_stats_router_source()
    assert "pomiń unmapped" in src.lower() or "skip unmapped" in src.lower()


def test_stats_positions_skips_unmapped():
    """Test 10c: /stats/positions pomija unmapped (machine_id is not None)."""
    src = _read_stats_router_source()
    # articles split: article_id → machine_id; unmapped skip via machine_id/service_id/is_additional_service
    assert 'p["machine_id"] is not None' in src or 'p["machine_id"] is not None or p["service_id"]' in src


def test_stats_additional_fees_skips_unmapped():
    """Test 10d: /stats/additional-fees pomija unmapped (is_service is None lub machine_id/service_id check)."""
    src = _read_stats_router_source()
    # articles split: filter używa machine_id/service_id/is_additional_service zamiast is_service is None
    assert 'p["machine_id"] is not None' in src or 'is_additional_service' in src or 'p["is_service"] is None' in src


def test_stats_fleet_summary_top_machine_skips_unmapped():
    """Test 10e: fleet_summary top_machine pomija unmapped (is_service is False)."""
    src = _read_stats_router_source()
    assert 'p["is_service"] is False' in src


# ── Test: integrations schemas — issue_date propagation ──────────────────────

def test_invoice_out_has_issue_date_field():
    from integrations.fakturownia.schemas import InvoiceOut
    assert "issue_date" in InvoiceOut.model_fields


def test_resolved_invoice_out_has_issue_date_field():
    from integrations.fakturownia.schemas import ResolvedInvoiceOut
    assert "issue_date" in ResolvedInvoiceOut.model_fields


def test_resolved_invoice_line_has_fakturownia_product_name():
    from integrations.fakturownia.schemas import ResolvedInvoiceLine
    assert "fakturownia_product_name" in ResolvedInvoiceLine.model_fields


@pytest.mark.asyncio
async def test_resolve_invoice_propagates_issue_date():
    """_resolve_invoice propaguje issue_date z InvoiceOut do ResolvedInvoiceOut."""
    from decimal import Decimal as D
    from integrations.fakturownia.schemas import InvoiceLine, InvoiceOut
    from integrations.fakturownia.service import _resolve_invoice

    db = MagicMock()
    rows_result = MagicMock()
    rows_result.all.return_value = []
    db.execute = AsyncMock(return_value=rows_result)

    invoice = InvoiceOut(
        invoice_number="FV/1/2026",
        lines=[InvoiceLine(
            fakturownia_product_id=999,
            fakturownia_product_name="Test produkt",
            quantity=D("1"),
            price_net=D("100"),
            total_net=D("100"),
            invoice_number="FV/1/2026",
        )],
        total_net=D("100"),
        issue_date=date(2026, 6, 15),
    )
    out = await _resolve_invoice(db, invoice)
    assert out.issue_date == date(2026, 6, 15)


# ── Test: settlements schemas — pola w Response ──────────────────────────────

def test_settlement_response_has_unmapped_fields():
    from settlements.schemas import ContractSettlementResponse
    fields = ContractSettlementResponse.model_fields
    assert "article_name_snapshot" in fields
    assert "fakturownia_product_id" in fields
    assert "fakturownia_invoice_number" in fields
    assert "source" in fields
    assert "settled_at" in fields


def test_settlement_create_does_not_have_unmapped_fields():
    from settlements.schemas import ContractSettlementCreate
    fields = ContractSettlementCreate.model_fields
    assert "article_name_snapshot" not in fields
    assert "fakturownia_product_id" not in fields
    assert "source" not in fields


# ── Test: client._parse_invoices — issue_date parsing ────────────────────────

def test_client_parse_invoices_extracts_issue_date():
    from integrations.fakturownia.client import FakturowniaClient

    client = FakturowniaClient.__new__(FakturowniaClient)
    raw = [{
        "number": "FV/1/2026",
        "issue_date": "2026-06-15",
        "price_net": "100.00",
        "positions": [{
            "product_id": 100,
            "name": "Młotowiertarka",
            "quantity": "1",
            "price_net": "100.00",
            "total_price_net": "100.00",
        }],
    }]
    invoices = client._parse_invoices(raw)
    assert len(invoices) == 1
    assert invoices[0].issue_date == date(2026, 6, 15)


def test_client_parse_invoices_handles_missing_issue_date():
    from integrations.fakturownia.client import FakturowniaClient

    client = FakturowniaClient.__new__(FakturowniaClient)
    raw = [{
        "number": "FV/2/2026",
        "price_net": "50.00",
        "positions": [],
    }]
    invoices = client._parse_invoices(raw)
    assert invoices[0].issue_date is None


def test_client_parse_invoices_handles_invalid_issue_date():
    from integrations.fakturownia.client import FakturowniaClient

    client = FakturowniaClient.__new__(FakturowniaClient)
    raw = [{
        "number": "FV/3/2026",
        "issue_date": "not-a-date",
        "price_net": "0",
        "positions": [],
    }]
    invoices = client._parse_invoices(raw)
    assert invoices[0].issue_date is None
