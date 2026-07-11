from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db
from reservations.schemas import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse,
    ReservationWithMachineResponse,
    CalendarEvent,
)
from reservations.service import reservation_service

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=list[ReservationResponse])
async def list_all_reservations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all reservations (for management view)."""
    return await reservation_service.list_all(db)


@router.get("/with-machines", response_model=list[ReservationWithMachineResponse])
async def list_all_reservations_with_machines(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all reservations joined with machine names (for analytics tab)."""
    return await reservation_service.list_all_with_machines(db)


@router.get("/machine/{machine_id}", response_model=list[ReservationResponse])
async def list_for_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all reservations for a specific machine."""
    return await reservation_service.list_for_machine(db, machine_id)


@router.get("/machine/{machine_id}/active", response_model=list[ReservationResponse])
async def get_active_reservations(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List active (future/current) reservations for a specific machine."""
    return await reservation_service.get_active_for_machine(db, machine_id)


@router.post("", response_model=ReservationResponse, status_code=201)
async def create_reservation(
    data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new reservation. Returns 409 if dates conflict."""
    return await reservation_service.create(db, data, user.id)


@router.get("/calendar", response_model=list[CalendarEvent])
async def list_calendar(
    date_from: date = Query(..., description="Początek zakresu kalendarza (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Koniec zakresu kalendarza (YYYY-MM-DD)"),
    machine_id: int | None = Query(None, description="Filtr po ID maszyny"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Zwraca eventy kalendarza (rezerwacje + umowy) pokrywające się z [date_from, date_to]."""
    return await reservation_service.list_calendar(db, date_from, date_to, machine_id)


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an existing reservation (partial). 404 if not found, 409 on conflict."""
    return await reservation_service.update(db, reservation_id, data, user.id)


@router.delete("/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a reservation. Requires admin role."""
    await reservation_service.delete(db, reservation_id)
