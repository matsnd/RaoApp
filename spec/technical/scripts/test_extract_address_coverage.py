"""Test extract-address endpoint on real DB data (P1-017 coverage check)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import asyncio
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text
from integrations.nominatim import (
    clean_address, is_self_pickup, extract_postal_code,
)
from explorer.router import extract_city as extract_city_offline


async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text(
            "SELECT delivery_address FROM contracts "
            "WHERE delivery_address IS NOT NULL AND delivery_address != '' "
            "GROUP BY delivery_address ORDER BY COUNT(*) DESC LIMIT 100"
        ))
        rows = r.fetchall()

        stats = {"self_pickup": 0, "offline_both": 0, "offline_city_only": 0,
                 "offline_postal_only": 0, "nominatim_needed": 0, "none": 0}
        examples = {"self_pickup": [], "offline_both": [], "offline_city_only": [],
                    "offline_postal_only": [], "nominatim_needed": [], "none": []}

        for row in rows:
            addr = row[0]
            cleaned = clean_address(addr)
            if not cleaned:
                stats["none"] += 1
                continue
            if is_self_pickup(cleaned):
                stats["self_pickup"] += 1
                if len(examples["self_pickup"]) < 3:
                    examples["self_pickup"].append(addr)
                continue
            postal = extract_postal_code(cleaned)
            city_off = extract_city_offline(cleaned)
            city = None if city_off == "Nieznane" else city_off
            if city and postal:
                stats["offline_both"] += 1
                if len(examples["offline_both"]) < 3:
                    examples["offline_both"].append((addr, city, postal))
            elif city and not postal:
                stats["offline_city_only"] += 1
                if len(examples["offline_city_only"]) < 3:
                    examples["offline_city_only"].append((addr, city))
            elif postal and not city:
                stats["offline_postal_only"] += 1
                if len(examples["offline_postal_only"]) < 3:
                    examples["offline_postal_only"].append((addr, postal))
            elif not city and not postal:
                stats["nominatim_needed"] += 1
                if len(examples["nominatim_needed"]) < 5:
                    examples["nominatim_needed"].append(addr)

        total = sum(stats.values())
        print(f"=== Coverage analysis on {total} distinct delivery_address values ===\n")
        for k, v in stats.items():
            pct = v / total * 100 if total else 0
            print(f"  {k:25s}: {v:3d} ({pct:5.1f}%)")
        offline_coverage = stats["offline_both"] + stats["offline_city_only"] + stats["offline_postal_only"]
        print(f"\n  OFFLINE total (no Nominatim needed): {offline_coverage} ({offline_coverage/total*100:.1f}%)")
        print(f"  SELF_PICKUP (skip entirely):         {stats['self_pickup']} ({stats['self_pickup']/total*100:.1f}%)")
        print(f"  NOMINATIM fallback needed:           {stats['nominatim_needed']} ({stats['nominatim_needed']/total*100:.1f}%)")

        print("\n=== Examples ===")
        for k, exs in examples.items():
            if exs:
                print(f"\n  {k}:")
                for e in exs:
                    print(f"    {e!r}")


if __name__ == "__main__":
    asyncio.run(main())
