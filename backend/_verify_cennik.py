"""Weryfikuj cenniki kaskadowe i logikę _build_positions_and_fees."""
import seed_demo_data as s

print("=== CENNIKI_KASKADOWE ===")
for name, data in s.CENNIKI_KASKADOWE.items():
    print(f"\n{name}:")
    for w in data["warunki"]:
        print(f"  rate1={w['rate1']}, rate2={w['rate2']}, period_count={w['period_count']}, desc={w['description']}")

print("\n=== STAWKA_EFEKTYWNA (do rozliczeń) ===")
for name, stawka in s.STAWKA_EFEKTYWNA.items():
    print(f"  {name}: {stawka}")

print("\n=== ZESTAWY_USLUG (presety) ===")
for z in s.ZESTAWY_USLUG:
    print(f"\n[{z['contract_type']}] {z['group_name']} (default={z['is_default']})")
    for t in z['templates']:
        print(f"  - {t['name']} | art={t['article']} | price={t['default_price']}")

print(f"\n=== FIRMA_CONFIG ===")
for k, v in s.FIRMA_CONFIG.items():
    print(f"  {k}: {v}")

print(f"\n=== RATE_TYPES ({len(s.RATE_TYPES)}) ===")
for r in s.RATE_TYPES:
    print(f"  - {r['name']}: {r['description']}")
