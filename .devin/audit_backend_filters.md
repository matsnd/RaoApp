# Audyt backendu Analytics — filtry endpointow stats/

**Data:** 2026-05-21
**Audytowany plik:** `backend/stats/router.py` (1236 linii)
**Helpery:** `backend/shared/revenue.py`, `backend/shared/locations.py`, `backend/stats/calc.py`
**Zakres:** read-only audyt (bez modyfikacji kodu)

Legenda:
- ✅ = parametr przyjmowany i faktycznie używany w logice
- ❌ = parametr NIE przyjmowany (brak w sygnaturze endpointu)
- ⚠️ = parametr przyjmowany ale ignorowany / nie działa

---

## Tabela 1 — Filtry query per endpoint

| Endpoint | contractor_id | city | article_type | internal_number | category_main | Inne parametry | Logika filtracji | Cache TTL |
|---|---|---|---|---|---|---|---|---|
| `/stats/fleet-summary` (L78) | ❌ | ❌ | ❌ | ✅ | ❌ | `date_from`, `date_to` | `internal_number` filtruje 3 zapytania SQL: total_machines (L100), rented_query (L124), all_pos Python (L135-136). Brak filtra contractor/city. | ✅ 5 min (key: df,dt,in) |
| `/stats/top-machines` (L187) | ✅ | ✅ | ❌ | ✅ | ❌ | `date_from`, `date_to`, `limit` | `_compute_position_revenues(service_filter=False)` (L209) → `_apply_position_filters(contractor_id, city, internal_number)` in-memory (L210-212). | ✅ 5 min (key: df,dt,in,cid,city,lim) |
| `/stats/currently-rented` (L240) | ❌ | ❌ | ❌ | ❌ | ❌ | (brak) | Czysto SQL: JOIN ContractPosition↔Contract↔Article WHERE active today (L274-282). Brak możliwości filtru. | ✅ 5 min (key: {}) |
| `/stats/machine-roi` (L309) | ❌ | ❌ | ❌ | ❌ | ❌ | `article_id` (wymagany), `date_from`, `date_to`, `include_archival` | `_compute_position_revenues(exclude_archival=False)` (L344) → Python filter `article_id` (L345). | ✅ 5 min (key: aid,df,dt,ia) |
| `/stats/additional-fees` (L366) | ✅ | ❌ | ❌ (hardcoded services) | ❌ | ❌ | `date_from`, `date_to` | `_compute_position_revenues(service_filter=True, exclude_archival=False)` (L382) → `_apply_position_filters(contractor_id)` (L383). City NIE przyjmowane. | ✅ 5 min (key: df,dt,cid) |
| `/stats/locations` (L411) | ✅ | ❌ | ❌ | ✅ | ❌ | `date_from`, `date_to`, `group_by=city\|pna` | `_compute_position_revenues(exclude_archival=False)` (L431) → `_apply_position_filters(contractor_id, internal_number)` (L432-434) → `aggregate_by_pna()` (L438). **City NIE jest parametrem ani filtrem** — agregacja po city jest wewnątrz `aggregate_by_pna` (group_by). | ✅ 5 min (key: df,dt,in,cid,gb) |
| `/stats/by-category` (L447) | ❌ | ❌ | ✅ | ❌ | ✅ (multi) | `level`, `date_from`, `date_to`, `category_sub1`, `category_sub2` | `_compute_position_revenues(service_filter, category_main_filter, category_sub1_filter, category_sub2_filter)` (L500-507) — filtry w SQL. `article_type` → `service_filter` mapping (L489). | ✅ 5 min (key: lvl,df,dt,cm,cs1,cs2,at) |
| `/stats/by-period` (L539) | ❌ | ❌ | ✅ | ❌ | ✅ (multi) | `granularity=month\|year`, `date_from`, `date_to` | `_compute_position_revenues(service_filter, category_main_filter)` (L582-587). `article_type` → `service_filter` (L571). | ✅ 5 min (key: g,df,dt,cm,at) |
| `/stats/positions` (L671) | ✅ | ✅ | ❌ (jest `type` nie `article_type`) | ❌ | ❌ | `type=all\|machines\|services` (alias position_type), `date_from`, `date_to`, `limit`, `offset`, `sort_by`, `sort_dir` | `_compute_position_revenues(service_filter=None)` (L729) → in-memory filter `type` (L736-739) → `_apply_position_filters(contractor_id, city)` (L742). **Brak `internal_number` mimo że inne KPI go mają.** | ✅ 5 min (key: t,df,dt,cid,city,lim,off,sb,sd) |
| `/stats/by-contract-type` (L824) | ✅ | ✅ | ❌ | ❌ | ❌ | `date_from`, `date_to` | `_compute_position_revenues(service_filter=None)` (L847) → `_apply_position_filters(contractor_id, city)` (L848) → `aggregate_by_contract_type`. | ❌ **BRAK CACHE** |
| `/stats/by-branch` (L875) | ✅ | ✅ | ❌ | ❌ | ❌ | `date_from`, `date_to` | `_compute_position_revenues(service_filter=None)` (L902) → `_apply_position_filters(contractor_id, city)` (L903) → `aggregate_by_branch`. | ❌ **BRAK CACHE** |
| `/stats/categories-list` (L609) | ❌ | ❌ | ❌ | ❌ | ❌ | (brak) | Czysto SQL: SELECT Category + COUNT(Article) GROUP BY category_id WHERE not archival (L635-640). | ✅ 5 min (key: {}) |
| `/stats/expiring-contracts` (L964) | ❌ | ❌ | ❌ | ❌ | ❌ | `days` (1-90, default 14) | SQL: WHERE date_to ∈ [today, today+days] AND is_settled=False (L982-985). | ❌ **BRAK CACHE** |
| `/stats/overdue-contracts` (L1010) | ❌ | ❌ | ❌ | ❌ | ❌ | (brak) | SQL: WHERE date_to < today AND is_settled=False (L1024-1027). | ❌ **BRAK CACHE** |
| `/stats/deliveries-today` (L1043) | ❌ | ❌ | ❌ | ❌ | ❌ | `lookahead` (1-7, default 1) | SQL: WHERE delivery_date ∈ [today, today+lookahead-1] (L1061). | ❌ **BRAK CACHE** |
| `/stats/unprinted-contracts` (L1076) | ❌ | ❌ | ❌ | ❌ | ❌ | (brak) | SQL: WHERE print_date IS NULL AND (date_to >= today OR created_at >= today-60d) (L1092-1095). | ❌ **BRAK CACHE** |
| `/stats/stale-print-contracts` (L1110) | ❌ | ❌ | ❌ | ❌ | ❌ | (brak) | SQL: WHERE print_date < updated_at AND (date_to >= today OR updated_at >= today-30d) (L1126-1131). | ❌ **BRAK CACHE** |
| `/stats/commissions` (L1149) | ❌ | ❌ | ❌ | ❌ | ❌ | `date_from`, `date_to` | `_compute_position_revenues(exclude_archival=False)` (L1186) + SQL settlement margin (L1163-1175). Brak filtra contractor_id (mimo że prowizja per salesperson). | ❌ **BRAK CACHE** |

**Podsumowanie cache:** 11/18 endpointów ma cache (TTL_STATS=5min). 7 NIE ma: by-contract-type, by-branch, expiring-contracts, overdue-contracts, deliveries-today, unprinted-contracts, stale-print-contracts, commissions.

---

## Tabela 2 — KPI endpoints: revenue / rented_days / contracts_count

| Endpoint | Revenue algorytm | rented_days | contracts_count |
|---|---|---|---|
| `/stats/fleet-summary` | `compute_position_revenues(exclude_archival=False)` (L134), `sum(p["revenue"])` (L137). Breakdown actual/estimate (L139-140). | **NIE LICZONE** — FleetSummary nie ma pola rented_days. | `contracts_in_period` = `COUNT(Contract)` SQL (L150-155) — **NIE distinct contract_id z pozycji**, raw count umów w okresie. |
| `/stats/top-machines` | `compute_position_revenues(service_filter=False, exclude_archival=False)` (L209), `agg[key]["revenue"] += p["revenue"]` (L223). | `sum(p["clamped_days"])` (L224) — **dni kalendarzowe** clamped do [df,dt], wszystkie pozycje (maszyny). | `len(set(contract_id))` (L225, L232) — distinct contract_id. |
| `/stats/positions` | `compute_position_revenues(service_filter=None, exclude_archival=False)` (L729), `agg[key]["revenue"] += p["revenue"]` (L762). | `sum(p["clamped_days"]) if not is_service else 0` (L763) — **TYLKO maszyny**, dni kalendarzowe. | `len(set(contract_id))` (L777) — distinct contract_id. `times_billed` = raw count pozycji (L765) — NIE distinct. |
| `/stats/by-category` | `compute_position_revenues(...)` (L500-507) → `aggregate_by_category` (L510), `sum(p["revenue"])` (calc.py L160). | `aggregate_by_category`: `agg[cat]["days"] += p.get("clamped_days", 0)` (calc.py L161) — **WSZYSTKIE pozycje (w tym usługi!)** — NIESPÓJNOŚĆ z positions/by-contract-type/by-branch. | `len(set(contract_id))` (calc.py L162). |
| `/stats/by-period` | `compute_position_revenues(...)` (L582-587) → `aggregate_by_period` (L589), `sum(p["revenue"])` (calc.py L224). | `aggregate_by_period`: `agg[key]["days"] += p.get("clamped_days", 0)` (calc.py L225) — **WSZYSTKIE pozycje (w tym usługi!)** — NIESPÓJNOŚĆ. | `len(set(contract_id))` (calc.py L226). |
| `/stats/by-contract-type` | `compute_position_revenues(...)` (L847) → `aggregate_by_contract_type` (L851), `sum(p["revenue"])` (calc.py L278). | `aggregate_by_contract_type`: `if not is_service: rented_days += clamped_days` (calc.py L276-277) — **TYLKO maszyny**. | `len(set(contract_id))` (calc.py L272). |
| `/stats/by-branch` | `compute_position_revenues(...)` (L902) → `aggregate_by_branch` (L910), `sum(p["revenue"])` (calc.py L347). | `aggregate_by_branch`: `if not is_service: rented_days += clamped_days` (calc.py L345-346) — **TYLKO maszyny**. | `len(set(contract_id))` (calc.py L342). |
| `/stats/additional-fees` | `compute_position_revenues(service_filter=True, exclude_archival=False)` (L382), `sum(p["revenue"])` (L390). | **NIE LICZONE** (AdditionalFeesResponse nie ma rented_days). | `times_billed = len(set(contract_id))` (L397) — **MISNOMER**: to distinct contracts, nie "times billed". Powinno się nazywać `contracts_count`. |
| `/stats/locations` | `compute_position_revenues(exclude_archival=False)` (L431) → `aggregate_by_pna` (L438), `bucket["rev"] += p["revenue"]` (locations.py L150). | **NIE LICZONE** (LocationStatItem nie ma rented_days). | `rentals_count = len(set(contracts))` (locations.py L173) — distinct contract_id. |
| `/stats/machine-roi` | `compute_position_revenues(exclude_archival=False)` (L344) → Python filter article_id (L345), `sum(p["revenue"])` (L347). | `sum(p["clamped_days"])` (L348) — wszystkie pozycje (ale article_id filter). | `len(set(contract_id))` (L349) — distinct contract_id. |
| `/stats/commissions` | `compute_position_revenues(exclude_archival=False)` (L1186) → `agg[sp_id]["revenue"] += p["revenue"]` (L1198). **PLUS** marża z `contract_settlements.cost_client - cost_company` (L1163-1175) — prowizja liczona od marży (L1210), revenue tylko backward-compat (L1213-1216). | **NIE LICZONE**. | `len(set(contract_id))` (L1222) — distinct contract_id per salesperson. |

### Kluczowe definicje

**`compute_position_revenues`** (`shared/revenue.py` L101-295):
- 3 źródła przychodu z precedence **actual > lookup > tiered** (L244-254):
  1. `actual` = `SUM(contract_settlements.cost_client)` per pozycja (L213-223)
  2. `estimate_lookup` = `compute_position_value_lookup` — reimplementacja `cena_pozycji` z WinForms (L46-98)
  3. `estimate_tiered` = `calculate_position_value` — kaskadowy algorytm z `stats/calc.py`
- Filtry SQL: `service_filter`, `exclude_archival`, `category_main_filter`, `category_sub1_filter`, `category_sub2_filter`, `contract_ids` (L164-180)
- `clamped_days = max((c_to - c_from).days + 1, 0)` (L264) — **dni kalendarzowe inclusive**, clamped do [df,dt]. Fallback df/dt gdy date_from/date_to=NULL (umowa na czas nieokreślony, L257-263).

**`aggregate_by_pna`** (`shared/locations.py` L31-181):
- Rollup po (city, gmina, powiat, wojewodztwo) z LEFT JOIN do `postal_codes` (L70-93)
- `group_by='city'` (default, RAO-P2-069): 1 wiersz per miasto, pomija bucket "(brak PNA)" (L164)
- `group_by='pna'`: 1 wiersz per PNA (rozbicie miasta)
- `rentals_count = len(set(contracts))`, `total_revenue = sum(revenue)`

---

## Odpowiedzi na 7 pytań

### Pytanie 1: Czy `/stats/fleet-summary` reaguje na contractor_id/city/article_type?

**NIE.** Potwierdzone podejrzenie.
- Sygnatura (L79-85): `date_from`, `date_to`, `internal_number`, `db`, `_`. Brak `contractor_id`, `city`, `article_type`.
- `internal_number` filtruje 3 zapytania: `machines_query` (L100), `rented_query` (L124), `all_pos` Python (L135-136).
- Cache key (L90): `{df, dt, in}` — spójny z przyjmowanymi parametrami (nie ma cid bo go nie ma).
- **Konsekwencja:** KPI floty na dashboardzie nie można przefiltrować po kontrahencie/mieście/typie artykułu. Jeśli frontend przekazuje te parametry — są ignorowane (FastAPI zwróci 422 jeśli są w query a nie w sygnaturze, lub zostaną odrzucone).

### Pytanie 2: Czy `/stats/positions` używa `article_type` do filtrowania?

**NIE.** Endpoint NIE ma parametru `article_type`.
- Ma `type` (alias dla `position_type`, L673) z wartościami `all|machines|services`.
- To jest filtr **kategorii maszyna/usługa** (czyli `Article.is_service`), NIE `article_type`.
- Filtracja in-memory po pobraniu wszystkich pozycji (L736-739):
  ```python
  if position_type == "machines":
      all_pos = [p for p in all_pos if not p["is_service"]]
  elif position_type == "services":
      all_pos = [p for p in all_pos if p["is_service"]]
  ```
- **Brak `internal_number`** w sygnaturze (L671-695) — niespójność z top-machines/locations/fleet-summary które go mają.

### Pytanie 3: Czy `/stats/by-category` wspiera contractor_id/city?

**NIE.** Potwierdzone podejrzenie.
- Sygnatura (L448-474): `level`, `date_from`, `date_to`, `category_main[]`, `category_sub1`, `category_sub2`, `article_type`. Brak `contractor_id`, `city`.
- Filtry przechodzą do `compute_position_revenues` jako SQL WHERE (L500-507), ale tylko po kategorii i service_filter.
- **Konsekwencja:** Nie można przefiltrować statystyk kategorii po kontrahencie ani mieście — np. "przychód po kategoriach dla kontrahenta X" wymagałoby dodania parametrów.

### Pytanie 4: Czy `/stats/locations` wspiera city?

**NIE.** Potwierdzone podejrzenie.
- Sygnatura (L412-419): `date_from`, `date_to`, `internal_number`, `contractor_id`, `group_by`. Brak `city`.
- `_apply_position_filters` wywołany bez `city` (L432-434).
- `city` pojawia się tylko w `aggregate_by_pna` jako **klucz agregacji** (group_by='city'), NIE jako filtr.
- **Konsekwencja:** Nie można poprosić o "lokalizacje tylko dla miasta Kraków". Można tylko pogrupować po city. Do filtrowania po konkretnym mieście trzeba użyć `/explorer/locations/city/{city}` (RAO-P2-069).

### Pytanie 5: Czy algorytm przychodu jest ten sam we wszystkich endpointach?

**TAK — spójne, bez duplikatów.**
- Wszystkie 11 endpointów KPI używa `compute_position_revenues` z `shared/revenue.py` (import L19: `from shared.revenue import compute_position_revenues as _compute_position_revenues`).
- Legacy kod usunięty (RAO-P2-028, komentarz L73-75). Re-eksport pod oryginalną nazwą dla `reports/service.py` zachowany.
- 3 źródła przychodu z precedence `actual > lookup > tiered` (revenue.py L244-254) — spójne wszędzie.
- **Jedyny wyjątek:** `/stats/commissions` dodatkowo oblicza **marżę** z `contract_settlements.cost_client - cost_company` (L1163-1175) i prowizję liczy od marży (L1210), ale `revenue` nadal z `compute_position_revenues` (L1186) — backward compat.

### Pytanie 6: Jak liczone są "dni wynajmu" w fleet-summary vs top-machines vs positions?

**NIESPÓJNOŚĆ ZNALEZIONA.**

| Endpoint | rented_days | Definicja |
|---|---|---|
| fleet-summary | **NIE LICZONE** | FleetSummary nie ma pola rented_days. |
| top-machines | `sum(clamped_days)` wszystkie pozycje | Dni kalendarzowe inclusive, clamped do [df,dt]. |
| positions | `sum(clamped_days) if not is_service else 0` | **TYLKO maszyny** (L763). |
| by-category | `sum(clamped_days)` wszystkie pozycje (calc.py L161) | **WSZYSTKIE pozycje w tym usługi** — ⚠️ BUG/niespójność. |
| by-period | `sum(clamped_days)` wszystkie pozycje (calc.py L225) | **WSZYSTKIE pozycje w tym usługi** — ⚠️ BUG/niespójność. |
| by-contract-type | `sum(clamped_days) if not is_service` (calc.py L276-277) | **TYLKO maszyny**. |
| by-branch | `sum(clamped_days) if not is_service` (calc.py L345-346) | **TYLKO maszyny**. |
| machine-roi | `sum(clamped_days)` wszystkie pozycje (L348) | Wszystkie, ale po filtrze article_id. |

**Definicja `clamped_days`** (revenue.py L257-264):
```python
c_from = p[13] if p[13] >= df else df   # Contract.date_from
c_to   = p[14] if p[14] <= dt else dt   # Contract.date_to
# fallback: df/dt gdy date_from/date_to=NULL (umowa na czas nieokreślony)
clamped_days = max((c_to - c_from).days + 1, 0)
```
To są **dni kalendarzowe inclusive** (np. 1-31 stycznia = 31 dni), NIE robocze. Clamped do zakresu [df, dt].

**Niespójność:** `aggregate_by_category` (calc.py L161) i `aggregate_by_period` (calc.py L225) sumują `clamped_days` dla WSZYSTKICH pozycji łącznie z usługami, podczas gdy `aggregate_by_contract_type` (L276-277), `aggregate_by_branch` (L345-346) i `/stats/positions` (L763) liczą `rented_days` TYLKO dla maszyn (`if not is_service`). Komentarz w calc.py L275 ("rented_days liczone tylko dla maszyn (usługi mają billing != DAILY)") dokumentuje intencję, ale `aggregate_by_category` i `aggregate_by_period` tej intencji nie przestrzegają.

### Pytanie 7: Czy cache key uwzględnia WSZYSTKIE parametry filtru?

**TAK dla endpointów z cache — spójne.** Ale 7 endpointów NIE ma cache w ogóle.

| Endpoint | Cache? | Key zawiera | Spójne? |
|---|---|---|---|
| fleet-summary | ✅ | df, dt, in | ✅ (nie ma cid bo nie przyjmuje) |
| top-machines | ✅ | df, dt, in, cid, city, lim | ✅ |
| currently-rented | ✅ | {} | ✅ (brak parametrów) |
| machine-roi | ✅ | aid, df, dt, ia | ✅ |
| additional-fees | ✅ | df, dt, cid | ✅ (nie ma city bo nie przyjmuje) |
| locations | ✅ | df, dt, in, cid, gb | ✅ |
| by-category | ✅ | lvl, df, dt, cm, cs1, cs2, at | ✅ |
| by-period | ✅ | g, df, dt, cm, at | ✅ |
| positions | ✅ | t, df, dt, cid, city, lim, off, sb, sd | ✅ |
| categories-list | ✅ | {} | ✅ |
| **by-contract-type** | ❌ | — | **BRAK CACHE** — endpoint agreguje pełny zbiór pozycji, potencjalnie wolny. |
| **by-branch** | ❌ | — | **BRAK CACHE** — j.w. |
| **expiring-contracts** | ❌ | — | Zapytanie SQL lekkie, brak cache uzasadniony (alarmy). |
| **overdue-contracts** | ❌ | — | j.w. |
| **deliveries-today** | ❌ | — | j.w. |
| **unprinted-contracts** | ❌ | — | j.w. |
| **stale-print-contracts** | ❌ | — | j.w. |
| **commissions** | ❌ | — | **BRAK CACHE** — agregacja pozycji + settlement, potencjalnie wolny. |

**Wniosek:** Cache keys są spójne z przyjmowanymi parametrami (nie ma buga typu "cache nie uwzględnia contractor_id"). Ale `by-contract-type`, `by-branch`, `commissions` wykonują pełną agregację `_compute_position_revenues` bez cache — przy dużej liczbie umów mogą być wolne. Alarm-contracts (expiring/overdue/deliveries/unprinted/stale) słusznie nie mają cache (dane czasowo-wrażliwe).

---

## Znalezione problemy (podsumowanie)

1. **Niespójność `rented_days` dla usług** (BUG): `aggregate_by_category` i `aggregate_by_period` liczą dni dla usług, podczas gdy inne agregatory pomijają usługi. Lokalizacja: `stats/calc.py` L161, L225 (brak warunku `if not is_service`).

2. **Brak filtra contractor_id/city w `/stats/fleet-summary`** (GAP): KPI floty nie można przefiltrować po kontrahencie/mieście. Frontend może przekazywać te parametry ale zostaną odrzucone (422) lub zignorowane.

3. **Brak filtra contractor_id/city w `/stats/by-category` i `/stats/by-period`** (GAP): Nie można przefiltrować statystyk kategorii/okresów po kontrahencie ani mieście.

4. **Brak filtra `city` w `/stats/locations`** (GAP): Mimo że endpoint agreguje po city, nie pozwala filtrować po konkretnym mieście. Alternatywa: `/explorer/locations/city/{city}`.

5. **Brak `internal_number` w `/stats/positions`** (NIESPÓJNOŚĆ): Inne KPI (top-machines, locations, fleet-summary) mają `internal_number`, positions nie.

6. **MISNOMER `times_billed` w `/stats/additional-fees`** (L397): Wartość to `len(set(contracts))` = distinct contracts, nie "times billed". Powinno się nazywać `contracts_count`.

7. **Brak cache w `/stats/by-contract-type`, `/stats/by-branch`, `/stats/commissions`** (PERF): Agregują pełny zbiór pozycji bez cache.

8. **`contracts_in_period` w fleet-summary** (L150-155): Liczone jako `COUNT(Contract)` SQL, NIE jako `distinct contract_id` z pozycji. Spójne logicznie (umowy w okresie), ale inne niż `contracts_count` w innych KPI (które liczą distinct contract_id z pozycji).

## MCP usage
- MCP tools: N/A (subagent nie ma dostępu)
- Tech Lead MCP context: NIE (brak wyników MCP w prompcie)
- grep count: 2 (wyszukanie funkcji w calc.py + wzorce w explorer/router.py)
