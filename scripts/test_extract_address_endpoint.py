"""Test extract-address endpoint via API (P1-017)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

BASE = "http://localhost:8000/rao/api"

token = requests.post(f"{BASE}/auth/login", json={"login": "admin", "password": "admin123"}).json()["access_token"]

tests = [
    "odbiór własny",
    "ul. Kłobucka 6B, 02-699 Warszawa",
    "Magdalenka",
    "Góra Kalwaria ul. Dominikańska 2/4",
    "Wirażowa 35, Warszawa",
    "27-220Mirzec Poddabrowa 48A",
    "Wroclaw, ul. Krzemieniecka 110 (wjazd z tyłu budynku)",
    "Gdańsku na ul. Szczęśliwa 3",
    "Metro\r\nSzeligowska 30C, 01-320 Warszawa",
    "Budowa SAS, Ul. Wrocławska 55-020 Wojkowice",
]

for addr in tests:
    r = requests.post(
        f"{BASE}/integrations/extract-address",
        headers={"Authorization": f"Bearer {token}"},
        json={"address": addr},
    )
    if r.status_code == 200:
        d = r.json()
        print(f"Q: {addr!r}")
        print(f"  city={d.get('city')!r} postal={d.get('postal_code')!r} self_pickup={d.get('self_pickup')} source={d.get('source')}")
    else:
        print(f"Q: {addr!r} → ERROR {r.status_code}: {r.text[:200]}")
    print()
