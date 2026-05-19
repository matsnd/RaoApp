# TERYT Postal Codes Generator

**Skrypt:** `teryt_postal_codes_generator.py`
**Data utworzenia:** 2026-05-19
**Zadanie:** RAO-P2-015

## Opis

Generator słownika kodów pocztowych dla głównych miast w Polsce. Zamiast pobierać dane z GUS TERYT API (wymaga rejestracji), generuje statyczną bazę 200+ kodów pocztowych z największych miast Polski.

## Użycie

```bash
cd spec/technical/scripts
python teryt_postal_codes_generator.py
```

## Wyniki

Skrypt generuje dwa pliki:
- `postal_codes_inserts.sql` — SQL inserty dla tabeli postal_codes (220 rekordów)
- `postal_codes.json` — JSON dump z tymi samymi danymi

## Struktura danych

Każdy rekord zawiera:
- `postal_code` — kod pocztowy format XX-XXX (np. "00-001")
- `city` — nazwa miasta (np. "Warszawa")
- `wojewodztwo` — województwo (np. "mazowieckie")
- `powiat` — powiat (np. "Warszawa")
- `gmina` — gmina (np. "Warszawa")

## Pokrycie

Baza zawiera kody pocztowe dla miast:
- Warszawa (40 kodów)
- Kraków (35 kodów)
- Wrocław (30 kodów)
- Poznań (30 kodów)
- Gdańsk (30 kodów)
- Łódź (30 kodów)
- Katowice (25 kodów)

Łącznie: 220 kodów pocztowych

## Integracja z RAO

1. Skopiuj wygenerowany `postal_codes_inserts.sql` do `backend/integrations/teryt/`
2. Użyj endpointu `POST /integrations/teryt/sync` aby załadować dane do bazy
3. Użyj endpointu `GET /integrations/postal-codes/{code}` aby pobrać miasto po kodzie pocztowym

## Rozszerzenie do pełnej bazy

W produkcji można rozszerzyć do pełnej bazy ~20k kodów pocztowych przez:
1. Rejestrację w GUS TERYT (teryt_ws1@stat.gov.pl)
2. Zakup komercyjnej bazy (np. Algolytics, Geopostcodes)
3. Użycie publicznego API (np. kodpocztowy.intami.pl, adresy.app)

## Uwagi

- Skrypt nie wymaga zależności zewnętrznych (bez requests, httpx)
- Jest deterministyczny — zawsze generuje te same dane
- Dane są wystarczające do developmentu i testów
- Format SQL jest kompatybilny z MariaDB