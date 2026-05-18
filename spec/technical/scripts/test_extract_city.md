# test_extract_city.py

## Opis
Skrypt testowy do weryfikacji funkcji `extract_city()` z `backend/explorer/router.py`. Testuje różne formaty adresów polskich.

## Użycie

```bash
cd spec/technical/scripts
python test_extract_city.py
```

## Wymagania
- Backend musi być dostępny (import z `explorer.router`)
- Funkcja `extract_city()` musi być zaimplementowana w `backend/explorer/router.py`

## Przypadki testowe
- Standardowe formaty z kodami pocztowymi (00-123 Warszawa)
- Miasto przed ulicą (Warszawa ul. Marszałkowska)
- Złożone adresy (Warszawa-Ursus, Warszawa, Wola)
- Różne formaty (ul. Krakowska 12, 00-123 Warszawa)
- Edge cases (pusty string, tylko ulica)
- Miasta w tekście (Niedaleko Warszawy)
- Wielowyrazowe miasta (Bielsko-Biała, Gorzów Wielkopolski)
- Dzielnice/obszary (Warszawa Praga-Północ)

## Wynik
```
🧪 Testowanie funkcji extract_city():
============================================================
✅ Input: 00-123 Warszawa, ul. Krakowska 12
   Expected: Warszawa             Got: Warszawa

...
============================================================
📊 Wyniki: 20 passed, 0 failed
🎉 Wszystkie testy przeszły!
```

## Użycie w RAO
- Development — weryfikacja poprawności ekstrakcji miasta z adresu
- Testing — regresja po zmianach w `extract_city()`
- Explorer — poprawne wyświetlanie miasta w explorerze kontrahentów/umów

## Powiązane
- Function: `backend/explorer/router.py::extract_city()`
- Integration: Nominatim (geocoding)