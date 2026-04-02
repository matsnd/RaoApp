import asyncio
import aiomysql
import bcrypt

async def fix():
    conn = await aiomysql.connect(
        host='localhost', port=3306,
        user='rao_user', password='RaoPass2026!', db='rao_new'
    )
    h = bcrypt.hashpw(b'Admin123!', bcrypt.gensalt()).decode()
    cur = await conn.cursor()
    await cur.execute('UPDATE users SET password=%s WHERE login=%s', (h, 'admin'))
    await conn.commit()
    print('done:', h[:25])
    conn.close()

asyncio.run(fix())
