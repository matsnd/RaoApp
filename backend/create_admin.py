import asyncio
import sys
sys.path.insert(0, '.')

import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "mysql+aiomysql://rao_user:RaoPass2026!@localhost:3306/rao_new"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    print(f"New hash: {hashed}")

    async with async_session() as session:
        # Check existing users
        result = await session.execute(text("SELECT id, login, LEFT(password,10) as pw FROM users"))
        rows = result.fetchall()
        print("Existing users:", rows)

        if rows:
            await session.execute(
                text("UPDATE users SET password=:pw, is_active=1, must_change_password=0 WHERE login='admin'"),
                {"pw": hashed}
            )
        else:
            await session.execute(
                text("INSERT INTO users (login, email, password, first_name, last_name, role, is_active, must_change_password, created_at) VALUES (:login, :email, :pw, 'Admin', 'RAO', 'admin', 1, 0, NOW())"),
                {"login": "admin", "email": "admin@rao.pl", "pw": hashed}
            )
        await session.commit()
        print("Done — admin password set to admin123")

        # Verify
        result = await session.execute(text("SELECT id, login, password FROM users WHERE login='admin'"))
        user = result.fetchone()
        if user:
            ok = bcrypt.checkpw(b"admin123", user.password.encode())
            print(f"Verify checkpw: {ok}")

    await engine.dispose()

asyncio.run(main())
