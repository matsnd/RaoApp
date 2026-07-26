"""RAO-P2-071: Seed demo users for fresh database.

Tworzy konta: admin, lukasz, test, patrycja znanymi hasłami (bcrypt).
Idempotentny (INSERT IGNORE po login).

Użycie:
    cd backend && python seed_users.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
import bcrypt
from datetime import datetime

from sqlalchemy import select
from database import AsyncSessionLocal
from auth.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


DEMO_USERS = [
    {"login": "admin", "password": "admin123", "email": "admin@rao.local",
     "first_name": "Admin", "last_name": "System", "role": "admin"},
    {"login": "lukasz", "password": "lukasz123", "email": "lukasz@rao.local",
     "first_name": "Łukasz", "last_name": "Kowalski", "role": "admin"},
    {"login": "test", "password": "test123", "email": "test@rao.local",
     "first_name": "Test", "last_name": "User", "role": "user"},
    {"login": "patrycja", "password": "patrycja123", "email": "patrycja@rao.local",
     "first_name": "Patrycja", "last_name": "Nowak", "role": "user"},
]


async def main():
    print("=" * 60)
    print("RAO-P2-071: Seed demo users")
    print("=" * 60)
    created = 0
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        for u in DEMO_USERS:
            existing = await db.execute(select(User).where(User.login == u["login"]))
            if existing.scalar_one_or_none():
                print(f"  [SKIP] {u['login']} — already exists")
                continue
            user = User(
                login=u["login"],
                email=u["email"],
                password=hash_password(u["password"]),
                first_name=u["first_name"],
                last_name=u["last_name"],
                role=u["role"],
                is_active=True,
                must_change_password=False,
                created_at=now,
                updated_at=now,
            )
            db.add(user)
            created += 1
            print(f"  [OK] {u['login']} / {u['password']} (role={u['role']})")
        await db.commit()
    print(f"\nDONE — {created} users created")
    print("Login: admin / admin123")


if __name__ == "__main__":
    asyncio.run(main())
