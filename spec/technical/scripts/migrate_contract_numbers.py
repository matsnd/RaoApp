"""
RAO-P1-022: One-off data fix for contract numbers with SG*/UG* pattern.
Moves 'G' from position 2 to the end of the number.
Idempotent: skips numbers already ending with 'G'.

Usage:
    cd backend && python migrate_contract_numbers.py
"""
import asyncio
import aiomysql
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'backend'))
from config import settings


def _parse_db_url(url: str) -> dict:
    rest = url.replace("mysql+aiomysql://", "").replace("mysql+asyncmy://", "")
    user_pass, host_db = rest.split("@", 1)
    user, password = user_pass.split(":", 1)
    host_port, db = host_db.rsplit("/", 1)
    if ":" in host_port:
        host, port = host_port.split(":", 1)
        port = int(port)
    else:
        host = host_port
        port = 3306
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "db": db,
    }


async def fix_sg_contract_numbers():
    conn_kwargs = _parse_db_url(settings.RAO_DATABASE_URL)
    conn = await aiomysql.connect(**conn_kwargs)
    cur = await conn.cursor()

    await cur.execute("""
        UPDATE contracts
        SET number = CONCAT(LEFT(number, 1), SUBSTRING(number, 3), 'G')
        WHERE number LIKE 'SG%'
          AND RIGHT(number, 1) != 'G'
    """)
    sg_fixed = cur.rowcount

    await cur.execute("""
        UPDATE contracts
        SET number = CONCAT(LEFT(number, 1), SUBSTRING(number, 3), 'G')
        WHERE number LIKE 'UG%'
          AND RIGHT(number, 1) != 'G'
    """)
    ug_fixed = cur.rowcount

    await conn.commit()
    await cur.close()
    conn.close()

    total = sg_fixed + ug_fixed
    print(f"[P1-022] Fixed {sg_fixed} SG* contracts and {ug_fixed} UG* contracts (total {total}).")
    if total == 0:
        print("[P1-022] No contracts needed fixing — script is idempotent.")
    return sg_fixed, ug_fixed


if __name__ == "__main__":
    asyncio.run(fix_sg_contract_numbers())