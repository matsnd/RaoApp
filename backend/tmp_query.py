import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from contracts.models import ContractServiceFee
async def main():
    async with AsyncSessionLocal() as db:
        rows=await db.execute(select(ContractServiceFee.description, ContractServiceFee.amount_from, ContractServiceFee.amount_to).limit(20))
        for r in rows.all():
            print(r)
asyncio.run(main())
