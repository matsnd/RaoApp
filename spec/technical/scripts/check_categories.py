import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
import asyncio
import asyncmy
from config import settings

async def check_categories():
    conn = await asyncmy.create_connect(
        host='localhost',
        user='rao_user',
        password=settings.db_password,
        db='rao_new',
        charset='utf8mb4'
    )
    cursor = await conn.cursor()
    
    await cursor.execute('''
        SELECT DISTINCT 
            category_main, 
            category_sub1, 
            category_sub2, 
            category_sub3 
        FROM articles 
        WHERE category_main IS NOT NULL 
        ORDER BY category_main, category_sub1, category_sub2, category_sub3
    ''')
    
    rows = await cursor.fetchall()
    print('category_main | category_sub1 | category_sub2 | category_sub3')
    print('-' * 80)
    for row in rows:
        main = row[0] or ''
        sub1 = row[1] or ''
        sub2 = row[2] or ''
        sub3 = row[3] or ''
        print(f'{main} | {sub1} | {sub2} | {sub3}')
    
    await cursor.close()
    conn.close()

asyncio.run(check_categories())
