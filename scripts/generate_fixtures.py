#!/usr/bin/env python3
"""
Generate E2E test fixtures from extracted legacy PDF data.
Output: e2e/tests/legacy-fixtures.json

Each fixture contains:
  - category: pattern type name
  - source_file: legacy PDF filename
  - contract: contract metadata (type, dates, prepayment, delivery)
  - contractor: najemca data (name, nip, address)
  - positions: array of {article_name, rental_days, conditions}
  - service_fees: array of {name, amount_text}
  - total_in_category: how many legacy contracts match this pattern
"""

import json
import os
import sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else r"C:\Temp\legacy_pdfs\test_cases.json"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(__file__), "..", "..", "e2e", "tests", "legacy-fixtures.json"
)


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    fixtures = []
    for cat, tc in sorted(test_cases.items()):
        fixture = {
            "category": cat,
            "source_file": tc["example_file"],
            "total_in_category": tc["total_in_category"],
            "contract": {
                "contract_number": tc["contract_number"],
                "contract_type": tc["contract_type"],
                "date_from": tc["date_from"],
                "date_to": tc["date_to"],
                "prepayment": tc["prepayment"],
                "delivery_address": tc["delivery_address"],
                "working_days_per_week": tc["working_days_per_week"],
            },
            "contractor": {
                "name": tc["contractor"]["name"] if tc["contractor"] else None,
                "nip": tc["contractor"]["nip"] if tc["contractor"] else None,
                "street": tc["contractor"]["street"] if tc["contractor"] else None,
                "postal_code": tc["contractor"]["postal_code"] if tc["contractor"] else None,
                "city": tc["contractor"]["city"] if tc["contractor"] else None,
            },
            "positions": [],
            "service_fees": tc.get("service_fees", []),
        }

        for pos in tc["positions"]:
            fixture["positions"].append({
                "article_name": pos["article_name"],
                "rental_days": pos.get("rental_days"),
                "replacement_value": pos.get("replacement_value"),
                "conditions": pos["conditions"],
            })

        fixtures.append(fixture)

    # Write output
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(fixtures, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(fixtures)} fixtures -> {OUTPUT}")
    for fx in fixtures:
        print(f"  {fx['category']}: {fx['total_in_category']} contracts, {len(fx['positions'])} pos, source={fx['source_file']}")


if __name__ == "__main__":
    main()
