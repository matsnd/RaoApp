# RAO Backlog — Sprint 2026-07-21 →

> **Status:** Oczyszczony 2026-07-21 (31 tasków zarchiwizowanych → `archiwum/BACKLOG_SPRINT_20260711_20260721.md`)
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260711_20260721.md`
> **Decision log:** `spec/backlog/DECISION_LOG.md` — pełna historia decyzji (co, dlaczego, status)
> **Cel:** Nowe zadania będą dodawane na podstawie współpracy z klientem
> **Kontekst:** Aplikacja działa stabilnie na prod. User ma nowe uwagi — po czyszczeniu backlogu zostaną dodane.

---

## ℹ️ Zasady

- Nowe taski dodawane na podstawie wymagań klienta / operatora
- Format: YAML front-matter + sekcje (jak w poprzednim backlogu)
- Status flow: `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)`
- Po zakończeniu zadania → lokalny commit + update `DECISION_LOG.md`
- Każda decyzja architektoniczna/biznesowa → sekcja w `DECISION_LOG.md`
- Agent ustawia MAX `team-verified`; `user-verified`/`client-approved` = CZŁOWIEK, nigdy agent
- Sweep done→archiwum gdy BACKLOG > 400 linii

---

## 🚨 P0 — Production Blockers

*Brak aktywnych P0. Aplikacja działa stabilnie na prod (2026-07-21).*

---

## 🔴 P1 — Must-Have

### P1-201: Przedpłata w PDF — dopisek "brutto"

```yaml
id: P1-201
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/reports/templates/contract.html + contract_u.html
migration_impact: no
```

**Opis:** W szablonie PDF umowy (S i U) w górnej tabeli informacyjnej przedpłata wyświetla się jako "Przedpłata: 1 200,00 zł" — klient chce dopisek "brutto" po kwocie: "Przedpłata: 1 200,00 zł brutto".

**Zadania:**
1. `backend/reports/templates/contract.html` (linia 136) — dodać " brutto" po `{{ contract.prepayment_amount | money }}`
2. `backend/reports/templates/contract_u.html` (linia 126) — to samo

**Definition of Done:**
- [x] PDF umowy S pokazuje "Przedpłata: ... zł brutto"
- [x] PDF umowy U pokazuje "Przedpłata: ... zł brutto"
- [x] Brak zmian w innych sekcjach PDF
- [x] Smoke `01-login.spec.ts` zielony (zmiana w template HTML, nie dotyka kodu)

---

### P1-204: Niebieski pasek nagłówka PDF — marginesy boczne aligned z contentem

```yaml
id: P1-204
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/reports/templates (6 PDF: contract.html, contract_u.html, protocol_zo.html, protocol_zo_nodata.html, protocol_zo_u.html, protocol_zo_nodata_u.html)
migration_impact: no
```

**Opis:** Niebieski pasek nagłówka (`table.hdr` z `background: #1D2B53`) na PDF rozciągał się edge-to-edge (width: 100%). Na ekranie wygląda OK, ale drukarki obcinają boki (nie drukują do krawędzi). Klient chce żeby pasek zaczął się równo z contentem formularzy (z białymi marginesami bocznymi).

**Stan obecny (przed):**
- `table.hdr { width: 100%; }` — pełna szerokość strony
- `.hdr-left { padding: ... 11mm/14mm ... }` — tekst headera miał 11mm/14mm padding wewnętrzny (symulował margines, ale tło niebieskie szło do krawędzi)
- `.content { padding: ... 11mm/14mm ... }` — content miał 11mm (umowy) / 14mm (protokoły) margines boczny

**Fix:**
- `table.hdr { width: calc(100% - 22mm); margin: 0 11mm; }` (umowy) / `width: calc(100% - 28mm); margin: 0 14mm;` (protokoły) — niebieski pasek z marginesami = aligned z contentem
- `.hdr-left` / `.hdr-right` — padding wewnętrzny z 11mm/14mm → 10px (tekst nadal ma mały inset od krawędzi niebieskiego, ale nie podwójny)

**Zadania:**
1. `contract.html` — `table.hdr` + `.hdr-left` + `.hdr-right` (margin 11mm, padding 10px)
2. `contract_u.html` — to samo
3. `protocol_zo.html` — `table.hdr` + `.hdr-left` + `.hdr-right` (margin 14mm, padding 10px)
4. `protocol_zo_nodata.html` — to samo
5. `protocol_zo_u.html` — to samo
6. `protocol_zo_nodata_u.html` — to samo

**Definition of Done:**
- [x] Niebieski pasek nagłówka we wszystkich 6 PDF ma marginesy boczne = padding contentu
- [x] Pasek zaczyna się i kończy równo z contentem formularzy
- [x] Tekst w headerze zachowuje czytelny inset (10px od krawędzi niebieskiego)
- [x] Brak zmian w innych sekcjach PDF
- [x] Smoke `01-login.spec.ts` zielony (zmiana w template HTML/CSS)

---

### P1-203: Protokół S — usunąć tekst "poziom uzupełnienia zbiornika/naładowania"

```yaml
id: P1-203
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/reports/templates/protocol_zo.html + protocol_zo_nodata.html
migration_impact: no
```

**Opis:** W PDF protokołu S (z danymi i nodata) jest linia "poziom uzupełnienia zbiornika/naładowania: ......................................." — klient chce usunąć ten tekst, zostawić pustą linię żeby nie zakłócić porządku na formularzu.

**Zadania:**
1. `backend/reports/templates/protocol_zo.html:165` — usunąć tekst z `div.fuel-line`, zostawić pusty `&nbsp;` (zachować div dla layoutu)
2. `backend/reports/templates/protocol_zo_nodata.html:131` — to samo

**Definition of Done:**
- [x] PDF protokołu S (z danymi) nie ma tekstu "poziom uzupełnienia zbiornika/naładowania"
- [x] PDF protokołu S (nodata) nie ma tego tekstu
- [x] Pusta linia zachowana (layout bez zmian — `div.fuel-line` z `&nbsp;`)
- [x] Brak zmian w protokole U (nie miał tej linii)
- [x] Smoke `01-login.spec.ts` zielony (zmiana w template HTML)

---

### P1-202: Rozdzielenie `contracts.notes` na `notes_contract` + `notes_protocol`

```yaml
id: P1-202
status: triaged
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/contracts (model+schema+service) + backend/reports/templates (4 PDF) + frontend/ContractFormView + DB migracja
migration_impact: yes (ALTER TABLE contracts: ADD 2 + backfill + DROP old)
decisions:
  ui: 2 textarea obok siebie ("Uwagi do umowy" + "Uwagi do protokołu")
  migration: ADD 2 + backfill + DROP old notes
  backfill: notes -> notes_protocol (stare uwagi = uwagi do protokołu, bo obecnie notes był tylko na protokole)
```

**Kontekst (stan obecny — analiza 2026-07-21):**
- `contracts.notes` (TEXT, nullable) — jedna kolumna w DB (`backend/contracts/models.py:29`)
- **PDF umowy S** (`contract.html`): `contract.notes` **usunięte** z sekcji "Uwagi" (komentarz `Zg3: contract.notes usunięte z umowy — uwagi mają być tylko na protokole`). Sekcja "Uwagi" ma 4 sztywne akapity (Doba wynajmu, Zgłoszenie zwrotu, Naliczanie, Dokumentacja zdjęciowa) i tyle.
- **PDF umowy U** (`contract_u.html`): też usunięte (komentarz `Puste notes = pusty blok uwag`).
- **PDF protokołu S** (`protocol_zo.html:214` + `protocol_zo_nodata.html:164`): `{% if contract.notes %}<div ...>{{ contract.notes }}</div>{% endif %}` — wyświetla `contract.notes` w sekcji "UWAGI BOX".
- **PDF protokołu U** (`protocol_zo_u.html:192` + `protocol_zo_nodata_u.html:139`): to samo.
- **Formularz** (`ContractFormView.vue:206-208`): jedno textarea `form.notes`, label "Uwagi".
- **Backend schemas** (`contracts/schemas.py`): `notes` w ContractOut/ContractCreate/ContractUpdate + 2 w settlement-related.
- **Backend service** (`contracts/service.py:100`): `notes` w liście mutowalnych pól; `:660`, `:760` — kopiowanie `c.notes` w response.

**Cel:** Rozdzielić na 2 niezależne pola, żeby operator mógł wpisać różne uwagi na umowę i na protokół. Obecnie `notes` = tylko protokół (umowa ma 4 sztywne akapity i nie czyta `notes`). Po zmianie:
- `notes_contract` → renderowane na PDF umowy (S i U) pod 4 sztywnymi akapitami (lub zamiast, do ustalenia w implementacji)
- `notes_protocol` → renderowane na PDF protokołu (S i U, z nodata wariantami) — zachowanie obecne

**Zadania:**

**Faza 1 — DB (deterministyczna migracja):**
1. `spec/core/01_database.md` — zaktualizować DDL `contracts`: usunąć `notes TEXT`, dodać `notes_contract TEXT NULL` + `notes_protocol TEXT NULL`
2. `backend/contracts/models.py:29` — zastąpić `notes = Column(Text, nullable=True)` dwiema kolumnami
3. `backend/main.py` startup migrations — 4 operacje w jednej transakcji (forward-only, idempotentne):
   ```python
   # 1. ADD notes_contract (IF NOT EXISTS)
   await conn.execute(sa.text(
       "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS notes_contract TEXT NULL"
   ))
   # 2. ADD notes_protocol (IF NOT EXISTS)
   await conn.execute(sa.text(
       "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS notes_protocol TEXT NULL"
   ))
   # 3. Backfill: notes -> notes_protocol (tylko gdy notes_protocol IS NULL, żeby nie nadpisać przy re-run)
   await conn.execute(sa.text(
       "UPDATE contracts SET notes_protocol = notes "
       "WHERE notes IS NOT NULL AND notes_protocol IS NULL"
   ))
   # 4. DROP notes (IF EXISTS) — wymaga MariaDB 10.6+ dla IF EXISTS; fallback try/except
   try:
       await conn.execute(sa.text("ALTER TABLE contracts DROP COLUMN IF EXISTS notes"))
   except Exception:
       pass  # MariaDB <10.6 bez IF EXISTS — pominąć, kolumna zostanie (deprecated)
   ```
4. Weryfikacja: restart backendu × 2 (pierwszy = migracja, drugi = bez błędu "Duplicate column") + `DESCRIBE contracts` (brak `notes`, są `notes_contract` + `notes_protocol`)

**Faza 2 — Backend:**
5. `backend/contracts/schemas.py` — zastąpić `notes` przez `notes_contract` + `notes_protocol` w ContractOut/Create/Update (linie 230, 267, 314, 362, 391, 403, 410)
6. `backend/contracts/service.py:100` — zaktualizować listę mutowalnych pól (zastąpić `notes` przez 2 nowe)
7. `backend/contracts/service.py:660, 760` — zaktualizować response (kopiować `notes_contract` + `notes_protocol`)
8. `backend/migrate.py` (skrypt migracji starych danych) — zaktualizować mapowanie `przedplata_kwota, przedplata_dokument, uwagi` → `..., notes_protocol` (linia 322, 345)

**Faza 3 — PDF templates:**
9. `backend/reports/templates/contract.html` — dodać render `contract.notes_contract` w sekcji "Uwagi" (po 4 sztywnych akapitach, z `<div class="inne-item">` lub podobnym stylem — decyzja wizualna w implementacji)
10. `backend/reports/templates/contract_u.html` — to samo
11. `backend/reports/templates/protocol_zo.html:214` — zmienić `contract.notes` → `contract.notes_protocol`
12. `backend/reports/templates/protocol_zo_nodata.html:164` — to samo
13. `backend/reports/templates/protocol_zo_u.html:192` — to samo
14. `backend/reports/templates/protocol_zo_nodata_u.html:139` — to samo

**Faza 4 — Frontend:**
15. `frontend/src/views/ContractFormView.vue:204-208` — zastąpić 1 textarea dwoma obok siebie (form-row-2):
    - "Uwagi do umowy" → `v-model="form.notes_contract"`
    - "Uwagi do protokołu" → `v-model="form.notes_protocol"`
16. `frontend/src/views/ContractFormView.vue:1123` — `notes: ''` → `notes_contract: '', notes_protocol: ''` w `initialForm`
17. `frontend/src/views/ContractFormView.vue:1675` — zaktualizować listę białych pól mutowalnych (zastąpić `notes` przez 2 nowe)
18. `frontend/src/stores/contracts.ts` (jeśli jest typ `Contract`) — zaktualizować typ
19. `frontend/src/views/ArchiveView.vue:117` — jeśli pokazuje `prepayment_amount`, sprawdzić czy nie pokazuje też `notes` (zaktualizować jeśli tak)
20. `frontend/src/stores/archive.ts:24, 103` — zaktualizować typ jeśli ma `notes`

**Faza 5 — Weryfikacja:**
21. `pytest -x --tb=short` — backend testy (po aktualizacji testów używających `notes`)
22. `vue-tsc --noEmit` — frontend typecheck
23. Smoke `e2e/tests/01-login.spec.ts` — zielony
24. Manual: wygeneruj PDF umowy S z `notes_contract` wypełnione → uwagi na umowie; wygeneruj protokół S z `notes_protocol` → uwagi na protokole; oba puste → brak uwag na PDF
25. Regresja: PDF umowy bez zmian w 4 sztywnych akapitach; PDF protokołu bez zmian w stylu "UWAGI BOX"

**Ryzyka:**
- **DROP COLUMN `notes`** = hard stop wg reguł (reguła nienaruszalna #6: DROP/TRUNCATE = hard stop). User wyraźnie zaakceptował w pytaniu (2026-07-21) — OK.
- **MariaDB <10.6** — `DROP COLUMN IF EXISTS` nieobsługiwane. Fallback `try/except` — kolumna `notes` zostanie w DB (deprecated), kod jej nie używa. Akceptowalne.
- **Skrypt `backend/migrate.py`** — jednorazowy skrypt migracji starych danych (legacy WinForms). Jeśli nie będzie już używany (prod już zmigrowane), można pominąć aktualizację. Zweryfikować w implementacji.
- **Stare umowy** — po backfill `notes_protocol = notes`, stare uwagi nadal na protokole (zachowanie obecne). `notes_contract = NULL` → puste na umowie (nowe pole, brak danych). Jeśli user chce skopiować stare uwagi też na umowę — dodatkowy backfill (ale user wybrał `notes -> notes_protocol` tylko).
- **4 sztywne akapity na umowie** — pozostają. `notes_contract` renderowane po nich. Jeśli user chce je usunąć/zastąpić — osobny task.

**Definition of Done:**
- [ ] DB: `contracts` ma `notes_contract` + `notes_protocol`, nie ma `notes` (lub `notes` deprecated gdy MariaDB <10.6)
- [ ] Backfill: stare `notes` skopiowane do `notes_protocol` (gdzie `notes_protocol IS NULL`)
- [ ] Restart backendu ×2 bez błędu (idempotentne)
- [ ] Backend schemas/service: `notes` zastąpione przez 2 nowe pola
- [ ] PDF umowy S/U: `contract.notes_contract` renderowane w sekcji "Uwagi"
- [ ] PDF protokołu S/U (z nodata): `contract.notes_protocol` renderowane (zachowanie obecne)
- [ ] Formularz umowy: 2 textarea obok siebie (Uwagi do umowy + Uwagi do protokołu)
- [ ] `pytest` zielony, `vue-tsc` zielony
- [ ] Smoke `01-login.spec.ts` zielony
- [ ] Manual: PDF umowy z `notes_contract` → uwagi widoczne; PDF protokołu z `notes_protocol` → uwagi widoczne
- [ ] Spec sync: `01_database.md`, `02_backend_api.md`, `03_frontend_screens.md`, `11_reports_stats.md`

---

---

## 🟡 P2 — Should-Have

*Brak aktywnych P2.*

---

## 🟢 P3 — Nice-to-Have

*Brak*

---

## 📝 Nowe uwagi (do triage'u)

> **Instrukcja:** Wklej nowe uwagi poniżej. Po analizie Tech Lead zaklasyfikuje je (P0/P1/P2/P3) i utworzy taski z YAML front-matter w odpowiednich sekcjach powyżej.

<!-- Wklej uwagi tutaj -->

---

## ✅ Done — Ukończone zadania

*Brak done w bieżącym sprincie. Historia w `archiwum/`.*
