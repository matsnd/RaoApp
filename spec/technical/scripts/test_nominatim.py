"""Test Nominatim API directly (P1-017 investigation)."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import httpx
import json

tests = [
    "ul. Kłobucka 6B, 02-699 Warszawa",  # full with ul. and postal
    "Kłobucka 6B Warszawa",                # without ul. and postal
    "Kłobucka 6B, 02-699 Warszawa",        # without ul.
    "Magdalenka",                          # village
    "Bydgoszcz Jana Pawła II 115",         # city + street
    "Cukiernicza 16, 05-506 Kolonia Lesznowola",  # full
    "Bogatka 83-011",                      # village + postal
]

for q in tests:
    try:
        r = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": "RAO-App/1.0", "Accept-Language": "pl"},
            timeout=10,
        )
        d = r.json()
        if d:
            addr = d[0].get("address", {})
            print(f"Q: {q!r}")
            print(f"  display: {d[0].get('display_name', '')[:100]}")
            print(f"  city={addr.get('city')} town={addr.get('town')} village={addr.get('village')} hamlet={addr.get('hamlet')}")
            print(f"  postcode={addr.get('postcode')} road={addr.get('road')} house={addr.get('house_number')}")
            print()
        else:
            print(f"Q: {q!r} → EMPTY")
            print()
    except Exception as e:
        print(f"Q: {q!r} → ERROR: {e}")
        print()
