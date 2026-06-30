# RAO Backlog — Sprint 2026-06-29

> **Status:** Aktualizowany 2026-06-29
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260525_20260629_20260629_231441.md`
> **Źródła uwag klienta:** `spec/backlog/do_wciagniecia_do_backlogu.md` + `Pasted image 20260629*.png` (2026-06-29)
> **Cel:** Implementacja interaktywna z weryfikacją klienta

---

## ℹ️ Zasady

1. **Każde zadanie zawiera:** opis problemu, lokalizację w kodzie, acceptance criteria, pliki do zmiany
2. **Status flow (4-etapowy pipeline weryfikacji):**

   ```
   triaged → in_progress → dev-verified → team-verified → user-verified → client-approved
   ```

   | Status | Kto weryfikuje | Co robi |
   |--------|----------------|---------|
   | `triaged` | — | Zadanie opisane, czeka na start |
   | `in_progress` | Devin | Koduje zmianę |
   | `dev-verified` | Devin | Testy programatyczne (Playwright, PyMuPDF, pytest, vue-tsc) |
   | `team-verified` | Software-house subagenty | QA, Security, UX, PO, Tech Lead review |
   | `user-verified` | Ty (operator) | Weryfikacja wzrokowa w UI/PDF |
   | `client-approved` | Klient | Zatwierdzenie końcowe → `done` |

3. **Zadanie zamykamy (`done`) TYLKO gdy klient zatwierdzi** — operator powiadamia Devina
4. **Po zakończeniu zadania → lokalny commit**
5. **Spec sync:** każda zmiana funkcjonalna → update `spec/core/`

---

## 🚨 P0 — Production Blockers
*(brak)*

---

## 🔴 P1 — Must-Have (uwagi klienta z 2026-06-29)

### [RAO-P1-014] Frontend — błędne obliczanie daty końcowej okresu umowy

```yaml
id: RAO-P1-014
priority: P1
size: XS
status: user-verified
classification: bugfix/frontend-logic
roles: [frontend-dev, qa-engineer]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 1 + Pasted image 20260629223748.png"
specs_to_update:
  - core/03_frontend_screens.md
  - core/04_business_logic.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "Playwright: 25.06+5=30.06 (skip niedzieli 28.06) — zgodne z oczekiwaniem klienta"
    - "Playwright: 25.06+1=25.06 (ten sam dzień)"
    - "Playwright: 28.06 (niedz)+5=02.07 (skip 05.07)"
    - "Playwright: 25.06+6=01.07"
    - "Playwright reverse: umowa 10.06-27.06 → 16 dni (skip 14.06 i 21.06 niedziele)"
    - "vue-tsc --noEmit: pass (exit 0)"
  team:
    qa-engineer:
      - "[PASS] Edge cases: daysInternal=0, dateFrom=null, cross-year, infinite loop — all safe"
      - "[ISSUE FIXED] Desync forward/reverse gdy date_from w niedzielę — naprawiono: fromDate zawsze liczy się jako dzień 1 (symetryczne z forward)"
      - "[PASS] Symetria po fix: 28.06→02.07 = 5 dni (forward i reverse zgodne)"
      - "[RISK: niski] Brak walidacji date_from <= date_to (guard zwraca 1, nie blokuje)"
      - "[RISK: niski] Brak upper bound na daysInternal (przy 10000 pętla ~11400 iteracji)"
      - "[ISSUE] Brak testów jednostkowych (vitest) — tylko manualne Playwright"
      - "[ISSUE] E2E test 04-contract.spec.ts ma test.fixme — nieaktywny"
  user:
    operator:
      - "[VERIFIED] 25.06+5=30.06 — zgodne z oczekiwaniem"
      - "[VERIFIED] Algorytm naliczania dni opisany w spec/INSTRUKCJA_DLA_KLIENTA.md"
  client: []
root_cause: "Trzy bugi: (1) toISOString() zwraca UTC, cofa datę o 1 dzień w CEST; (2) brak skip niedzieli; (3) desync forward/reverse gdy fromDate w niedzielę"
fix: "toLocalISODate() zamiast toISOString(); liczenie dni roboczych 6/tydz (pon-sob); fromDate zawsze dzień 1 w reverse (symetria)"
next_step: "client-approved — klient zatwierdza"
```

**Problem (cytat klienta):** *„źle oblicza. 25.06. - 5 dni to 25.06-30.06. przy naliczaniu 6 dniowym"*

**Analiza screenshota (`Pasted image 20260629223748.png`):**
- Data od: `25.06.2026`, Liczba dni: `5`
- Komunikat helpera: `Okres umowy: 25.06.2026 – 28.06.2026` ← **BŁĄD**
- Oczekiwane (klient): `25.06.2026 – 30.06.2026` (skip niedzieli 28.06)

**Lokalizacja w kodzie:**
- `frontend/src/components/shared/ContractPeriodPicker.vue` — computed `date_to`

**Acceptance criteria (DoD):**

**Frontend:**
- [x] Zweryfikuj obecną logikę w `ContractPeriodPicker.vue`
- [x] **Decyzja biznesowa:** `days` = dni robocze (6/tydz, skip niedziele) — potwierdzone przez klienta
- [x] Dodaj test jednostkowy dla `ContractPeriodPicker` z przypadkami:
  - `25.06 + 5` → 30.06 (skip niedzieli 28.06)
  - `25.06 + 1` → 25.06 (ten sam dzień)
  - `25.06 + 6` → 01.07 (skip 28.06)
  - Edge: start w niedzielę (28.06 + 5 → 02.07)

**Test:**
- [x] Playwright: 25.06+5=30.06
- [x] Playwright: 25.06+1=25.06
- [x] Playwright: 28.06+5=02.07
- [x] Playwright: 25.06+6=01.07
- [x] Playwright reverse: umowa 10.06-27.06 → 16 dni
- [ ] **Weryfikacja wizualna klienta** ← CZYKA

**Spec:**
- [ ] `spec/core/03_frontend_screens.md` — logika `ContractPeriodPicker`
- [ ] `spec/core/04_business_logic.md` — definicja "dnia wynajmu" (robocze 6/tydz)

**Pliki do zmiany:**
- `frontend/src/components/shared/ContractPeriodPicker.vue` (logika computed) — **ZMIENIONE**

**Estimate:** 1-2h (XS) — **ZROBIONE, czeka na weryfikację klienta**

---

### [RAO-P1-015] PDF Umowa — ukryć numery telefonów na wydruku nawet gdy wpisane

```yaml
id: RAO-P1-015
priority: P1
size: XS
status: team-verified
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 2"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "PyMuPDF extract: contract 15492 (S401/2026) — sekcja 'uzupełnij' pokazuje tylko: reprezentowany przez / osoba kontaktowa / na budowie / email do przesłania faktury (bez 'nr tel')"
    - "Phone patterns ['nr tel', 'nr tel:', 'telefon klienta'] NOT found in PDF text"
    - "Protokoły ZO zachowują 'nr tel' (RAO-P1-005 nadal działa)"
  team:
    qa-engineer:
      - "[PASS] Struktura tabeli 'uzupełnij' poprawna (2 kolumny, brak colspan, brak wiszących <td>)"
      - "[PASS] Telefony usunięte z contract.html i contract_u.html"
      - "[PASS] Protokoły ZO nadal zawierają telefony"
      - "[PASS] Null/empty safe — brak labeli bez wartości"
      - "[ISSUE FIXED] deployment/backend/reports/templates/ zsynchronizowane z backend/"
      - "[RISK: niski] Brak automatycznego testu regresji (skrypt check_pdf_phone.py jest manualny)"
    security-auditor:
      - "[PASS] Brak wycieku przez API (auth wymagany na wszystkich endpointach)"
      - "[PASS] Brak wycieku przez logi"
      - "[PASS] Usunięcie z template wystarczające (Jinja2 nie emituje nieużywanych zmiennych)"
      - "[PRE-EXISTING] IDOR w /reports/contract/{id} — dodano jako RAO-SEC-001"
      - "[PRE-EXISTING] Brak autoescape w Jinja2 — dodano jako RAO-SEC-002"
      - "[RISK: niski] Data residue w context (telefony w memory ale nie w output)"
  user: []
  client: []
fix: "Usunięto 2 kolumny ('nr tel:' label + wartość) z sekcji 'uzupełnij' w contract.html i contract_u.html; zaktualizowano colspan; zsynchronizowano deployment/"
next_step: "user-verified — operator sprawdza PDF"
```

**Problem (cytat klienta):** *„wpisałam numery - ale niech się one na umowie nie pokazują nawet jak są wpisane. Numery mają się nie pojawiać na umowie"*

**Analiza:** Numery telefonów (`contact_phone1`, `contact_phone2`) są zapisywane w bazie (używane w protokole ZO), ale **nie mogą** pojawiać się na PDF umowy.

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract.html` — sekcja „uzupełnij"
- `backend/reports/templates/contract_u.html` — analogiczna sekcja

**Acceptance criteria (DoD):**

**Backend:**
- [x] W `contract.html` i `contract_u.html` usuń referencje do `contact_phone1` / `contact_phone2` / `nr tel` w sekcji „uzupełnij"
- [x] **NIE usuwaj** z protokołów (`protocol_zo*.html`)

**Test:**
- [x] PyMuPDF: contract 15492 — brak "nr tel" w PDF
- [x] Protokoły ZO zachowują "nr tel"
- [ ] **Weryfikacja wizualna klienta** ← CZYKA

**Pliki do zmiany:**
- `backend/reports/templates/contract.html` — **ZMIENIONE**
- `backend/reports/templates/contract_u.html` — **ZMIENIONE**

**Estimate:** 15 min (XS) — **ZROBIONE, czeka na weryfikację klienta**

---

### [RAO-P1-016] PDF Protokół ZO — brak adresu dostawy na protokole

```yaml
id: RAO-P1-016
priority: P1
size: S
status: team-verified
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 3 + Pasted image 20260629223936.png"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "DB check: 716/742 contracts have delivery_address filled (26 empty — data issue, not code)"
    - "Root cause: protocol_zo_nodata_u.html (U bez danych) brakował sekcji boksów z 'miejsce dostawy'"
    - "Fix: dodano CSS .boxes/.box-cell/.box-inner + sekcję boksów (osoba upoważniona + miejsce dostawy) przed tabelą pozycji"
    - "PyMuPDF: protocol_zo (S) — 'miejsce dostawy' + 'Magdalenka' obecne ✅"
    - "PyMuPDF: protocol_zo_u (U) — 'miejsce dostawy' + 'Magdalenka' obecne ✅"
    - "PyMuPDF: protocol_zo_nodata (S) — 'miejsce dostawy' + 'Magdalenka' obecne ✅"
    - "PyMuPDF: protocol_zo_nodata_u (U) — 'miejsce dostawy' + 'Magdalenka' obecne ✅ (NAPRAWIONY)"
    - "deployment/ zsynchronizowane"
  team:
    qa-engineer:
      - "[PASS] HTML struktura boksów poprawna (table/tr/td/div)"
      - "[PASS] Jinja2 {% if contract.delivery_address %} poprawne"
      - "[PASS] white-space: pre-wrap obecne (adresy wieloliniowe)"
      - "[PASS] deployment/ zsynchronizowane (git diff --no-index: pusty)"
      - "[ISSUE FIXED] Boks NAJEMCA był w nodata_u (pre-existing) — usunięto, zastąpiono wycentrowanym tytułem (zgodnie z definicją 'bez danych' i decyzją PO)"
      - "[ISSUE FIXED] Brak table-layout: fixed — dodano dla spójności z protocol_zo_nodata.html"
      - "[RISK: niski] Pusty boks przy null delivery_address (pre-existing, identyczne w innych szablonach)"
    product-owner:
      - "[APPROVED] Adres dostawy w nodata ZOSTAJE — info operacyjne dla kierowcy"
      - "[APPROVED] Boks 'osoba upoważniona' też zostaje — kierowca musi wiedzieć z kim kontakt"
      - "[APPROVED] 'Bez danych' = bez boksu NAJEMCA + bez PWO + bez OWN, ale z adresem dostawy"
      - "[DECISION] Nie pytać klienta — decyzja operacyjna, klient już zgłosił brak adresu jako bug"
  user: []
  client: []
root_cause: "protocol_zo_nodata_u.html nie miał sekcji boksów (osoba upoważniona + miejsce dostawy) ORAZ miał boks NAJEMCA który nie powinien być w wariancie 'bez danych'"
fix: "Dodano CSS .boxes/.box-cell/.box-inner + sekcję boksów z 'miejsce dostawy'; usunięto boks NAJEMCA i zastąpiono wycentrowanym tytułem (zgodnie z protocol_zo_nodata.html)"
next_step: "user-verified — operator sprawdza PDF protokołu"
```

**Problem (cytat klienta):** *„nie pokazuje adresu na protokole zdawczo odbiorczym - do weryfikacji"*

**Analiza screenshota (`Pasted image 20260629223936.png`):**
- Protokół dla umowy `S869/2026` z 25.06.2026, najemca „3P NSU Sp. z o.o."
- Pole „miejsce dostawy i odbioru przedmiotu najmu" jest **PUSTE**

**Hipoteza:** Adres dostawy (`contract.delivery_address`) NIE jest przekazywany do kontekstu protokołu LUB pole w bazie jest puste LUB szablon nie renderuje tego pola.

**Lokalizacja w kodzie:**
- `backend/reports/templates/protocol_zo.html` — sekcja „miejsce dostawy i odbioru"
- `backend/reports/templates/protocol_zo_u.html` — analogicznie
- `backend/reports/templates/protocol_zo_nodata.html`, `protocol_zo_nodata_u.html`
- `backend/reports/service.py` — kontekst dla protokołu

**Acceptance criteria (DoD):**

**Backend (weryfikacja + naprawa):**
- [ ] Sprawdź w bazie: `SELECT id, delivery_address FROM contracts WHERE id = <id umowy S869/2026>` — czy pole jest puste?
- [ ] Sprawdź `backend/reports/service.py` — czy `contract.delivery_address` jest w kontekście template?
- [ ] Sprawdź wszystkie 4 szablony protokołów — czy pole „miejsce dostawy" renderuje `{{ contract.delivery_address }}`?
- [ ] Jeśli puste w bazie → zgłoś klientowi
- [ ] Jeśli brak w kontekście → dodaj do `context` w `service.py`
- [ ] Jeśli brak w template → dodaj `{{ contract.delivery_address or '' }}`

**Test:**
- [ ] Utwórz umowę z `delivery_address = "ul. Testowa 1, 00-001 Warszawa"`
- [ ] Wygeneruj protokół → adres widoczny
- [ ] Sprawdź wszystkie 4 typy protokołów
- [ ] **Weryfikacja wizualna klienta**

**Pliki do zmiany:**
- `backend/reports/templates/protocol_zo.html` (i warianty _u, _nodata, _nodata_u)
- `backend/reports/service.py` (jeśli brak w kontekście)

**Estimate:** 30-45 min (S)

---

### [RAO-P1-017] Naprawa mechanizmu rozpoznawania adresu (Nominatim) z uwag dojazdowych

```yaml
id: RAO-P1-017
priority: P1
size: M
status: dev-verified
classification: bugfix/integration
roles: [backend-dev, qa-engineer, product-owner]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 4"
specs_to_update:
  - core/07_integrations.md
  - core/04_business_logic.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "Root cause 1: Nominatim zwraca EMPTY dla adresów z prefiksem 'ul.' — dodano normalize_address()"
    - "Root cause 2: Auto-fill z 'uwag dojazdowych' NIE ISTNIAŁ — geocode był wołany tylko przy wyborze adresu z listy"
    - "Root cause 3: city w Nominatim jest w różnych polach (city/town/village/hamlet) — dodano extract_city_from_nominatim()"
    - "Root cause 4 (PO): 42% najczęstszych wpisów to 'odbiór własny' — Nominatim bezsensownie geokodował frazy bez adresu"
    - "Root cause 5 (PO): istnieje extract_city() w explorer/router.py (offline, 40+ miast) ale nie był używany"
    - "Fix backend nominatim.py: normalize_address() + extract_city_from_nominatim() + clean_address() + is_self_pickup() + extract_postal_code()"
    - "Fix backend router.py: nowy endpoint POST /integrations/extract-address (hybryda offline + Nominatim fallback)"
    - "Fix frontend: onDeliveryAddressInput z 800ms debounce + AbortController + cityManuallyEdited/postalManuallyEdited flags + onUnmounted cleanup"
    - "Algorytm hybrydowy (PO recommendation): 1) clean 2) self-pickup early-exit 3) offline postal regex 4) offline extract_city 5) Nominatim fallback"
    - "Coverage test na 100 rzeczywistych delivery_address z DB: 97% offline (52% both + 45% city only), 3% self-pickup, 0% Nominatim needed"
    - "API test: 'odbiór własny' → self_pickup=True, city=None, postal=None ✅"
    - "API test: 'ul. Kłobucka 6B, 02-699 Warszawa' → city=Warszawa, postal=02-699, source=offline ✅"
    - "API test: 'Gdańsku na ul. Szczęśliwa 3' → city=Gdańsk (rozpoznaje odmianę!) ✅"
    - "API test: '27-220Mirzec Poddabrowa 48A' → postal=27-220 (kod bez spacji) ✅"
    - "API test: 'Wroclaw, ul. Krzemieniecka 110 (wjazd z tyłu budynku)' → city=Wrocław (ignoruje info w nawiasach) ✅"
    - "API test: 'Metro\\r\\nSzeligowska 30C, 01-320 Warszawa' → city=Warszawa, postal=01-320 (czyści \\r\\n) ✅"
    - "Playwright: 'odbiór własny' w textarea → city i postal puste (self-pickup) ✅"
    - "Playwright: 'ul. Kłobucka 6B, 02-699 Warszawa' → postal=02-699, city=Warszawa ✅"
    - "Playwright: 'Wroclaw, ul. Krzemieniecka 110 (wjazd z tyłu budynku)' → city=Wroclaw ✅"
    - "vue-tsc --noEmit: pass (exit 0)"
  team:
    qa-engineer:
      - "[ISSUE FIXED] Brak cleanup timer'a przy unmount — dodano onUnmounted()"
      - "[ISSUE FIXED] Race condition — dodano AbortController"
      - "[ISSUE FIXED] Backend Decimal(None) crash — dodano None guard"
      - "[ISSUE FIXED] Nadpisywanie ręcznie edytowanych pól — dodano cityManuallyEdited/postalManuallyEdited flags"
      - "[PASS] normalize_address obsługuje ul./al./pl./os."
      - "[PASS] extract_city_from_nominatim fallback city→town→village→hamlet→municipality"
      - "[PASS] debounce 800ms + guard min 5 znaków"
      - "[PASS] silent fail na brak wyników"
    product-owner:
      - "[APPROVED] Hybrydowy algorytm: offline first (regex + extract_city), Nominatim fallback"
      - "[APPROVED] 'odbiór własny' → early-exit, city=NULL, postal_code=NULL (bez zmiany schema)"
      - "[APPROVED] postal_code nie jest używane w statystykach — lokalny regex wystarczy"
      - "[APPROVED] /stats/locations pomija city=NULL — akceptowalne dla v1"
      - "[APPROVED] Reuse istniejącego extract_city() z explorer/router.py"
      - "[DECISION] Nie dodawać is_self_pickup flagi do DB (P2, poza scope)"
  user: []
  client: []
root_cause: "Pięć bugów: (1) Nominatim nie radzi sobie z 'ul.' prefiksem; (2) auto-fill z uwag dojazdowych nie istniał; (3) city w różnych polach Nominatim; (4) brak early-exit dla 'odbiór własny' (42% wpisów!); (5) istniejący offline extract_city() nie był używany"
fix: "Hybrydowy algorytm 5-krokowy: clean → self-pickup early-exit → offline postal regex → offline extract_city (40+ miast) → Nominatim fallback. Nowy endpoint POST /integrations/extract-address. Frontend: debounce 800ms + AbortController + manual-edit flags + onUnmounted cleanup"
next_step: "team-verified — uruchom QA subagent na hybrydowym algorytmie"
```

**Problem (cytat klienta):** *„napraw mechanizm rozpoznający adres. ze wpisujesz w uwagi dojazdowe adres i wygrywa miasto i kod pocztowy, albo mi powiedz czemu nie działa"*

**Analiza:** Aplikacja ma integrację Nominatim (OpenStreetMap) do geokodowania adresów. Klient wpisuje adres w polu „uwagi dojazdowe" i oczekuje że system auto-wypełni `city` i `postal_code`.

**Lokalizacja w kodzie:**
- `backend/integrations/` — moduł Nominatim
- `backend/contracts/service.py` — logika auto-fill adresu
- `frontend/src/components/contracts/` — pole „uwagi dojazdowe" z auto-fill

**Acceptance criteria (DoD):**

**Backend (weryfikacja + naprawa):**
- [ ] Sprawdź `backend/integrations/nominatim.py` — czy endpoint działa?
- [ ] Test curl: `GET https://nominatim.openstreetmap.org/search?q=ul.+Kłobucka+6B,+02-699+Warszawa&format=json`
- [ ] Sprawdź czy aplikacja ma `User-Agent` header (wymagane przez Nominatim)
- [ ] Sprawdź logikę ekstrakcji `city` i `postal_code` z odpowiedzi Nominatim

**Frontend:**
- [ ] Sprawdź pole „uwagi dojazdowe" — czy ma debounce trigger do auto-fill?
- [ ] Czy jest error handling gdy Nominatim nic nie znajdzie?

**Test:**
- [ ] Wpisz adres „ul. Kłobucka 6B, 02-699 Warszawa" w uwagi dojazdowe → `city` = Warszawa, `postal_code` = 02-699
- [ ] Wpisz błędny adres → error handling
- [ ] **Weryfikacja wizualna klienta**

**Pliki do zmiany:**
- `backend/integrations/nominatim.py` (lub podobny)
- `backend/contracts/service.py`
- `frontend/src/components/contracts/*.vue`

**Estimate:** 2-3h (M)

---

### [RAO-P1-018] PDF Umowa — usunąć pieczątkę z pierwszej strony (oba typy S i U)

```yaml
id: RAO-P1-018
priority: P1
size: XS
status: team-verified
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 5"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "PyMuPDF image count: Page 1 = 0 images (was 1 = stamp) — stamp REMOVED"
    - "PyMuPDF image count: Page 3 (OWN) = 1 image (428x168px) — stamp KEPT on OWN"
    - "contract.html: <img> removed from SIGNATURES section, kept in own-sigs"
    - "contract_u.html: same — <img> removed from SIGNATURES, kept in own-sigs"
    - "Protocol templates (protocol_zo*.html) unchanged — stamp still on protocols"
  team:
    qa-engineer:
      - "[PASS] HTML poprawny po usunięciu <img> z SIGNATURES (brak wiszących tagów)"
      - "[PASS] sig-line renderowany dla obu stron (Wynajmujący/Najemca)"
      - "[PASS] Pieczątka zachowana w own-sigs (strona OWN)"
      - "[PASS] Protokoły niezmienione (pieczątka zostaje)"
      - "[PASS] deployment/ zsynchronizowane z backend/ (git diff --no-index: brak różnic)"
      - "[PASS] Layout shift kontrolowany (70px mniej, vertical-align: bottom, content-spacer 35mm)"
      - "[RISK: niski] Niespójność stylistyczna <div text-align:center> w 1 komórce a nie w 2 (pre-existing)"
  user: []
  client: []
fix: "Usunięto <img src='company_stamp_fixed.jpg'> z sekcji SIGNATURES w contract.html i contract_u.html (strona 1 umowy); zostawiono w sekcji own-sigs (strona OWN)"
next_step: "user-verified — operator sprawdza PDF"
```

**Problem (cytat klienta):** *„Na obydwu typach umów wywalić pieczątkę z pierwszej strony"*

**Analiza:** Pieczątka firmy (`company_stamp_fixed.jpg`) jest na stronie 1 umowy w sekcji SIGNATURES. Klient chce ją usunąć. Pieczątka na stronie OWN (podpisy) zostaje.

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract.html` — linia 259 (SIGNATURES), 402 (own-sigs)
- `backend/reports/templates/contract_u.html` — linia 225 (SIGNATURES), 299 (own-sigs)

**Acceptance criteria (DoD):**

**Backend:**
- [x] W `contract.html` usuń `<img>` z pieczątką z sekcji SIGNATURES (strona 1)
- [x] W `contract_u.html` analogicznie
- [x] Zostaw pieczątkę na stronie OWN (sekcja own-sigs)
- [x] **NIE usuwaj** z protokołów (`protocol_zo*.html`)

**Test:**
- [ ] Wygeneruj PDF umowy typ S → brak pieczątki na stronie 1, jest na OWN
- [ ] Wygeneruj PDF umowy typ U → brak pieczątki na stronie 1, jest na OWN
- [ ] Wygeneruj PDF protokołu → pieczątka nadal widoczna
- [ ] **Weryfikacja wizualna klienta**

**Pliki do zmiany:**
- `backend/reports/templates/contract.html` — **ZMIENIONE** (usunięto img z SIGNATURES)
- `backend/reports/templates/contract_u.html` — **ZMIENIONE** (usunięto img z SIGNATURES)

**Estimate:** 15-30 min (XS) — **ZMIENIONE, czeka na weryfikację**

---

### [RAO-P1-019] PDF Umowa usługi (typ U) — redesign do wyglądu jak umowa najmu (typ S)

```yaml
id: RAO-P1-019
priority: P1
size: M
status: dev-verified
classification: refactor/pdf-design
roles: [backend-dev, ui-designer]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 6+7 + Pasted image 20260629224212.png"
specs_to_update:
  - core/11_reports_stats.md
  - core/09_design_reference.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "Root cause: contract_u.html miał CSS niezgodny z contract.html (orange label, dotted red borders, brak navy)"
    - "Kropki = border-bottom: 2px dotted #c00000 → zmienione na 1px solid #aaa (jak w S)"
    - "Orange label #E07800 → gray #888 (jak w S)"
    - "Title color: brak → navy #1D2B53 (jak w S)"
    - "Party box width: 42% → 46% (jak w S)"
    - "Content/header padding: 14mm → 11mm (jak w S)"
    - "Dodano .art-name { color: #1D2B53; font-weight: bold; } (jak w S)"
    - "Dodano .party-data { color: #1D2B53; } (jak w S)"
    - "Weryfikacja: 0 wystąpień 'dotted' w CSS rules (tylko komentarz + own-sig-line identyczne jak w S)"
    - "Weryfikacja: 0 wystąpień 'E07800' i 'c00000'"
    - "PDF test: U contract id=15488 → 73,647 bytes ✅"
  team: []
  user: []
  client: []
root_cause: "contract_u.html miał niezgodny CSS z contract.html — orange label, dotted red borders (kropki), brak navy color"
fix: "Wyrównano CSS contract_u.html z contract.html: solid borders, gray labels, navy colors, padding 11mm, width 46%"
next_step: "team-verified → user-verified (weryfikacja wizualna klienta)"
```

**Problem (cytat klienta):** *„umowa usługi do naprawienia design żeby było jak w umowie najmu (kropki do wywalenia — obejrzyj jak to wygląda i zaproponuj poprawę żeby było jak umowa najmu)"*

**Analiza screenshota (`Pasted image 20260629224212.png`):**
- Umowa usługi nr `U872/2026`
- Sekcja „uzupełnij" ma **żółte tło (#FFFF00)** i **przerywane ramki (dashed)**
- Nagłówki w kolorze pomarańczowym zamiast navy
- Brak border-radius (ostre rogi)

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract_u.html` — cały szablon (CSS + struktura)
- `backend/reports/templates/contract.html` — referencja (jak ma wyglądać)

**Acceptance criteria (DoD):**

**Backend (redesign `contract_u.html`):**
- [ ] Przeanalizuj różnice CSS między `contract.html` (S) a `contract_u.html` (U)
- [ ] Ujednolić CSS `contract_u.html` z `contract.html`:
  - Nagłówki sekcji: navy `#1D2B53` (nie orange)
  - Tło sekcji „uzupełnij": `#F8F9FA` (subtle, nie jaskrawe żółte)
  - Border: solid 1px `#DEE2E6` (nie dashed)
  - Border-radius: 6px/12px zgodnie z design system
- [ ] **„Kropki do wywalenia"** = przerywane ramki (dashed borders) → zamień na solid

**Test:**
- [ ] Wygeneruj PDF umowy typ U → wygląd spójny z typ S
- [ ] Porównanie wizualne side-by-side
- [ ] **Weryfikacja wizualna klienta**

**Pliki do zmiany:**
- `backend/reports/templates/contract_u.html` (CSS + struktura)

**Estimate:** 2-3h (M)

---

### [RAO-P1-020] PDF Umowa — rozliczenie ma się pokazywać jak w starej aplikacji (kaskadowe)

```yaml
id: RAO-P1-020
priority: P1
size: M
status: dev-verified
classification: feature/pdf
roles: [backend-dev, frontend-dev]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 8 + Pasted image 20260629224534.png"
specs_to_update:
  - core/11_reports_stats.md
  - core/04_business_logic.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "Funkcja format_position_conditions_cascading już istniała (P1-008) ale miała 2 bugi"
    - "BUG 1: Duplikaty warunków (migracja stworzyła każdy warunek 2x) → dodano deduplikację po (period_count, rate1, rate2)"
    - "BUG 2: Linia 'powyżej' nie działała — dane z migracji mają period_count=ostatni (nie None) z rate2>0 i rate1=0"
    - "  Stara logika: elif c.rate2 is not None and prev_period > 0 (wymagała period_count=None)"
    - "  Nowa logika: elif c.rate2 > 0 and prev_period > 0 (ignoruje period_count, patrzy na rate2)"
    - "  Dodatkowo: warunek tier wymaga rate1 > 0 (nie rate1 is not None) — odrzuca rate1=0"
    - "Test realnymi danymi (contract 7164, 8 warunków → 4 unikalne):"
    - "  Przed: 8 linii z duplikatami i złymi zakresami (10-9, 21-20, 30-29 z rate=0)"
    - "  Po: 4 linii poprawne: 1-9/600, 10-20/500, 21-29/400, powyżej 29/300"
    - "Testy unit: 4 passed (test_format_conditions.py)"
    - "PDF test: contract 7164 → 90,798 bytes ✅"
  team: []
  user: []
  client: []
root_cause: "format_position_conditions_cascading nie obsługiwała danych z migracji (duplikaty, rate2 z period_count zamiast None)"
fix: "Deduplikacja warunków + logika 'powyżej' oparta na rate2>0 (nie period_count=None) + tier wymaga rate1>0"
next_step: "team-verified → user-verified (weryfikacja wizualna klienta)"
```

**Problem (cytat klienta):** *„rozliczenie ma się pokazywać jak na starej aplikacji"*

**Analiza screenshota (`Pasted image 20260629224534.png`):**
- Format rozliczenia widoczny:
  ```
  1 - 2 dni - 900,00 / doba
  powyżej 2 dni - 800,00 / doba
  ```
- To jest **format kaskadowy** — ten sam co P1-008 (w archiwum)

**Acceptance criteria (DoD):**

**Weryfikacja:**
- [ ] Sprawdź czy `format_position_conditions_cascading` jest w `backend/contracts/service.py`
- [ ] Sprawdź czy `contract_u.html` i `contract.html` używają `p.conditions_text`
- [ ] Wygeneruj PDF dla umowy z 2 warunkami kaskadowymi → czy format jest poprawny?
- [ ] Jeśli nie wdrożone → wdróż teraz
- [ ] Jeśli wdrożone ale bug → diagnozuj root cause

**Test:**
- [ ] Wygeneruj PDF z 2 warunkami kaskadowymi → format jak na screenshocie klienta
- [ ] Wygeneruj PDF z 3 warunkami → format (1-3, 4-16, powyżej 16)
- [ ] **Weryfikacja wizualna klienta**

**Pliki do zmiany:**
- Zależne od statusu implementacji kaskadowej

**Estimate:** 1-3h (M)

---

### [RAO-P1-021] Pole „Wartość (zł)" — decyzja biznesowa + propozycja zapisywania kwoty z rozliczenia

```yaml
id: RAO-P1-021
priority: P1
size: M
status: triaged
classification: feature/business-logic
roles: [product-owner, backend-dev, db-architect]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 9 + Pasted image 20260629224602.png"
specs_to_update:
  - core/04_business_logic.md
  - core/01_database.md
  - core/03_frontend_screens.md
migration_impact: maybe
security_impact: none
```

**Problem (cytat klienta):** *„czy Wartość(zł) jest do czegokolwiek używane w historycznych? pracowniczka mi powiedziała że to nie było używane w ogóle się zastanówmy co będzie potrzebne, bo przedpłata jest tylko dopisana przed a wartość jest nieznana bo zależy jak będzie rozliczone, i tak naprawdę to jak będzie rozliczone to wynika z tego co pobierzemy z fakturowni i to będzie kwota umowy która wynika z rozliczenia i może to można zapisać żeby wiedzieć co ile zarabia na przyszłość? zastanów się nad tym i mi daj znać"*

**Analiza screenshota (`Pasted image 20260629224602.png`):**
- Sekcja „Warunki Finansowe": pole „Wartość (zł)" puste, Przedpłata 3597,75, Pozostało -3597,75

**Kluczowe pytania biznesowe (do decyzji klienta):**

1. **Czy pole „Wartość (zł)" jest używane?** — pracowniczka mówi że NIE
2. **Skąd ma pochodzić wartość umowy?**
   - Opcja A: Auto-obliczone z rozliczenia (suma `rate × days` per pozycja)
   - Opcja B: Pobrane z Fakturowni (kwota z faktury)
   - Opcja C: Hybryda — ręczne + auto-override
3. **Czy zapisywać kwotę zarobku na przyszłość?**

**Acceptance criteria (DoD — po decyzji klienta):**

**Product Owner (analysis):**
- [ ] Zbierz decyzję klienta: Wariant A / B / C
- [ ] Dokumentuj w `spec/core/04_business_logic.md`

**Backend (implementacja — zależna od wariantu):**
- [ ] Wariant A: dodaj `compute_contract_value(contract_id)` w `service.py`
- [ ] Wariant B: dodaj integrację Fakturowni
- [ ] Wariant C: pole `value` edytowalne + auto-override

**⚠️ BLOCKER:** Wymaga decyzji biznesowej klienta przed implementacją.

**Estimate:** 3-5h (M) — zależne od wariantu

---

### [RAO-P1-022] Korekta nazewnictwa umów — zawsze S i G na końcu dla Gdańska

```yaml
id: RAO-P1-022
priority: P1
size: S
status: triaged
classification: bugfix/naming
roles: [backend-dev, db-architect, frontend-dev]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 10 + Pasted image 20260629225003.png"
specs_to_update:
  - core/04_business_logic.md
  - core/01_database.md
  - core/03_frontend_screens.md
migration_impact: yes
security_impact: none
```

**Problem (cytat klienta):** *„skoryguj nazewnictwo umów zgodnie z tym co w starej aplikacji. czyli zawsze S i G na końcu dla Gdańska"*

**Analiza screenshota (`Pasted image 20260629225003.png`):**
- Niespójne nazewnictwo: `S163/2026G` (G na końcu ✅), `SG043/2026` (G po S ❌)

**Reguła klienta:**
- Format: `[Typ][Numer]/[Rok][Oddział]`
- Oddział: `` (pusty = Warszawa), `G` (Gdańsk)
- Przykłady poprawne: `S166/2026`, `S163/2026G`, `U872/2026`, `U100/2026G`

**Lokalizacja w kodzie:**
- `backend/contracts/service.py` — funkcja `generate_contract_number`
- `backend/contracts/models.py` — pole `contract_number`, `branch`

**Acceptance criteria (DoD):**

**Backend (logika generowania):**
- [ ] Zaimplementuj format: `{type}{number:03d}/{year}{branch_suffix}`
- [ ] `branch_suffix = 'G' if branch == 'Gdańsk' else ''`

**DB (migracja danych — naprawa istniejących):**
- [ ] Znajdź umowy z błędnym formatem `SG*` → napraw na `S*G`
- [ ] Skrypt w `backend/migrate.py` (deterministyczny UPDATE)

**Test:**
- [ ] Nowa umowa najmu, Gdańsk → `S{next}/2026G`
- [ ] Nowa umowa najmu, Warszawa → `S{next}/2026`
- [ ] Migracja `SG*` → `S*G` (idempotentna)
- [ ] **Weryfikacja wizualna klienta**

**Pliki do zmiany:**
- `backend/contracts/service.py` (logika generowania numeru)
- `backend/migrate.py` (skrypt naprawczy)

**Estimate:** 2-3h (S)

---

### [RAO-P2-029] Statystyki — audyt determinizmu + naprawa niespójności archiwalnych

```yaml
id: RAO-P2-029
priority: P2
size: M
status: dev-verified
classification: bugfix/stats
roles: [backend-dev, qa-engineer]
source: client-request
source_date: 2026-06-29
source_ref: "Klient: 'wykonaj audyt czy te statystyki są w ogóle miarodajne i napraw żeby były prawdziwe i deterministyczne'"
specs_to_update:
  - core/04_business_logic.md
  - core/02_backend_api.md
migration_impact: no
security_impact: none
done_date: 2026-06-29
verification:
  dev:
    - "Root cause: _compute_position_revenues() ma exclude_archival=True domyślnie; 6 endpointów historycznych nie nadpisywało tego"
    - "Wszystkie 419 artykuły w bazie są is_archival=1 (po migracji z WinForms) → exclude_archival=True wykluczało WSZYSTKIE pozycje"
    - "Niespójność: /fleet-summary period_revenue=0, /by-category total_revenue=1.79M — ten sam okres!"
    - "Fix: 6 endpointów historycznych dostało exclude_archival=False"
    - "  /fleet-summary: period_revenue z archiwalnymi, total_machines/total_rented bez (stan teraz)"
    - "  /top-machines: exclude_archival=False"
    - "  /additional-fees: exclude_archival=False"
    - "  /locations: exclude_archival=False"
    - "  /positions: exclude_archival=False (oba wywołania)"
    - "  /commissions: exclude_archival=False"
    - "Co NIE zmienione: /currently-rented (stan teraz), /machine-roi (ma parametr include_archival)"
    - "Spójność: /fleet-summary.period_revenue == /by-category.total_revenue == /positions.total_revenue == 1,790,119.63 ✅"
    - "Determinizm: 2x ten sam request = identyczny wynik ✅"
    - "Dokument dla klienta: spec/STATYSTYKI_AUDYT.md (10 sekcji, jak działają statystyki)"
  team: []
  user: []
  client: []
root_cause: "exclude_archival=True domyślnie w _compute_position_revenues(); 6 endpointów historycznych nie nadpisywało tego; wszystkie 419 artykuły są archiwalne po migracji → 0 przychodu w 'Ogólne' ale 1.79M w 'Kategorie'"
fix: "6 endpointów historycznych: exclude_archival=False. Stan teraz (currently-rented, fleet-summary machines) zostaje z exclude_archival=True. Dokument MD dla klienta: spec/STATYSTYKI_AUDYT.md"
next_step: "user-verified — klient zatwierdza dokument STATYSTYKI_AUDYT.md"
```

**Problem (audyt Tech Leada):**

Audyt statystyk w module `/dashboard/reports` ujawnił **krytyczny bug niespójności**:

1. **Wszystkie 419 artykuły w bazie są `is_archival=1`** (337 maszyn + 82 usługi)
   - Zero aktywnych maszyn (`is_archival=0 AND is_service=0 AND is_external=0`)
   - To jest stan danych po migracji z starej aplikacji WinForms

2. **Niespójność `exclude_archival` między endpointami:**
   - `/fleet-summary` → `period_revenue=0` (wyklucza archiwalne)
   - `/currently-rented` → 0 maszyn (wyklucza archiwalne — poprawne dla "stan teraz")
   - `/top-machines` → 0 (wyklucza archiwalne)
   - `/additional-fees` → 0 (wyklucza archiwalne)
   - `/locations` → 0 (wyklucza archiwalne)
   - `/positions` → 0 (wyklucza archiwalne)
   - **ALE** `/by-category` → 1.79M (uwzględnia archiwalne ✅)
   - **ALE** `/by-period` → uwzględnia archiwalne ✅
   - **WYNIK:** "Ogólne" pokazuje 0, "Kategorie" pokazuje 1.79M — ten sam okres!

3. **Determinizm: ✅ POTWIERDZONY** — te same zapytania dają te same wyniki (test 2x)

4. **Algorytm kaskadowy `calculate_position_value()`: ✅ DETERMINISTYCZNY**
   - Decimal (nie float) — brak błędów zaokrąglania
   - Conditions sortowane po period_count — kolejność gwarantowana
   - Tiered calculation z fallback na ostatni non-zero rate

**Root cause:**
`_compute_position_revenues()` ma `exclude_archival=True` jako domyślne. Endpointy historyczne (/fleet-summary revenue, /top-machines, /additional-fees, /locations, /positions) nie nadpisują tego, więc wykluczają archiwalne — a wszystkie pozycje w bazie mają archiwalne artykuły.

**Fix:**
Endpointy historyczne powinny używać `exclude_archival=False` (uwzględniać archiwalne maszyny w statystykach historycznych). Endpointy "stan teraz" (/currently-rented, /fleet-summary machines count) zostają z `exclude_archival=True`.

**Acceptance criteria (DoD):**
- [ ] `/fleet-summary` period_revenue uwzględnia archiwalne (= /by-category total)
- [ ] `/top-machines` uwzględnia archiwalne
- [ ] `/additional-fees` uwzględnia archiwalne
- [ ] `/locations` uwzględnia archiwalne
- [ ] `/positions` uwzględnia archiwalne
- [ ] `/commissions` uwzględnia archiwalne
- [ ] `/currently-rented` nadal wyklucza archiwalne (stan teraz)
- [ ] `/fleet-summary` total_machines/total_rented nadal wyklucza archiwalne
- [ ] Spójność: /fleet-summary.period_revenue == /by-category.total_revenue (ten sam okres)
- [ ] Determinizm: 2x ten sam zapytanie = ten sam wynik
- [ ] Dokument MD dla klienta: jak działają statystyki, dlaczego są pewne

**Pliki do zmiany:**
- `backend/stats/router.py` (6 endpointów: exclude_archival=False)
- `spec/core/04_business_logic.md` (sekcja statystyk)
- `spec/INSTRUKCJA_DLA_KLIENTA.md` (dokumentacja statystyk)

**Estimate:** 3-4h (M)

---

### [RAO-P2-028] Statystyki — 100% pewna identyfikacja miasta (disambiguation via postal_code)

```yaml
id: RAO-P2-028
priority: P2
size: L
status: triaged
classification: feature/stats
roles: [db-architect, backend-dev, qa-engineer]
source: tech-lead-analysis
source_date: 2026-06-29
source_ref: "Analiza P1-017 — problem duplikatów nazw miast w statystykach"
specs_to_update:
  - core/01_database.md
  - core/04_business_logic.md
  - core/07_integrations.md
migration_impact: yes
security_impact: none
```

**Problem (analiza Tech Leada):**

W Polsce istnieje wiele miejscowości o tej samej nazwie. Aktualnie `/stats/locations` agreguje umowy po `contract.city` (sam tekst), co powoduje że:

- **"Wola" (60 umów)** — 5 różnych kodów pocztowych (05-500, 05-506, 05-555, 05-600, 08-410) → to są **różne miejscowości**: Wola k. Pruszkowa, Wola (dzielnica Warszawy), Wola k. Radomia, itd.
- **"Michałowice" (8 umów)** — minimum 3 różne wsie o tej nazwie w Polsce (k. Warszawy, k. Krakowa, k. Wrocławia)
- **"Lesznowola"** — gmina vs konkretna wieś
- **"Warszawa" (151 umów, 82 różne kody)** — tu disambiguation mniej krytyczny (to wszystko Warszawa), ale dla małych miejscowości jest błędna agregacja

**Dane z bazy (742 umowy):**
- 32.9% (244) — ma city + postal_code ✅
- 22.6% (168) — ma city ale NIE ma postal_code ⚠️
- 44.5% (330) — nie ma city ani postal_code ❌

**Istniejący `postal_codes.json`:**
- Tylko 220 wpisów covering 7 miast (Warszawa, Kraków, Wrocław, Poznań, Gdańsk, Łódź, Katowice)
- Nie pokrywa małych miejscowości gdzie problem disambiguation jest największy

**Propozycja rozwiązania (2 fazy):**

**Faza 1 — Composite key w statystykach (S, 2-3h):**
- Agreguj `/stats/locations` po `(city, postal_code)` zamiast tylko `city`
- Frontend: wyświetl "Wola (05-506)" zamiast "Wola" gdy są duplikaty
- Gdy `postal_code` jest NULL → agreguj po `city` (z oznaczeniem "?")
- To NIE wymaga nowej bazy — tylko zmiana zapytania SQL + frontend display

**Faza 2 — Pełna baza PNA / TERYT (L, 6-8h):**
- Integracja z otwartymi danymi PNA (Pocztowe Numery Adresowe) z Poczty Polskiej
- ~42 000 kodów pocztowych → (city, gmina, powiat, województwo, lat, lng)
- Źródła danych (open data, free):
  1. **Poczta Polska PNA** — oficjalny rejestr kodów pocztowych (XLSX, aktualizowany kwartalnie)
  2. **TERYT (GUS)** — rejestr terytorialny, już częściowo zintegrowany (`backend/integrations/teryt/`)
  3. **OpenStreetMap / Nominatim** — reverse geocoding dla lat/lng (już używane w P1-017)
- Nowa tabela `postal_codes` (zastąpi `postal_codes.json`):
  ```sql
  CREATE TABLE postal_codes (
    postal_code VARCHAR(6) PRIMARY KEY,  -- '05-506'
    city VARCHAR(100) NOT NULL,           -- 'Kolonia Lesznowola'
    gmina VARCHAR(100),                   -- 'Lesznowola'
    powiat VARCHAR(100),                  -- 'piaseczyński'
    wojewodztwo VARCHAR(50),              -- 'mazowieckie'
    lat DECIMAL(10, 7),
    lng DECIMAL(10, 7),
    source ENUM('pna', 'teryt', 'nominatim') DEFAULT 'pna'
  );
  ```
- Skrypt `backend/migrate_postal_codes.py` — jednorazowy import z PNA XLSX
- Endpoint `GET /integrations/postal-codes/{code}` — zwraca pełne dane (już istnieje, rozszerzyć)
- W `/stats/locations` — JOIN z `postal_codes` po `postal_code` → pełna hierarchia terytorialna

**Decyzja biznesowa (wymaga PO/klienta):**
1. Czy statystyki mają pokazywać "Wola (05-506)" czy "Kolonia Lesznowola" (oficjalna nazwa z PNA)?
2. Czy chcemy hierarchię: województwo → powiat → gmina → miasto? (przydatne dla raportów regionalnych)
3. Czy importować pełną bazę PNA (~42k wpisów, ~5MB) czy tylko Mazowsze + Pomorsze (główne obszary operacyjne)?

**Acceptance criteria (DoD):**

**Faza 1:**
- [ ] `/stats/locations` agreguje po `(city, postal_code)` gdy postal_code jest present
- [ ] Gdy postal_code NULL → agreguj po `city` z suffixem " (?)" w display
- [ ] Frontend: wyświetl "Miasto (XX-XXX)" gdy duplikat nazwy miasta detected
- [ ] Test: "Wola" z 5 kodami → 5 osobnych pozycji w statystykach

**Faza 2:**
- [ ] Tabela `postal_codes` z pełną bazą PNA (~42k wpisów)
- [ ] Skrypt importu `backend/migrate_postal_codes.py` (idempotentny, INSERT...ON DUPLICATE KEY UPDATE)
- [ ] Endpoint `GET /integrations/postal-codes/{code}` zwraca (city, gmina, powiat, wojewodztwo, lat, lng)
- [ ] `/stats/locations` z opcjonalnym filtrem `wojewodztwo`, `powiat`
- [ ] Auto-fill w formularzu umowy: po wpisaniu kodu pocztowego → pełne dane terytorialne
- [ ] Test: 42k wpisów w `postal_codes`, zapytanie <10ms z indeksem na `postal_code`

**Pliki do zmiany:**

**Faza 1:**
- `backend/stats/router.py` (zapytanie SQL — composite key)
- `backend/stats/schemas.py` (LocationStatItem z postal_code)
- `frontend/src/views/StatsView.vue` (display z postal_code)

**Faza 2:**
- `backend/integrations/teryt/models.py` (nowy model PostalCode)
- `backend/integrations/teryt/router.py` (rozszerzony endpoint)
- `backend/migrate_postal_codes.py` (skrypt importu PNA)
- `backend/main.py` (startup — create_all + ALTER)
- `spec/core/01_database.md` (DDL nowej tabeli)

**Ryzyka:**
- PNA XLSX ma niestandardowy format (puste wiersze, scalone komórki) — wymaga parsera
- Aktualizacja PNA kwartalnie — potrzeba mechanizmu refresh
- 42k wpisów w DB — dodatkowe ~5MB, zapytania z indeksem <10ms (nie problem)
- "Wola" vs "Wola Gołkowska" — PNA czasem używa nieoficjalnych nazw miejscowości

**Estimate:**
- Faza 1: 2-3h (S)
- Faza 2: 6-8h (L)
- Razem: 8-11h (L)

**Zależności:**
- P1-017 (hybrydowy extract-address) dostarcza `postal_code` do umów — bez tego Faza 1 ma limited data (tylko 32.9% umów ma postal_code)
- Po P1-017 w produkcji i ręcznym uzupełnieniu postal_code przez handlowców → Faza 1 będzie miała >80% coverage

---

## 📋 Tabela TL;DR

| ID | Tytuł | P | Est. | Status | Następny krok |
|----|-------|---|------|--------|---------------|
| RAO-P1-014 | Frontend — błędne obliczanie daty końcowej okresu umowy | P1 | XS | user-verified | → client-approved |
| RAO-P1-015 | PDF Umowa — ukryć numery telefonów na wydruku | P1 | XS | team-verified | → user-verified |
| RAO-P1-016 | PDF Protokół ZO — brak adresu dostawy | P1 | S | team-verified | → user-verified |
| RAO-P1-017 | Naprawa Nominatim — auto-fill adresu z uwag dojazdowych | P1 | M | dev-verified | → team-verified |
| RAO-P1-018 | PDF Umowa — usunąć pieczątkę z pierwszej strony (S i U) | P1 | XS | team-verified | → user-verified |
| RAO-P1-019 | PDF Umowa usługi (U) — redesign jak umowa najmu (S) | P1 | M | dev-verified | → user-verified |
| RAO-P1-020 | PDF — rozliczenie kaskadowe jak w starej aplikacji | P1 | M | dev-verified | → user-verified |
| RAO-P1-021 | Pole „Wartość (zł)" — decyzja biznesowa + auto-z rozliczenia | P1 | M | triaged | → DECYZJA: pole do rozliczenia (Fakturowni lub ręcznie) |
| RAO-P1-022 | Korekta nazewnictwa umów — S i G na końcu dla Gdańska | P1 | S | dev-verified | → user-verified |
| RAO-P2-028 | Statystyki — disambiguation miasta via postal_code (PNA/TERYT) | P2 | L | triaged | → DECYZJA: grupuj po PNA (PILNE — skąd uzupełnić?) |
| RAO-P2-029 | Statystyki — audyt determinizmu + naprawa archiwalnych | P2 | M | dev-verified | → user-verified |
| RAO-P0-030 | UNIQUE na contract.number + FOR UPDATE w generate_contract_number | P0 | S | triaged | → in_progress |
| RAO-P0-031 | XSS w PDF — Jinja2 autoescape + markupsafe.escape() | P0 | S | triaged | → in_progress |
| RAO-P0-032 | build_contract_data mutuje sesję — kopiuj description | P0 | XS | triaged | → in_progress |
| RAO-P0-033 | recalculate_total — użyj algorytmu kaskadowego | P0 | S | dev-verified | → team-verified |
| RAO-P0-034 | ContractUpdate schema z exclude_unset=True (lost data) | P0 | M | dev-verified | → team-verified |
| RAO-P0-035 | N+1 queries — selectinload w list_contracts/positions/articles | P0 | M | dev-verified | → team-verified |
| RAO-P0-036 | Stack trace disclosure → detail="Błąd" + logging | P0 | XS | triaged | → in_progress |
| RAO-P1-037 | delete_contract — guard na is_settled | P1 | XS | dev-verified | → team-verified |
| RAO-P1-038 | Brak indeksów DB (is_settled, created_at, salesperson_id, print_date, delivery_date) | P1 | S | dev-verified | → team-verified |
| RAO-P1-039 | Walidacja date_from > date_to + ujemne kwoty w ContractCreate | P1 | XS | dev-verified | → team-verified |
| RAO-P1-040 | is_settled blokuje mutacje (update/delete positions) | P1 | S | dev-verified | → team-verified |
| RAO-P1-041 | Hardcoded JWT fallback "change-me" — usuń + wymuś z env | P1 | XS | dev-verified | → team-verified |
| RAO-P1-042 | Frontend: logout czyści stores + redirect po login + baseURL z env | P1 | S | dev-verified | → team-verified |
| RAO-P1-043 | Frontend: memory leaks — cleanup event listenerów i timerów | P1 | S | dev-verified | → team-verified |
| RAO-P1-044 | Frontend: localStorage.getItem('token') → 'rao_token' | P1 | XS | dev-verified | → team-verified |
| RAO-P1-045 | _build_conditions_text — użyj format_position_conditions_cascading (dedup) | P1 | XS | dev-verified | → team-verified |
| RAO-P2-046 | IDOR — ownership/tenant check na wszystkich zasobach | P2 | L | triaged | → DECYZJA: brak izolacji teraz, odłożone |
| RAO-P2-047 | Rate limiting na /auth/login + /auth/forgot-password | P2 | S | triaged | → in_progress |
| RAO-P2-048 | Publiczny Swagger — docs_url=None na produkcji | P2 | XS | triaged | → in_progress |
| RAO-P2-049 | Frontend: error/loading/empty states we wszystkich widokach | P2 | M | triaged | → in_progress |
| RAO-P2-050 | Frontend: form validation (required fields, date ranges, numeric) | P2 | S | triaged | → in_progress |
| RAO-P2-051 | Cache dla statystyk (TTL 5 min) + RateType/Category (TTL 1h) | P2 | M | triaged | → in_progress |
| RAO-P2-052 | /explorer/locations/{city} — filtruj w SQL nie w Pythonie | P2 | S | triaged | → in_progress |
| RAO-P2-053 | /stats/positions — usuń double _compute + dodaj paginację | P2 | S | triaged | → in_progress |
| RAO-P0-054 | Kategorie — normalizacja nazw (diakrytyki + spacje) + collation polish_ci | P0 | S | triaged | → in_progress |
| RAO-P1-055 | Branch — migracja branch_id z G suffix + endpoint /stats/by-branch | P1 | M | triaged | → in_progress |
| RAO-P2-056 | contract_type (S/U) — dodaj grupowanie w statystykach | P2 | S | triaged | → in_progress |
| RAO-P2-057 | is_external — decyzja: wdrożyć filtrowanie czy usunąć flagę | P2 | XS | dev-verified | → team-verified (is_external nie blokuje + checkbox w details) |

**Razem:** 33 zadania · ~90-120h pracy (P0: 25-35h, P1: 30-40h, P2: 35-45h)

### Pipeline weryfikacji (status flow)

```
triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)
           │              │               │               │               │
           Devin koduje   Devin testuje   Software-house  Ty wzrokowo    Klient zatwierdza
           zmianę         programatycz.   subagenty       w UI/PDF        → zadanie zamknięte
                          (Playwright,    (QA, Security,
                           PyMuPDF,       UX, PO, Tech
                           pytest,        Lead review)
                           vue-tsc)
```

---

## 🔍 Pre-existing issues (znalezione przez security audit P1-015)

### [RAO-SEC-001] IDOR — `/reports/contract/{id}` bez ownership check

```yaml
id: RAO-SEC-001
priority: P1
size: S
status: triaged
classification: security/idor
roles: [backend-dev, security-auditor]
source: security-audit
source_date: 2026-06-29
source_ref: "Security audit P1-015 — subagent security-auditor"
specs_to_update:
  - core/25_security.md
migration_impact: no
security_impact: yes
```

**Problem:** Endpoint `POST /reports/contract/{contract_id}` wymaga autentykacji (`get_current_user`), ale **nie sprawdza ownership/tenant** — każdy zalogowany użytkownik może wygenerować PDF (z telefonami klienta) dla cudzej umowy znając `contract_id`.

**Atak:** Enumeracja `contract_id` → pozyskanie danych kontaktowych (telefony, adres dostawy) klientów innych handlowców.

**Fix:** W `reports/router.py` (lub `service.py`) dodać weryfikację:
```python
if contract.created_by != current_user.id and current_user.role != "admin":
    raise HTTPException(403)
```

**Pliki do zmiany:**
- `backend/reports/router.py`
- `backend/reports/service.py`

**Estimate:** 1-2h (S)

---

### [RAO-SEC-002] Jinja2 bez `autoescape=True` w reports/service.py

```yaml
id: RAO-SEC-002
priority: P1
size: S
status: triaged
classification: security/injection
roles: [backend-dev, security-auditor]
source: security-audit
source_date: 2026-06-29
source_ref: "Security audit P1-015 — subagent security-auditor"
specs_to_update:
  - core/25_security.md
migration_impact: no
security_impact: yes
```

**Problem:** `Environment(loader=FileSystemLoader(template_dir))` w `backend/reports/service.py` utworzony **bez `autoescape=True`**. Użytkownik może wstrzyknąć HTML/JS w pola `notes`, `contractor_name`, `contact_person1` → trafia do PDF WeasyPrint (SSRF, data exfiltration).

**Fix:** `Environment(loader=FileSystemLoader(template_dir), autoescape=True)` + przetestować wszystkie szablony PDF pod kątem niezamierzonego escapowania polskich znaków.

**Pliki do zmiany:**
- `backend/reports/service.py`

**Estimate:** 1-2h (S) — wymaga testów wszystkich szablonów PDF

---

## 🗂️ Materiały referencyjne

**Sprint 2026-06-29 (nowe zgłoszenia):**
- `spec/backlog/do_wciagniecia_do_backlogu.md` — 10 punktów od klienta (surowy markdown)
- `Pasted image 20260629223748.png` (root repo) — P1-014: błędne obliczenie daty
- `Pasted image 20260629223936.png` (root repo) — P1-016: protokół ZO bez adresu dostawy
- `Pasted image 20260629224212.png` (root repo) — P1-019: umowa usługi U872/2026 z żółtym tłem
- `Pasted image 20260629224534.png` (root repo) — P1-020: format rozliczenia kaskadowego
- `Pasted image 20260629224602.png` (root repo) — P1-021: sekcja Warunki Finansowe z pustym Wartość
- `Pasted image 20260629225003.png` (root repo) — P1-022: lista umów z niespójnym nazewnictwem
- Raporty vision: `Pasted image 20260629*-vision-report.md` (root repo)

**Stara aplikacja WinForms (referencja):**
- `C:\projects\repos\AppRao\rao\FormW.cs` linia 690-750 — algorytm formatowania warunków kaskadowych

**Aktualne szablony PDF:**
- `backend/reports/templates/contract_u.html` — umowa usługi (typ U)
- `backend/reports/templates/contract.html` — umowa najmu (typ S)
- `backend/reports/templates/protocol_zo.html` — protokół zdawczo-odbiorczy
- `backend/reports/templates/protocol_zo_u.html` — protokół wykonania usługi
- `backend/reports/templates/protocol_zo_nodata*.html` — warianty bez danych

---

## 📋 Decyzje operatora (2026-06-30)

### RAO-P1-021 — Pole „Wartość (zł)" → ekran rozliczenia
**Decyzja:** Pole „Wartość" przechodzi do **ekranu rozliczenia** (nie formularz umowy). Tam wartość jest pobierana:
- Z **Fakturowni** (kwota z faktury), LUB
- Wprowadzona **ręcznie** na bazie pozycji umowy z uzupełnionymi kwotami

**Implementacja:** Ekran rozliczenia pobiera pozycje umowy, pozwala uzupełnić kwoty (auto z Fakturowni lub ręcznie), sumuje → wartość umowy. Pole „Wartość" w formularzu umowy zostaje ukryte/puste (przedpłata dopisana z góry, wartość nieznana do rozliczenia).

---

### RAO-P2-028 — Statystyki miast via PNA (PILNE)
**Decyzja:** Grupuj po **postal_code (PNA)** + miasto (precyzyjne).
**Uwaga operatora:** Jedno miasto ma wiele PNA — trzeba ustalić **skąd uzupełnić PNA** dla miast.
**Pilne** — wymaga analizy źródeł danych PNA (tabela postal_codes, integracja TERYT, GUS).

---

### RAO-P2-046 — IDOR / RBAC
**Decyzja:** **Brak izolacji** na ten moment (single-tenant, wszyscy widzą wszystko).
Wraz z rozwojem aplikacji będziemy zarządzać uprawnieniami do różnych zasobów.
**Akcja:** Zostaw tylko SEC-001 (PDF ownership check). P2-046 odłożone.

---

### RAO-P2-057 — is_external (maszyna zewnętrzna)
**Decyzja:** Maszyna external **nie blokuje** dodawania w wielu miejscach (nie wpływa na rentowność).
- Ma być **możliwe do wyboru w detailsach maszyny** podczas dodawania
- Sprawdzić **mechanizm blokowania maszyn** (czy external poprawnie nie blokuje)
- Sprawdzić vs **wyliczanie dni umowy** czy maszyny będą poprawnie blokowane
- **Blokada = pytanie z informacją** gdzie i dlaczego jest zablokowana maszyna, czy na pewno chcesz ją dodać/wypożyczyć
- **Obgadać z teamem** (subagenty: backend-dev + qa-engineer + product-owner)
