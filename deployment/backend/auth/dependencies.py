from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database import get_db
from auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# RAO-P2-065 #12: cache user-per-token na czas życia requestu (via request.state).
# Redukuje zapytanie DB per request z 1 → 0 dla powtarzających się wywołań w tym samym
# żądaniu (np. gdy ten sam token używany przez kilka Depends w łańcuchu).
# Cache jest per-request (krótko żyjący, bezpieczny — token nie zmienia się w trakcie req).
_USER_CACHE_ATTR = "_rao_cached_user"


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # Spróbuj cache per-request (gdy ten sam Depends wywoływany wielokrotnie w łańcuchu)
    cached = getattr(request.state, _USER_CACHE_ATTR, None)
    if cached is not None:
        return cached

    try:
        payload = jwt.decode(token, settings.RAO_SECRET_KEY, algorithms=["HS256"])
        user_id: int = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token nieprawidłowy")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Użytkownik nie istnieje lub nieaktywny")

    # Zapisz w request.state — ten sam obiekt request jest współdzielony przez wszystkie
    # Depends w łańcuchu resolucji jednego żądania.
    setattr(request.state, _USER_CACHE_ATTR, user)
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    # NOTE (2026-07-11): IDOR WYŁĄCZONY — single-user mode. No-op (zwraca każdego zalogowanego).
    # Pełny RBAC wdrożony gdy pojawią się wymagania wieloużytkownikowe.
    return user
