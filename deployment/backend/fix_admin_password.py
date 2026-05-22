import asyncio
import aiomysql
import bcrypt

async def fix():
    conn = await aiomysql.connect(
        host='localhost',
        port=3306,
        user='rao_user',
        password='RaoPass2026!',
        db='rao_new'
    )
    cur = await conn.cursor()
    
    pw = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    await cur.execute(
        'UPDATE users SET password = %s WHERE login = %s',
        (pw, 'admin')
    )
    await conn.commit()
    print(f'Updated admin password: {pw}')
    
    await cur.close()
    conn.close()

asyncio.run(fix())
