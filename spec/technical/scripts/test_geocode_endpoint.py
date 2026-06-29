"""Test geocode endpoint via API (P1-017)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

BASE = "http://localhost:8000/rao/api"

token = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"}).json()["access_token"]

tests = [
    "Kłobucka 6B Warszawa",
    "ul. Kłobucka 6B, 02-699 Warszawa",
    "Magdalenka",
    "Bydgoszcz Jana Pawła II 115",
    "Cukiernicza 16, 05-506 Kolonia Lesznowola",
    "Bogatka 83-011",
]

for addr in tests:
    r = requests.post(
        f"{BASE}/integrations/geocode",
        headers={"Authorization": f"Bearer {token}"},
        json={"address": addr},
    )
    print(f"Q: {addr!r}")
    if r.status_code == 200:
        data = r.json()
        print(f"  lat={data.get('lat')} lon={data.get('lon')}")
        a = data.get('address') or {}
        print(f"  city={a.get('city')} town={a.get('town')} village={a.get('village')} hamlet={a.get('hamlet')}")
        print(f"  postcode={a.get('postcode')}")
    else:
        print(f"  ERROR {r.status_code}: {r.text[:200]}")
    print()
