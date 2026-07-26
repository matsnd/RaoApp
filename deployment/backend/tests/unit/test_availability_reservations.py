"""RAO-P2-066: testy check_availability z uwzględnieniem machine_reservations.

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

from machines.service import MachineService
from machines.models import Machine
from reservations.models import MachineReservation


def _mk_reservation(r_id, mach_id, r_from, r_to, note=None, contractor_id=None):
    """Tworzy mock MachineReservation z polami używanymi przez check_availability."""
    r = MagicMock(spec=MachineReservation)
    r.id = r_id
    r.machine_id = mach_id
    r.reserved_from = r_from
    r.reserved_to = r_to
    r.note = note
    r.contractor_id = contractor_id
    return r


def _mk_machine(is_external=False):
    a = MagicMock(spec=Machine)
    a.is_external = is_external
    return a


def _mock_db(machine=None, contract_rows=None, reservations=None):
    """Buduje AsyncMock(AsyncSession):
    - db.get(Machine, id) → machine (lub None)
    - db.execute(stmt) → result z .all() = contract_rows / reservation tuples
    Kolejność execute: 1) contracts, 2) reservations.
    RAO-L-Phase2: reservations query zwraca tuple (MachineReservation, contractor_name).
    """
    db = AsyncMock()

    async def _get(cls, _id):
        return machine
    db.get = AsyncMock(side_effect=_get)

    contract_result = MagicMock()
    contract_result.all.return_value = contract_rows or []

    # Reservation rows are now tuples (reservation, contractor_name)
    res_tuples = []
    for r in (reservations or []):
        contractor_name = "ACME Sp. z o.o." if r.contractor_id else None
        res_tuples.append((r, contractor_name))

    res_result = MagicMock()
    res_result.all.return_value = res_tuples

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
    svc = MachineService()
    db = _mock_db(machine=_mk_machine(), contract_rows=[], reservations=[])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is True
    assert out.conflicting_contracts == []
    assert out.conflicting_reservations == []


@pytest.mark.asyncio
async def test_availability_overlapping_reservation_blocks():
    """Rezerwacja 05.01–15.01 pokrywa się z badanym okresem 01.01–10.01 → blokada."""
    svc = MachineService()
    res = _mk_reservation(7, 1, date(2026, 1, 5), date(2026, 1, 15), note="Serwis")
    db = _mock_db(machine=_mk_machine(), contract_rows=[], reservations=[res])
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
    svc = MachineService()
    res = _mk_reservation(7, 1, date(2026, 1, 11), date(2026, 1, 20))
    db = _mock_db(machine=_mk_machine(), contract_rows=[], reservations=[])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is True
    assert out.conflicting_reservations == []


@pytest.mark.asyncio
async def test_availability_external_machine_ignores_reservations():
    """Maszyna zewnętrzna (is_external=True) → zawsze dostępna, rezerwacje ignorowane."""
    svc = MachineService()
    res = _mk_reservation(7, 1, date(2026, 1, 5), date(2026, 1, 15))
    db = _mock_db(machine=_mk_machine(is_external=True), reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is True
    assert out.conflicting_reservations == []
    assert out.conflicting_contracts == []


@pytest.mark.asyncio
async def test_availability_both_contract_and_reservation_conflict():
    """Konflikt z umową i rezerwacją naraz → oba listy wypełnione, is_available=False."""
    svc = MachineService()
    res = _mk_reservation(7, 1, date(2026, 1, 5), date(2026, 1, 15))
    contract_row = (10, "U/2026/001", date(2026, 1, 1), date(2026, 1, 31), "ACME Sp. z o.o.")
    db = _mock_db(machine=_mk_machine(), contract_rows=[contract_row], reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is False
    assert len(out.conflicting_contracts) == 1
    assert len(out.conflicting_reservations) == 1
    assert out.conflicting_contracts[0].contract_number == "U/2026/001"


@pytest.mark.asyncio
async def test_availability_reservation_available_from_is_reserved_to_plus_one():
    """available_from musi być reserved_to + 1 dzień (data, od której maszyna wolna)."""
    svc = MachineService()
    res = _mk_reservation(1, 1, date(2026, 2, 1), date(2026, 2, 28))
    db = _mock_db(machine=_mk_machine(), contract_rows=[], reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 2, 10), date(2026, 2, 20))
    assert out.conflicting_reservations[0].available_from == date(2026, 3, 1)
    assert out.conflicting_reservations[0].available_from == res.reserved_to + timedelta(days=1)


@pytest.mark.asyncio
async def test_availability_reservation_conflict_includes_contractor():
    """RAO-L-Phase2: conflicting_reservations zawiera contractor_id i contractor_name."""
    svc = MachineService()
    res = _mk_reservation(
        7, 1, date(2026, 1, 5), date(2026, 1, 15),
        note="Serwis", contractor_id=42,
    )
    db = _mock_db(machine=_mk_machine(), contract_rows=[], reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    assert out.is_available is False
    rc = out.conflicting_reservations[0]
    assert rc.contractor_id == 42
    assert rc.contractor_name is not None


@pytest.mark.asyncio
async def test_availability_reservation_conflict_no_contractor():
    """RAO-L-Phase2: rezerwacja bez contractor_id → contractor_id=None, contractor_name=None."""
    svc = MachineService()
    res = _mk_reservation(7, 1, date(2026, 1, 5), date(2026, 1, 15), contractor_id=None)
    db = _mock_db(machine=_mk_machine(), contract_rows=[], reservations=[res])
    out = await svc.check_availability(db, 1, date(2026, 1, 1), date(2026, 1, 10))
    rc = out.conflicting_reservations[0]
    assert rc.contractor_id is None
    assert rc.contractor_name is None
