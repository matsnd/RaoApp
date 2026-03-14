from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from auth.schemas import (
    ChangePasswordRequest, ForgotPasswordRequest, LoginRequest,
    ProfileUpdate, RegisterRequest, ResetPasswordRequest,
    TokenResponse, UserListItem, UserResponse, UserUpdate,
)
from auth.service import auth_service
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    token, user = await auth_service.login(db, data.login, data.password)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
        must_change_password=user.must_change_password or False,
    )


@router.post("/register", response_model=UserResponse)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = await auth_service.register(db, data)
    return UserResponse.model_validate(user)


@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await auth_service.change_password(
        db, current_user,
        data.current_password, data.new_password, data.confirm_password,
    )
    return {"message": "Hasło zmienione pomyślnie"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.forgot_password(db, data.email)
    return {"message": "Jeśli email istnieje w systemie, wysłaliśmy link do resetu hasła"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(db, data.token, data.new_password, data.confirm_password)
    return {"message": "Hasło zostało ustawione. Możesz się zalogować."}


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import update as sql_update
    from fastapi import HTTPException
    if data.email and data.email != current_user.email:
        existing = await db.execute(
            select(User).where(User.email == data.email, User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, "Email już istnieje")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        await db.execute(sql_update(User).where(User.id == current_user.id).values(**update_data))
        await db.commit()
        await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@admin_router.get("/users", response_model=list[UserListItem])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.login))
    users = result.scalars().all()
    out = []
    for u in users:
        item = UserListItem(
            id=u.id, login=u.login, email=u.email,
            first_name=u.first_name, last_name=u.last_name,
            role=u.role, branch_id=u.branch_id, branch_name=None,
            is_active=u.is_active, last_login=u.last_login,
            created_at=u.created_at,
        )
        out.append(item)
    return out


@admin_router.post("/users", response_model=UserResponse)
async def create_user(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = await auth_service.register(db, data)
    return UserResponse.model_validate(user)


@admin_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    from sqlalchemy import update as sql_update
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from shared.exceptions import not_found
        raise not_found("Użytkownik")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        await db.execute(sql_update(User).where(User.id == user_id).values(**update_data))
        await db.commit()
        await db.refresh(user)
    return UserResponse.model_validate(user)


@admin_router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from sqlalchemy import update as sql_update
    if current_user.id == user_id:
        from fastapi import HTTPException
        raise HTTPException(400, "Nie możesz deaktywować samego siebie")
    await db.execute(sql_update(User).where(User.id == user_id).values(is_active=False))
    await db.commit()
    return {"message": "Użytkownik dezaktywowany"}


@admin_router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    from sqlalchemy import update as sql_update
    await db.execute(sql_update(User).where(User.id == user_id).values(is_active=True))
    await db.commit()
    return {"message": "Użytkownik aktywowany"}


@admin_router.post("/users/{user_id}/force-password-reset")
async def force_password_reset(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    from sqlalchemy import update as sql_update
    await db.execute(sql_update(User).where(User.id == user_id).values(must_change_password=True))
    await db.commit()
    return {"message": "Wymuszono zmianę hasła"}
