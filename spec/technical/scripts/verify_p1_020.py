"""P1-020: Verify cascading conditions format in PDF."""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text
from contracts.service import format_position_conditions_cascading
from contracts.models import PositionCondition


async def main():
    async with AsyncSessionLocal() as db:
        # Find contracts with multiple conditions (cascading)
        r = await db.execute(text(
            "SELECT cp.contract_id, cp.article_name, COUNT(pc.id) as cond_count "
            "FROM contract_positions cp "
            "JOIN position_conditions pc ON pc.position_id = cp.id "
            "GROUP BY cp.contract_id, cp.article_name "
            "HAVING COUNT(pc.id) >= 2 "
            "ORDER BY cond_count DESC LIMIT 10"
        ))
        cascading = r.fetchall()
        print(f"=== Contracts with cascading conditions (>=2): {len(cascading)} ===")
        for row in cascading[:5]:
            print(f"  contract_id={row[0]} article={row[1]!r} conditions={row[2]}")

        if not cascading:
            print("No cascading conditions found — testing with synthetic data")
            # Test format function directly
            class MockCond:
                def __init__(self, period_count, rate1, rate2, billing_label):
                    self.period_count = period_count
                    self.rate1 = rate1
                    self.rate2 = rate2
                    self.billing_label = billing_label

            conds = [
                MockCond(2, 900.00, None, 'doba'),
                MockCond(None, None, 800.00, 'doba'),
            ]
            result = format_position_conditions_cascading(conds)
            print(f"\nSynthetic test (2 conditions):")
            print(result)
            print(f"\nExpected: '1 - 2 dni - 900,00 / doba\\npowyżej 2 dni - 800,00 / doba'")

            conds3 = [
                MockCond(3, 540.00, None, 'doba'),
                MockCond(16, 410.00, None, 'doba'),
                MockCond(None, None, 350.00, 'doba'),
            ]
            result3 = format_position_conditions_cascading(conds3)
            print(f"\nSynthetic test (3 conditions):")
            print(result3)
            return

        # Test with real conditions
        contract_id = cascading[0][0]
        r2 = await db.execute(text(
            "SELECT pc.period_count, pc.rate1, pc.rate2, pc.minimum, pc.rate_type_id "
            "FROM position_conditions pc "
            "JOIN contract_positions cp ON cp.id = pc.position_id "
            "WHERE cp.contract_id = :cid "
            "ORDER BY pc.period_count",
        ), {"cid": contract_id})
        rows = r2.fetchall()
        print(f"\n=== Real conditions for contract {contract_id} ===")
        for row in rows:
            print(f"  period_count={row[0]} rate1={row[1]} rate2={row[2]} min={row[3]} type={row[4]}")

        # Build PositionCondition objects and format
        conds = []
        for row in rows:
            c = PositionCondition()
            c.period_count = row[0]
            c.rate1 = row[1]
            c.rate2 = row[2]
            c.billing_label = 'doba'
            conds.append(c)
        result = format_position_conditions_cascading(conds)
        print(f"\n=== Formatted output ===")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
