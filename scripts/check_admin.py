import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from database import AsyncSessionLocal
from sqlalchemy import select
from auth.models import User

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.login == 'admin'))
        user = result.scalar_one_or_none()
        print(f'Admin exists: {user is not None}')
        if user:
            print(f'ID: {user.id}, Login: {user.login}, Role: {user.role}')
        else:
            print('No admin user found in database')

asyncio.run(check())