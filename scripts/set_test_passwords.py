"""
Set known test passwords for migrated users.
Usage: python set_test_passwords.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
import bcrypt
import aiomysql

DB_HOST = os.environ.get("RAO_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("RAO_DB_PORT", "3306"))
DB_USER = os.environ.get("RAO_DB_USER", "rao_user")
DB_PASS = os.environ.get("RAO_DB_PASSWORD", "")
DB_NAME = os.environ.get("RAO_DB_NAME", "rao_new")

TEST_PASSWORDS = {
    "admin": "admin123",
    "lukasz": "lukasz123",
    "test": "test123",
    "patrycja": "patrycja123",
}


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def main():
    print("Setting test passwords...")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    for login, password in TEST_PASSWORDS.items():
        hashed = hash_password(password)
        await cur.execute(
            "UPDATE users SET password = %s, must_change_password = 0 WHERE login = %s",
            (hashed, login)
        )
        if cur.rowcount > 0:
            print(f"  ✓ {login}: password set to '{password}', must_change_password=0")
        else:
            print(f"  ✗ {login}: user not found")

    await conn.commit()
    await cur.close()
    conn.close()
    print("\nDone! You can now log in with:")
    for login, password in TEST_PASSWORDS.items():
        print(f"  {login} / {password}")


if __name__ == "__main__":
    asyncio.run(main())
