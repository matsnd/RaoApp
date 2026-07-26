"""RAO-P2-071: Clean live tables after archiving.

Usuwa WSZYSTKIE rekordy z tabel live (children-first, FK-safe).
Zachowuje: users, company, postal_codes, rate_types, salespeople, branches,
            categories, contractors, contractor_addresses, fee_preset_groups.

Użycie:
    cd backend && python clean_live_tables.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
from sqlalchemy import text
from database import engine


async def clean():
    print("=" * 60)
    print("RAO-P2-071: Clean live tables (post-archive)")
    print("=" * 60)

    async with engine.begin() as conn:
        # Children-first (FK order)
        tables = [
            "contract_settlements",
            "contract_service_fees",
            "position_conditions",
            "contract_positions",
            "article_reservations",
            "contract_costs",
            "deliveries",
            "article_rate_preset_items",
            "article_rate_presets",
            "service_fee_templates",
            "contracts",
            "articles",
        ]
        for t in tables:
            result = await conn.execute(text(f"DELETE FROM `{t}`"))
            print(f"  {t}: {result.rowcount} rows deleted")

    print("\n" + "=" * 60)
    print("DONE — live tables cleaned")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(clean())
