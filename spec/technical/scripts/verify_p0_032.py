"""Verify P0-032: PDF generation does not mutate fee.description in DB."""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text
from reports.service import build_contract_data


async def main():
    async with AsyncSessionLocal() as db:
        # Find a contract with service fees that have $1/$2 placeholders
        r = await db.execute(text(
            "SELECT csf.id, csf.contract_id, csf.description, csf.amount_from, csf.amount_to "
            "FROM contract_service_fees csf "
            "WHERE csf.description LIKE '%$1%' OR csf.description LIKE '%$2%' "
            "LIMIT 5"
        ))
        fees = r.fetchall()
        print(f"=== Found {len(fees)} fees with $1/$2 placeholders ===")
        for f in fees:
            print(f"  fee_id={f[0]} contract_id={f[1]} desc={f[2]!r} from={f[3]} to={f[4]}")

        if not fees:
            # Find any contract with service fees
            r2 = await db.execute(text(
                "SELECT contract_id FROM contract_service_fees LIMIT 1"
            ))
            cid = r2.scalar()
            if not cid:
                print("No service fees in DB — test skipped")
                return
        else:
            cid = fees[0][1]

        # Snapshot description BEFORE
        r3 = await db.execute(text(
            "SELECT id, description FROM contract_service_fees WHERE contract_id = :cid"
        ), {"cid": cid})
        before = {row[0]: row[1] for row in r3.fetchall()}
        print(f"\n=== BEFORE PDF gen (contract_id={cid}) ===")
        for fid, desc in before.items():
            print(f"  fee_id={fid} desc={desc!r}")

        # Generate PDF data
        data = await build_contract_data(db, cid)
        print(f"\n=== build_contract_data returned {len(data.get('fees', []))} fees ===")
        for fd in data.get("fees", []):
            fee = fd["fee"]
            print(f"  fee_id={fee.id} original_desc={fee.description!r} rendered_desc={fd['description']!r}")

        # Snapshot description AFTER
        r4 = await db.execute(text(
            "SELECT id, description FROM contract_service_fees WHERE contract_id = :cid"
        ), {"cid": cid})
        after = {row[0]: row[1] for row in r4.fetchall()}
        print(f"\n=== AFTER PDF gen (DB state) ===")
        for fid, desc in after.items():
            print(f"  fee_id={fid} desc={desc!r}")

        # Compare
        mutated = []
        for fid in before:
            if before[fid] != after[fid]:
                mutated.append((fid, before[fid], after[fid]))
        print(f"\n=== RESULT: {len(mutated)} mutated fees ===")
        for fid, b, a in mutated:
            print(f"  fee_id={fid} BEFORE={b!r} AFTER={a!r}")
        if not mutated:
            print("  ✅ PASS — no mutation, DB descriptions intact")
        else:
            print("  ❌ FAIL — DB descriptions were mutated!")


if __name__ == "__main__":
    asyncio.run(main())
