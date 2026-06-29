"""Analyze postal_codes.json + city duplication problem (P2 backlog item)."""
import sys, io, json, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


def analyze_postal_codes_json():
    d = json.load(open('integrations/teryt/postal_codes.json', encoding='utf-8'))
    print(f"=== postal_codes.json ===")
    print(f"Total entries: {len(d)}")
    print(f"Sample 3: {d[:3]}")
    cities = {}
    for x in d:
        c = x.get('city', '')
        cities.setdefault(c, []).append(x.get('postal_code', ''))
    print(f"Distinct cities: {len(cities)}")
    dupes = {c: codes for c, codes in cities.items() if len(codes) > 1}
    print(f"Cities with multiple postal codes: {len(dupes)}")
    print("Top 10 duplicated city names:")
    for c, codes in sorted(dupes.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {c}: {len(codes)} codes → {codes[:5]}{'...' if len(codes)>5 else ''}")


async def analyze_db_cities():
    async with AsyncSessionLocal() as db:
        # How many contracts have city but no postal_code?
        r = await db.execute(text(
            "SELECT "
            "SUM(CASE WHEN city IS NOT NULL AND city != '' AND (postal_code IS NULL OR postal_code = '') THEN 1 ELSE 0 END) as city_no_postal, "
            "SUM(CASE WHEN city IS NOT NULL AND city != '' AND postal_code IS NOT NULL AND postal_code != '' THEN 1 ELSE 0 END) as city_with_postal, "
            "SUM(CASE WHEN (city IS NULL OR city = '') THEN 1 ELSE 0 END) as no_city, "
            "COUNT(*) as total "
            "FROM contracts"
        ))
        row = r.fetchone()
        print(f"\n=== contracts.city / postal_code fill rate ===")
        print(f"  city + postal_code: {row[1]} ({row[1]/row[3]*100:.1f}%)")
        print(f"  city but NO postal: {row[0]} ({row[0]/row[3]*100:.1f}%)")
        print(f"  no city:            {row[2]} ({row[2]/row[3]*100:.1f}%)")
        print(f"  total:              {row[3]}")

        # Duplicate city names in stats — how many contracts share city name but might be different places?
        r2 = await db.execute(text(
            "SELECT city, COUNT(*) as cnt, COUNT(DISTINCT postal_code) as distinct_postals "
            "FROM contracts "
            "WHERE city IS NOT NULL AND city != '' "
            "GROUP BY city HAVING COUNT(*) > 1 "
            "ORDER BY cnt DESC LIMIT 20"
        ))
        print(f"\n=== Top 20 cities by contract count (duplication risk) ===")
        print(f"{'city':40s} {'contracts':>10s} {'distinct postals':>17s}")
        for row in r2.fetchall():
            print(f"  {row[0]:40s} {row[1]:>10d} {row[2]:>17d}")

        # Same city name, different postal codes — THE problem
        r3 = await db.execute(text(
            "SELECT city, COUNT(DISTINCT postal_code) as distinct_postals, "
            "GROUP_CONCAT(DISTINCT postal_code) as postals "
            "FROM contracts "
            "WHERE city IS NOT NULL AND city != '' AND postal_code IS NOT NULL AND postal_code != '' "
            "GROUP BY city HAVING COUNT(DISTINCT postal_code) > 1 "
            "ORDER BY distinct_postals DESC LIMIT 15"
        ))
        print(f"\n=== SAME city name, DIFFERENT postal codes (the disambiguation problem) ===")
        for row in r3.fetchall():
            print(f"  {row[0]:40s} → {row[1]} postals: {row[2][:80]}")


if __name__ == "__main__":
    analyze_postal_codes_json()
    asyncio.run(analyze_db_cities())
