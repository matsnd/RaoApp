"""RAO-P2-066: testy check_availability z uwzględnieniem article_reservations.

Weryfikują, że:
- maszyna bez rezerwacji i bez umów → is_available=True, conflicting_reservations=[]
- maszyna z rezerwacją pokrywającą się z badanym okresem → is_available=False,
  conflicting_reservations zawiera wpis z `available_from = reserved_to + 1 dzień`
- maszyna zewnętrzna (is_external=True) → zawsze dostępna (ignoruje rezerwacje)
- rezerwacja poza zakresem (reserved_to < date_from) → brak konfliktu
"""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from articles.service import ArticleService
from articles.models import Article
from reservations.models import ArticleReservation


def _mk_reservation(r_id, art_id, r_from, r_to, note=None):
    """Tworzy mock ArticleReservation z polami używanymi przez check_availability."""
    r = MagicMock(spec=ArticleReservation)
    r.id = r_id
    r.article_id = art_id
    r.reserved_from = r_from
    r.reserved_to = r_to
    r.note = note
    return r


def _mk_article(is_external=False):
    a = MagicMock(spec=Article)
    a.is_external = is_external
    return a


def _mock_db(article=None, contract_rows=None, reservations=None):
    """Buduje AsyncMock(AsyncSession):
    - db.get(Article, id) → article (lub None)
    - db.execute(stmt) → result z .all() = contract_rows / .scalars().all() = reservations
    Kolejność execute: 1) contracts, 2) reservations.
    """
    db = AsyncMock()

    async def _get(cls, _id):
        return article
    db.get = AsyncMock(side_effect=_get)

    contract_result = MagicMock()
    contract_result.all.return_value = contract_rows or []

    res_result = MagicMock()
    res_scalars = MagicMock()
    res_scalars.all.return_value = reservations or []
    res_result.scalars.return_value = res_scalars

    calls = {"i": 0}

    async def _execute(stmt):
        calls["i"] += 1
        # Pierwsze execute = contracts (SELECT z JOIN), drugie = reservations
        if calls["i"] == 1:
            return contract_result
        return res_result
    db.execute = AsyncMock(side_effect=_execute)
    return db


@pytest.mark.asyncio
async def test_availability_no_reservations_no_contracts_available():
    svc = ArticleService()
    db = _mock_db(article=_mk_article(), contract_rows=[], reservations=[])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is True
    assert out.conflicting_contracts == []
    assert out.conflicting_reservations == []


@pytest.mark.asyncio
async def test_availability_overlapping_reservation_blocks():
    """Rezerwacja 05.01–15.01 pokrywa się z badanym okresem 01.01–10.01 → blokada."""
    svc = ArticleService()
    res = _mk_reservation(7, 1, date(2026, 1, 5), date(2026, 1, 15), note="Serwis")
    db = _mock_db(article=_mk_article(), contract_rows=[], reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is False
    assert len(out.conflicting_reservations) == 1
    rc = out.conflicting_reservations[0]
    assert rc.reservation_id == 7
    assert rc.reserved_from == date(2026, 1, 5)
    assert rc.reserved_to == date(2026, 1, 15)
    assert rc.note == "Serwis"
    # available_from = reserved_to + 1 dzień
    assert rc.available_from == date(2026, 1, 16)


@pytest.mark.asyncio
async def test_availability_reservation_outside_range_no_conflict():
    """Rezerwacja 11.01–20.01 nie pokrywa się z okresem 01.01–10.01 → brak konfliktu.

    Logika SQL: reserved_from (11.01) <= date_to (10.01)? NIE → brak w wyniku.
    """
    svc = ArticleService()
    res = _mk_reservation(7, 1, date(2026, 1, 11), date(2026, 1, 20))
    db = _mock_db(article=_mk_article(), contract_rows=[], reservations=[])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is True
    assert out.conflicting_reservations == []


@pytest.mark.asyncio
async def test_availability_external_machine_ignores_reservations():
    """Maszyna zewnętrzna (is_external=True) → zawsze dostępna, rezerwacje ignorowane."""
    svc = ArticleService()
    res = _mk_reservation(7, 1, date(2026, 1, 5), date(2026, 1, 15))
    db = _mock_db(article=_mk_article(is_external=True), reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is True
    assert out.conflicting_reservations == []
    assert out.conflicting_contracts == []


@pytest.mark.asyncio
async def test_availability_both_contract_and_reservation_conflict():
    """Konflikt z umową i rezerwacją naraz → oba listy wypełnione, is_available=False."""
    svc = ArticleService()
    res = _mk_reservation(7, 1, date(2026, 1, 5), date(2026, 1, 15))
    contract_row = (10, "U/2026/001", date(2026, 1, 1), date(2026, 1, 31), "ACME Sp. z o.o.")
    db = _mock_db(article=_mk_article(), contract_rows=[contract_row], reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is False
    assert len(out.conflicting_contracts) == 1
    assert len(out.conflicting_reservations) == 1
    assert out.conflicting_contracts[0].contract_number == "U/2026/001"


@pytest.mark.asyncio
async def test_availability_reservation_available_from_is_reserved_to_plus_one():
    """available_from musi być reserved_to + 1 dzień (data, od której maszyna wolna)."""
    svc = ArticleService()
    res = _mk_reservation(1, 1, date(2026, 2, 1), date(2026, 2, 28))
    db = _mock_db(article=_mk_article(), contract_rows=[], reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 2, 10), date(2026, 2, 20))
    assert out.conflicting_reservations[0].available_from == date(2026, 3, 1)
    assert out.conflicting_reservations[0].available_from == res.reserved_to + timedelta(days=1)
