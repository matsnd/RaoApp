"""Skrypt do resetowania haseł wszystkich użytkowników na {login}123"""
import asyncio
import bcrypt
import os
import sys

# Upewnij się że backend jest w path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'backend'))

from database import AsyncSessionLocal
from sqlalchemy import select, update
from auth.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def reset_all_passwords():
    async with AsyncSessionLocal() as db:
        # Pobierz wszystkich użytkowników
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            # Nowe hasło: {login}123
            new_password = f"{user.login}123"
            new_hash = hash_password(new_password)

            # Zaktualizuj w bazie
            await db.execute(
                update(User).where(User.id == user.id).values(
                    password=new_hash,
                    must_change_password=False,
                )
            )
            print(f"Hasło dla '{user.login}' zmienione na '{new_password}'")

        await db.commit()
        print(f"\nZaktualizowano {len(users)} użytkowników")


if __name__ == "__main__":
    asyncio.run(reset_all_passwords())
