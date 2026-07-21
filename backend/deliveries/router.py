"""P1-205 Faza 1: Router dla read-only kalendarza dostaw (źródło: umowy)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from deliveries.schemas import DeliveryCalendarEvent
from deliveries.service import delivery_service

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.get("/calendar", response_model=list[DeliveryCalendarEvent])
async def list_deliveries_calendar(
    date_from: date = Query(..., description="Początek zakresu kalendarza (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Koniec zakresu kalendarza (YYYY-MM-DD)"),
    machine_id: int | None = Query(None, description="Filtr po ID maszyny"),
    contractor_id: int | None = Query(None, description="Filtr po ID kontrahenta"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Zwraca dostawy (z umów) pokrywające się z [date_from, date_to].

    Źródło: umowy (S + U) z date_from w zakresie. Read-only, brak osobnej tabeli.
    """
    return await delivery_service.list_calendar(
        db, date_from, date_to, machine_id, contractor_id
    )
