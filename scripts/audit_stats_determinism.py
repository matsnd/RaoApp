"""Audit stats determinism — compare API results with raw DB queries (P2-029)."""
import os
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import asyncio, requests, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import AsyncSessionLocal
from sqlalchemy import text
from decimal import Decimal

BASE = "http://localhost:8000/rao/api"


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal): return float(o)
        return super().default(o)


async def audit_fleet_summary():
    """Compare /stats/fleet-summary with raw DB counts."""
    token = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("=" * 70)
    print("AUDIT 1: /stats/fleet-summary")
    print("=" * 70)

    # API response
    r = requests.get(f"{BASE}/stats/fleet-summary", headers=headers)
    api = r.json()
    print(f"API: total_machines={api['total_machines']}, total_rented={api['total_rented']}, "
          f"utilization_pct={api['utilization_pct']}, period_revenue={api['period_revenue']}, "
          f"contracts_in_period={api['contracts_in_period']}")

    async with AsyncSessionLocal() as db:
        # Raw DB: total machines (not service, not archival, not external)
        q = await db.execute(text(
            "SELECT COUNT(*) FROM articles "
            "WHERE is_service=0 AND is_archival=0 AND is_external=0"
        ))
        db_total = q.scalar()
        print(f"DB:  total_machines={db_total} (is_service=0 AND is_archival=0 AND is_external=0)")

        # Raw DB: currently rented (active contracts)
        today = date.today().isoformat() if False else "CURDATE()"
        q2 = await db.execute(text(
            "SELECT COUNT(DISTINCT cp.article_id) FROM contract_positions cp "
            "JOIN contracts c ON c.id=cp.contract_id "
            "JOIN articles a ON a.id=cp.article_id "
            "WHERE a.is_service=0 AND a.is_archival=0 AND a.is_external=0 "
            "AND c.date_from <= CURDATE() AND c.date_to >= CURDATE()"
        ))
        db_rented = q2.scalar()
        print(f"DB:  total_rented={db_rented} (active contracts today)")

        # Raw DB: contracts in period (this month)
        q3 = await db.execute(text(
            "SELECT COUNT(*) FROM contracts "
            "WHERE date_from <= LAST_DAY(CURDATE()) "
            "AND date_to >= DATE_FORMAT(CURDATE(), '%Y-%m-01')"
        ))
        db_contracts = q3.scalar()
        print(f"DB:  contracts_in_period={db_contracts} (overlapping this month)")

        # Compare
        match_total = "✅" if db_total == api['total_machines'] else "❌ MISMATCH"
        match_rented = "✅" if db_rented == api['total_rented'] else "❌ MISMATCH"
        match_contracts = "✅" if db_contracts == api['contracts_in_period'] else "❌ MISMATCH"
        print(f"\nMATCH: total_machines={match_total}, total_rented={match_rented}, contracts={match_contracts}")

        # Revenue check — sum of position conditions for this month
        q4 = await db.execute(text(
            "SELECT SUM(pc.rate1 * LEAST(c.date_to, LAST_DAY(CURDATE())) - GREATEST(c.date_from, DATE_FORMAT(CURDATE(), '%Y-%m-01')) + 1) "
            "FROM position_conditions pc "
            "JOIN contract_positions cp ON cp.id=pc.position_id "
            "JOIN contracts c ON c.id=cp.contract_id "
            "WHERE c.date_from <= LAST_DAY(CURDATE()) AND c.date_to >= DATE_FORMAT(CURDATE(), '%Y-%m-01') "
            "AND pc.period_count=1"  # tylko pierwszy tier dla uproszczenia
        ))
        db_rev_approx = q4.scalar() or 0
        print(f"\nDB:  approx revenue (first-tier only, rough)={db_rev_approx}")
        print(f"API: period_revenue={api['period_revenue']}")
        print("(NOTE: API używa pełnego algorytmu kaskadowego, DB to tylko przybliżenie pierwszego tieru)")


async def audit_currently_rented():
    token = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "=" * 70)
    print("AUDIT 2: /stats/currently-rented")
    print("=" * 70)

    r = requests.get(f"{BASE}/stats/currently-rented", headers=headers)
    api = r.json()
    print(f"API: total_rented={api['total_rented']}, total_machines={api['total_machines']}, "
          f"utilization_pct={api['utilization_pct']}, items_count={len(api['items'])}")

    async with AsyncSessionLocal() as db:
        q = await db.execute(text(
            "SELECT COUNT(DISTINCT cp.article_id) FROM contract_positions cp "
            "JOIN contracts c ON c.id=cp.contract_id "
            "JOIN articles a ON a.id=cp.article_id "
            "WHERE a.is_service=0 AND a.is_archival=0 AND a.is_external=0 "
            "AND c.date_from <= CURDATE() AND c.date_to >= CURDATE()"
        ))
        db_rented = q.scalar()
        match = "✅" if db_rented == api['total_rented'] else "❌ MISMATCH"
        print(f"DB:  total_rented={db_rented} → {match}")

        # Check for duplicates in items
        article_ids = [i['article_id'] for i in api['items']]
        dupes = [aid for aid in set(article_ids) if article_ids.count(aid) > 1]
        if dupes:
            print(f"⚠️  DUPLICATE article_ids in items: {dupes[:5]}")
        else:
            print("✅ No duplicate article_ids in items")


async def audit_locations():
    token = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "=" * 70)
    print("AUDIT 3: /stats/locations (disambiguation problem)")
    print("=" * 70)

    r = requests.get(f"{BASE}/stats/locations", headers=headers)
    api = r.json()
    print(f"API: {len(api)} locations returned")
    for loc in api[:10]:
        print(f"  {loc['city']:40s} umów={loc['rentals_count']:3d} przychód={loc['total_revenue']}")

    async with AsyncSessionLocal() as db:
        # Check "Wola" problem
        q = await db.execute(text(
            "SELECT city, postal_code, COUNT(*) as cnt FROM contracts "
            "WHERE city='Wola' GROUP BY city, postal_code"
        ))
        print(f"\nDB: 'Wola' breakdown by postal_code:")
        for row in q.fetchall():
            print(f"  city={row[0]} postal={row[1]} count={row[2]}")

        # How many contracts have city but no postal_code?
        q2 = await db.execute(text(
            "SELECT "
            "SUM(CASE WHEN city IS NOT NULL AND city != '' AND (postal_code IS NULL OR postal_code='') THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN city IS NOT NULL AND city != '' AND postal_code IS NOT NULL AND postal_code != '' THEN 1 ELSE 0 END) "
            "FROM contracts"
        ))
        row = q2.fetchone()
        print(f"\nDB: contracts with city but NO postal: {row[0]}")
        print(f"DB: contracts with city AND postal:    {row[1]}")


async def audit_revenue_determinism():
    """Check if same query gives same result twice (idempotency)."""
    token = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "=" * 70)
    print("AUDIT 4: Revenue determinism (same query twice)")
    print("=" * 70)

    r1 = requests.get(f"{BASE}/stats/fleet-summary?date_from=2026-01-01&date_to=2026-06-30", headers=headers).json()
    r2 = requests.get(f"{BASE}/stats/fleet-summary?date_from=2026-01-01&date_to=2026-06-30", headers=headers).json()

    match = "✅ DETERMINISTIC" if r1['period_revenue'] == r2['period_revenue'] else "❌ NON-DETERMINISTIC"
    print(f"Call 1: period_revenue={r1['period_revenue']}")
    print(f"Call 2: period_revenue={r2['period_revenue']}")
    print(f"Result: {match}")

    # Check top-machines determinism
    r3 = requests.get(f"{BASE}/stats/top-machines?date_from=2026-01-01&date_to=2026-06-30&limit=10", headers=headers).json()
    r4 = requests.get(f"{BASE}/stats/top-machines?date_from=2026-01-01&date_to=2026-06-30&limit=10", headers=headers).json()
    revs1 = [m['revenue'] for m in r3]
    revs2 = [m['revenue'] for m in r4]
    match2 = "✅ DETERMINISTIC" if revs1 == revs2 else "❌ NON-DETERMINISTIC"
    print(f"\ntop-machines revenues match: {match2}")
    if revs1 != revs2:
        print(f"  Call 1: {revs1[:3]}")
        print(f"  Call 2: {revs2[:3]}")


async def audit_archival_handling():
    """Check how archival articles affect stats."""
    token = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "=" * 70)
    print("AUDIT 5: Archival articles in stats")
    print("=" * 70)

    async with AsyncSessionLocal() as db:
        # How many archival articles exist?
        q = await db.execute(text("SELECT COUNT(*) FROM articles WHERE is_archival=1"))
        archival_count = q.scalar()
        print(f"DB: archival articles: {archival_count}")

        # How many contracts have positions with archival articles?
        q2 = await db.execute(text(
            "SELECT COUNT(DISTINCT c.id) FROM contracts c "
            "JOIN contract_positions cp ON cp.contract_id=c.id "
            "JOIN articles a ON a.id=cp.article_id "
            "WHERE a.is_archival=1"
        ))
        contracts_with_archival = q2.scalar()
        print(f"DB: contracts with archival positions: {contracts_with_archival}")

        # Revenue from archival positions (rough)
        q3 = await db.execute(text(
            "SELECT COUNT(*) FROM contract_positions cp "
            "JOIN articles a ON a.id=cp.article_id WHERE a.is_archival=1"
        ))
        archival_positions = q3.scalar()
        print(f"DB: archival positions: {archival_positions}")

    # /fleet-summary excludes archival (exclude_archival=True default)
    r = requests.get(f"{BASE}/stats/fleet-summary?date_from=2025-01-01&date_to=2025-12-31", headers=headers).json()
    print(f"\nAPI /fleet-summary (2025, excludes archival): period_revenue={r['period_revenue']}")

    # /by-category includes archival (exclude_archival=False)
    r2 = requests.get(f"{BASE}/stats/by-category?date_from=2025-01-01&date_to=2025-12-31", headers=headers).json()
    print(f"API /by-category (2025, includes archival):   total_revenue={r2['total_revenue']}")
    print(f"  → DIFFERENCJA = archival revenue excluded from /fleet-summary but included in /by-category")


if __name__ == "__main__":
    from datetime import date
    asyncio.run(audit_fleet_summary())
    asyncio.run(audit_currently_rented())
    asyncio.run(audit_locations())
    asyncio.run(audit_revenue_determinism())
    asyncio.run(audit_archival_handling())
