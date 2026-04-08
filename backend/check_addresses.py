import asyncio
from sqlalchemy import text
from database import AsyncSessionLocal

async def check_addresses():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text('SELECT DISTINCT delivery_address FROM contract WHERE delivery_address IS NOT NULL AND delivery_address != "" LIMIT 20'))
        addresses = result.fetchall()
        print('Przykładowe adresy z bazy:')
        for i, (addr,) in enumerate(addresses, 1):
            print(f'{i}. {addr}')
            
if __name__ == "__main__":
    asyncio.run(check_addresses())
