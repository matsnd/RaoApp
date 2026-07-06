"""RAO-P3-011: testy dla ReservationService (mockowane DB)."""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException

from reservations.service import ReservationService
from reservations.schemas import ReservationCreate


def _mock_db_with_conflict(conflict: bool):
    """Buduje AsyncMock(AsyncSession) który zwraca lub nie zwraca rezerwacji."""
    db = AsyncMock()
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
    out = await svc.check_conflict(db, article_id=1,
                                   from_date=date(2026, 1, 1),
                                   to_date=date(2026, 1, 10))
    assert out is True


@pytest.mark.asyncio
async def test_check_conflict_returns_false_when_no_overlap():
    svc = ReservationService()
    db = _mock_db_with_conflict(False)
    out = await svc.check_conflict(db, article_id=1,
                                   from_date=date(2026, 1, 1),
                                   to_date=date(2026, 1, 10))
    assert out is False


@pytest.mark.asyncio
async def test_create_raises_409_on_conflict():
    svc = ReservationService()
    db = _mock_db_with_conflict(True)
    data = ReservationCreate(
        article_id=1,
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
        article_id=1,
        reserved_from=date(2026, 1, 1),
        reserved_to=date(2026, 1, 10),
    )
    obj = await svc.create(db, data, user_id=42)
    assert obj is not None
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
