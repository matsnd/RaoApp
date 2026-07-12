"""RAO-P3-011: testy dla ReservationService (mockowane DB)."""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from reservations.service import ReservationService
from reservations.schemas import ReservationCreate, ReservationUpdate


def _mock_db_with_conflict(conflict: bool):
    """Buduje AsyncMock(AsyncSession) który zwraca lub nie zwraca rezerwacji."""
    db = AsyncMock()
    # P2-003: db.get(Machine, id) → maszyna wewnętrzna (is_external=False)
    machine = MagicMock()
    machine.is_external = False
    contractor = MagicMock()  # dla testów z contractor_id

    async def _get(cls, _id):
        if cls.__name__ == "Machine":
            return machine
        if cls.__name__ == "Contractor":
            return contractor
        return None
    db.get = AsyncMock(side_effect=_get)

    result = MagicMock()
    result.scalar_one_or_none.return_value = MagicMock() if conflict else None
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_check_conflict_returns_true_when_overlap():
    svc = ReservationService()
    db = _mock_db_with_conflict(True)
    out = await svc.check_conflict(db, machine_id=1,
                                   from_date=date(2026, 1, 1),
                                   to_date=date(2026, 1, 10))
    assert out is True


@pytest.mark.asyncio
async def test_check_conflict_returns_false_when_no_overlap():
    svc = ReservationService()
    db = _mock_db_with_conflict(False)
    out = await svc.check_conflict(db, machine_id=1,
                                   from_date=date(2026, 1, 1),
                                   to_date=date(2026, 1, 10))
    assert out is False


@pytest.mark.asyncio
async def test_create_raises_409_on_conflict():
    svc = ReservationService()
    db = _mock_db_with_conflict(True)
    data = ReservationCreate(
        machine_id=1,
        reserved_from=date(2026, 1, 1),
        reserved_to=date(2026, 1, 10),
    )
    with pytest.raises(HTTPException) as exc_info:
        await svc.create(db, data, user_id=42)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_create_succeeds_when_no_conflict():
    svc = ReservationService()
    db = _mock_db_with_conflict(False)
    data = ReservationCreate(
        machine_id=1,
        reserved_from=date(2026, 1, 1),
        reserved_to=date(2026, 1, 10),
    )
    obj = await svc.create(db, data, user_id=42)
    assert obj is not None
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_with_contractor_id():
    """RAO-L-Phase2: POST z contractor_id."""
    svc = ReservationService()
    db = _mock_db_with_conflict(False)
    data = ReservationCreate(
        machine_id=1,
        reserved_from=date(2026, 1, 1),
        reserved_to=date(2026, 1, 10),
        contractor_id=5,
    )
    obj = await svc.create(db, data, user_id=42)
    assert obj is not None
    db.add.assert_called_once()


# --- PUT /reservations/{id} (update) ---

def _mock_db_for_update(existing_obj, conflict: bool = False):
    """Mock dla update: db.get → existing_obj, db.execute → conflict result."""
    db = AsyncMock()

    async def _get(cls, _id):
        return existing_obj
    db.get = AsyncMock(side_effect=_get)

    result = MagicMock()
    result.scalar_one_or_none.return_value = MagicMock() if conflict else None
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _mk_existing_reservation(r_id=1, mach_id=1, r_from=date(2026, 1, 1), r_to=date(2026, 1, 10)):
    r = MagicMock()
    r.id = r_id
    r.machine_id = mach_id
    r.reserved_from = r_from
    r.reserved_to = r_to
    r.note = None
    r.contractor_id = None
    return r


@pytest.mark.asyncio
async def test_update_happy_path_change_dates():
    """PUT — zmiana daty, brak konfliktu → 200, pola zaktualizowane."""
    svc = ReservationService()
    existing = _mk_existing_reservation()
    db = _mock_db_for_update(existing, conflict=False)
    data = ReservationUpdate(reserved_from=date(2026, 2, 1), reserved_to=date(2026, 2, 10))
    out = await svc.update(db, 1, data, user_id=42)
    assert out is existing
    assert existing.reserved_from == date(2026, 2, 1)
    assert existing.reserved_to == date(2026, 2, 10)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_404_when_not_found():
    """PUT — nieistniejąca rezerwacja → 404."""
    svc = ReservationService()
    db = _mock_db_for_update(None, conflict=False)
    data = ReservationUpdate(note="zmiana")
    with pytest.raises(HTTPException) as exc_info:
        await svc.update(db, 999, data, user_id=42)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_409_on_conflict():
    """PUT — nowy zakres dat koliduje z inną rezerwacją → 409."""
    svc = ReservationService()
    existing = _mk_existing_reservation()
    db = _mock_db_for_update(existing, conflict=True)
    data = ReservationUpdate(reserved_from=date(2026, 2, 1), reserved_to=date(2026, 2, 10))
    with pytest.raises(HTTPException) as exc_info:
        await svc.update(db, 1, data, user_id=42)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_update_partial_only_note():
    """PUT — aktualizacja tylko note, daty bez zmian (exclude_unset)."""
    svc = ReservationService()
    existing = _mk_existing_reservation()
    db = _mock_db_for_update(existing, conflict=False)
    data = ReservationUpdate(note="nowa notatka")
    out = await svc.update(db, 1, data, user_id=42)
    assert out is existing
    assert existing.note == "nowa notatka"
    # daty bez zmian
    assert existing.reserved_from == date(2026, 1, 1)


@pytest.mark.asyncio
async def test_update_contractor():
    """PUT — zmiana contractor_id."""
    svc = ReservationService()
    existing = _mk_existing_reservation()
    db = _mock_db_for_update(existing, conflict=False)
    data = ReservationUpdate(contractor_id=7)
    out = await svc.update(db, 1, data, user_id=42)
    assert out is existing
    assert existing.contractor_id == 7


# --- check_conflict exclude_contractor_id ---

@pytest.mark.asyncio
async def test_check_conflict_exclude_contractor_id():
    """RAO-L-Phase2: exclude_contractor_id ignoruje rezerwacje tego kontrahenta."""
    svc = ReservationService()
    db = _mock_db_with_conflict(False)  # no conflict returned (excluded)
    out = await svc.check_conflict(
        db, machine_id=1,
        from_date=date(2026, 1, 1), to_date=date(2026, 1, 10),
        exclude_contractor_id=5,
    )
    assert out is False


# --- list_calendar ---

def _mock_db_for_calendar(reservation_rows=None, contract_rows=None):
    """Mock dla list_calendar: 1 execute = reservations, 2 = contracts."""
    db = AsyncMock()
    res_result = MagicMock()
    res_result.all.return_value = reservation_rows or []
    contract_result = MagicMock()
    contract_result.all.return_value = contract_rows or []
    calls = {"i": 0}

    async def _execute(stmt):
        calls["i"] += 1
        if calls["i"] == 1:
            return res_result
        return contract_result
    db.execute = AsyncMock(side_effect=_execute)
    return db


@pytest.mark.asyncio
async def test_list_calendar_happy_path_reservation_and_contract():
    """GET /calendar — eventy z rezerwacji i umów, sortowane po date_from."""
    svc = ReservationService()
    # reservation: 05.01–15.01, contract: 01.01–31.01
    res_row = (1, 10, "Koparka", "S001", 5, "ACME", date(2026, 1, 5), date(2026, 1, 15), "Serwis", None, None)  # P1-119: +salesperson_id, salesperson_name (bez status)
    contract_row = (100, 10, "Koparka", "S001", 5, "ACME", date(2026, 1, 1), date(2026, 1, 31), "U/2026/001")
    db = _mock_db_for_calendar(reservation_rows=[res_row], contract_rows=[contract_row])
    events = await svc.list_calendar(db, date(2026, 1, 1), date(2026, 1, 31))
    assert len(events) == 2
    # sorted by date_from: contract (01.01) first, reservation (05.01) second
    assert events[0].source == "contract"
    assert events[0].source_id == 100
    assert events[0].note == "U/2026/001"
    assert events[1].source == "reservation"
    assert events[1].source_id == 1
    assert events[1].contractor_name == "ACME"


@pytest.mark.asyncio
async def test_list_calendar_empty_result():
    """GET /calendar — brak eventów w zakresie → pusta lista."""
    svc = ReservationService()
    db = _mock_db_for_calendar(reservation_rows=[], contract_rows=[])
    events = await svc.list_calendar(db, date(2026, 6, 1), date(2026, 6, 30))
    assert events == []


@pytest.mark.asyncio
async def test_list_calendar_with_machine_filter():
    """GET /calendar — filtr machine_id przekazany do obu źródeł (refaktor articles→machines)."""
    svc = ReservationService()
    res_row = (1, 10, "Koparka", "S001", None, None, date(2026, 1, 5), date(2026, 1, 15), None, None, None)  # P1-119: +salesperson_id, salesperson_name (bez status)
    db = _mock_db_for_calendar(reservation_rows=[res_row], contract_rows=[])
    events = await svc.list_calendar(db, date(2026, 1, 1), date(2026, 1, 31), machine_id=10)
    assert len(events) == 1
    assert events[0].machine_id == 10


# --- P2-003: Rezerwacje tylko na maszyny wewnętrzne ---

def _mock_db_with_external_machine(is_external: bool = True):
    """Mock dla create: db.get(Machine, id) → maszyna z is_external."""
    db = AsyncMock()
    machine = MagicMock()
    machine.is_external = is_external

    async def _get(cls, _id):
        if cls.__name__ == "Machine":
            return machine
        return None
    db.get = AsyncMock(side_effect=_get)

    result = MagicMock()
    result.scalar_one_or_none.return_value = None  # brak konfliktu
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_create_rejects_external_machine_400():
    """P2-003: create rezerwacji na maszynie zewnętrznej → 400."""
    svc = ReservationService()
    db = _mock_db_with_external_machine(is_external=True)
    data = ReservationCreate(
        machine_id=99,
        reserved_from=date(2026, 1, 1),
        reserved_to=date(2026, 1, 10),
    )
    with pytest.raises(HTTPException) as exc_info:
        await svc.create(db, data, user_id=42)
    assert exc_info.value.status_code == 400
    assert "zewnętrz" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_create_allows_internal_machine():
    """P2-003: create rezerwacji na maszynie wewnętrznej → sukces."""
    svc = ReservationService()
    db = _mock_db_with_external_machine(is_external=False)
    data = ReservationCreate(
        machine_id=1,
        reserved_from=date(2026, 1, 1),
        reserved_to=date(2026, 1, 10),
    )
    # Mock check_conflict + MachineReservation constructor (unika SQLAlchemy mapper init)
    with patch.object(svc, "check_conflict", new_callable=AsyncMock, return_value=False), \
         patch("reservations.service.MachineReservation") as MockReservation:
        MockReservation.return_value = MagicMock()
        obj = await svc.create(db, data, user_id=42)
    assert obj is not None
    db.add.assert_called_once()


@pytest.mark.asyncio
async def test_update_rejects_external_machine_400():
    """P2-003: update rezerwacji zmieniająca machine_id na zewnętrzną → 400."""
    svc = ReservationService()
    existing = _mk_existing_reservation()
    external_machine = MagicMock()
    external_machine.is_external = True

    db = _mock_db_for_update(existing, conflict=False)

    async def _get(cls, _id):
        if cls.__name__ == "Machine":
            return external_machine
        return existing
    db.get = AsyncMock(side_effect=_get)

    data = ReservationUpdate(machine_id=99)
    with pytest.raises(HTTPException) as exc_info:
        await svc.update(db, 1, data, user_id=42)
    assert exc_info.value.status_code == 400
    assert "zewnętrz" in str(exc_info.value.detail).lower()
