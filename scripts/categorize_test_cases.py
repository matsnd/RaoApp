#!/usr/bin/env python3
"""
Categorize extracted legacy contracts into unique test patterns.
Selects representative examples for E2E test generation.

Categories:
  1. single_rate_n    — N-type, single flat rate per day (e.g. "700,00zł / doba")
  2. single_rate_hour — N-type, single rate per hour (e.g. "110,00zł / godzina")
  3. tiered_2_n       — N-type, 2-tier rates (1-N dni + powyżej N)
  4. tiered_3_n       — N-type, 3-tier rates (1-N, N-M, powyżej M)
  5. single_day_n     — N-type, single day rate (1 dzień)
  6. multi_pos_n      — N-type, multiple positions (2+)
  7. flat_hourly_u    — U-type, flat hourly + każda kolejna
  8. flat_rate_u      — U-type, flat rate (do N godzin)
  9. multi_pos_u      — U-type, multiple positions
"""

import json
import os
import sys
from collections import defaultdict


def categorize(contract: dict) -> str | None:
    """Categorize a contract into a test pattern."""
    if contract["positions_count"] == 0:
        return None

    c_type = contract["contract_type"]
    pos_count = contract["positions_count"]
    pattern_types = set(contract["pattern_types"])

    if c_type == "U":
        if "flat_hourly" in pattern_types:
            if pos_count > 1:
                return "multi_pos_u"
            return "flat_hourly_u"
        if "flat_rate" in pattern_types:
            return "flat_rate_u"
        return None

    if c_type == "N":
        if pos_count > 1:
            return "multi_pos_n"

        if "tiered" in pattern_types and "tiered_above" in pattern_types:
            # Count tiers
            total_conds = contract["conditions_count"]
            if total_conds >= 3:
                return "tiered_3_n"
            return "tiered_2_n"

        if "single_day" in pattern_types:
            return "single_day_n"

        if "single_rate" in pattern_types:
            # Check if it's hourly or daily
            for p in contract["positions"]:
                for c in p["conditions"]:
                    if "godzin" in (c.get("billing_label") or ""):
                        return "single_rate_hour"
            return "single_rate_n"

    return None


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Temp\legacy_pdfs\extracted_contracts.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else r"C:\Temp\legacy_pdfs\test_cases.json"

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Categorize all contracts
    categories = defaultdict(list)
    for c in data:
        cat = categorize(c)
        if cat:
            categories[cat].append(c)

    # Select best representative for each category
    # Best = has the most complete data (contractor with NIP, clear rate text, etc.)
    test_cases = {}
    for cat, contracts in sorted(categories.items()):
        # Sort by data completeness
        def completeness(c):
            score = 0
            if c.get("contractor") and c["contractor"].get("nip"):
                score += 10
            if c.get("contract_number"):
                score += 5
            if c.get("date_from"):
                score += 5
            if c.get("prepayment"):
                score += 3
            if c.get("delivery_address"):
                score += 3
            for p in c["positions"]:
                if p.get("article_name"):
                    score += 2
                if p.get("rental_days"):
                    score += 1
                if p.get("replacement_value"):
                    score += 1
                if p.get("conditions"):
                    score += len(p["conditions"])
            return score

        best = max(contracts, key=completeness)
        test_cases[cat] = {
            "example_file": best["filename"],
            "contract_number": best["contract_number"],
            "contract_type": best["contract_type"],
            "date_from": best["date_from"],
            "date_to": best["date_to"],
            "prepayment": best["prepayment"],
            "delivery_address": best["delivery_address"],
            "working_days_per_week": best["working_days_per_week"],
            "contractor": best["contractor"],
            "positions": best["positions"],
            "service_fees": best["service_fees"],
            "pattern_types": best["pattern_types"],
            "conditions_count": best["conditions_count"],
            "total_in_category": len(contracts),
        }

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"=== TEST CASE CATEGORIES ===")
    print(f"Total contracts: {len(data)}")
    print(f"Categories found: {len(test_cases)}")
    print()
    for cat, tc in sorted(test_cases.items()):
        print(f"  {cat}: {tc['total_in_category']} contracts, example: {tc['example_file']}")
        print(f"    contract: {tc['contract_number']} type={tc['contract_type']} conditions={tc['conditions_count']}")
        if tc["contractor"]:
            print(f"    contractor: {tc['contractor']['name'][:50]} NIP={tc['contractor']['nip']}")
        for i, p in enumerate(tc["positions"]):
            print(f"    pos {i+1}: {p['article_name'][:50]} days={p.get('rental_days')} conds={len(p['conditions'])}")
            for c in p["conditions"]:
                print(f"      cond: rate1={c['rate1']} rate2={c.get('rate2')} pf={c.get('period_from')} pt={c.get('period_to')} flat={c.get('is_flat_rate')} type={c['pattern_type']}")
        print()


if __name__ == "__main__":
    main()
