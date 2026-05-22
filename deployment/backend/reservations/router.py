from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db
from reservations.schemas import ReservationCreate, ReservationResponse
from reservations.service import reservation_service

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=list[ReservationResponse])
async def list_all_reservations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all reservations (for management view)."""
    return await reservation_service.list_all(db)


@router.get("/article/{article_id}", response_model=list[ReservationResponse])
async def list_for_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all reservations for a specific article."""
    return await reservation_service.list_for_article(db, article_id)


@router.get("/article/{article_id}/active", response_model=list[ReservationResponse])
async def get_active_reservations(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List active (future/current) reservations for a specific article."""
    return await reservation_service.get_active_for_article(db, article_id)


@router.post("", response_model=ReservationResponse, status_code=201)
async def create_reservation(
    data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new reservation. Returns 409 if dates conflict."""
    return await reservation_service.create(db, data, user.id)


@router.delete("/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a reservation. Requires admin role."""
    await reservation_service.delete(db, reservation_id)
