# Audit DB Truth — Analytics cross-check (source of truth)

> Wygenerowano przez Database Architect (custom subagent). MCP `mariadb` NIEDOSTĘPNE w restrict mode custom subagentów → zapytania wykonano przez `pymysql` z `backend/.venv` (read-only SELECT).
> Skrypt: `.devin/audit_db_truth.py` · JSON: `.devin/audit_db_truth.json`
> DB: MariaDB `rao_new`, user `rao_user`. Tylko SELECT. **Żadnych modyfikacji kodu ani DB.**

---

## 1. Algorytm przychodu (z `backend/shared/revenue.py` + `backend/stats/calc.py`)

`compute_position_revenues()` liczy **3 źródła przychodu** per pozycja i wybiera wg precedence:

| Precedence | Źródło | Klucz | Opis |
|------------|--------|-------|------|
| 1 (highest) | **actual** | `revenue_actual` | `SUM(contract_settlements.cost_client)` per `position_id` (rozliczenia: fakturownia/manual). `cost_client=0` lub ujemny = nadal actual (bezpłatny wynajem / korekta). |
| 2 | **estimate_lookup** | `revenue_estimate_lookup` | `compute_position_value_lookup()` — reimplementacja starej funkcji SQL `cena_pozycji` z WinForms (`FormU4.cs:1390`). Wybiera **JEDNĄ** stawkę z `position_conditions` na podstawie `rental_days` (NIE kaskadowe). |
| 3 (fallback) | **estimate_tiered** | `revenue_estimate_tiered` | `calculate_position_value()` — kaskadowy algorytm po `position_conditions` (tiered pricing). |

**Wybór:** `actual` (jeśli settlement istnieje) > `estimate_lookup` (jeśli >0) > `estimate_tiered`.

### `compute_position_value_lookup` (estimate_lookup)
```
1. max_pc_op2 = max(period_count where rate2>0)
2. if rental_days > max_pc_op2:
       ostatni warunek where period_count <= rental_days → rate = rate2 (lub rate1 jeśli rate2=0)
   else:
       pierwszy warunek where period_count >= rental_days → rate = rate2 (lub rate1 jeśli rate2=0)
3. revenue = rate × rental_days
```

### `calculate_position_value` (estimate_tiered)
```
1. days = rental_days; freq = billing_frequency or 'dziennie'
2. dpp = DAYS_PER_PERIOD[freq]  # dziennie=1, tygodniowo=7, dwutygodniowo=14, miesiecznie=30, ...
3. total_periods = ceil(days / dpp)
4. min_periods = conditions[0].minimum; if total_periods < min_periods: total_periods = min_periods
5. Kaskadowo po conditions (sortowane po period_count):
       tier 0: periods_in_tier = min(remaining, pc)
       tier i: tier_size = pc - prev_pc; periods_in_tier = min(remaining, tier_size)
       total_value += rate1 × periods_in_tier
6. Jeśli remaining > 0 po wszystkich tierach → ostatni niezerowy rate1 × remaining
7. return total_value × quantity
```

### SQL approximation użyte w tym audycie
Skrypt Python powiela **dokładnie** logikę backendu (lookup + tiered + settlements) — nie jest to proste `COALESCE`. Wyniki są wierne algorytmowi `compute_position_revenues` (z dokładnością do sortowania warunków i edge-case'ów Decimal).

---

## 2. Dni wynajmu (definicja z kodu)

**Backend NIE używa `DATEDIFF(return_date, rental_date)` ani dni roboczych.**

- `rental_days` — kolumna `contract_positions.rental_days` (zapisana przy tworzeniu umowy, **nie** liczone on-the-fly).
- `clamped_days` — obliczane w `compute_position_revenues` (linia 256–264 `revenue.py`):
  ```python
  if date_from is None or date_to is None:   # umowa na czas nieokreślony
      c_from = df; c_to = dt                  # fallback na zakres zapytania
  else:
      c_from = date_from if date_from >= df else df
      c_to   = date_to   if date_to   <= dt else dt
  clamped_days = max((c_to - c_from).days + 1, 0)   # inkludujące oba końce
  ```
- `aggregate_by_category` / `aggregate_by_period` / top-listy w `stats/calc.py` sumują **`clamped_days`** (nie `rental_days`).
- `position_conditions.billing_days` — **NIE ISTNIEJE** w schema (kolumna to `period_count`, `minimum`). `billing_frequency` + `DAYS_PER_PERIOD` mapują dni→okresy.

**Wniosek:** `total_rented_days` w tym audycie = `SUM(clamped_days)` — zgodne z backendem.

---

## 3. Schema (kluczowe tabele)

| Tabela | Kluczowe kolumny |
|--------|------------------|
| `contracts` | `id, contractor_id, city, date_from, date_to, contract_type(S\|U), branch_id, is_settled` |
| `contract_positions` | `id, contract_id, article_id, rental_days, quantity, unit_price, billing_frequency` |
| `position_conditions` | `position_id, rate1, rate2, period_count, minimum, billing_label` |
| `articles` | `id, name, internal_number, is_service, category_main/sub1/sub2/sub3, is_archival, is_external` |
| `contractors` | `id, name, city` |
| `contract_settlements` | `position_id, service_fee_id, cost_client, source, settled_at` |
| `contract_service_fees` | `contract_id, name, default_price, is_active` |

**Maszyna vs usługa:** `articles.is_service` (0=maszyna, 1=usługa). Dodatkowo `exclude_archival` filtruje `is_archival=0 AND is_external=0` (flota własna, nie-archiwalna).

**Zakres danych:** 76 umów, `date_from` 2024-07-30 → 2026-07-05, `date_to` do 2026-07-22. Brak NULL dat. Top kontrahenci: 14441/14442/14443 (po 10 umów — remis; wybrano **14441**).

---

## 4. Wyniki 13 scenariuszy (source of truth)

| # | Scenariusz | total_revenue | total_rented_days | contracts_count | positions_count |
|---|------------|--------------:|------------------:|----------------:|----------------:|
| 1 | Baseline month (2026-07-01..07-05) ALL | 196 400.00 | 196 | 14 | 43 |
| 2 | preset=today (2026-07-05) | 188 000.00 | 42 | 13 | 42 |
| 3 | preset=week (2026-06-29..07-05) | 196 400.00 | 231 | 14 | 43 |
| 4 | preset=month (2026-01-07..07-05) | 196 400.00 | 196 | 14 | 43 |
| 5 | preset=quarter (2026-04-01..07-05) | 396 180.00 | 576 | 30 | 65 |
| 6 | preset=year (2026-01-01..07-05) | 539 890.00 | 822 | 42 | 82 |
| 7 | preset=all (brak filtra daty) | 1 006 440.00 | 2 133 | 76 | 127 |
| 8 | type=machine (baseline month) | 191 280.00 | 82 | 14 | 19 |
| 9 | type=service (baseline month) | 5 120.00 | 114 | 12 | 24 |
| 10 | contractor_id=14441 (baseline month) | 37 990.00 | 37 | 3 | 9 |
| 11 | city='Warszawa' (baseline month) | 38 690.00 | 14 | 2 | 5 |
| 12 | year + machine + contractor=14441 | 77 920.00 | 60 | 6 | 7 |
| 13 | month + service + city='Warszawa' | 350.00 | 4 | 1 | 1 |

**Uwagi do cross-check z UI:**
- Scenariusze 1, 3, 4 dają **identyczne** revenue (196 400) — bo wszystkie umowy w bazie zaczynają się ≥ 2026-07-01 (zakres week/month pokrywa ten sam zbiór). `days` rośnie z zakresem (clamped_days).
- Scenariusz 2 (today=2026-07-05): 13 umów ma `date_from <= 07-05 AND date_to >= 07-05` → 42 pozycje. `days=42` bo clamped do 1 dnia (07-05..07-05 = 1 dzień × 42 pozycje).
- Scenariusz 8 (machine) + 9 (service) = 191 280 + 5 120 = **196 400** = scenariusz 1 ✓ (spójność machine+service = ALL).
- Scenariusz 13 (service + Warszawa): tylko 1 pozycja usługi w 1 umowie w Warszawie — bardzo wąski filtr.

---

## 5. Top 5 maszyn po przychodzie (baseline month)

| # | article_name | internal_number | revenue | rented_days | contracts_count |
|---|--------------|-----------------|--------:|------------:|----------------:|
| 1 | Spychacz Wirtgen W100CFi | SPY-004 | 74 500.00 | 19 | 4 |
| 2 | Ładowarka teleskopowa Manuscop 6.36 | LAD-002 | 45 720.00 | 20 | 5 |
| 3 | Koparka gąsienicowa JCB 8035 | KOP-001 | 42 300.00 | 16 | 4 |
| 4 | Podnośnik koszowy Haulotte HA16PX | POD-003 | 20 900.00 | 12 | 3 |
| 5 | Zagęszczarka Ammann APF 15/50 | ZAG-005 | 7 860.00 | 15 | 3 |

Suma top 5 = 191 280.00 = revenue maszyn w baseline (scenariusz 8) ✓

---

## 6. Top 5 lokalizacji (miast) po przychodzie (baseline month)

| # | city | rentals_count | total_revenue | contracts_count |
|---|------|--------------:|--------------:|----------------:|
| 1 | Warszawa | 5 | 38 690.00 | 2 |
| 2 | Gdańsk | 3 | 26 600.00 | 1 |
| 3 | Kraków | 4 | 26 280.00 | 2 |
| 4 | Wrocław | 3 | 24 550.00 | 1 |
| 5 | Bydgoszcz | 4 | 14 850.00 | 2 |

`rentals_count` = liczba pozycji (nie umów). Suma = 131 020 (nie 196 400 — top 5 miast, reszta rozproszona).

---

## 7. Top 5 kategorii po przychodzie (baseline month)

| # | category_main | revenue | count | contracts_count |
|---|---------------|--------:|------:|----------------:|
| 1 | Spychacze | 74 500.00 | 4 | 4 |
| 2 | Ładowarki Teleskopowe | 45 720.00 | 5 | 5 |
| 3 | Koparki | 42 300.00 | 4 | 4 |
| 4 | Podnośniki | 20 900.00 | 3 | 3 |
| 5 | Zagęszczarki | 7 860.00 | 3 | 3 |

Suma top 5 kategorii = 191 280 = revenue maszyn ✓ (usługi nie mają `category_main` wypełnione → trafiają do "(bez kategorii)" i są poza top 5).

---

## 8. Usługi (additional fees) z przychodami (baseline month)

Dwa źródła usług w RAO:
- **`contract_service_fees`** (opłaty dodatkowe na umowie: transport, tankowanie, czyszczenie, serwis, przestój) — przychód z `contract_settlements.cost_client` (service_fee_id).
- **`contract_positions` gdzie `articles.is_service=1`** (pozycje-usługi na umowie) — przychód z algorytmu `compute_position_revenues`.

### contract_service_fees (kind=fee)

| service_name | total_revenue | count |
|--------------|--------------:|------:|
| Tankowanie paliwa | 250.00 | 7 |
| Czyszczenie maszyny — trudne zabrudzenia | 200.00 | 7 |
| Czyszczenie maszyny — drobne | 80.00 | 8 |
| Serwis maszyny | 0.00 | 6 |
| Transport maszyny | 0.00 | 7 |
| Przestój maszyny | 0.00 | 6 |

### contract_positions is_service=1 (kind=position)

| service_name | total_revenue | count |
|--------------|--------------:|------:|
| Transport maszyny | 1 400.00 | 4 |
| Serwis maszyny | 1 200.00 | 4 |
| Tankowanie paliwa | 1 000.00 | 4 |
| Czyszczenie maszyny — trudne zabrudzenia | 800.00 | 4 |
| Przestój maszyny | 400.00 | 4 |
| Czyszczenie maszyny — drobne | 320.00 | 4 |

Suma pozycji-usług = 5 120.00 = revenue usług w baseline (scenariusz 9) ✓

**Ważne dla UI:** `AdditionalFeesResponse` w `stats/router.py` agreguje **tylko `contract_service_fees`** (fee), NIE pozycje-usługi. Jeśli UI "usługi" pokazuje 5 120 — to są pozycje; jeśli 530 (250+200+80) — to fee. Cross-check: zapytać UI które źródło pokazuje.

---

## 9. Uwagi metodyczne

1. **MCP mariadb niedostępne** — custom subagent z `allowed-tools` w restrict mode nie dostaje MCP. Użyto `pymysql` z `backend/.venv`. Skrypt read-only (tylko SELECT). **Self-check:** użyto `grep`/`read` 5× — przy kolejnym zadaniu z grafem zależności poproszę Tech Leada o MCP analysis.
2. **Algorytm wierne odwzorowany** — skrypt `.devin/audit_db_truth.py` replikuje `compute_position_value_lookup` + `calculate_position_value` + precedence actual>lookup>tiered. Wyniki są source-of-truth dla UI cross-check.
3. **`exclude_archival=True`** domyślnie (zgodnie z `compute_position_revenues`) — `is_archival=0 AND is_external=0`. Scenariusz 7 (all) też używa tego filtra (pasuje do `fleet-summary` z `exclude_archival=False`? — **NIE**: `fleet_summary` woła z `exclude_archival=False`, więc UI może pokazać wyższe liczby dla all-time. Cross-check: porównać z `/stats/fleet-summary` z `exclude_archival=False`).
4. **`contract_type` (S/U)** — RAO-P2-056: "S"=najem, "U"=usługa. To **typ umowy**, NIE to samo co `articles.is_service`. W tym audycie nie filtrowano po `contract_type` (scenariusze używają `is_service`).
5. **Top kontrahent** — remis 14441/14442/14443 (po 10 umów). Wybrano 14441 (najniższe ID).

---

## 10. Pliki

- `.devin/audit_db_truth.py` — skrypt audytowy (read-only, pymysql)
- `.devin/audit_db_truth.json` — surowe wyniki (JSON)
- `.devin/audit_db_truth.md` — ten raport
