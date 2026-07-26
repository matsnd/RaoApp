import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
import pymysql
from urllib.parse import urlparse
from config import settings

# RAO-SEC: Read DB credentials from settings (.env) — never hardcode passwords.
_url = urlparse(settings.RAO_DATABASE_URL)
conn = pymysql.connect(
    host=_url.hostname or 'localhost',
    user=_url.username or 'rao_user',
    password=_url.password or '',
    database=_url.path.lstrip('/') or 'rao_new',
    port=_url.port or 3306,
    charset='utf8mb4',
)
try:
    with conn.cursor() as cur:
        cur.execute('SELECT number, COUNT(*) FROM contracts GROUP BY number HAVING COUNT(*) > 1')
        dups = cur.fetchall()
        print('Duplicate contract numbers:', len(dups))
        for r in dups[:10]: print(r)

        cur.execute("SELECT id, number, branch_id FROM contracts WHERE branch_id IS NULL AND number LIKE '%G'")
        rows = cur.fetchall()
        print('branch_id=NULL with G suffix:', len(rows))
        for r in rows[:10]: print(r)

        cur.execute('SELECT COUNT(*) FROM contract_positions cp LEFT JOIN position_conditions pc ON cp.id = pc.position_id WHERE pc.id IS NULL')
        print('Positions without conditions:', cur.fetchone()[0])

        cur.execute('SELECT COUNT(*) FROM position_conditions WHERE rate1=0 AND rate2=0')
        print('Conditions with rate1=0 and rate2=0:', cur.fetchone()[0])

        cur.execute('SELECT COUNT(*) FROM contracts WHERE date_from IS NOT NULL AND date_to IS NOT NULL AND date_from > date_to')
        print('Contracts with date_from > date_to:', cur.fetchone()[0])

        cur.execute('SELECT COUNT(*) FROM contract_positions WHERE rental_days=0 OR rental_days IS NULL')
        print('Positions with rental_days=0 or NULL:', cur.fetchone()[0])

        cur.execute("SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS WHERE table_schema='rao_new' AND table_name='contracts' AND constraint_type='UNIQUE'")
        uniqs = cur.fetchall()
        print('Unique constraints on contracts:', uniqs)

        cur.execute('SELECT c.id, c.position_count, COUNT(cp.id) as real_count FROM contracts c LEFT JOIN contract_positions cp ON c.id=cp.contract_id GROUP BY c.id HAVING c.position_count != COUNT(cp.id)')
        mism = cur.fetchall()
        print('Contracts with mismatched position_count:', len(mism))
        for r in mism[:10]: print(r)

        cur.execute('SELECT COUNT(*) FROM contracts WHERE is_settled=1 AND settled_at IS NULL')
        print('Settled contracts without settled_at:', cur.fetchone()[0])

        cur.execute('SELECT COUNT(*) FROM contracts WHERE total_value IS NULL')
        print('Contracts with total_value NULL:', cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM contract_settlements cs JOIN contracts c ON cs.contract_id=c.id WHERE c.contract_type='S' AND cs.position_id IS NULL")
        print('Settlements for machine contracts with NULL position_id:', cur.fetchone()[0])
finally:
    conn.close()
