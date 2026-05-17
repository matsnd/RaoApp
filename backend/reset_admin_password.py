"""Skrypt do resetowania hasła admina na 'password'"""
import asyncio
import bcrypt
import os
import sys

# Upewnij się że backend jest w path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import AsyncSessionLocal, engine
from sqlalchemy import select, update
from auth.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def reset_admin_password():
    async with AsyncSessionLocal() as db:
        # Znajdź użytkownika admin
        result = await db.execute(select(User).where(User.login == "admin"))
        user = result.scalar_one_or_none()

        if not user:
            print("Nie znaleziono użytkownika 'admin'")
            return

        # Zhashuj nowe hasło
        new_hash = hash_password("admin123")

        # Zaktualizuj w bazie
        await db.execute(
            update(User).where(User.id == user.id).values(
                password=new_hash,
                must_change_password=False,
            )
        )
        await db.commit()

        print(f"Hasło dla użytkownika 'admin' (ID: {user.id}) zostało zmienione na 'admin123'")


if __name__ == "__main__":
    asyncio.run(reset_admin_password())
