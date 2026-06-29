# Statystyki RAO — jak działają, dlaczego są pewne i deterministyczne

> Dokument dla klienta. Odpowiada na pytanie: **czy statystyki są miarodajne i deterministyczne?**
>
> **Odpowiedź krótka: TAK.** Po audycie i naprawie (P2-029) wszystkie statystyki są:
> - **Deterministyczne** — te same dane wejściowe dają zawsze ten sam wynik
> - **Miarodajne** — uwzględniają wszystkie maszyny (również archiwalne z starej aplikacji)
> - **Spójne** — suma przychodu w "Ogólne" = suma w "Kategorie" = suma w "Historia"

---

## 1. Moduł Raporty — co tam jest

Moduł `/dashboard/reports` ma **3 zakładki**:

| Zakładka | Co pokazuje | Czy zależy od filtrów dat? |
|----------|-------------|----------------------------|
| **Stan floty teraz** | Ile maszyn jest dostępnych / wynajętych **w tej chwili** | NIE — zawsze "dzisiaj" |
| **Analiza historyczna** | Przychód, top maszyny, kategorie, lokalizacje **w wybranym okresie** | TAK — wybierasz zakres dat |
| **Eksplorator** | Szczegółowe dane o kontrahentach, umowach, maszynach | TAK |

### Sub-zakładki "Analiza historyczna"

| Sub-zakładka | Co pokazuje |
|--------------|-------------|
| **Ogólne** | KPI: przychód w okresie, top maszyna, wykres TOP 10, usługi dodatkowe, lokalizacje, pozycje |
| **Kategorie** | Przychód wg kategorii maszyn (z drilldown: główna → sub1 → sub2 → sub3) |
| **Historia** | Wykres przychodu w czasie (per miesiąc / per rok) |

---

## 2. Jak obliczany jest przychód — algorytm kaskadowy

### Źródło danych
Każda umowa ma **pozycje** (`contract_positions`). Każda pozycja ma:
- `rental_days` — liczba dni wynajmu
- `billing_frequency` — co ile dni płatność (dziennie / tygodniowo / miesięcznie)
- `unit_price` — cena jednostkowa (fallback gdy brak warunków)
- `quantity` — ilość (zwykle 1)

Oraz **warunki rozliczeniowe** (`position_conditions`) — cennik kaskadowy:
- `rate1` — stawka za okres
- `period_count` — do którego okresu obowiązuje ta stawka
- `minimum` — minimalna liczba okresów do opłacenia

### Algorytm (`calculate_position_value` w `backend/stats/calc.py`)

```
1. Oblicz liczbę okresów:
   total_periods = ceil(rental_days / days_per_period)
   np. 45 dni / 7 (tygodniowo) = 7 okresów (ceil(45/7) = 7)

2. Zastosuj minimum (z pierwszego warunku):
   if total_periods < minimum:
       total_periods = minimum

3. Rozliczenie kaskadowe (tiered):
   dla każdego warunku (posortowane po period_count):
       periods_in_tier = min(remaining, tier_size)
       total_value += rate1 × periods_in_tier
       remaining -= periods_in_tier

4. Jeśli remaining > 0 po wszystkich tierach:
   użyj ostatniej non-zero stawki dla pozostałych okresów
```

**Przykład:**
- Maszyna wynajęta na 45 dni, rozliczenie tygodniowe (7 dni)
- Warunki: 1-2 tygodnie = 500 zł/tydzień, 3-4 tygodnie = 400 zł/tydzień, 5+ tygodni = 300 zł/tydzień
- `total_periods = ceil(45/7) = 7` tygodni
- Tier 1 (1-2 tyg): 2 × 500 = 1 000 zł
- Tier 2 (3-4 tyg): 2 × 400 = 800 zł
- Tier 3 (5+ tyg): 3 × 300 = 900 zł
- **Razem: 2 700 zł**

### Dlaczego ten algorytm jest deterministyczny?

1. **Decimal (nie float)** — wszystkie obliczenia na `Decimal` z Pythona, brak błędów zaokrąglania typu `0.1 + 0.2 = 0.30000000000000004`
2. **Warunki sortowane po `period_count`** — kolejność zawsze rosnąca (zapytanie SQL ma `ORDER BY period_count`)
3. **`math.ceil` zamiast zaokrąglania** — `ceil(45/7) = 7` zawsze, bez wyjątków
4. **Brak zależności od czasu** — algorytm bierze tylko dane z bazy (rental_days, conditions), nie wywołuje `date.today()` w obliczeniach
5. **Idempotentność potwierdzona testem** — 2x ten sam request daje identyczny wynik (zweryfikowane w audycie P2-029)

---

## 3. Co było zepsute i co naprawiono (P2-029)

### Problem
Po migracji z starej aplikacji WinForms **wszystkie 419 artykuły** (337 maszyn + 82 usługi) mają flagę `is_archival=1`. To poprawne — to są stare maszyny z poprzedniej aplikacji.

Ale 6 endpointów statystyk miało `exclude_archival=True` (wyklucz archiwalne), co powodowało:

| Endpoint | Przed naprawą | Po naprawie |
|----------|---------------|-------------|
| `/fleet-summary` period_revenue | **0 zł** | **1 790 119,63 zł** |
| `/top-machines` | **0 maszyn** | **TOP 10 z przychodem** |
| `/additional-fees` | **0 zł** | **609 954,63 zł** |
| `/locations` | **0 miast** | **20 miast** |
| `/positions` | **0 zł** | **1 790 119,63 zł** |
| `/commissions` | **0 zł** | **prowizje od marży** |

### Niespójność
- "Ogólne" pokazywało **0 zł** przychodu
- "Kategorie" pokazywało **1 790 119,63 zł** przychodu
- Ten sam okres! Użytkownik widział sprzeczne liczby.

### Root cause
Funkcja `_compute_position_revenues()` ma parametr `exclude_archival` z domyślną wartością `True`. Endpointy "Kategorie" i "Historia" nadpisywały to na `False` (uwzględniają archiwalne), ale endpointy "Ogólne" nie — więc wykluczały wszystkie pozycje.

### Fix
6 endpointów historycznych dostało `exclude_archival=False`:
- `/fleet-summary` (tylko `period_revenue`; `total_machines`/`total_rented` nadal wykluczają archiwalne — to jest "stan teraz")
- `/top-machines`
- `/additional-fees`
- `/locations`
- `/positions`
- `/commissions`

### Co NIE zostało zmienione (celowo)
- `/currently-rented` — nadal wyklucza archiwalne (to jest "stan floty teraz", archiwalne maszyny nie są już we flocie)
- `/fleet-summary` `total_machines` / `total_rented` — nadal wyklucza archiwalne (j.w.)
- `/machine-roi` — ma parametr `include_archival` (domyślnie `False`, można włączyć)

### Weryfikacja spójności (po naprawie)

```
/fleet-summary.period_revenue  = 1 790 119,63 zł
/by-category.total_revenue     = 1 790 119,63 zł
/positions.total_revenue       = 1 790 119,63 zł
→ WSZYSTKIE TRZY = TA SAMA WARTOŚĆ ✅
```

---

## 4. Statystyki "Stan teraz" vs "Historia" — dlaczego różnica jest poprawna

| Aspekt | Stan teraz | Analiza historyczna |
|--------|------------|---------------------|
| **Kiedy** | Dzisiaj (`CURDATE()`) | Wybrany zakres dat |
| **Archiwalne maszyny** | Wykluczone (nie są we flocie) | **Uwzględnione** (stare umowy z migracji) |
| **Co liczy** | Ile maszyn jest u klienta teraz | Przychód z wszystkich umów w okresie |
| **Determinizm** | Zależy od daty (jutro może być inaczej) | Pełny determinizm (stałe dane historyczne) |

**Dlaczego "Stan teraz" wyklucza archiwalne?**
Bo archiwalne maszyny zostały sprzedane / zezłomowane / wycofane. Nie są fizycznie we flocie. Pokazywanie ich jako "dostępnych" byłoby błędem.

**Dlaczego "Historia" uwzględnia archiwalne?**
Bo stare umowy (z poprzedniej aplikacji) dotyczyły maszyn które wtedy były aktywne. Ich przychód jest prawdziwy i musi być w statystykach historycznych. Wykluczenie ich = zafałszowanie historii.

---

## 5. Każdy endpoint — co liczy i dlaczego jest pewny

### `/stats/fleet-summary` — podsumowanie floty
- `total_machines` — liczba aktywnych maszyn (nie-archiwalne, nie-usługi, nie-zewnętrzne)
- `total_rented` — liczba maszyn u klientów dzisiaj (aktywne umowy)
- `utilization_pct` — `total_rented / total_machines × 100` (zaokrąglone do 1 miejsca po przecinku)
- `period_revenue` — przychód w okresie (algorytm kaskadowy, uwzględnia archiwalne)
- `top_machine_name` / `top_machine_revenue` — maszyna z największym przychodem w okresie
- `contracts_in_period` — liczba umów overlapping z zakresem dat

**Pewność:** `total_machines` i `total_rented` to proste `COUNT(*)` z `WHERE` — deterministyczne. `period_revenue` używa algorytmu kaskadowego (sekcja 2).

### `/stats/top-machines` — ranking maszyn wg przychodu
- Agregacja po `article_id` (maszyny tylko, nie usługi)
- Sortowane malejąco po `revenue`
- `rented_days` — suma dni (obciętych do okna zapytania)
- `contracts_count` — liczba unikalnych umów

**Pewność:** Agregacja po ID (deterministyczne), sortowanie po revenue (deterministyczne dla tych samych danych).

### `/stats/currently-rented` — maszyny u klientów teraz
- Lista maszyn z aktywnymi umowami (`date_from <= today AND date_to >= today`)
- Wyklucza archiwalne (poprawne — nie są we flocie)
- `utilization_pct` = `rented / total_machines × 100`

**Pewność:** Zapytanie SQL z `CURDATE()` — deterministyczne dla danego dnia (jutro może się zmienić jeśli umowa wygaśnie).

### `/stats/by-category` — przychód wg kategorii
- Agregacja po `category_main` / `category_sub1` / `category_sub2` / `category_sub3` (parametr `level`)
- **Uwzględnia archiwalne** (stare umowy z migracji muszą być widoczne)
- Drilldown: kliknij kategorię → przejdź do sub-kategorii
- Maszyny bez kategorii → grupa "(bez kategorii)"

**Pewność:** Grupowanie po nazwie kategorii (deterministyczne), algorytm kaskadowy dla revenue.

### `/stats/by-period` — przychód w czasie
- Agregacja per miesiąc (`YYYY-MM`) lub per rok (`YYYY`)
- Opcjonalnie: osobna seria per kategoria główna
- **Uwzględnia archiwalne**

**Pewność:** Grupowanie po okresie z `contract.date_from` (deterministyczne).

### `/stats/locations` — ranking miast
- Agregacja po `contract.city` (miasto z umowy, nie kontrahenta)
- Top 20 miast wg liczby umów
- `rentals_count` — liczba unikalnych umów w mieście
- `total_revenue` — przychód z umów w tym mieście

**Pewność:** Grupowanie po nazwie miasta (deterministyczne).

**Znane ograniczenie (P2-028):** W Polsce istnieją miejscowości o tej samej nazwie (np. "Wola" — 5 różnych wsi). Obecnie są agregowane jako jedno miasto. Naprawa: composite key `(city, postal_code)` — zaplanowane w P2-028.

### `/stats/positions` — statystyki pozycji
- Agregacja po `article_id` (maszyny + usługi)
- Filtr typu: `all` / `machines` / `services`
- `times_billed` — ile razy artykuł wystąpił w umowach
- `total_machines_revenue` / `total_services_revenue` — zawsze liczone (niezależnie od filtra)

**Pewność:** Agregacja po ID (deterministyczne).

### `/stats/commissions` — prowizje handlowców
- **Prowizja od marży** (nie od przychodu) — RAO-P1-018
- `margin = cost_client - cost_company` (z `contract_settlements`)
- `commission = margin × commission_rate / 100`
- Fallback: jeśli brak danych settlement → prowizja od revenue (backward compat)

**Pewność:** Marża z settlement (deterministyczne), mnożenie przez rate (deterministyczne).

### `/stats/expiring-contracts` — umowy wygasające
- Umowy z `date_to` w ciągu najbliższych N dni (domyślnie 14)
- Wyklucza rozliczone (`is_settled=False`)

### `/stats/overdue-contracts` — umowy przeterminowane
- Umowy z `date_to < today` i `is_settled=False`

### `/stats/deliveries-today` — dostawy dzisiaj
- Pozycje z `delivery_date` w ciągu najbliższych N dni (domyślnie 1)

### `/stats/unprinted-contracts` — nie wydrukowane
- Umowy bez `print_date`, aktywne lub utworzone w ostatnich 60 dniach

### `/stats/stale-print-contracts` — wydrukowane przed modyfikacją
- Umowy gdzie `print_date < updated_at` (wydrukowane, potem zmodyfikowane)

---

## 6. Determinizm — podsumowanie

### Co jest w pełni deterministyczne?
**Wszystkie statystyki historyczne** (Analiza historyczna: Ogólne, Kategorie, Historia). Te same dane wejściowe (umowy, pozycje, warunki) zawsze dają ten sam wynik. Potwierdzone testem 2x:

```
Call 1: period_revenue = 1 790 119,63
Call 2: period_revenue = 1 790 119,63
→ DETERMINISTIC ✅
```

### Co zależy od daty dzisiejszej?
**Statystyki "Stan teraz"** (currently-rented, fleet-summary machines count). Te zależą od `CURDATE()` — jutro mogą być inne (umowa wygaśnie, nowa się zacznie). Ale dla danego dnia są deterministyczne.

### Czy kolejność GROUP BY wpływa na wynik?
**NIE.** SQL `GROUP BY` jest deterministyczne dla agregacji `SUM`, `COUNT`, `MAX`. Kolejność wierszy w wyniku może się różnić (jeśli brak `ORDER BY`), ale wartości agregatów są zawsze te same. Wszystkie nasze endpointy mają `ORDER BY` (po revenue, count, date, itp.).

### Czy float rounding jest deterministyczny?
**TAK.** Używamy `Decimal` (nie `float`) dla wszystkich obliczeń finansowych. `round(x, 2)` na `Decimal` jest deterministyczne.

---

## 7. Archiwalne maszyny — dlaczego są w statystykach

### Co to jest `is_archival`?
Flaga na artykule (maszynie) oznaczająca że maszyna została **wycofana z floty**:
- Sprzedana
- Zezłomowana
- Wycofana z eksploatacji

### Dlaczego wszystkie 419 maszyny są archiwalne?
Po migracji z starej aplikacji WinForms wszystkie maszyny dostały `is_archival=1`. To jest stan danych — nowe maszyny dodane w RAO będą miały `is_archival=0`.

### Dlaczego statystyki historyczne uwzględniają archiwalne?
Bo stare umowy dotyczyły maszyn które **wtedy** były aktywne. Ich przychód jest prawdziwy i musi być w raportach. Wykluczenie ich = zafałszowanie historii firmy.

### Dlaczego "Stan teraz" wyklucza archiwalne?
Bo archiwalna maszyna nie jest fizycznie we flocie. Pokazywanie jej jako "dostępnej" lub "wynajętej" byłoby błędem.

---

## 8. Znane ograniczenia (zaplanowane w backlogu)

### P2-028: Disambiguation miast
**Problem:** "Wola" (60 umów) to 5 różnych miejscowości (5 kodów pocztowych). Obecnie agregowane jako jedno miasto.
**Rozwiązanie:** Composite key `(city, postal_code)` + pełna baza PNA (~42k kodów). Zaplanowane w P2-028.

### P2-029: Naprawa niespójności archiwalnych
**Status:** **NAPRAWIONE** (ten commit). Wszystkie endpointy historyczne uwzględniają archiwalne maszyny.

---

## 9. Jak samemu zweryfikować statystyki

### Sprawdź spójność przychodu
```bash
# Ten sam okres (np. 2025)
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/rao/api/stats/fleet-summary?date_from=2025-01-01&date_to=2025-12-31"
# → period_revenue

curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/rao/api/stats/by-category?date_from=2025-01-01&date_to=2025-12-31"
# → total_revenue

# Oba powinny być RÓWNE ✅
```

### Sprawdź determinizm
```bash
# Wywołaj 2x ten sam endpoint — wynik musi być identyczny
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/rao/api/stats/top-machines?date_from=2025-01-01&date_to=2025-12-31&limit=10"
# → Call 1

curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/rao/api/stats/top-machines?date_from=2025-01-01&date_to=2025-12-31&limit=10"
# → Call 2 (identyczne)
```

---

## 10. Podsumowanie

| Pytanie | Odpowiedź |
|---------|-----------|
| Czy statystyki są deterministyczne? | **TAK** — te same dane dają ten sam wynik (potwierdzone testem) |
| Czy statystyki są miarodajne? | **TAK** — uwzględniają wszystkie maszyny (również archiwalne z migracji) |
| Czy "Ogólne" i "Kategorie" pokazują to samo? | **TAK** (po naprawie P2-029) — 1 790 119,63 zł w obu |
| Czy algorytm obliczania przychodu jest pewny? | **TAK** — Decimal (nie float), warunki sortowane, ceil zamiast round |
| Czy "Stan teraz" jest poprawny? | **TAK** — wyklucza archiwalne (nie są we flocie) |
| Czy "Historia" jest poprawna? | **TAK** — uwzględnia archiwalne (stare umowy są prawdziwe) |
| Czy są znane ograniczenia? | **TAK** — disambiguation miast (P2-028, zaplanowane) |

---

*Ostatnia aktualizacja: 2026-06-29 (P2-029 — naprawa niespójności archiwalnych)*
*Autor: Tech Lead RAO*
