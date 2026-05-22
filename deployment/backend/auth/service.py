import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt as _bcrypt
from jose import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from auth.schemas import RegisterRequest
from config import settings
from shared.exceptions import bad_request, conflict, not_found

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.RAO_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.RAO_SECRET_KEY, algorithm="HS256")


class AuthService:
    async def login(self, db: AsyncSession, login: str, password: str):
        result = await db.execute(
            select(User).where(User.login == login, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password):
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Nieprawidłowy login lub hasło")

        await db.execute(
            update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(user)
        token = create_access_token(user.id, user.role)
        return token, user

    async def register(self, db: AsyncSession, data: RegisterRequest) -> User:
        existing = await db.execute(select(User).where(User.login == data.login))
        if existing.scalar_one_or_none():
            raise conflict("Login już istnieje")
        if data.email:
            existing_email = await db.execute(select(User).where(User.email == data.email))
            if existing_email.scalar_one_or_none():
                raise conflict("Email już istnieje")

        user = User(
            login=data.login,
            email=data.email,
            password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            branch_id=data.branch_id,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def change_password(
        self, db: AsyncSession, user: User,
        current_password: str, new_password: str, confirm_password: str
    ):
        if not verify_password(current_password, user.password):
            raise bad_request("Aktualne hasło jest nieprawidłowe")
        if new_password != confirm_password:
            raise bad_request("Hasła nie są identyczne")
        if verify_password(new_password, user.password):
            raise bad_request("Nowe hasło musi być inne niż aktualne")
        await db.execute(
            update(User).where(User.id == user.id).values(
                password=hash_password(new_password),
                must_change_password=False,
            )
        )
        await db.commit()

    async def forgot_password(self, db: AsyncSession, email: str):
        from auth.email_service import email_service
        result = await db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            return

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires = datetime.utcnow() + timedelta(hours=1)
        await db.execute(
            update(User).where(User.id == user.id).values(
                password_reset_token=token_hash,
                password_reset_expires=expires,
            )
        )
        await db.commit()

        reset_link = f"{settings.RAO_FRONTEND_URL}/reset-password?token={token}"
        user_name = user.first_name or user.login
        await email_service.send_password_reset(email, reset_link, user_name)

    async def reset_password(
        self, db: AsyncSession, token: str, new_password: str, confirm_password: str
    ):
        if new_password != confirm_password:
            raise bad_request("Hasła nie są identyczne")
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await db.execute(
            select(User).where(
                User.password_reset_token == token_hash,
                User.password_reset_expires > datetime.utcnow(),
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            raise bad_request("Token nieprawidłowy lub wygasł")
        await db.execute(
            update(User).where(User.id == user.id).values(
                password=hash_password(new_password),
                password_reset_token=None,
                password_reset_expires=None,
                must_change_password=False,
            )
        )
        await db.commit()


auth_service = AuthService()
