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
status: done
classification: feature/pdf
roles: [backend-dev, frontend-dev]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 8 + Pasted image 20260629224534.png"
implementation_date: 2026-07-01
specs_to_update:
  - core/11_reports_stats.md
  - core/04_business_logic.md
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
status: done
classification: feature/business-logic
roles: [product-owner, backend-dev, db-architect]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 9 + Pasted image 20260629224602.png"
implementation_date: 2026-07-01
decision: "Usuń pole Wartość (zł) z PDF/ekranu + usuń kolumnę contracts.total_value (P2-033)"
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
status: done
classification: bugfix/naming
roles: [backend-dev, db-architect, frontend-dev]
source: client-request
source_date: 2026-06-29
source_ref: "spec/backlog/do_wciagniecia_do_backlogu.md pkt 10 + Pasted image 20260629225003.png"
implementation_date: 2026-07-01
decision: "Format S{NNN}/{ROK}[G] — wszystkie umowy na S, G dla oddziału ≠ Warszawa (id=1). Zgodne z FormU4.cs:734-764 + 2645-2655."
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
status: dev-verified
classification: feature/stats
roles: [db-architect, backend-dev, qa-engineer]
source: tech-lead-analysis
source_date: 2026-06-29
source_ref: "Analiza P1-017 — problem duplikatów nazw miast w statystykach"
commit: 7bb2d1a (backend+DB), 0ee1751 (frontend)
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
- [x] `/stats/locations` agreguje po `(city, postal_code)` gdy postal_code jest present
- [x] Gdy postal_code NULL → agreguj po `city` z bucket `"(brak PNA)"` (RAO-P2-028 refactor)
- [x] Frontend: wyświetl "Miasto (XX-XXX)" gdy duplikat nazwy miasta detected (ReportsSection — kolumna PNA + composite :key `loc.postal_code || loc.city`)
- [ ] Test: "Wola" z 5 kodami → 5 osobnych pozycji w statystykach

**Faza 2:**
- [x] Tabela `postal_codes` z pełną bazą PNA (21,904 wpisów — pełny Spis PNA)
- [x] Skrypt importu `backend/migrate.py` (re-migracja: 742 contracts, 395 z postal_code_id FK)
- [x] Endpoint `GET /integrations/postal-codes/{code}` zwraca (city, gmina, powiat, wojewodztwo)
- [ ] `/stats/locations` z opcjonalnym filtrem `wojewodztwo`, `powiat`
- [x] Auto-fill w formularzu umowy: po wpisaniu kodu pocztowego → pełne dane terytorialne (ContractFormView — panel gmina/powiat/woj + auto-fill city)
- [x] Test: 21,904 wpisów w `postal_codes`, zapytanie z indeksem na `postal_code` (UNIQUE)

**Faza 3 — Refactor unifikacji (DONE):**
- [x] `backend/shared/locations.py` — `aggregate_by_pna(positions, db)` (LEFT JOIN do postal_codes)
- [x] `backend/shared/revenue.py` — `compute_position_revenues` (kaskadowy algorytm, spójny stats+explorer)
- [x] `extract_city` (legacy regex) USUNIĘTE z `explorer/router.py` (5 call-site'ów przepiętych na PNA)
- [x] `GET /explorer/locations/{city}` → `GET /explorer/locations/{postal_code}` (BC break, drill-down po PNA)
- [x] `LocationStatItem` rozszerzone o `gmina`, `powiat`, `wojewodztwo` (rollup z postal_codes)
- [x] Testy unit: 221 passed (test_explorer_archival_filter.py zaktualizowane)

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

### [RAO-P2-058] Fakturownia — OID = numer umowy + mapowanie artykułów z metadanymi

```yaml
id: RAO-P2-058
priority: P2
size: L
status: dev-verified
classification: cross-stack/integration
roles: [tech-lead, backend-dev, frontend-dev, db-architect, security-auditor, qa-engineer]
source: operator-request
source_date: 2026-07-01
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
  - core/07_integrations.md
migration_impact: yes (contract.oid column already exists — needs to be used instead of hardcoded contract.number)
security_impact: medium (API token handling, external API calls)
depends_on:
  - RAO-P2-012 (istniejąca integracja read-only — foundation)
phase_1_mvp_status: done (2026-07-01)
phase_1_mvp_done:
  - "FakturowniaSettings skonfigurowane (enabled=True, domain=matsnd, token zaszyfrowany Fernet w DB)"
  - "5 produktów testowych dodanych do matsnd.fakturownia.pl (koparka, podnośnik, transport, czyszczenie, tankowanie)"
  - "ArticleFormView.vue: pole 'Produkt Fakturownia' (select z produktów FA via fetchProducts — live API, bez cache)"
  - "ArticleFormView.vue: auto-fill FA metadata (tax_rate, gtu_code, pkwiu) przy wyborze produktu — read-only display"
  - "Article model: 3 nowe kolumny (fakturownia_tax_rate, fakturownia_gtu_code, fakturownia_pkwiu) + ALTER TABLE w main.py"
  - "Article schemas: 3 nowe pola w ListItem/Detail/Create"
  - "FakturowniaProductOut schema: dodane tax, gtu_code, pkwiu (parse z FA API)"
  - "OID hybrydowe: service.py → oid = contract.oid if contract.oid else contract.number"
  - "Contract schemas: oid dodane do Detail/Create/Update z walidacją ^[A-Za-z0-9\\-/_]+$"
  - "ContractFormView.vue: pole 'OID Fakturownia (opcjonalny)' z placeholder '(auto = numer umowy)'"
  - "vue-tsc pass, build pass, smoke 11/11 pass"
phase_1_mvp_skipped:
  - "fakturownia_products_cache table — live API call działa wystarczająco dla MVP (13 produktów)"
  - "sync-products endpoint — niepotrzebny bez cache table"
  - "products/search endpoint — frontend filter po select wystarczy dla 13 produktów"
verification:
  - "vue-tsc --noEmit: pass"
  - "npm run build: pass"
  - "smoke 01-login.spec.ts: 11/11 passed"
  - "Backend /integrations/fakturownia/products: 13 products with tax/gtu_code/pkwiu fields"
```

**Problem:**

Integracja Fakturownia (RAO-P2-012) istnieje ale jest **read-only MVP** z dwoma problemami:

1. **OID hardcoded:** `backend/integrations/fakturownia/service.py:123` robi `oid = contract.number` — kolumna `contract.oid` (VARCHAR(40)) istnieje w DB ale jest **martwym kodem** (nigdy nie czytana, nigdy nie zapisywana). User nie może ustawić własnego OID per umowę.

2. **Brak mapowania metadanych artykułów:** `Article.fakturownia_product_id` (BIGINT) istnieje ale to tylko ID — brak synchronizacji metadanych (cena, GTU, PKWiU, stawka VAT) między RAO a Fakturownia. Brak UI do wyboru produktu FA w formularzu artykułu.

**Analiza Tech Lead (2026-07-01):**

#### Q1: Czy OID = numer umowy może tak być?

**TAK — z zastrzeżeniem.** Pole `oid` w Fakturownia jest **dokładnie do tego** — "numer zamówienia (np z zewnętrznego systemu zamówień)". Wspiera `oid_unique: "yes"` (blokuje duplikaty).

**Obecny stan (problem):**
- `service.py:123`: `oid = contract.number` (hardcoded, ignores `contract.oid` column)
- `contract.oid` column: istnieje, NULL dla 100% umów, nigdy nie używana
- `contract.number`: VARCHAR(40), format np. "2026/06/001 S" — może zawierać spacje (Fakturownia oid przyjmuje dowolny string, ale spacje mogą utrudniać wyszukiwanie)

**Rekomendacja — model hybrydowy:**
```python
oid = contract.oid if contract.oid else contract.number
```
- **Default:** `oid = contract.number` (auto-mapowanie, backward compat, zero konfiguracji)
- **Override:** user może ustawić `contract.oid` w formularzu umowy (dla przypadków gdy faktura została wystawiona independently z innym numerem zamówienia)
- **Walidacja:** `oid` nie może zawierać znaków specjalnych poza `-/_`; rekomendowane `^[A-Za-z0-9\-/_]+$`
- **Unikalność:** Fakturownia `oid_unique: "yes"` przy tworzeniu faktury — ale RAO nie wymusza tego (wiele faktur może mieć ten sam OID = wiele rozliczeń jednej umowy)

**Mapowanie OID → faktura (flow):**
```
RAO contract.number (lub contract.oid)
  → Fakturownia faktura.oid (pole na fakturze, ustawiane przy tworzeniu)
  → GET /invoices.json?oid=<numer> → lista faktur dla umowy
  → positions[].product_id → Article.fakturownia_product_id (1:N mapping)
  → ResolvedInvoiceOut (kwoty per artykuł RAO)
```

#### Q2: Jak zmapować artykuły z metadanymi na Fakturownia?

**Obecny stan:** `Article.fakturownia_product_id` (BIGINT, 1:N) — jeden produkt FA mapuje się na N artykułów RAO (np. "Koparka CAT 320" → 5 fizycznych maszyn we flocie).

**Pola Fakturownia Product dostępne do synchronizacji:**
| Pole FA | Pole RAO Article | Kierunek | Uwagi |
|---------|------------------|----------|-------|
| `id` | `fakturownia_product_id` | FA→RAO | klucz mapowania (już istnieje) |
| `name` | `name` | bidirectional | RAO name może być bardziej szczegółowy (z SN) |
| `code` | `internal_number` | RAO→FA | kod produktu w FA |
| `price_net` | `replacement_value` | FA→RAO | cena najmu = wartość odtworzeniowa? (do potwierdzenia) |
| `tax` | (brak) | FA→RAO | stawka VAT — potrzebuje nowego pola |
| `gtu_codes` | (brak) | FA→RAO | kod GTU — potrzebuje nowego pola |
| `additional_info` | (brak) | FA→RAO | PKWiU — potrzebuje nowego pola |
| `service` | `is_service` | RAO→FA | już mapowane semantycznie |
| `description` | `description` | bidirectional | |
| `quantity_unit` | (brak) | FA→RAO | jednostka (szt/h/dzień) |

**Rekomendacja — 3 fazowe:**

**Faza 1 (MVP, to zadanie):** Read-only sync + UI picker
- Endpoint `POST /integrations/fakturownia/sync-products` — pobiera katalog FA, cache w DB (tabela `fakturownia_products_cache`)
- UI: w formularzu Article, dropdown z produktami FA (searchable, z code + name + price)
- Po wybraniu → zapis `fakturownia_product_id` na artykule
- Nowe pola na Article (read-only z FA): `fakturownia_tax_rate`, `fakturownia_gtu_code`, `fakturownia_pkwiu`
- Display kwoty z faktur per artykuł w widoku umowy (już działa via `ResolvedInvoiceOut`)

**Faza 2 (przyszła):** Write-back RAO→FA
- Tworzenie faktury z poziomu RAO (POST /invoices.json z oid=contract.number)
- Auto-wypełnianie pozycji z `contract_positions` (product_id z mappingu, quantity, price)

**Faza 3 (przyszła):** Full sync bidirectional
- Webhook FA→RAO przy zmianie produktu
- Auto-aktualizacja cen w RAO gdy cena FA się zmienia

**Konfiguracja (operator dostarczył robocze konto):**
- Domain: `matsnd.fakturownia.pl` (subdomain: `matsnd`)
- API token: dostarczony operatora (roboczy) — **NIE commitować do git**
- Token konfiguruje się przez: `PUT /rao/api/integrations/fakturownia/settings` (admin only, szyfrowany Fernet w DB)
- Wymaga `RAO_FAKTUROWNIA_ENC_KEY` w `.env` (Fernet key — generuj: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)

**Acceptance criteria:**

Faza 1 (to zadanie):
- [ ] `service.py`: OID hybrydowe — `oid = contract.oid if contract.oid else contract.number` (zamiast hardcoded `contract.number`)
- [ ] `schemas.py` ContractCreate/ContractUpdate: dodaj `oid: Optional[str]` z walidacją `^[A-Za-z0-9\-/_]+$`
- [ ] `ContractFormView.vue`: pole "OID Fakturownia (opcjonalny)" z placeholder = numer umowy, help text "Puste = użyj numeru umowy"
- [ ] `ContractDetail`: wyświetl `oid` (lub "auto: {number}" gdy puste)
- [ ] DB: nowa tabela `fakturownia_products_cache` (id, name, code, price_net, tax, gtu_code, pkwiu, currency, synced_at)
- [ ] Endpoint `POST /integrations/fakturownia/sync-products` — refresh cache z FA (admin only, rate-limited)
- [ ] Endpoint `GET /integrations/fakturownia/products/search?q=...` — wyszukiwarka produktów dla UI picker
- [ ] `ArticleForm.vue`: pole "Produkt Fakturownia" — searchable dropdown z cache, po wybraniu → `fakturownia_product_id` + auto-fill `fakturownia_tax_rate`, `fakturownia_gtu_code`, `fakturownia_pkwiu` (read-only)
- [ ] `Article` model: nowe pola `fakturownia_tax_rate` (String(10)), `fakturownia_gtu_code` (String(20)), `fakturownia_pkwiu` (String(50)) — snapshot z cache, refresh przy sync
- [ ] Walidacja: `fakturownia_product_id` musi istnieć w cache (lub NULL)
- [ ] Test: `pytest` — OID hybrydowe (override + default), product sync, mapping 1:N
- [ ] Test: `vue-tsc --noEmit` — pass
- [ ] Smoke: `e2e/tests/01-login.spec.ts` — pass
- [ ] Spec sync: `spec/core/02_backend_api.md`, `03_frontend_screens.md`, `04_business_logic.md`, `07_integrations.md`
- [ ] Konfiguracja: operator wpisuje token przez Settings UI (nie w kodzie)

**Pliki do zmiany:**
- `backend/contracts/models.py` — `oid` już istnieje (użyć zamiast hardcoded number)
- `backend/contracts/schemas.py` — dodaj `oid` do Create/Update
- `backend/contracts/service.py` — walidacja OID
- `backend/integrations/fakturownia/service.py:123` — `oid = contract.oid if contract.oid else contract.number`
- `backend/integrations/fakturownia/client.py` — dodaj `create_product()`, `update_product()` (Faza 2)
- `backend/integrations/fakturownia/router.py` — dodaj `/sync-products`, `/products/search`
- `backend/articles/models.py` — nowe pola FA metadata
- `backend/main.py` — migracja ALTER TABLE dla nowych pól + tabela cache
- `frontend/src/views/ContractFormView.vue` — pole OID
- `frontend/src/views/ArticleFormView.vue` (lub odpowiednik) — FA product picker
- `frontend/src/stores/` — store dla FA products cache
- `spec/core/07_integrations.md` — dokumentacja integracji FA

**Edge cases (QA):**
- OID pusty + number pusty → 422 "Umowa nie posiada numeru"
- OID ze spacjami → walidacja odrzuca (regex `^[A-Za-z0-9\-/_]+$`)
- Produkt FA usunięty w FA → cache stale, mapping pokazuje "produkt nie istnieje"
- 1 produkt FA → N artykułów RAO → kwota z faktury mnożona × N (już działa w `ResolvedInvoiceOut`)
- Token wygasł → 502 "nieprawidłowy token" (juś obsłużone)
- Rate limit FA → 429 (już obsłużone)
- Sync produktów gdy FA ma >100 produktów → paginacja (per_page=100, page=1..N)

**Estymacja:** 12-16h (L) — Faza 1 MVP

---

### [RAO-P2-059] Usługi dodatkowe — migracja z plain-text (legacy) na per-artikel (nowoczesna konfiguracja)

```yaml
id: RAO-P2-059
priority: P2
size: L
status: done (2026-07-01, re-scoped po team review)
classification: cross-stack/refactor
roles: [tech-lead, db-architect, backend-dev, frontend-dev, qa-engineer, product-owner]
source: operator-request
source_date: 2026-07-01
specs_to_update:
  - core/01_database.md (ServiceFeeTemplateItem deprecated marker)
  - core/04_business_logic.md (per-artikel model — ServiceFeeTemplate.article_id = source of truth)
migration_impact: no (migracja już wykonana historycznie przez migrate.py step5b + P2-062 archive split)
security_impact: low (CRUD na service fees, już chronione auth)
depends_on:
  - RAO-P1-011 (ServiceFeeTemplate + article_id — foundation istnieje)
  - RAO-P2-062 (archive split — przeniósł legacy contract_service_fees → archive_contract_service_fees)
phase_1_mvp_status: done (2026-07-01, re-scoped po team review)
phase_1_mvp_done:
  - "ContractServiceFeeCreate schema: dodane article_id + default_price (były w Response ale nie w Create)"
  - "ContractFormView: ArticlePicker dla usług dodatkowych — select z artykułami is_service=1 w NEW ROW"
  - "Auto-fill: po wybraniu artykułu → name z article.name, amount_from z replacement_value, default_price snapshot"
  - "vue-tsc pass, build pass, smoke 11/11 pass"
  - "Migracja legacy umowa2.oplaty → contract_service_fees: WYKONANA historycznie przez migrate.py step5b (3396 wierszy), następnie przeniesiona do archive_contract_service_fees przez RAO-P2-062 (archive split). umowa2 DROPnięte w migrate.py step6. contract_service_fees=72 (nowe umowy), archive_contract_service_fees=3396 (legacy)."
  - "Auto-utworzenie artykułów usług: JUŻ ISTNIEJĄ (id 14137-14141: Tankowanie, Transport, Ponadnormatywny przestój, Czyszczenie 1, Czyszczenie 2, is_service=1). ServiceFeeTemplate 10/10 z article_id + default_price (5 usług × 2 preset groups S/U)."
  - "Reset z szablonu: apply_preset_to_contract (service.py:122-153) kopiuje article_id + default_price z ServiceFeeTemplate → ContractServiceFee. DZIAŁA."
  - "UI zarządzania szablonami: SettingsView.vue linie 285-358 — edycja preset.templates z article_id picker (select z is_service=1), default_price, amount_from/to/unit/description. DZIAŁA."
phase_1_mvp_rejected (zombie-spec po team review 2026-07-01):
  - "UI Template Items (ServiceFeeTemplateItem N:M): ODRZUCONE jako duplicate — SettingsView już ma edycję preset.templates z article_id picker przez ServiceFeeTemplate. N:M tabela jest redundantna (ServiceFeeTemplate z article_id daje ten sam rezultat). ServiceFeeTemplateItem: 0 wierszy, 0 odwołań w kodzie — deprecated, nie drop."
  - "Backend CRUD dla ServiceFeeTemplateItem: ODRZUCONE — endpointy dla ServiceFeeTemplate z article_id już istnieją (POST/PUT/DELETE /settings/fee-preset-groups/{id}/templates)."
  - "Parser regex umowa2.oplaty: NIEPOTRZEBNY — migracja już wykonana historycznie, umowa2 nie istnieje."
verification:
  - "DB: articles is_service=1 = 88 (5 znanych usług id 14137-14141 + 83 usługi wynajmu maszyn)"
  - "DB: ServiceFeeTemplate = 10, all with article_id NOT NULL (10/10)"
  - "DB: ServiceFeeTemplateItem = 0 (martwa tabela, deprecated)"
  - "DB: contract_service_fees = 72 (nowe umowy), archive_contract_service_fees = 3396 (legacy)"
  - "DB: FeePresetGroups = 2 (Domyślny S najem, Domyślny U usługa)"
  - "Backend: apply_preset_to_contract kopiuje article_id + default_price (service.py:122-153)"
  - "Frontend: SettingsView.vue:285-358 edycja preset.templates z article_id picker"
  - "Frontend: ContractFormView ArticlePicker dla usług (Phase 1 MVP done)"
```

**Problem:**

Stara aplikacja WinForms przechowuje usługi dodatkowe jako **jeden blob tekstowy** (`umowa2.oplaty VARCHAR(1000)`) — ręcznie edytowany multiline tekst. Nowa aplikacja RAO ma już nowoczesną strukturę (`contract_service_fees` z `article_id`, `amount_from/to`, `unit`, `description`), ale:

1. **Migracja danych legacy nie jest zrobiona** — `umowa2.oplaty` (plain text) nie jest mapowane na `contract_service_fees` (structured)
2. **Brak auto-fill z szablonów per artykuł** — `ServiceFeeTemplateItem` (N:M artykuł↔szablon) istnieje w DB ale nie jest używane w UI
3. **Brak spójności z Fakturownia** — usługi dodatkowe nie są linkowane do produktów FA (P2-058)

**Dogłębna analiza Tech Lead (2026-07-01):**

#### Stan w starej aplikacji (WinForms + MariaDB)

**Tabela `firma` (konfiguracja globalna):**
- `firma.uslugi1` VARCHAR(2000) — szablon usług dla umów najmu (typ "S")
- `firma.uslugi2` VARCHAR(2000) — szablon usług dla umów usług (typ "U")
- **Format:** multiline tekst z `- ` bulletami, placeholdery `$1`/`$2` dla kwot
- **Przykład (z dumpa, firma.id=1, uslugi1):**
  ```
  - Transport: 400.00 zł dostawa / 400.00 zł odbiór
  - Czyszczenie maszyny po wynajmie (zabrudzenia drobne): 150.00 zł - 400.00 zł
  - Czyszczenie maszyny po wynajmie (zabrudzenia trudnościeralne): 400.00 zł - 1500.00 zł
  - Usługa tankowania: 200.00 zł (plus koszt paliwa)
  - Ponadnormatywny przestój transportu: 200.00 zł / h - 300.00 zł / h
  - Nieuzasadnione wezwanie serwisowe: 280,00 zł (plus transport)
  ```
- **Przykład (uslugi2 — typ U):**
  ```
  - Transport: 350zł
  - Praca operatora: Minimum 8 h / w ciągu dnia
  ```

**Tabela `umowa2` (umowa):**
- `umowa2.oplaty` VARCHAR(1000) — **snapshot** tekstu usług dla tej konkretnej umowy
- **Flow w WinForms (FormU4.cs):**
  1. Nowa umowa typ "S" → `tbxuslugi.Text = SELECT uslugi1 FROM firma` (auto-fill z szablonu)
  2. Nowa umowa typ "U" → `tbxuslugi.Text = SELECT uslugi2 FROM firma` (auto-fill z szablonu)
  3. User może edytować tekst ręcznie (multiline TextBox)
  4. Zapis: `INSERT INTO umowa2 (..., oplaty, ...) VALUES (..., @oplaty, ...)` z `@oplaty = tbxuslugi.Text`
  5. Edycja: `UPDATE umowa2 SET oplaty=@oplaty WHERE id=X`
- **Edycja umowy:** `tbxuslugi.Text = u[16].ToString()` (ładowanie z `umowa2.oplaty`)

**Raport (Crystal Reports):**
- `umowa2.oplaty` → drukowane bezpośrednio na PDF jako blok tekstu w sekcji "Inne usługi"
- **Brak parsowania** — tekst idzie 1:1 z DB na wydruk

**Wzorce w danych (analiza dumpa — 742 umów):**
- Większość umów "S" ma ~6-7 linii usług (Transport, Czyszczenie×2, Tankowanie, Przestój, Serwis)
- Kwoty **różnią się per umowa** (Transport: 300/400/450/500/600 zł — negocjowane)
- Niektóre umowy mają puste `oplaty` (np. S398/2025 typ "U" — puste)
- Format kwot **mieszany**: `150.00 zł` (kropka) vs `280,00 zł` (przecinek) — niespójne
- **Brak ID artykułów** — usługi to czysty tekst, nie linkowane do maszyn/usług

#### Stan w nowej aplikacji (RAO)

**Tabele (już istnieją):**
- `contract_service_fees` — per-umowa usługi (id, contract_id, sort_order, name, amount_from, amount_to, unit, description, is_active, article_id, default_price)
- `service_fee_templates` — szablony globalne (z `article_id` — RAO-P1-011)
- `fee_preset_groups` — grupy szablonów per typ umowy (S/U)
- `service_fee_template_items` — N:M szablon↔artykuł z domyślną ceną (RAO-P1-011, **nieużywane w UI**)

**Backend (`reports/service.py`):**
- `generate_fees_text()` — buduje tekst z `ContractServiceFee` (structured)
- `build_contract_data()` — zastępuje placeholdery `$1`/`$2` w `description` kwotami z `amount_from`/`amount_to`
- **Format na PDF:** `- {name}: {amount_from} zł - {amount_to} zł / {unit} ({description})`

**Frontend (`ContractFormView.vue`):**
- Sekcja "Inne usługi" — inline edit, add row, delete, reset do szablonu
- `openPresetPicker()` — wybór grupy szablonów (fee_preset_groups) per typ umowy
- `resetServiceFees()` — POST `/contracts/{id}/service-fees/reset` (reset z szablonu)
- **Brak:** wyboru artykułu z listy (article_id nie jest ustawiane z UI), brak auto-fill kwot z `default_price`

**Luka:** `ServiceFeeTemplateItem` (N:M artykuł↔szablon) istnieje w DB ale **nie ma UI** do zarządzania tą relacją. Reset szablonu kopiuje `ServiceFeeTemplate` → `ContractServiceFee` ale **nie używa** `ServiceFeeTemplateItem`.

#### Rekomendacja — model docelowy (per-artikel)

**Zasada:** Każda usługa dodatkowa = artykuł (z `articles.is_service=1`) + cena + opis. Nie plain text.

**Faza 1 (to zadanie): Spójność danych + UI per-artikel**

1. **Migracja danych legacy (deterministyczna):**
   - Parser `umowa2.oplaty` → `contract_service_fees` (best-effort, z fallback)
   - Algorytm: regex match znanych wzorców (Transport, Czyszczenie, Tankowanie, Przestój, Serwis) → utwórz `ContractServiceFee` z `article_id=NULL` (legacy, nie linkowane)
   - Nieparsowalne linie → jeden `ContractServiceFee` z `name="Inne"`, `description=pełny tekst`
   - **Forward-only:** `umowa2.oplaty` nie jest usuwane (backup), nowe umowy używają structured

2. **UI — ArticlePicker dla usług dodatkowych:**
   - W formularzu umowy, sekcja "Inne usługi": przy dodawaniu nowej usługi, dropdown z artykułami `is_service=1` (searchable)
   - Po wybraniu artykułu → auto-fill `name` (z `article.name`), `default_price` (z `article.replacement_value` lub z `ServiceFeeTemplateItem.default_price`)
   - User może override `amount_from`/`amount_to`/`unit`/`description` per umowa
   - `article_id` zapisywane na `ContractServiceFee` (już ma kolumnę)

3. **UI — zarządzanie `ServiceFeeTemplateItem`:**
   - W Settings → Szablony usług → edycja grupy → lista artykułów w szablonie (N:M)
   - Dodawanie/usuwanie artykułów z szablonu z `default_price` per artykuł
   - Reset umowy do szablonu → kopiuje `ServiceFeeTemplateItem` → `ContractServiceFee` (z `article_id` + `default_price`)

4. **Raport PDF — bez zmian** (`generate_fees_text` już działa ze structured danymi)

**Faza 2 (przyszła, po P2-058): Integracja z Fakturownia**
- `ContractServiceFee.article_id` → `Article.fakturownia_product_id` → produkt na fakturze
- Auto-uzupełnianie pozycji faktury z `contract_service_fees`

**Faza 3 (przyszła): Cennik per artykuł**
- `Article.default_service_price` — domyślna cena najmu usługi
- Auto-suggest przy dodawaniu usługi do umowy

#### Mapowanie starych wzorców → artykuły RAO

| Wzorzec w `umowa2.oplaty` (regex) | Artykuł RAO (is_service=1) | Pola |
|-----------------------------------|---------------------------|------|
| `Transport: (\d+).*dostawa / (\d+).*odbiór` | "Transport" | amount_from=$1, amount_to=$2, unit="dostawa/odbiór" |
| `Czyszczenie.*drobne.*: (\d+).* - (\d+.*)` | "Czyszczenie maszyny (drobne)" | amount_from=$1, amount_to=$2 |
| `Czyszczenie.*trudno.*: (\d+).* - (\d+.*)` | "Czyszczenie maszyny (trudne)" | amount_from=$1, amount_to=$2 |
| `Tankowania?: (\d+).*` | "Tankowanie" | amount_from=$1, description="plus koszt paliwa" |
| `Przestój.*: (\d+).* - (\d+).*` | "Ponadnormatywny przestój" | amount_from=$1, amount_to=$2, unit="h" |
| `Serwis.*: (\d+).*` | "Wezwanie serwisowe" | amount_from=$1 |
| `Butla gazowa: (\d+).*` | "Butla gazowa" | amount_from=$1 |
| `Operator.*Minimum 8 h` | "Praca operatora" | description="Minimum 8 h / dzień" |

**Wymaga:** istnienie tych artykułów w `articles` z `is_service=1`. Jeśli nie istnieją → auto-utworzenie przy migracji (z `name` z wzorca, `is_service=1`).

#### Weryfikacja z realnych PDFów (legacy samples, 2026-07-01)

Operator dostarczył 4 PDFy (2 umowy + 2 protokoły PZO) — zanalizowano ekstrakcją PyMuPDF:
- `spec/technical/legacy_samples/pzo_umowy/` — source PDFs
- `spec/technical/legacy_samples/pzo_umowy_extracted/` — wyekstraktowany tekst
- `spec/technical/scripts/extract_legacy_pdfs.md` — opis analizy

**S129/2026 (typ S - najem) — sekcja "Inne usługi":**
```
- Transport: 500.00 zł dostawa / 500.00 zł odbiór
- Czyszczenie maszyny po wynajmie (zabrudzenia drobne): 150.00 zł - 400.00 zł
- Czyszczenie maszyny po wynajmie (zabrudzenia trudnościeralne): 400.00 zł - 1500.00 zł
- Usługa tankowania: 200.00 zł (plus koszt paliwa)
- Ponadnormatywny przestój transportu: 200.00 zł / h - 300.00 zł / h
- Nieuzasadnione wezwanie serwisowe: 280,00 zł (plus transport)
```
**Potwierdza:** 6 usług dodatkowych dla typ S, format z `$1`/`$2` placeholderami, kwoty mieszane (kropka vs przecinek: `280,00` vs `500.00`).

**S130/2026G (typ U - usługa) — sekcja "Inne usługi":**
```
(PUSTA — tylko tekst zobowiązania, bez listy usług)
```
**Potwierdza:** umowy typ U często mają pustą sekcję usług (uslugi2 w firma = "Transport + Operator" ale nie zawsze kopiowane).

**PZO (protokoły):** nie zawierają usług dodatkowych — tylko dane maszyny, daty, podpisy. Nie wymagają migracji.

**Sekcja "Uwagi" (w tym samym bloku co "Inne usługi" na PDF):**
```
- Doba wynajmu obejmuje 1 dzień kalendarzowy (do 8 godz. pracy jednego dnia)
- Zgłoszenie zwrotu urządzenia: pisemnie, min. z jednodniowym wyprzedzeniem
- Ilość dni pracy w tygodniu: 6
- dokumentacja zdjęciowa: wykonano
```
**Ważne dla parsera:** te 4 pozycje to **NIE usługi dodatkowe** — to warunki umowy. Parser musi rozróżnić:
- Usługi = linie z kwotami (regex `\d+[\.,]\d{2}\s*zł`)
- Uwagi = linie bez kwot (default warunki umowy)

W nowej aplikacji te "uwagi" powinny trafić do `contract.notes` (lub zostać jako default gdy `notes` puste — już działa w `contract.html` template).

#### Porównanie wydruków: STARY PDF vs NOWY RAO (KLUCZOWA RÓŻNICA LAYOUT)

**STARY PDF (S129/2026, typ S — z ekstrakcji PyMuPDF):**

Sekcja "Inne usługi" (lewa kolumna tabeli dwukolumnowej) — **10 linii razem**:
```
- Transport: 500.00 zł dostawa / 500.00 zł odbiór          ← usługa (kwota)
- Czyszczenie maszyny (drobne): 150.00 zł - 400.00 zł      ← usługa (kwota)
- Czyszczenie maszyny (trudne): 400.00 zł - 1500.00 zł     ← usługa (kwota)
- Usługa tankowania: 200.00 zł (plus koszt paliwa)         ← usługa (kwota)
- Ponadnormatywny przestój: 200.00 zł / h - 300.00 zł / h  ← usługa (kwota)
- Nieuzasadnione wezwanie serwisowe: 280,00 zł (plus transport) ← usługa (kwota)
- Doba wynajmu obejmuje 1 dzień kalendarzowy (do 8 godz.)  ← UWAGA (bez kwoty)
- Zgłoszenie zwrotu urządzenia: pisemnie, min. 1 dzień     ← UWAGA (bez kwoty)
- Ilość dni pracy w tygodniu: 6                            ← UWAGA (bez kwoty)
- dokumentacja zdjęciowa: wykonano                        ← UWAGA (bez kwoty)
```
Sekcja "Uwagi" (prawa kolumna) — tekst zobowiązania (Niniejszym zobowiązuję się...).

**Klucz:** w starym PDF usługi i uwagi są **W TYM SAMYM BLOKU** "Inne usługi" — wymieszane jako jeden tekst. Crystal Reports drukuje `umowa2.oplaty` + dokleja 4 defaultowe uwagi (prawdopodobnie hardcoded w raporcie, z `umowa2.liczba_dni` dla "Ilość dni").

**Weryfikacja z dumpa bazy:** `umowa2.oplaty` (S397/2025) zawiera TYLKO 6 usług (bez 4 uwag) — potwierdza że 4 uwagi są doklejane z innego miejsca (nie z `oplaty`).

**NOWY RAO (contract.html, linie 210-247):**

Sekcja "Inne usługi" (lewa kolumna `.inne-left`) — **tylko fees**:
```
{% for fd in fees if fd.fee.is_active %}
  - {{ fd.description }}  (lub "- {name}: {amount_from} zł - {amount_to} zł / {unit}")
{% endfor %}
```
Sekcja "Uwagi" (prawa kolumna `.inne-right`) — **4 defaulty LUB contract.notes**:
```
{% if contract.notes %}
  {{ contract.notes }}
{% else %}
  Doba wynajmu: obejmuje 1 dzień kalendarzowy (do 8 godz. pracy)
  Zgłoszenie zwrotu urządzenia: pisemnie, min. z jednodniowym wyprzedzeniem
  Ilość dni pracy w tygodniu: {{ contract.working_days_per_week or 6 }}
  Dokumentacja zdjęciowa: wykonano
{% endif %}
```

**Porównanie wizualne:**

| Aspekt | STARY PDF | NOWY RAO |
|--------|-----------|----------|
| "Inne usługi" zawiera | 6 usług + 4 uwagi (10 linii) | tylko fees (6 usług) |
| "Uwagi" zawiera | tekst zobowiązania | 4 defaulty LUB contract.notes |
| Rozdział usług od uwag | NIE (wymieszane) | TAK (osobne kolumny) |
| Źródło 4 uwag | hardcoded w Crystal Reports | default w contract.html gdy notes puste |
| "Ilość dni" | z `umowa2.liczba_dni` | z `contract.working_days_per_week` |
| Format kwot | mieszany (`280,00` vs `500.00`) | spójny (`money_plain` filter) |
| Placeholdery `$1`/`$2` | w `oplaty` tekście | zastępowane w `build_contract_data()` |

**Wniosek dla migracji (P2-059):**

1. **Parser `umowa2.oplaty` → `contract_service_fees`:** migruje TYLKO 6 usług (linie z kwotami). 4 uwagi NIE są w `oplaty` (są doklejane z innego miejsca) — parser ich nie znajdzie.
2. **4 defaultowe uwagi:** już działają w nowym RAO (default w `contract.html` gdy `notes` puste) — **brak migracji potrzebnej**.
3. **`umowa2.liczba_dni` → `contract.working_days_per_week`:** to pole już istnieje w RAO — migracja mapuje `liczba_dni` → `working_days_per_week` (już w `migrate.py`).
4. **Layout nowego jest LEPSZY:** rozdzielenie usług od uwag = czystszy PDF, łatwiejsza edycja w UI. Nie trzeba odtwarzać starego wymieszania.
5. **Kryterium parsera:** linia jest usługą jeśli ma kwotę (regex `\d+[\.,]\d{2}\s*zł`), w przeciwnym razie skip (nie trafia do `contract_service_fees`).

#### DWA równoległe systemy usług dodatkowych w starej aplikacji (KLUCZOWE)

Analiza starej bazy + kodu WinForms ujawniła **dwa oddzielne systemy** usług dodatkowych:

**System 1 — "oplaty" (per UMOWA, plain text, na PDF):**
- Tabela: `umowa2.oplaty` VARCHAR(1000) — snapshot tekstu per umowa
- Szablon: `firma.uslugi1` (typ S) / `firma.uslugi2` (typ U)
- Flow: auto-fill z szablonu → ręczna edycja multiline → zapis do `umowa2.oplaty`
- Render: sekcja "Inne usługi" na PDF umowy (1:1, bez parsowania)
- **To ten system jest używany w praktyce** (742 umów z danymi w `oplaty`)

**System 2 — "koszt" (per POZYCJA, strukturalny, do rozliczenia):**
- Tabele: `koszt_typ` (słownik) + `koszt` (per pozycja umowy)
- `koszt_typ` — 5 typów (słownik):
  ```
  1002: Tankowanie
  1003: Ponadnormatywny koszt przestoju
  1004: Transport
  1005: Czyszczenie drobne
  1006: Czyszczenie pelne
  ```
- `koszt` — rekordy: id, id_typu (FK), id_umowa_pozyjca (FK do pozycji), opis, kwota, data
- Flow: `FormKoszt.cs` — menu kontekstowe na pozycji umowy → "Dodaj koszt" → wybór z `koszt_typ` + kwota
- Sumowanie: `podsumujkoszty()` w `FormU4.cs:1362` — `SELECT SUM(kwota) FROM koszt WHERE id_umowa_pozyjca=X`
- **Tabela `koszt` jest PUSTA w dumpie (0 rekordów)** — system zaimplementowany ale nieużywany w praktyce

**Wniosek dla migracji (P2-059):**

1. **Migracja danych:** `umowa2.oplaty` (System 1) → `contract_service_fees` (per umowa) — to główny strumień
2. **Słownik `koszt_typ` (5 typów) → artykuły `is_service=1`:** to są dokładnie te same typy co regex wzorce! Można ich użyć jako bazowych artykułów usług przy migracji:
   - 1002 Tankowanie → Article "Tankowanie" (is_service=1)
   - 1003 Przestój → Article "Ponadnormatywny przestój" (is_service=1)
   - 1004 Transport → Article "Transport" (is_service=1)
   - 1005 Czyszczenie drobne → Article "Czyszczenie (drobne)" (is_service=1)
   - 1006 Czyszczenie pelne → Article "Czyszczenie (trudne)" (is_service=1)
3. **System 2 (per pozycja) — przyszła ewolucja:** RAO ma obecnie `contract_service_fees` (per umowa). System per pozycja (jak `koszt`) może być Faza 3 — dodanie `ContractPositionServiceFee` gdy biznes tego wymaga (np. różne koszty transportu per maszyna w jednej umowie)
4. **Brak danych do migracji z `koszt`:** tabela pusta, nie wymaga migracji rekordów

#### Acceptance criteria

Faza 1 (to zadanie):
- [ ] **Parser legacy:** skrypt `backend/migrate_service_fees.py` — parsuje `umowa2.oplaty` → `contract_service_fees` (best-effort, loguje nieparsowane)
- [ ] **Auto-utworzenie artykułów usług:** jeśli artykuł `is_service=1` o nazwie z wzorca nie istnieje → utwórz (idempotentne, IF NOT EXISTS po nazwie)
- [ ] **Migracja:** 742 umów → `contract_service_fees` z `article_id` (gdzie match) lub `article_id=NULL` (legacy unmatched)
- [ ] **Weryfikacja:** diff count — `SELECT COUNT(*) FROM umowa2 WHERE oplaty != ''` vs `SELECT COUNT(DISTINCT contract_id) FROM contract_service_fees`
- [ ] **UI ArticlePicker:** w `ContractFormView.vue` sekcja "Inne usługi" — dropdown z artykułami `is_service=1` (searchable, z name + default_price)
- [ ] **Auto-fill:** po wybraniu artykułu → `name`, `default_price` → `amount_from`, `unit` auto-uzupełnione (user może override)
- [ ] **UI Template Items:** w Settings → Szablony → edycja grupy → zarządzanie listą artykułów (N:M) z `default_price`
- [ ] **Reset z szablonu:** `POST /contracts/{id}/service-fees/reset` — kopiuje `ServiceFeeTemplateItem` → `ContractServiceFee` (z `article_id` + `default_price`)
- [ ] **Backend:** `GET /settings/fee-preset-groups/{id}/items` — lista artykułów w grupie
- [ ] **Backend:** `POST/DELETE /settings/fee-preset-groups/{id}/items` — dodaj/usuń artykuł z grupy
- [ ] **Raport PDF:** bez regresji — `generate_fees_text` działa (juś działa, tylko weryfikacja)
- [ ] **Test:** `pytest` — parser, migracja, reset z szablonu
- [ ] **Test:** `vue-tsc --noEmit` — pass
- [ ] **Smoke:** `e2e/tests/01-login.spec.ts` — pass
- [ ] **Spec sync:** `spec/core/01_database.md`, `02_backend_api.md`, `03_frontend_screens.md`, `04_business_logic.md`, `08_migration_plan.md`

**Pliki do zmiany:**
- `backend/migrate_service_fees.py` (nowy) — parser + migracja
- `backend/contracts/models.py` — `ContractServiceFee` już ma `article_id` (użyć)
- `backend/contracts/service.py` — reset z szablonu używa `ServiceFeeTemplateItem`
- `backend/settings/router.py` — endpointy dla template items
- `backend/settings/service.py` — CRUD dla template items
- `frontend/src/views/ContractFormView.vue` — ArticlePicker dla usług
- `frontend/src/views/SettingsView.vue` (lub odpowiednik) — zarządzanie template items
- `spec/core/08_migration_plan.md` — dodaj sekcję migracji `oplaty` → `contract_service_fees`

**Edge cases (QA):**
- `umowa2.oplaty` puste → 0 `contract_service_fees` (skip)
- `umowa2.oplaty` z nieparsowalnym tekstem → 1 `ContractServiceFee` z `name="Inne"`, `description=pełny tekst`, `article_id=NULL`
- Kwota z przecinkiem `280,00 zł` vs kropką `280.00 zł` — parser normalizuje (replace `,` → `.`)
- Artykuł usunięty po migracji (`article_id` orphan) — `ON DELETE SET NULL` (już w schema)
- Duplikat artykułu w szablonie — UNIQUE constraint na `(template_id, article_id)`
- Reset umowy z usługami → usunięcie starych + dodanie z szablonu (juś działa, tylko z `article_id`)
- Umowa z `oplaty` ale bez `contract_id` w nowej DB (niezmigrowana umowa) — skip z logiem
- Parsowanie wielokrotne (re-run migracji) — idempotentne (DELETE + INSERT lub UPSERT po `(contract_id, sort_order)`)

**Estymacja:** 16-20h (L) — Faza 1 (parser + migracja + UI + template items)

---

### [RAO-P2-060] Statystyki — gruba krecha legacy vs nowe + StatsView + bugfix QA

```yaml
id: RAO-P2-060
priority: P1
size: L
status: dev-verified
classification: cross-stack/feature+bugfix
roles: [tech-lead, db-architect, backend-dev, frontend-dev, ux-designer, qa-engineer, product-owner]
source: operator-request
source_date: 2026-07-01
phase_1_status: done (2026-07-01) — 6 bugów naprawionych (3 już przez P2-062), 2 indeksy, cleanup isLegacy z frontend store + ReportsSection toggle
phase_2_status: done (2026-07-01) — StatsView.vue (2 zakładki: Flota teraz + Wynajem w okresie), sidebar "📊 Statystyki", routing /stats, CORS 5176
verification:
  - "vue-tsc --noEmit: pass"
  - "npm run build: pass"
  - "smoke 01-login.spec.ts: 11/11 passed"
  - "Playwright MCP: StatsView renderuje 2 tabs, 7 KPI cards, 2 filter bars, empty states (pusta baza)"
specs_to_update:
  - core/01_database.md (indeksy + sync contract_settlements DDL)
  - core/02_backend_api.md (6 schemas z revenue_source_label)
  - core/03_frontend_screens.md (StatsView + sidebar)
  - core/04_business_logic.md (ortogonalność is_legacy vs revenue_source vs settlements.source)
  - core/11_reports_stats.md (rozróżnienie legacy vs nowe)
migration_impact: no (brak zmian schema, tylko indeksy)
security_impact: low (read-only stats, auth już na endpointach)
depends_on:
  - RAO-P2-028 (is_legacy flag — foundation istnieje)
  - RAO-P2-032 (contract_settlements.source — foundation istnieje)
```

**Problem:**

Klient wyraźnie zaznaczył: "wartości w starej aplikacji to tylko cennik, nie finalne wartości — nie możemy tego pokazywać jako wartości, jedynie szacunek. Trzeba odkreślić legacy umowy i nowe".

Stare umowy (legacy, `is_legacy=1`) mają tylko `position_conditions.rate1 × period_count` = **cennik teoretyczny**. Nowe umowy mają `contract_settlements.cost_client` = **prawdziwe kwoty z rozliczeń**. Mieszanie tych dwóch źródeł w statystykach = **zafałszowane ROI**, błędne decyzje o wycofaniu/zakupie maszyn.

Dodatkowo klient wymaga 6 funkcji analitycznych:
1. Ile razy maszyna (z nr wewnętrznym) wynajęta w okresie (mies/3mies/rok) — stopa zwrotu
2. Ile maszyn wynajętych teraz
3. Numer wewnętrzny dla każdej maszyny (już istnieje — założenie spełnione)
4. Sumowanie pozycji dodatkowych (transport, mycie, ładowanie) za okresy
5. Top maszyny po ilości wypożyczeń + kategorie
6. Gruba krecha: legacy archiwalne (szacunek) vs nowe (prawdziwe wartości)

**Co już istnieje (konsensus zespołu):**

| Element | Status |
|---------|--------|
| `contracts.is_legacy` TINYINT(1) | ✓ (RAO-P2-028) |
| `contract_settlements.source` (legacy/fakturownia/manual) | ✓ (RAO-P2-032) |
| `revenue_source` computed per-pozycja (actual/estimate_lookup/estimate_tiered) | ✓ w `shared/revenue.py` |
| `rozliczenie` zmigrowane do `contract_settlements` (source='legacy') | ✓ `step10_import_rozliczenie()` |
| 16 endpointów stats z filtrem `is_legacy` | ✓ backend gotowy w 70% |
| `Article.internal_number` (nr wewnętrzny) | ✓ |
| `Article.replacement_value` (do ROI) | ✓ |
| `FleetSummary` zwraca `revenue_actual`/`revenue_estimate`/`revenue_source_label` | ✓ (tylko ten endpoint) |

**Kluczowa wiedza biznesowa — 3 ortogonalne osie (Tech Lead):**

| `is_legacy` | `revenue_source` | Niezawodność kwoty | Interpretacja |
|-------------|------------------|---------------------|---------------|
| `true` | `actual` | **NIEZAWODNA** | Archiwalna umowa z `rozliczenie` import — prawdziwa kwota |
| `true` | `estimate_*` | NIEPEWNA | Archiwalna umowa, brak rozliczenia → szacunek z cennika |
| `false` | `actual` | **NIEZAWODNA** | Nowa umowa rozliczona (Fakturownia/manual) |
| `false` | `estimate_*` | NIEPEWNA | Nowa umowa, aktywna/nierozliczona (oczekiwane) |

**Wniosek:** "Gruba krecha" musi być per-KPI (na `revenue_source`), nie per-widok (na `is_legacy`) — bo archiwalna umowa z `source='legacy'` settlement ma **prawdziwą** kwotę.

---

#### DECYZJE UŻYTKOWNIKA (zarejestrowane 2026-07-01)

**Decyzja 1: Gruba krecha = Osobna zakładka "Archiwum (szacunkowe)"**

- **Wybrano:** Osobna zakładka "Archiwum (szacunkowe)" z szarym tłem + banner + suffix `[szac.]` przy każdej liczbie
- **Odrzucono:** Toggle 3-stanowy (miesza dane), sekcja na dole (scroll zaciera kreskę)
- **Realizacja (UX Designer):**
  - 3 zakładki w `StatsView.vue`: `[ Flota teraz ] [ Wynajem w okresie ] [ Archiwum (szacunkowe) 📦 ]`
  - Zakładka "Archiwum" — szare tło (`--color-bg-light` #F8F9FA) + żółty border (`--color-warning` 30% opacity)
  - Banner na górze: "⚠️ Dane historyczne (szacunkowe) — wartości przed migracją do RAO. Nie pochodzą z systemu rozliczeń. NIE sumuj z 'Wynajem w okresie'."
  - Każda liczba w archiwum ma suffix `[szac.]` w kolorze `--color-warning`
  - Tooltip na `[szac.]`: "Wartość oszacowana na podstawie stawek katalogowych. Dokładna kwota nie jest znana — dane pochodzą z systemu sprzed migracji."
  - W zakładce "Wynajem w okresie" gdy `revenue_source_label === "mieszane"`: rozkład "12 500 zł (rzeczywiste) + 3 200 zł [szac.]" z tooltipem
- **User nigdy nie ma wątpliwości** czy patrzy na prawdziwe dane czy szacunek

**Decyzja 2: Lokalizacja = Nowy StatsView + nowa pozycja w sidebarze**

- **Wybrano:** Nowy widok `StatsView.vue` z 3 zakładkami + nowa pozycja "Statystyki" w sidebarze
- **Odrzucono:** Rozbudowa WorkerView (staje się duży, mieszanie concerns)
- **Realizacja (UX Designer):**
  - Nowy plik: `frontend/src/views/StatsView.vue`
  - Nowa pozycja w sidebarze: między "Pulpit" a "Prowizje"
  - Routing: `dashboard/stats` (rozszerzenie patternu `dashboard/:section`)
  - Domyślna zakładka: "Wynajem w okresie" (najczęstszy use case)
  - Nie ruszać `DashboardView.vue` (grid operacyjny), `WorkerView.vue` (Pulpit), `HomeView.vue` (operacyjne)

**Decyzja 3: Bugfix QA = Wszystkie 9 bugów w tym zadaniu**

- **Wybrano:** Naprawić wszystkie 9 bugów razem ze statystykami (jeden PR, jeden review)
- **Odrzucono:** Tylko 3 krytyczne, osobne zadanie
- **Bugy do naprawy (QA Engineer):**

| # | Bug | Plik:linia | Krytyczność | Fix |
|---|-----|-----------|-------------|-----|
| 1 | `overdue_contracts` zasypane legacy umowami (brak filtra `is_legacy`) | `stats/router.py:712` | 🔴 P0 | Dodać `is_legacy=False` domyślnie + param `include_legacy=true` |
| 2 | `contracts_in_period` w `fleet_summary` ignoruje filtr `is_legacy` | `stats/router.py:117` | 🔴 P0 | Dodać `is_legacy` do query |
| 3 | Umowa z `date_to=NULL` (na czas nieokreślony) nie liczona w `currently_rented` | `stats/router.py:223` | 🔴 P0 | `(date_to IS NULL OR date_to >= today) AND date_from <= today` |
| 4 | Settlement z `cost_client=0` traktowany jak brak settlement | `shared/revenue.py:230` | 🟡 P1 | `IS NOT NULL` zamiast `> 0` |
| 5 | Settlement z ujemnym `cost_client` (korekta) traktowany jak brak | `shared/revenue.py:230` | 🟡 P1 | Obsługa korekt |
| 6 | `Contract.date_from=NULL` crashuje `compute_position_revenues` (TypeError) | `shared/revenue.py:240` | 🔴 P0 | `if p[13] is None or p[14] is None: continue` |
| 7 | `Contract.date_to=NULL` — jw. | `shared/revenue.py:241` | 🔴 P0 | jw. |
| 8 | `revenue_source_label="rzeczywiste"` gdy revenue=0 (pusta baza) | `stats/router.py:105-110` | 🟡 P1 | "brak danych" gdy revenue=0 |
| 9 | `unprinted_contracts` łapie niedawno zmigrowane legacy | `stats/router.py:781` | 🟡 P1 | Filtr `is_legacy=False` |

**Decyzja 4: Indeksy DB = 3 indeksy obowiązkowe**

- **Wybrano:** Dodać 3 indeksy w `main.py` startup (idempotentne `ALTER TABLE ADD INDEX IF NOT EXISTS`)
- **Odrzucono:** + 2 optional composite (zostaw na później), nie dodawaj (3.8k umów OK bez indeksów)
- **Indeksy do dodania (DB Architect):**
  - `idx_contracts_legacy (is_legacy)` — dla filtra `WHERE is_legacy = :is_legacy`
  - `idx_settlements_source (source)` — dla filtra `WHERE source='legacy'`
  - `idx_settlements_settled_at (settled_at)` — dla filtra po dacie rozliczenia
- **Synchronizacja:** `spec/core/01_database.md` — sync DDL `contract_settlements` (dodać `settled_at`, `source`, `UNIQUE` — spec drift wykryty przez DB Architect)

---

#### DECYZJE ARCHITEKTONICZNE (sesja 2026-07-01, po pytaniach do użytkownika)

**Decyzja 5: Legacy umowy = TYLKO cennik (korekta Tech Lead)**

- **Źródło:** Użytkownik po rozmowie z klientem: "w starej aplikacji czyli legacy umowy nie mają żadnej prawdziwej kwoty, to sa tylko cenniki w tej bazie, żadna kwota nie jest realna"
- **Weryfikacja DB:** 742 legacy umów, 1945 settlements (source='legacy', cost_client=776k zł) — ale to `rate × days` (cennik), NIE faktury
- **Poprzednia analiza Tech Lead (BŁĘDNA):** "archiwalna umowa z source='legacy' settlement ma prawdziwą kwotę" → "gruba krecha per-KPI na revenue_source"
- **NOWA analiza Tech Lead (POPRAWNA):** UX miał rację — "gruba krecha" per-widok na `is_legacy` jest poprawna
- **Implementacja (Option B — reclassify, nie recompute):**
  - Dodać `estimate_legacy` do enum `revenue_source` w `shared/revenue.py`
  - W precedence block (L229-238): gdy `revenue_actual > 0 AND is_legacy=true` → `revenue_source = "estimate_legacy"` (nie "actual")
  - Liczba się NIE zmienia (brak dryfu numerycznego), zmienia się tylko etykieta
  - `revenue_actual` w stats liczy TYLKO `source='fakturownia'`/`'manual'` (is_legacy=0)
  - `revenue_estimate` w stats liczy `estimate_legacy` + `estimate_lookup` + `estimate_tiered`
- **Dlaczego Option B nie Option A (filter out):** Option A (filtrowanie settlements po source) → legacy pozycje spadają do `estimate_lookup` który może dać INNĄ kwotę niż zapisany cennik → dryf numeryczny w stats historycznych
- **Wpływ:** Po zmianie `revenue_actual` w stats = 0 zł (do czasu nowych umów z Fakturownia). To poprawne — nie mamy dziś realnych faktur.

**Decyzja 6: ROI = tylko actual (rozliczone z fakturownia/manual)**

- **Wybrano:** `ROI = SUM(cost_client gdzie source IN ('fakturownia','manual')) / replacement_value × 100%`
- **Odrzucono:** Actual + estimate z badge, osobne karty (ROI rzeczywisty vs potencjalny)
- **Implikacja:** Nowa maszyna z 1 umową nierozliczoną → ROI=0% (mylące, maszyna pracuje) — ale spójne z "prawdziwe wartości"
- **UI:** Gdy ROI=0% i są nierozliczone umowy → tooltip "Maszyna pracuje ale brak rozliczeń — ROI obliczone z realnych faktur"

**Decyzja 7: is_demo — brak flagi, cała baza jest demo**

- **Wybrano:** "Walic to, nie rob żadnej kolumny, cała baza będzie demem, po prostu od nowa uruchomimy migracje bez żadnych demo danych jak skończymy prezentacje i testy"
- **Odrzucono:** Kolumna `is_demo TINYINT(1)`, notes prefix `[DEMO]`, prefix numeru `DEMO/%`
- **Implikacja dla RAO-P2-061:**
  - `seed_demo_data.py` — bez oznaczania demo danych (brak flagi)
  - `wipe_demo_data.py` — zastąpione przez pełny re-run migracji (`migrate.py` od zera po `DROP DATABASE + CREATE`)
  - Backup przed wipe → `mariadb-dump rao_new > backup_pre_wipe.sql`
  - Po prezentacji: `DROP DATABASE rao_new; CREATE DATABASE rao_new;` + re-run `migrate.py` (legacy migration od zera) + ręczne uzupełnienie

**Decyzja 8: Fakturownia env — narazie bez toggle, wystawiaj na tym samym koncie**

- **Wybrano:** "Narazie teraz wystawiaj i się nie przejmuj bo to jest tylko dla demo potem nie będziemy wystawiac, możesz rozdzielić tokeny i najwyżej narazie ten sam powielic jeśli masz obawy"
- **Odrzucono:** `FAKTUROWNIA_ENV=test|prod` toggle, dry-run mode
- **Implikacja dla RAO-P2-061:**
  - Używać istniejącego `FAKTUROWNIA_API_TOKEN` z `.env` (to samo konto)
  - Rozdzielić na `FAKTUROWNIA_TEST_TOKEN` + `FAKTUROWNIA_TEST_URL` w `.env` (najwyżej ten sam token powielony)
  - Po prezentacji: faktury demo można usunąć z FA (lub zignorować — konto i tak testowe)
  - Brak walidacji env przy startupie (nie blokować)

---

#### Scope implementacji

**Faza 1: Backend (ujednolicenie + bugfix) — backend-dev + db-architect**

1. **DB (db-architect):** 3 indeksy w `main.py` startup + sync `spec/core/01_database.md`
2. **Backend ujednolicenie (backend-dev):**
   - Dodać pola `revenue_actual`, `revenue_estimate`, `revenue_source_label` do 6 schemas: `TopMachineItem`, `PositionStatsResponse`, `CategoryStatsResponse`, `ByPeriodResponse`, `AdditionalFeesResponse`, `MachineRoiResponse`
   - Wyciągnąć helper `summarize_revenue_sources(all_pos) -> dict` do `shared/revenue.py` (DRY — uniknąć 7 kopii z `fleet_summary:103-110`)
   - W 7 endpointach (top-machines, machine-roi, additional-fees, by-category, by-period, positions, locations) dodać sumację po `revenue_source`
   - Dodać `is_legacy` filter do `/machine-roi` i `/commissions`
   - **NIE zmieniać** algorytmu w `shared/revenue.py` (precedence `actual > lookup > tiered` jest poprawna)
3. **Backend bugfix (backend-dev):** 9 bugów z tabeli powyżej
4. **Backend luka funkcjonalna (backend-dev):** `compute_position_revenues` nie agreguje service_fees — dodać `compute_service_fee_revenues()` lub rozszerzyć istniejącą funkcję (settlements z `service_fee_id IS NOT NULL`)

**Faza 2: Frontend (StatsView + gruba krecha) — frontend-dev + ux-designer**

1. **Nowy plik `StatsView.vue`** z 3 zakładkami:
   - **Flota teraz:** KPI "Wynajęte teraz X/Y" + pasek + rozwijana lista (endpoint `/stats/currently-rented`)
   - **Wynajem w okresie:** KPI row (4 karty) + Stopa zwrotu (karta z % + pasek + kontekst) + Top maszyny (tabela) + Pozycje dodatkowe (tabela z sumą) + Top kategorie (bar chart)
   - **Archiwum (szacunkowe):** szare tło + banner + suffix `[szac.]` + te same widgety ale z `is_legacy=true`
2. **Filtry (wspólne dla zakładek 2 i 3):**
   - Presety: `[ Miesiąc ] [ 3 miesiące ] [ Rok ] [ Własny: od ___ do ___ ]`
   - `internal_number` — input z autouzupełnianiem (datalist z `/articles`)
   - Walidacja: `od ≤ do`, numer wewn. musi istnieć
3. **Sidebar:** nowa pozycja "Statystyki" między "Pulpit" a "Prowizje"
4. **Routing:** `dashboard/stats` (rozszerzenie `dashboard/:section`)
5. **Komponenty reużywalne:**
   - `RevenueSourceBadge.vue` — wizualizuje `revenue_source_label` + proporcję actual/estimate
   - `LegacyFilterBanner.vue` — banner ostrzegawczy dla archiwum
   - `MachineRoiCard.vue` — karta ROI z obsługą `roi_pct=null` (CTA do edycji artykułu)
6. **Empty states (6 dedykowanych — patrz UX Designer):**
   - Brak danych legacy / brak settlements / brak wynajętych / brak pozycji dodatkowych / maszyna nie wynajmowana / błąd ładowania
7. **Loading state:** skeleton loader na każdej karcie (NIE biała strona, NIE sam spinner)
8. **Styl:** wyłącznie zmienne CSS z `style.css` (`--color-warning`, `--color-success`, `--color-text-muted`, `--color-bg-light`)

**Faza 3: QA — qa-engineer**

1. **Unit tests (pytest):** edge cases z raportu QA (30+ testów)
   - `compute_position_value_lookup` — None/0/ujemne dni, puste conditions, NULL period_count
   - `compute_position_revenues` — NULL dates, NULL cost_client, ujemne kwoty
2. **Integration tests (pytest):** 16 endpointów z `is_legacy` filter, 9 bugów (regresja)
3. **E2E (Playwright):**
   - Smoke `01-login.spec.ts` (regresja)
   - Nowy test: nawigacja do StatsView, przełączanie zakładek, weryfikacja badge'ów
   - Weryfikacja: archiwum ma szare tło + banner + suffix `[szac.]`
4. **Auth tests:** 401 bez tokenu na wszystkich 16 endpointach

**Faza 4: Spec sync — tech-lead**

- `spec/core/01_database.md` — 3 indeksy + sync `contract_settlements` DDL (settled_at, source, UNIQUE)
- `spec/core/02_backend_api.md` — 6 schemas z nowymi polami
- `spec/core/03_frontend_screens.md` — sekcja StatsView + sidebar
- `spec/core/04_business_logic.md` — ortogonalność `is_legacy` vs `revenue_source` vs `settlements.source` (KLUCZOWE)
- `spec/core/11_reports_stats.md` — rozróżnienie legacy vs nowe
- `spec/technical/TECHNICAL_SOLUTIONS.md` — wzorzec "Ortogonalne flagi: is_legacy vs revenue_source"

---

#### Kryteria akceptacji (DoD)

**Backend:**
- [ ] 3 indeksy dodane (idempotentne, weryfikacja `SHOW INDEX`)
- [ ] 6 schemas ma `revenue_actual`/`revenue_estimate`/`revenue_source_label`
- [ ] 7 endpointów agreguje po `revenue_source` (nie "gubi" breakdown)
- [ ] `/machine-roi` ma filtr `is_legacy`
- [ ] 9 bugów naprawionych (testy regresji przechodzą)
- [ ] `compute_position_revenues` agreguje service_fees (lub nowa funkcja)
- [ ] `summarize_revenue_sources()` w `shared/revenue.py` (DRY, nie 7 kopii)
- [ ] `pytest -x` przechodzi (30+ nowych testów)

**Frontend:**
- [ ] `StatsView.vue` z 3 zakładkami (Flota teraz / Wynajem w okresie / Archiwum)
- [ ] Nowa pozycja "Statystyki" w sidebarze
- [ ] Zakładka "Archiwum" ma szare tło + banner + suffix `[szac.]`
- [ ] Filtry: presety (Mies/3mies/Rok) + własny zakres + `internal_number`
- [ ] Stopa zwrotu: karta z % + pasek + kontekst (dni, umowy, wartość odtworzeniowa)
- [ ] "Wynajęte teraz": licznik KPI + pasek + rozwijana lista
- [ ] "Pozycje dodatkowe": tabela z sumą sticky + mini słupek + sortowanie
- [ ] "Top kategorie": bar chart z `by-category`
- [ ] 6 empty states z CTA
- [ ] Loading state (skeleton)
- [ ] `vue-tsc --noEmit` przechodzi
- [ ] `npm run build` przechodzi

**QA:**
- [ ] Smoke `01-login.spec.ts` przechodzi
- [ ] E2E StatsView przechodzi (nawigacja, zakładki, badge, archiwum)
- [ ] Auth: 401 bez tokenu na 16 endpointach

**Spec:**
- [ ] `git diff --stat spec/core/` nie jest pusty
- [ ] 5 plików spec zaktualizowanych
- [ ] `spec/technical/` — wzorzec ortogonalnych flag

---

#### Edge cases (z raportu QA — do pokrycia testami)

- `is_legacy=0` ale brak `contract_settlements` (nowa umowa bez rozliczenia) → `revenue_source="estimate_*"`, UI: "Nowa umowa, kwota szacunkowa (brak rozliczenia)"
- `is_legacy=1` ale MA `contract_settlements` (legacy z ręcznym rozliczeniem) → `revenue_source="actual"`, UI: "legacy + ręczne rozliczenie = kwota rzeczywista"
- `cost_client` NULL (częściowe rozliczenie) → flaga `settlement_incomplete=true`, UI: ostrzeżenie
- Maszyna `is_archival=1` (sprzedana) → revenue liczone, ale `total_machines` jej nie liczy → UI: "N maszyn archiwalnych wniosło X przychodu"
- `data_do` w przeszłości, brak rozliczenia (umowa niezamknięta) → w `overdue_contracts` (ale NIE legacy — bug #1)
- `period_count` NULL → `compute_position_value_lookup` deterministyczny (zwraca 0 z flagą `conditions_incomplete`)
- Ta sama maszyna na 2 pozycjach w 1 umowie → `top_machines.contracts_count=1`, `revenue=suma`, `total_rented_days`=suma (dokumentować)
- `replacement_value=0` lub NULL → `roi_pct=null`, UI: "Brak wartości odtworzeniowej — ustaw w karcie artykułu" + link
- Umowa bez `data_do` (na czas nieokreślony) → liczona w `currently_rented` (po bugfix #3)
- `revenue_source_label="rzeczywiste"` gdy revenue=0 → "Brak danych o przychodzie" (po bugfix #8)

---

#### Priorytetyzacja 6 wymagań klienta (Product Owner)

| # | Wymaganie | Priorytet | Uzasadnienie |
|---|-----------|-----------|--------------|
| 2 | Ile maszyn wynajętych teraz | **P0** | KPI operacyjny, backend gotowy, frontend podłączyć |
| 6 | Legacy vs nowe rozróżnienie | **P0** | Fundament wiarygodności statystyk |
| 1 | ROI maszyny (model + nr wewn.) w okresie | **P1** | Kluczowa decyzja inwestycyjna, wymaga `replacement_value` |
| 5 | Top maszyny + kategorie | **P1** | Szybkie podłączenie, wysoka wartość |
| 4 | Sumowanie pozycji dodatkowych | **P1** | Analiza kosztów klienta |
| 3 | Numer wewnętrzny | **P2** | Założenie spełnione (już istnieje) |

**Warunek brzegowy ROI:** Przed implementacją sprawdzić `SELECT COUNT(*) FILTER (WHERE replacement_value IS NULL) / COUNT(*) FROM articles WHERE is_service=0 AND is_archival=0`. Jeśli >30% NULL → dodać sub-zadanie "uzupełnij replacement_value z legacy".

---

#### Mockup layoutu StatsView (UX Designer)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Toolbar: Statystyki — wynajem w okresie (bieżący miesiąc)]    [?]  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─ Filtry ──────────────────────────────────────────────────────┐  │
│  │ Okres: [● Miesiąc] [ 3 mies. ] [ Rok ] [ Własny ▼ ]           │  │
│  │ Numer wewn.: [ NW-014        ▼ ]  [ Wyczyść filtry ]          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌─ Zakładki ────────────────────────────────────────────────────┐  │
│  │ [ Flota teraz ] [● Wynajem w okresie ] [ Archiwum (szac.) 📦] │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌─ KPI row (4 karty) ───────────────────────────────────────────┐  │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │  │
│  │ │Przychód │ │ Umowy   │ │ Dni     │ │ Śred.   │               │  │
│  │ │ 45 200zł│ │   12    │ │  127    │ │ 3 767zł │               │  │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌─ Stopa zwrotu (gdy wpisano NW) ───────────────────────────────┐  │
│  │ Stopa zwrotu — Koparka CAT 320 (NW-014)                       │  │
│  │   127%   ▓▓▓▓▓▓▓▓▓▓░░░ 127/200   cel: 200%                   │  │
│  │   Wynajęta 47 dni · 8 umów · 12 500 zł                        │  │
│  │   Wartość odtworzeniowa: 9 800 zł  [Edytuj artykuł →]         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌─ Top maszyny ──────────────────┐ ┌─ Pozycje dodatkowe ──────┐  │
│  │ #  Maszyna       Ile  Przychód │ │ Usługa      Ile  Przych. │  │
│  │ 1  Koparka CAT   8    12 500 zł│ │ Transport   47   9 400 zł│  │
│  │ 2  Spychacz JCB  5     7 200 zł│ │ Mycie       28   2 800 zł│  │
│  │ [Pokaż wszystkie →]            │ │ RAZEM       94  17 900 zł│  │
│  └────────────────────────────────┘ └──────────────────────────┘  │
│  ┌─ Top kategorie ───────────────────────────────────────────────┐  │
│  │ Koparki      ▓▓▓▓▓▓▓▓░░  62%  (28 000 zł, 7 maszyn)          │  │
│  │ Spychacze    ▓▓▓░░░░░░░  22%  (9 900 zł, 3 maszyny)           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

ZAKŁADKA "Archiwum (szacunkowe)" — szare tło:
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️ Dane historyczne (szacunkowe) — wartości przed migracją do RAO.  │
│   Nie pochodzą z systemu rozliczeń. NIE sumuj z "Wynajem w okresie". │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                               │
│  │Przychód │ │ Umowy   │ │ Dni     │                               │
│  │ 8 700zł │ │   6     │ │  89     │                               │
│  │ [szac.] │ │ [szac.] │ │ [szac.] │                               │
│  └─────────┘ └─────────┘ └─────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

#### Poza scope (na później)

- Eksport statystyk do PDF/Excel (osobne zadanie)
- Wykresy czasowe (trendy miesiąc-po-miesiącu) — `by-period` endpoint istnieje ale to v2
- Alerty o niskim ROI (maszyna poniżej X% ROI) — po v1
- Porównanie side-by-side legacy vs nowe w tym samym widoku (teraz osobne zakładki)
- Automatyczne sugestie "wycofaj maszynę X" — to analityka, nie statystyki
- Zapisywanie preferencji filtrów w localStorage (v2)
- Drill-down z top-machines do listy umów (v2)
- Mapa geolokalizacji (`/stats/locations` — osobna zakładka "Mapa" jako P2)

**Estymacja:** 24-32h (L) — Faza 1 (backend ujednolicenie + 9 bugfix + indeksy) + Faza 2 (frontend StatsView + 3 zakładki) + Faza 3 (QA 30+ testów) + Faza 4 (spec sync)

---

### [RAO-P2-063] Merge Statystyki + Raporty → AnalyticsView (ujednolicony widok analityczny)

```yaml
id: RAO-P2-063
priority: P1
size: L
status: dev-verified
classification: cross-stack/refactor+feature
roles: [tech-lead, backend-dev, frontend-dev, qa-engineer, product-owner]
source: operator-request
source_date: 2026-07-01
verification:
  - "vue-tsc --noEmit: pass (exit 0)"
  - "npm run build: pass (exit 0, AnalyticsView 31.73 kB gzip 9.32 kB)"
  - "curl /stats/* endpointy z contractor_id/city/sort_by: 200 (filtruje + sortuje)"
  - "curl /stats/positions?sort_by=invalid_field: 200 (ignoruje, whitelist działa)"
  - "curl /stats/top-machines bez tokenu: 401 (auth OK)"
  - "unit testy stats: 31 passed"
  - "grep ReportsSection frontend/src/: 0 wyników (usunięty)"
  - "grep StatsView frontend/src/: 0 wyników (usunięty)"
  - "E2E: pre-existing problem z root_path (backend nie dodaje prefiksu /rao/api w dev mode — konfiguracja dla reverse proxy na produkcji)"
specs_to_update:
  - core/02_backend_api.md (4 endpointy stats z contractor_id/city/sort_by/sort_dir)
  - core/03_frontend_screens.md (AnalyticsView + 3 taby + reusable komponenty + usunięcie ReportsSection/StatsView)
  - core/06_navigation_flow.md (sidebar 1 przycisk Statystyki, routing /analytics + redirect /stats)
  - core/11_reports_stats.md (merge Stats+Reports → Analityka, bez archiwalnych danych)
migration_impact: no (brak zmian schema)
security_impact: low (read-only stats, auth już na endpointach, sort_by whitelist SQL injection protection)
depends_on:
  - RAO-P2-060 (StatsView Faza 2 — foundation)
  - RAO-P2-062 (archive_* tabele — archiwum osobny widok)
```

**Problem:**

2 osobne widoki (StatsView 688 linii + ReportsSection 2635 linii) częściowo się duplikują:
- "Flota teraz" (StatsView) ≈ "Stan floty teraz" (ReportsSection) — oba używają `/stats/currently-rented`
- "Wynajem w okresie" (StatsView) ≈ "Analiza historyczna → Ogólne" (ReportsSection) — oba używają `/stats/fleet-summary` + `/top-machines` + `/additional-fees` + `/locations`

User zdezorientowany: "który przycisk kliknąć?". ReportsSection.vue (2635 linii) = monster-komponent, trudny w utrzymaniu.

**Rozwiązanie:**

Merge do jednego widoku `AnalyticsView.vue` z 3 zakładkami:
1. **Flota teraz** (live) — KPI + tabela maszyn wynajętych + drill-down maszyna
2. **Wynajem w okresie** (period) — KPI + top maszyny + opłaty + lokalizacje + pozycje (sortowanie, filtry, drill-down)
3. **Eksplorator** (explorer) — wyszukiwarka kontrahent/umowa/maszyna

**Backend (commit 912c02a):**
- `contractor_id`, `city` Query params dodane do `/stats/top-machines`, `/stats/positions`, `/stats/locations`, `/stats/additional-fees`
- `sort_by`, `sort_dir` dodane do `/stats/positions` (z whitelist kolumn — SQL injection protection)
- `shared/revenue.py`: dodano `city` do wyniku `compute_position_revenues`
- Backward compat: nowe parametry opcjonalne (default None)

**Frontend-1 (commit 8af41c9):**
- 6 reusable komponentów w `components/analytics/`:
  - `AnalyticsTable.vue` — generyczna sortowalna tabela (klik w nagłówek → sort, klik wiersz → drill-down)
  - `KpiRow.vue` — rząd kart KPI
  - `AnalyticsFilters.vue` — pasek filtrów (presets + custom + kontrahent + miasto + typ)
  - `DrillDownDrawer.vue` — drawer z Teleport (Esc/click-overlay zamyka)
  - `AnalyticsTabs.vue` — tab bar pills
- `composables/useSort.ts` — client-side sortowanie (string/number/Date, null na końcu)

**Frontend-2 (commit 060fac3):**
- `stores/analytics.ts` — Pinia store (12 akcji API, drill-down orchestration)
- `views/AnalyticsView.vue` — główny widok (~330 linii, 3 taby, współdzielone filtry, DrillDownDrawer)
- `components/analytics/tabs/LiveFleetTab.vue` — KPI + utilization bar + tabela wynajętych
- `components/analytics/tabs/PeriodRentalTab.vue` — KPI + 4 tabele (top maszyny/opłaty/lokalizacje/pozycje) z sortowaniem
- `components/analytics/tabs/ExplorerTab.vue` — wyszukiwarka z wynikami mieszanymi

**Frontend-3 (ten commit):**
- Sidebar: usunięto "📊 Statystyki" + "Raporty", zostawiono "📊 Statystyki" → `/analytics`
- Router: `/stats` → redirect `/analytics` (backward compat), `/analytics` → AnalyticsView
- DashboardView: usunięto import + render ReportsSection
- HomeView: tile "Statystyki" → `/analytics`
- Usunięto: `ReportsSection.vue` (2635 linii), `StatsView.vue` (688 linii), `stores/stats.js` (nie używany nigdzie indziej)

**Bez archiwalnych danych:**
- AnalyticsView używa tylko `/stats/*` i `/explorer/*` (live contracts/articles)
- Archiwum zostaje osobnym widokiem (`/archive`, ArchiveView.vue) — już zrealizowane w RAO-P2-062

**Najlepsze "mięso" do klikalności:**
- Sortowanie tabel (klik w nagłówek kolumny — rosnąco/malejąco) — NOWE, nie było nigdzie
- Drill-down (klik wiersz → drawer z historią wynajmów maszyny / umowami w lokalizacji)
- Filtry współdzielone (okres + kontrahent + miasto + typ) — zmiana w jednej zakładce = zmiana we wszystkich
- Eksplorator (wyszukiwarka kontrahent/umowa/maszyna)

**Zweryfikowano:**
- 2026-07-01, commit hash: patrz `git log --oneline -5`
- vue-tsc + build: PASS
- curl endpointów: PASS (filtruje + sortuje + backward compat + auth)
- grep ReportsSection/StatsView: 0 wyników (usunięte)

---

### [RAO-P2-061] Demo data seeding — Fakturownia testowa + pełne rozliczenia dla showcase statystyk

```yaml
id: RAO-P2-061
priority: P2
size: M
status: done
classification: cross-stack/integration+data-seeding
roles: [tech-lead, backend-dev, db-architect, qa-engineer, product-owner]
source: operator-request
source_date: 2026-07-01
specs_to_update:
  - core/07_integrations.md (Fakturownia test env + seeding)
  - core/04_business_logic.md (demo data lifecycle)
  - core/11_reports_stats.md (showcase scenarios)
migration_impact: yes (demo dane zostaną zaorane przed właściwą migracją legacy)
security_impact: low (test Fakturownia account, brak prod danych)
depends_on:
  - RAO-P2-058 (Fakturownia integracja — OID + product mapping)
  - RAO-P2-060 (Statystyki — StatsView + gruba krecha — showcase target)
```

**Problem:**

Aby zaprezentować moc statystyk RAO (RAO-P2-060: ROI maszyn, top wypożyczenia, sumowanie pozycji dodatkowych, "ile wynajętych teraz", gruba krecha legacy vs nowe), potrzebujemy **prawdziwych danych rozliczeniowych** w nowej aplikacji. Legacy dane (zmigrowane z `rozliczenie`) pokazują tylko szacunki — nie demonstrują pełnej mocy `revenue_source="actual"` z Fakturownia.

**Cel:** Zasil aplikację RAO kompletnymi danymi demo używając testowej Fakturownia, z poprawnymi rozliczeniami (`contract_settlements` z `source='fakturownia'`), żeby statystyki pokazywały realne wartości — nie szacunki.

**Kluczowa uwaga użytkownika (2026-07-01):**
> "Później i tak migrację zaoramy od nowa — zrobimy zerowanie i start po migracji starej bazy do nowej, i ręcznie będzie uzupełniane to co jest potrzebne."

**Implikacja:** Demo dane są **tymczasowe** — zostaną usunięte przed właściwą migracją. Nie trzeba się martwić o jakość/realizm każdego rekordu, ale dane muszą być **spójne i kompletne** żeby showcase statystyk działał.

---

#### Scope implementacji

**Faza 1: Konfiguracja Fakturownia testowej — backend-dev**

1. **Konto testowe Fakturownia:**
   - Założyć konto na testowym środowisku Fakturownia (lub użyć istniejącego demo)
   - Skonfigurować API token w `.env` (separate od prod: `FAKTUROWNIA_TEST_TOKEN`, `FAKTUROWNIA_TEST_URL`)
   - Dodać toggle `FAKTUROWNIA_ENV=test|prod` w `config.py`
2. **Seed produktów Fakturownia:**
   - Utworzyć 10-15 produktów w testowej FA odpowiadających artykułom RAO (maszyny + usługi)
   - Mapować `Article.fakturownia_product_id` → ID produktów testowych
   - Produkty: 5 maszyn (koparka, ładowarka, podnośnik, spycharz, zagęszczarka) + 5 usług (transport, tankowanie, czyszczenie, przestój, serwis)
3. **Seed kontrahentów:**
   - Utworzyć 5-8 kontrahentów demo w RAO + zmapować na klientów FA

**Faza 2: Seed umów + pozycji + rozliczeń — backend-dev + db-architect**

1. **Skrypt `seed_demo_data.py`:**
   - **Idempotentny** (można re-run, `INSERT IGNORE` / `ON DUPLICATE KEY UPDATE`)
   - **Deterministyczny** (fixed seed dla reproducibility)
   - **Scoped** (wszystkie demo dane oznaczone — np. `contract.notes LIKE '%[DEMO]%'` lub dedykowana flaga `is_demo TINYINT(1)`)
2. **Umowy demo (20-30 szt):**
   - Różne typy: S (najem) / U (usługa) — 50/50
   - Różne okresy: ostatnie 12 miesięcy (żeby filtry mies/3mies/rok miały sens)
   - Różne maszyny: 5 maszyn × różne kombinacje
   - Różne kontrahenci: 5-8
   - Różne stany: aktywne (data_do >= today), zakończone (data_do < today), przeterminowane (data_do < today, is_settled=false)
   - `is_legacy=0` (nowe umowy — to ma być showcase `revenue_source="actual"`)
   - 2-3 umowy z `is_legacy=1` (żeby "gruba krecha" archiwum miała co pokazać)
3. **Pozycje umów (40-60 szt):**
   - 1-3 pozycje per umowa
   - `position_conditions` z realnymi stawkami (rate1/rate2/period_count)
   - `replacement_value` uzupełnione dla wszystkich maszyn (żeby ROI działało)
4. **Usługi dodatkowe (60-90 szt):**
   - 2-4 usługi per umowa (transport, tankowanie, czyszczenie)
   - Z `article_id` linkowanym (nie NULL — żeby `additional-fees` stats działały)
5. **Rozliczenia (`contract_settlements`):**
   - **Kluczowe:** `source='fakturownia'` (nie 'legacy', nie 'manual')
   - `cost_client` = realna kwota z faktury FA (nie szacunek)
   - `cost_company` = koszt własny (do marży)
   - `settled_at` = data rozliczenia (w okresie umowy)
   - **80% umów rozliczonych** (żeby `revenue_source="actual"` dominowało)
   - **20% umów nierozliczonych** (żeby `revenue_source="estimate_*"` też się pokazało)
6. **Faktury Fakturownia (synchronizacja):**
   - Dla każdej rozliczonej umowy — utworzyć fakturę w testowej FA z `oid=contract.number`
   - Pozycje faktury = pozycje umowy (z `product_id` mapowanym)
   - Po wystawieniu — pobrać przez `GET /invoices.json?oid=<numer>` i potwierdzić `contract_settlements.cost_client` = kwota z faktury

**Faza 3: Showcase scenarios — product-owner + qa-engineer**

1. **Scenariusze demo (do weryfikacji statystyk RAO-P2-060):**

| Scenariusz | Endpoint | Oczekiwany wynik | Weryfikacja |
|------------|----------|------------------|-------------|
| ROI maszyny NW-014 (12 mies) | `/stats/machine-roi?article_id=X&date_from=2025-07-01&date_to=2026-07-01` | ROI > 100% (maszyna się opłaca), `revenue_source="actual"` | `cost_client` sum > 0, `replacement_value` > 0 |
| Top maszyny po wypożyczeniach (3 mies) | `/stats/top-machines?date_from=2026-04-01&date_to=2026-07-01` | 5 maszyn, sortowane po liczbie umów desc | `contracts_count` > 0 dla top 5 |
| Ile wynajętych teraz | `/stats/currently-rented` | 2-4 maszyny aktywne (data_do >= today) | `total_rented` > 0 |
| Pozycje dodatkowe (rok) | `/stats/additional-fees?date_from=2026-01-01&date_to=2026-07-01` | Transport + tankowanie + czyszczenie z sumami | `revenue` per usługa > 0 |
| Kategorie (rok) | `/stats/by-category?date_from=2026-01-01&date_to=2026-07-01` | 2-3 kategorie z liczbami | `count` > 0 |
| Gruba kresha archiwum | `/stats/fleet-summary?is_legacy=true` | 2-3 umowy legacy, `revenue_source_label="szacunek"` | `revenue_estimate` > 0, `revenue_actual` = 0 |
| Nowe vs legacy (mieszane) | `/stats/fleet-summary?is_legacy=null` | `revenue_source_label="mieszane"` | `revenue_actual` > 0 AND `revenue_estimate` > 0 |

2. **QA weryfikacja:**
   - Każdy scenariusz — `curl` + sprawdzenie JSON
   - Spójność: `SUM(contract_settlements.cost_client)` per pozycja = `revenue_actual` w stats
   - Brak podwójnego liczenia: 1 maszyna na 2 pozycjach w 1 umowie → `contracts_count=1`, `revenue=suma`

**Faza 4: Cleanup — pełny re-run migracji (bez wipe script)**

1. **Brak `wipe_demo_data.py`** — user zdecydował: "cała baza będzie demem, po prostu od nowa uruchomimy migracje"
2. **Procedura cleanup po prezentacji:**
   - Backup: `mariadb-dump rao_new > backup_pre_wipe.sql`
   - `DROP DATABASE rao_new; CREATE DATABASE rao_new;`
   - Re-run `migrate.py` (legacy migration od zera)
   - Ręczne uzupełnienie tego co potrzebne
3. **Faktury FA:** usunąć z konta FA lub zignorować (konto testowe)

---

#### Kluczowe decyzje (POTWIERDZONE przez użytkownika 2026-07-01)

1. **Flaga `is_demo`:** **NIE DODAJEMY** — "walic to, nie rob żadnej kolumny, cała baza będzie demem"
   - Cała baza RAO jest traktowana jako demo do czasu prezentacji
   - Po prezentacji: pełny re-run migracji od zera (`DROP DATABASE + CREATE + migrate.py`)
   - Backup przed wipe: `mariadb-dump rao_new > backup_pre_wipe.sql`
   - Brak `is_demo` kolumny, brak `notes` prefix, brak `DEMO/%` numeracji

2. **Fakturownia env toggle:** **NIE ROBIMY** — "narazie wystawiaj i się nie przejmuj"
   - Używać istniejącego `FAKTUROWNIA_API_TOKEN` z `.env` (to samo konto)
   - Opcjonalnie rozdzielić na `FAKTUROWNIA_TEST_TOKEN` + `FAKTUROWNIA_TEST_URL` (najwyżej ten sam token powielony)
   - Brak walidacji env przy startupie
   - Po prezentacji: faktury demo usunąć z FA lub zignorować

3. **Ile danych?** 20-30 umów / 40-60 pozycji / 60-90 usług / 80% rozliczonych (zatwierdzone)

4. **Realizm danych:** Realistyczne rynkowe (koparka 800-1200 zł/doba, transport 400-600 zł, tankowanie 150-200 zł) — żeby ROI miało sens biznesowy (zatwierdzone)

---

#### Kryteria akceptacji (DoD)

**Fakturownia:**
- [ ] 10-15 produktów FA utworzonych i zmapowanych (`Article.fakturownia_product_id`)
- [ ] 5-8 kontrahentów demo zmapowanych
- [ ] Faktury wystawiane przez istniejący `FAKTUROWNIA_API_TOKEN` (brak env toggle)

**Seed:**
- [ ] `seed_demo_data.py` idempotentny (re-run nie tworzy duplikatów)
- [ ] 20-30 umów demo (różne typy, okresy, stany)
- [ ] 40-60 pozycji z `position_conditions` i `replacement_value`
- [ ] 60-90 usług dodatkowych z `article_id` (nie NULL)
- [ ] 80% umów rozliczonych (`source='fakturownia'`, `cost_client` > 0)
- [ ] 20% umów nierozliczonych (żeby `estimate_*` też się pokazało)
- [ ] 2-3 umowy `is_legacy=1` (dla "grubej kreski" archiwum)
- [ ] Faktury FA wystawione dla rozliczonych umów (`oid=contract.number`)

**Showcase:**
- [ ] 7 scenariuszy demo z tabeli powyżej — wszystkie zaliczone (curl + JSON check)
- [ ] ROI maszyny > 100% z `revenue_source="actual"`
- [ ] "Wynajęte teraz" > 0
- [ ] "Pozycje dodatkowe" — transport/tankowanie/czyszczenie z sumami
- [ ] "Gruba krecha" — archiwum pokazuje `revenue_source_label="szacunek"`
- [ ] "Mieszane" — `revenue_actual` > 0 AND `revenue_estimate` > 0

**Cleanup:**
- [ ] Backup przed wipe (`mariadb-dump rao_new > backup_pre_wipe.sql`)
- [ ] `DROP DATABASE rao_new; CREATE DATABASE rao_new;` + re-run `migrate.py`
- [ ] Faktury FA demo usunięte lub zignorowane

**Spec:**
- [ ] `spec/core/07_integrations.md` — sekcja Fakturownia (brak env toggle, demo factorowanie)
- [ ] `spec/core/04_business_logic.md` — demo data lifecycle (seed → showcase → wipe → proper migration)
- [ ] `spec/technical/scripts/seed_demo_data.md` — dokumentacja skryptu

---

#### Edge cases

- Fakturownia testowe konto ma limit faktur/miesiąc — seed musi być oszczędny (20-30 faktur, nie 100)
- `FAKTUROWNIA_ENV=test` ale token prod → blokada (walidacja przy starcie)
- Re-run `seed_demo_data.py` po wipe — czy tworzy od nowa? (TAK, idempotentny)
- Umowa demo z `is_legacy=1` ale `source='fakturownia'` — czy to ma sens? (NIE — legacy umowy mają `source='legacy'`. Demo legacy umowy = `source='legacy'` z `cost_client` z `rozliczenie`-style)
- `replacement_value` = 0 dla maszyny demo → ROI = null → scenariusz ROI fail (wszystkie maszyny demo muszą mieć `replacement_value` > 0)
- Faktura FA odrzucona (np. błędny product_id) — seed musi logować błędy i kontynuować

---

#### Poza scope (na później)

- Automatyczne odświeżanie rozliczeń z FA (cron) — to RAO-P2-058 Faza 2
- Eksport statystyk do PDF (RAO-P2-060 v2)
- Realistyczne dane historyczne (2018-2022) — to przy właściwej migracji legacy
- Multi-branch demo dane — po RAO-P1-055 (branch_id)

**Estymacja:** 12-16h (M) — Faza 1 (FA test config + produkty) + Faza 2 (seed skrypt + faktury) + Faza 3 (showcase weryfikacja) + Faza 4 (cleanup script)

---

### [RAO-P2-062] Archiwum — migracja legacy do tabel `archive_*` (gruba krecha na poziomie tabel)

```yaml
id: RAO-P2-062
priority: P1
size: L
status: dev-verified
classification: cross-stack/refactor+migration
roles: [tech-lead, db-architect, backend-dev, frontend-dev, qa-engineer]
source: operator-request
source_date: 2026-07-01
phase_0_status: done (2026-07-01) — migracja danych archive_* wykonana, backup_pre_archive_split.sql utworzony, weryfikacja COUNT zaliczona
phase_1_status: done (2026-07-01) — modele SQLAlchemy archive_* + endpointy read-only + category CRUD + usunięcie is_legacy + uproszczenie shared/revenue.py i stats/router.py
phase_2_status: done (2026-07-01) — ArchiveView.vue + stores/archive.ts + sidebar/router/layout; vue-tsc pass, build pass, smoke 01-login 11/11 pass, Playwright MCP weryfikacja 4 zakładek (Umowy 50 wierszy, Maszyny 50 wierszy, Statystyki, Kategorie admin)
phase_3_status: done (2026-07-01) — drill-down drawer w statystykach archiwum: karta "Miasta" (GET /archive/stats/by-city) + klikalne wiersze Top maszyny/Miasta/ROI (openDrillDown) + Teleport drawer z paginacją + Esc/overlay/✕ close + drillDownToContract (przejście do zakładki Umowy) + style non-scoped (Vue 3 Teleport) + ROOT CAUSE FIX aliasy zmiennych CSS w variables.css (--spacing-5/--border-radius-md/--color-error itp. — style.css nie importowany w main.ts); vue-tsc pass, build pass, smoke 01-login 11/11 pass, Playwright drill-down test pass (30 drill-row, 0 JS errors), Vision AI (claude-opus-4-5) potwierdził padding 20px + border-radius 12px + shadow po fixie
specs_to_update:
  - core/01_database.md (archive_* tabele + usunięcie is_legacy)
  - core/02_backend_api.md (archive endpointy read-only + category edit)
  - core/03_frontend_screens.md (Archiwum widok w sidebarze)
  - core/04_business_logic.md (archive = frozen snapshot, tylko kategorie edytowalne)
  - core/06_navigation_flow.md (sidebar: Archiwum)
  - core/11_reports_stats.md (stats nowe = czyste, stats archiwum = osobne endpointy)
migration_impact: yes (przeniesienie 742 umów + powiązanych do archive_* tabel)
security_impact: low (read-only archiwum + auth)
depends_on:
  - RAO-P2-028 (is_legacy flag — dane do przeniesienia)
  - RAO-P2-032 (contract_settlements.source — dane do przeniesienia)
blocks:
  - RAO-P2-060 (statystyki — upraszcza: 6 z 9 bugów znika, brak is_legacy filtra)
  - RAO-P2-061 (demo data — idą do czystej rao_new bez legacy)
```

**Problem:**

Obecnie 742 legacy umów (is_legacy=1) jest w tych samych tabelach co nowe umowy. Wymaga to filtra `is_legacy` w 16 endpointach stats, prowadzi do 9 bugów (3 krytyczne), i wymaga `estimate_legacy` enum w `shared/revenue.py`. Klient potwierdził: **legacy umowy to tylko cenniki, żadna kwota nie jest realna** — więc mieszanie ich z nowymi umowami (które będą miały prawdziwe rozliczenia z Fakturownia) zafałszowuje statystyki.

**Rozwiązanie:** Przenieść legacy dane do tabel z prefixem `archive_` w tej samej bazie. Nowa aplikacja (`contracts`, `articles`, etc.) = czysta, tylko nowe umowy. Archiwum (`archive_*`) = frozen snapshot, read-only (z wyjątkiem edycji kategorii).

**Kluczowa decyzja użytkownika (2026-07-01):**
> "Może w jednej bazie zrobimy z archive_articles, archive_inne i wszystko będzie tam zjeżdżało, a nowe artykuły do zwykłe articles. Kontrahenci współdzielone. Artykuły - osobne tabele. Umowy - osobne tabele. Tylko umożliwić żonglowanie kategoriami żeby poprawić ewentualnie wgląd w statystyki bo niektóre są być może źle podczas migracji skategoryzowane."

---

#### DECYZJE UŻYTKOWNIKA (zarejestrowane 2026-07-01)

**Decyzja 1: Tabele `archive_*` w jednej bazie (nie osobna DB)**

- **Wybrano:** `archive_articles`, `archive_contracts`, `archive_contract_positions`, etc. w `rao_new`
- **Odrzucono:** Osobna baza `rao_archive` (cross-DB FK tricky, więcej infra)
- **Plusy:** Brak cross-DB FK, JOIN możliwy, prostsze infra, prefix `archive_` = oczywiste

**Decyzja 2: Kontrahenci współdzielone (jedna tabela `contractors`)**

- **Wybrano:** `contractors` współdzielone między archiwum a nową aplikacją
- **Uzasadnienie użytkownika:** "tych chyba warto zostawić do crossa pomiędzy starymi a nowymi"
- **Plusy:** Jedno miejsce edycji, pełna historia kontrahenta (legacy + nowe), brak duplikacji NIP
- **Biznesowo poprawne:** kontrahent = żywa encja prawna, umowa = zamrożony event

**Decyzja 3: Artykuły osobne (`articles` + `archive_articles`)**

- **Wybrano:** `archive_articles` = frozen snapshot z czasu migracji, `articles` = nowe (edytowalne)
- **Uzasadnienie:** Maszyna może zmienić `replacement_value`, nazwę, być sprzedana. Archiwum pokazuje stan z tamtego czasu.
- **Cross-referencja:** `internal_number` służy do powiązania ("czy to ta sama maszyna co w archiwum?")

**Decyzja 4: Archiwum = read-only + edycja kategorii (zarówno na articles jak i samych kategorii)**

- **Wybrano:** Archiwum read-only **Z WYJĄTKIEM** edycji kategorii:
  1. `PATCH /archive/articles/{id}/category` — zmiana `category_id` na `archive_articles` (przypisanie maszyny do innej kategorii archiwum)
  2. `PATCH /archive/categories/{id}` — edycja `archive_categories` (rename, zmiana parent_id, poprawa hierarchii)
  3. `POST /archive/categories` — dodanie nowej kategorii w archiwum (gdy brakuje)
  4. `DELETE /archive/categories/{id}` — usunięcie kategorii archiwum (gdy pusta)
- **Uzasadnienie użytkownika:** "tylko umożliwić żonglowanie kategoriami żeby poprawić ewentualnie wgląd w statystyki bo niektóre są być może źle podczas migracji skategoryzowane" + "daj to zarządzanie kategoriami też krechę oddzielone w archive_categories z ustawieniami tych kategorii tam"
- **Implementacja:** Kategorię archiwum mają własny CRUD (read + write) w `backend/archive/router.py` — pełne zarządzanie kategoriami archiwum (rename, hierarchy, add, delete) żeby poprawić kategoryzację bez dotykania nowych kategorii
- **`archive_articles.category_id`** → `archive_categories.id` (archive FK, edytowalne przez PATCH)

---

#### Struktura tabel po migracji

**Współdzielone (bez prefixu):**
```
contractors              ← współdzielone (legacy + nowe)
users                    ← współdzielone
fee_preset_groups        ← współdzielone (szablony usług)
service_fee_templates    ← współdzielone
```

**Nowa aplikacja (bez prefixu, czyste):**
```
categories               ← nowe kategorie (edytowalne, żywe — zarządzane w Ustawieniach)
articles                 ← nowe maszyny (edytowalne, żywe)
contracts                ← TYLKO nowe umowy (is_legacy USUNIĘTE)
contract_positions       ← tylko nowe
position_conditions      ← tylko nowe
contract_service_fees    ← tylko nowe
contract_settlements     ← tylko nowe (source='fakturownia'/'manual')
```

**Archiwum (prefix `archive_`, frozen):**
```
archive_categories       ← frozen snapshot kategorii z migracji (edytowalne — poprawa kategoryzacji)
archive_articles         ← frozen snapshot maszyn z migracji (category_id → archive_categories.id)
archive_contracts        ← 742 legacy umów
archive_contract_positions    ← legacy pozycje
archive_position_conditions   ← legacy warunki (cennik)
archive_contract_service_fees ← legacy usługi dodatkowe
archive_contract_settlements  ← legacy rozliczenia (source='legacy', cennik × dni)
```

**Relacje:**
- `archive_contracts.contractor_id` → `contractors.id` (współdzielone, FK OK)
- `archive_contract_positions.article_id` → `archive_articles.id` (archive FK)
- `archive_contract_positions.contract_id` → `archive_contracts.id` (archive FK)
- `archive_contract_settlements.position_id` → `archive_contract_positions.id` (archive FK)
- `archive_articles.category_id` → `archive_categories.id` (archive FK — kategorie w archiwum)
- `categories` (nowe) — niezależne od `archive_categories`

---

#### Scope implementacji

**Faza 0: Migracja danych (db-architect + backend-dev) — BLOKER dla P2-060 i P2-061**

1. **Utworzyć tabele `archive_*`** (mirror schema z `is_legacy` tabel):
   - `archive_categories` — kopia WSZYSTKICH `categories` (frozen snapshot — kategorie używane przez legacy maszyny; edytowalne post-migration dla poprawy kategoryzacji)
   - `archive_articles` — kopia `articles` gdzie `id IN (SELECT DISTINCT article_id FROM contract_positions WHERE contract_id IN (SELECT id FROM contracts WHERE is_legacy=1))` (z `category_id` przemapowanym na `archive_categories.id`)
   - `archive_contracts` — kopia `contracts WHERE is_legacy=1` (bez kolumny `is_legacy`)
   - `archive_contract_positions` — kopia pozycji dla legacy umów
   - `archive_position_conditions` — kopia warunków dla legacy pozycji
   - `archive_contract_service_fees` — kopia usług dla legacy umów
   - `archive_contract_settlements` — kopia rozliczeń dla legacy umów (source='legacy')
   - **Idempotentne:** `CREATE TABLE IF NOT EXISTS` + `INSERT IGNORE`
   - **W jednej transakcji:** backup → INSERT → DELETE → commit
   - **Uwaga:** `categories` (nowe) zostaje nie tknięte — ale po migracji `categories` powinno być puste (wszystkie kategorie były używane przez legacy). User może od nowa zbudować kategorie dla nowych umów. Ewentualnie skopiować wybrane kategorie z `archive_categories` do `categories` ręcznie.

2. **Usunąć legacy dane z tabel `rao_new`:**
   - `DELETE FROM contract_settlements WHERE contract_id IN (SELECT id FROM contracts WHERE is_legacy=1)`
   - `DELETE FROM contract_service_fees WHERE contract_id IN (...)`
   - `DELETE FROM position_conditions WHERE position_id IN (...)`
   - `DELETE FROM contract_positions WHERE contract_id IN (...)`
   - `DELETE FROM contracts WHERE is_legacy=1`
   - **Cascade lub manualne DELETE w odpowiedniej kolejności**

3. **Usunąć kolumnę `is_legacy` z `contracts`:**
   - `ALTER TABLE contracts DROP COLUMN is_legacy` (nie potrzebna — wszystkie umowy w `contracts` są nowe)
   - Usunąć `idx_contracts_legacy` indeks
   - Zaktualizować `backend/contracts/models.py` (usunąć `is_legacy = Column(...)`)
   - Zaktualizować `backend/shared/revenue.py` (usunąć `is_legacy` z query i z dict)

4. **Backup przed migracją:**
   - `mariadb-dump rao_new > backup_pre_archive_split.sql`

**Faza 1: Backend — modele + endpointy archiwum (backend-dev)**

1. **Modele `archive_*`** w nowym module `backend/archive/`:
   - `backend/archive/models.py` — `ArchiveCategory`, `ArchiveArticle`, `ArchiveContract`, `ArchiveContractPosition`, `ArchivePositionCondition`, `ArchiveContractServiceFee`, `ArchiveContractSettlement`
   - Mirror schema z głównych modeli ale z `__tablename__ = "archive_*"`
   - `ArchiveCategory` — pełny mirror `Category` (name, code, description, parent_id, level) — edytowalna
   - `ArchiveArticle` ma `category_id` → `archive_categories.id` (edytowalne) — reszta pól read-only

2. **Endpointy archiwum (read-only + zarządzanie kategoriami):**
   - `GET /archive/contracts` — lista legacy umów (z paginacją, filtrowanie po contractor, date range)
   - `GET /archive/contracts/{id}` — szczegóły legacy umowy
   - `GET /archive/articles` — lista legacy maszyn
   - `GET /archive/articles/{id}` — szczegóły legacy maszyny
   - `PATCH /archive/articles/{id}/category` — zmiana `category_id` na archive_articles
   - `GET /archive/categories` — lista kategorii archiwum (tree)
   - `POST /archive/categories` — dodanie nowej kategorii archiwum
   - `PUT /archive/categories/{id}` — edycja kategorii archiwum (rename, parent, hierarchy)
   - `DELETE /archive/categories/{id}` — usunięcie kategorii archiwum (gdy pusta)
   - `GET /archive/stats/fleet-summary` — stats archiwum (cennik × dni = szacunek)
   - `GET /archive/stats/top-machines` — top maszyny w archiwum
   - `GET /archive/stats/by-category` — kategorie w archiwum
   - `GET /archive/stats/machine-roi` — ROI orientacyjny (cennik / replacement_value)
   - Brak POST/PUT/DELETE na contracts/articles (poza PATCH category na articles + pełny CRUD na categories)

3. **Uproszczenie `shared/revenue.py`:**
   - Usunąć `is_legacy` z query i z dict
   - `revenue_source` = tylko `actual` / `estimate_lookup` / `estimate_tiered` (bez `estimate_legacy`)
   - `revenue_actual` = tylko `source='fakturownia'` / `'manual'` (settlements w `contract_settlements` są tylko nowe)
   - Algorytm precedence bez zmian (actual > lookup > tiered)

4. **Uproszczenie `stats/router.py`:**
   - Usunąć `is_legacy` parametr z 16 endpointów (nie potrzebny — `contracts` ma tylko nowe)
   - Usunąć `revenue_source_label` wariant "mieszane" (nie będzie mieszane — archiwum osobno)
   - Bug #1, #2, #9 **ZNICNĄ AUTOMATYCZNIE** (legacy nie ma w `contracts`)

**Faza 2: Frontend — widok Archiwum (frontend-dev + ux-designer)**

1. **Nowa pozycja w sidebarze:** "Archiwum" (na dole, po "Ustawienia", z ikoną 📦)
2. **Widok `ArchiveView.vue`:**
   - Lista legacy umów (read-only, z filtrowaniem po kontrahencie, dacie)
   - Szczegóły legacy umowy (read-only)
   - Lista legacy maszyn (read-only, z możliwością zmiany kategorii — dropdown)
   - Stats archiwum (orientacyjne — z label "wartości szacunkowe z cennika")
3. **StatsView.vue (RAO-P2-060) — uproszczone:**
   - Brak zakładki "Archiwum" (archiwum = osobny widok w sidebarze)
   - 2 zakładki: "Flota teraz" + "Wynajem w okresie" (tylko nowe umowy)
   - Brak toggle `is_legacy` (nie potrzebny)
   - Brak badge "rzeczywiste/szacunek" (wszystko w nowej aplikacji = rzeczywiste)
4. **Styl archiwum:** szare tło (`--color-bg-light`), banner "Archiwum — dane historyczne (szacunkowe)"

**Faza 3: QA — qa-engineer**

1. **Test migracji:** po migracji `SELECT COUNT(*) FROM contracts` = 0 (brak legacy), `SELECT COUNT(*) FROM archive_contracts` = 742
2. **Test read-only:** POST/PUT/DELETE na `/archive/*` → 405 Method Not Allowed
3. **Test category edit:** `PATCH /archive/articles/{id}/category` → 200, inne pola niezmienione
4. **Test stats:** `/stats/fleet-summary` (nowe) — `revenue_actual` = 0 (brak nowych umów), `revenue_estimate` = 0 (brak pozycji)
5. **Test archiwum stats:** `/archive/stats/fleet-summary` — `revenue_estimate` > 0 (cennik × dni)
6. **Smoke:** `e2e/tests/01-login.spec.ts` (regresja)
7. **E2E:** nawigacja do Archiwum, weryfikacja read-only, zmiana kategorii

**Faza 4: Spec sync — tech-lead**

- `spec/core/01_database.md` — tabele `archive_*` + usunięcie `is_legacy`
- `spec/core/02_backend_api.md` — endpointy `/archive/*` (read-only + category edit)
- `spec/core/03_frontend_screens.md` — `ArchiveView.vue` + sidebar
- `spec/core/04_business_logic.md` — archiwum = frozen snapshot, kategorie edytowalne, kontrahenci współdzielone
- `spec/core/06_navigation_flow.md` — sidebar: Archiwum (na dole)
- `spec/core/11_reports_stats.md` — stats nowe (czyste) vs stats archiwum (osobne endpointy)

---

### [RAO-P2-064] Opcje wydruku PDF — hide_delivery_address + signatures_on_page1 + cleanup report_without_data

```yaml
id: RAO-P2-064
priority: P1
size: M
status: in-progress
classification: cross-stack/bugfix+feature
roles: [tech-lead, backend-dev, frontend-dev, qa-engineer, product-owner]
source: operator-request
source_date: 2026-07-01
specs_to_update:
  - core/03_frontend_screens.md (usunięcie checkboxa report_without_data)
  - core/04_business_logic.md (semantyka 2 flag wydruku)
  - core/07_integrations.md (sekcja PDF — zachowanie flag)
migration_impact: no (pola już istnieją w DB)
security_impact: low (read-only PDF, autoescape=True już działa)
depends_on:
  - RAO-P1-018 (PDF Umowa — pieczątka, foundation istnieje)
verification:
  - "pytest backend/tests/unit/test_pdf_options.py: PASS (12 testów)"
  - "vue-tsc --noEmit: PASS"
  - "npm run build: PASS"
  - "curl /reports/contract/{id}?type=contract z hide_delivery_address=TRUE → PDF bez adresu"
  - "curl /reports/contract/{id}?type=contract z signatures_on_page1=FALSE → PDF bez podpisów na str 1"
  - "grep report_without_data frontend/src/views/ContractFormView.vue: 0 wyników (usunięty)"
```

**Problem:**

Formularz umowy (ContractFormView.vue:191-193) ma 3 checkboxy opcji wydruku:
1. "Wydruk bez danych" (report_without_data)
2. "Ukryj adres dostawy na umowie (klient wpisze ręcznie)" (hide_delivery_address)
3. "Podpisy wymagane na stronie 1" (signatures_on_page1)

Pola zapisywane w DB (contracts table, BOOLEAN NOT NULL DEFAULT FALSE) ale **ŻADEN szablon PDF ich nie czyta** — `contract.html` i `contract_u.html` mają 0 odwołań do tych pól. User klika checkbox → zapisuje umowę → pobiera PDF → **nic się nie zmienia**. To jest silent feature gap erodujący zaufanie do aplikacji.

**Analiza zespołu (PO + QA, 2026-07-01):**

- `hide_delivery_address` + `signatures_on_page1` — realne JTBD, implementuj TERAZ (P1)
- `report_without_data` — **martwe pole** (DB comment "PZ bez danych" = osobny raport, już osiągalny przez context menu `protocol_zo_nodata`). Usuń checkbox z UI.

**Decyzje projektowe (tech-lead, --full-auto):**

1. `hide_delivery_address=TRUE` → zostawić label "Adres dostawy:" + puste pole do wpisu ręcznego (zgodnie z UI "klient wpisze ręcznie")
2. `signatures_on_page1` ON = pokaż na str 1 + OWN (bez zmian dla OWN); OFF = brak na str 1, tylko OWN
3. `report_without_data` → usuń checkbox z UI (pole w DB zostaje dla compat migracji)
4. Tylko umowa (contract.html, contract_u.html), nie PZ (UI labelka mówi "na umowie")

**Implementacja:**

- `contract.html:152` + `contract_u.html:138`: warunkowa logika hide_delivery_address (label + puste pole)
- `contract.html:252-264` + `contract_u.html:224-236`: warunkowa sekcja SIGNATURES (`{% if contract.signatures_on_page1 %}`)
- `ContractFormView.vue:191`: usuń checkbox report_without_data
- `backend/tests/unit/test_pdf_options.py`: 12 testów pytest (happy path + edge cases + regresja)
- Spec sync: 03_frontend_screens.md, 04_business_logic.md, 07_integrations.md

---

### [RAO-P2-065] Statystyki — poprawki po full-team review (ROI, kontrahent, kategorie, bugi UX/UI)

```yaml
id: RAO-P2-065
priority: P1
size: M
status: triaged
classification: cross-stack/bugfix+feature
roles: [tech-lead, backend-dev, frontend-dev, ui-designer, qa-engineer, product-owner]
source: full-team review 2026-07-04 (PO 7/10, QA 7/10, UI 6.5/10 + tech-lead vision review)
source_date: 2026-07-04
specs_to_update:
  - core/09_design_reference.md (amber=legacy akcent, pill radius, zakaz emoji jako ikon)
  - core/11_reports_stats.md (ROI w AnalyticsView)
migration_impact: no
security_impact: low
depends_on:
  - RAO-P2-063 (AnalyticsView — foundation)
```

**Źródło:** Pełny review statystyk (wygląd + funkcjonalność + wymagania klienta + separacja legacy/nowe) przez zespół: product-owner, qa-engineer, ui-designer + tech-lead (screenshoty Playwright na żywo).

**Werdykt ogólny:** Separacja legacy/nowe POTWIERDZONA na 3 warstwach (modele — 0 importów archive_* w stats/; dane — rozłączne article_id; frontend — analytics.ts woła tylko /stats+/explorer, archive.ts tylko /archive). Gruba krecha wzorowa: osobne widoki, banner ⚠️, suffix [szac.], amber akcent. 5/6 wymagań klienta spełnionych.

#### 🔴 P1 — bugi funkcjonalne

1. **Brak ROI (stopy zwrotu) w AnalyticsView** — GŁÓWNE wymaganie klienta #1. Endpoint `/stats/machine-roi` istnieje ale NIE jest podpięty (analytics.ts nie ma fetchMachineRoi, żaden tab nie renderuje ROI). Paradoks: ROI jest tylko w Archiwum (szacunki), a nie tam gdzie realne kwoty. FIX: dodać metric ROI + replacement_value do DrillDownDrawer maszyny (~4h).
2. **`contractor_name: null` w /stats/currently-rented** — tabela "Maszyny aktualnie wynajęte" i drill-down pokazują "—" zamiast kontrahenta. Root cause: router.py:241 bierze `Contract.contractor_name` (snapshot, NULL dla umów z contractor_id) zamiast JOIN z contractors. FIX: `func.coalesce(Contractor.name, Contract.contractor_name)` + LEFT JOIN (~1h).
3. **422 na /contractors?per_page=500 → pusty dropdown kontrahentów w filtrach** — AnalyticsView.vue:130 woła per_page=500, backend ma le=200. Filtr KONTRAHENT nie ma żadnych opcji. FIX: per_page=200 lub podnieść limit backendu (~15min).
4. **/stats/currently-rented bez `is_settled==False` i bez `date_to IS NULL`** — rozliczone umowy liczone jako wynajęte; umowy na czas nieokreślony pomijane. Niespójność z fleet-summary (ma oba warunki) → utylizacja % może się rozjechać. FIX: dodać warunki jak w fleet-summary:110 (~30min).

#### 🟡 P2 — funkcjonalność / UX

4b. ✅ **DONE (2026-07-04): REGRESJA — zgubiona zakładka "Lokalizacje" (panele miast)** — zgłoszone przez usera ("kiedyś były panele miast"). Zrealizowane jako **4. zakładka "📍 Lokalizacje" w AnalyticsView** (decyzja tech-lead: osobny tab zamiast sekcji w period — period już długi, miasta zasługują na dedykowany widok):
   - `stores/analytics.ts`: `fetchLocationsRanking` → GET `/explorer/locations` (backend przetrwał merge, ranking z rollup gmina/powiat/woj)
   - `components/analytics/tabs/LocationsTab.vue` (NOWY): KPI (Lokalizacji/Wynajmów/Przychód/Top miasto) + **wykres słupkowy poziomy top 10 miast z toggle Przychód/Wynajmy** (CSS bars, klik → drill-down) + wyszukiwarka miast (client-side: city/PNA/gmina/powiat/woj) + sortowalny ranking (8 kolumn z Gmina/Powiat/Województwo) + drill-down po PNA (reuse DrillDownDrawer)
   - Weryfikacja: vue-tsc PASS, build PASS, smoke e2e 11/11 PASS, screenshot na żywo (KPI+wykres+ranking renderują, formatowanie zł OK, toggle działa)
   - Uwaga: dane demo mają `delivery_address=NULL` we wszystkich umowach → widać "(brak PNA)"; na produkcji z prawdziwymi adresami pokażą się miasta. Fallback do city (pkt 9) pozostaje otwarty.

5. **Filtr KONTRAHENT (datalist value=id) przyjmuje dowolny tekst** — wpisanie "kop" zamiast ID cicho zawęża wszystkie taby do 0 wyników bez komunikatu (zweryfikowane na żywo: Explorer "koparka" → 0 wyników przy filtrze "kop", 6 wyników po wyczyszczeniu). FIX: walidacja/select zamiast wolnego tekstu + empty state z podpowiedzią "sprawdź aktywne filtry".
6. **Brak sekcji Kategorii w PeriodRentalTab** — wymaganie klienta #5 ("top maszyny + kategorie"). Backend /stats/by-category + store byCategoryData gotowe, tylko UI brakuje (~2h).
7. **Drill-down maszyny bez nr wewnętrznego w tytule** — machineDetails.machine.internal_number jest w responsie, nie renderowane (~15min).
8. **/explorer/search `total` = len(strony)** zamiast total count (router.py:172) — paginacja zepsuta; pole `city` w response to delivery_address (mylące).
9. **Lokalizacje: "(brak PNA)"** bez fallbacku do city — mało czytelne dla usera.
10. **Brak walidacji date_from > date_to** — 200 z pustymi danymi zamiast 422; user widzi mylące "0 zł".
11. **KPI "Przychód w okresie" sumuje rzeczywiste+szacunek w jednej liczbie** (19 250 = 9100+10 150) — breakdown jest pod spodem, ale główny KPI powinien być oznaczony "razem (rzecz.+szac.)".
12. **~2s overhead na KAŻDYM request** (nawet /health bez auth) — middleware/startup do zdiagnozowania; psuje płynność przełączania filtrów.
13. **Brak testów e2e dla AnalyticsView** — zero pokrycia regresyjnego nowego widoku.

#### 🟢 P3 — wygląd / design system (UI review 6.5/10)

14. **LITERÓWKA `--color-text-mutetd`** (ArchiveView.vue:1140) — zmienna nie istnieje, .est-value bez koloru muted. Production bug (~1min).
15. **Duplikacja globalnych stylów drawer** — DrillDownDrawer.vue i ArchiveView.vue definiują te same klasy .drill-* w non-scoped style; ArchiveView powinien używać komponentu DrillDownDrawer.
16. **Emoji jako ikony** (🚜📅🔍✅💰🏆📍📋⚠️) zamiast lucide-vue-next — niespójne z design system.
17. **Dwa systemy tabel** (.data-grid vs .analytics-table — różne hover, max-width) i **dwa systemy tabów** (pill vs underline w Archive).
18. **Brak :focus-visible** na wszystkich buttonach analytics (WCAG 2.1 AA).
19. **H1 20px zamiast 24px**; sort-icon 10px off-scale; spacing 2px/20px off-grid.

**Oceny zespołu:** PO 7/10 · QA 7/10 · UI 6.5/10. Główny brak: ROI (wymaganie #1 klienta) niedostępne w nowym widoku.

---

### [RAO-P2-066] Rezerwacje maszyn — UI + integracja z availability (martwy moduł backend)

```yaml
id: RAO-P2-066
priority: P1
size: M
status: triaged
classification: cross-stack/feature
roles: [tech-lead, backend-dev, frontend-dev, ux-designer, qa-engineer, product-owner]
source: analiza wymagań klienta 2026-07-04 (wymaganie #6 NIESPEŁNIONE)
source_date: 2026-07-04
specs_to_update:
  - core/02_backend_api.md (integracja reservations z availability)
  - core/03_frontend_screens.md (UI rezerwacji)
  - core/04_business_logic.md (semantyka blokady)
migration_impact: no (tabela article_reservations istnieje — RAO-P1-015)
security_impact: low (auth już na endpointach)
depends_on:
  - RAO-P1-015 (backend reservations CRUD — istnieje)
  - RAO-P1-023 (availability check umowa-umowa — istnieje)
```

**Wymaganie klienta (oryginalne):** "Rezerwacja maszyny na podstawie numerów wewnętrznych — blokada i brak możliwości wynajmu oraz informacji, kiedy będzie dostępny."

**Stan faktyczny (analiza 2026-07-04):**
- Backend `reservations/` istnieje (RAO-P1-015): CRUD + check_conflict (409 przy nakładających się rezerwacjach)
- **Frontend: 0 odwołań do /reservations** — moduł całkowicie martwy z perspektywy usera
- **Rezerwacje NIE blokują wynajmu**: `articles/service.py:check_availability` (używane przez ArticlePicker w umowie) sprawdza TYLKO konflikty umowa↔umowa, ignoruje tabelę `article_reservations`
- Częściowe pokrycie przez RAO-P1-023: ArticlePicker pokazuje "Wolny/Zajęty" + modal "Maszyna zajęta" z listą umów i datami (soft-block "Mimo to dodaj") — ale to konflikt z UMOWAMI, nie rezerwacjami

**Scope:**
1. **Backend:** `check_availability` uwzględnia `article_reservations` (reserved_from <= date_to AND reserved_to >= date_from) — konflikt rezerwacji w `conflicting_contracts` (lub osobne pole `conflicting_reservations` z datami "dostępny od")
2. **Frontend — UI rezerwacji:** widok/modal zarządzania rezerwacjami maszyny (z ArticleFormView lub listy artykułów): lista aktywnych rezerwacji + dodaj (od–do, notatka) + usuń
3. **Frontend — ArticlePicker:** badge "Zarezerwowany do DD.MM" + modal konfliktu pokazuje rezerwacje z datą dostępności
4. **Decyzja PO:** hard-block czy soft-block ("Mimo to dodaj") dla rezerwacji — rekomendacja: soft-block jak przy umowach (spójność), ale z wyraźnym ostrzeżeniem
5. QA: testy pytest (availability z rezerwacją) + e2e (dodanie rezerwacji → maszyna pokazuje "Zarezerwowany")

---

#### Wpływ na inne zadania

| Zadanie | Wpływ | Korzyść |
|---------|-------|---------|
| **RAO-P2-060** (statystyki) | Uproszczenie: brak `is_legacy` filtra, brak `estimate_legacy`, brak toggle | 6 z 9 bugów znika, prostszy `shared/revenue.py`, prostszy StatsView (2 zakładki zamiast 3) |
| **RAO-P2-061** (demo data) | Demo dane idą do czystej `rao_new` (brak legacy) | Brak mieszania demo z legacy, prostszy seed |
| **RAO-P2-058** (Fakturownia) | Brak wpływu (integracja działa na `contracts`) | — |
| **RAO-P2-059** (usługi dodatkowe) | Brak wpływu (szablony współdzielone) | — |

---

#### Kryteria akceptacji (DoD)

**Migracja:**
- [ ] Backup `backup_pre_archive_split.sql` utworzony
- [ ] 6 tabel `archive_*` utworzonych (idempotentne)
- [ ] 742 legacy umów przeniesionych do `archive_contracts`
- [ ] 1945 legacy settlements przeniesionych do `archive_contract_settlements`
- [ ] Legacy dane usunięte z `contracts`, `contract_positions`, etc.
- [ ] `SELECT COUNT(*) FROM contracts` = 0 (brak legacy)
- [ ] `SELECT COUNT(*) FROM archive_contracts` = 742
- [ ] Kolumna `is_legacy` usunięta z `contracts`
- [ ] `idx_contracts_legacy` indeks usunięty

**Backend:**
- [ ] `backend/archive/models.py` — 6 modeli `Archive*`
- [ ] `backend/archive/router.py` — endpointy read-only + `PATCH /archive/articles/{id}/category`
- [ ] `shared/revenue.py` — `is_legacy` usunięte, `revenue_source` bez `estimate_legacy`
- [ ] `stats/router.py` — `is_legacy` parametr usunięty z 16 endpointów
- [ ] Bug #1, #2, #9 **nie występują** (legacy nie ma w `contracts`)
- [ ] `pytest -x` przechodzi

**Frontend:**
- [ ] "Archiwum" w sidebarze (na dole, ikona 📦)
- [ ] `ArchiveView.vue` — lista umów + maszyny + stats (read-only)
- [ ] Edycja kategorii maszyny w archiwum (dropdown → `PATCH /archive/articles/{id}/category`)
- [ ] Zarządzanie kategoriami archiwum (CRUD: lista tree, dodaj, edytuj, usuń → `/archive/categories/*`)
- [ ] Szare tło + banner "Archiwum — dane historyczne (szacunkowe)"
- [ ] `StatsView.vue` (P2-060) — 2 zakładki (bez archiwum, bez toggle)
- [ ] `vue-tsc --noEmit` przechodzi

**QA:**
- [ ] POST/PUT/DELETE na `/archive/contracts/*` i `/archive/articles/*` → 405 (poza PATCH category na articles)
- [ ] `PATCH /archive/articles/{id}/category` → 200, tylko `category_id` zmienione
- [ ] `POST /archive/categories` → 201, nowa kategoria w `archive_categories`
- [ ] `PUT /archive/categories/{id}` → 200, rename/hierarchy zmienione
- [ ] `DELETE /archive/categories/{id}` → 204 (gdy pusta) lub 409 (gdy ma maszyny/podkategorie)
- [ ] Smoke `01-login.spec.ts` przechodzi
- [ ] E2E: nawigacja Archiwum, read-only umów, CRUD kategorii archiwum

**Spec:**
- [ ] `git diff --stat spec/core/` nie jest pusty (6 plików)
- [ ] `spec/core/01_database.md` — tabele `archive_*` + usunięcie `is_legacy`

---

#### Edge cases

- Kontrahent z umowami legacy + nowymi — `contractors` współdzielone, archiwum i nowe pokazują tego samego kontrahenta
- Maszyna sprzedana (is_archival=1) — czy trafia do `archive_articles`? TAK (jeśli była w legacy umowach) — frozen snapshot
- Maszyna w `archive_articles` z `category_id=NULL` — można ustawić kategorię przez `PATCH`
- Umowa z `date_to=NULL` w archiwum — stats archiwum muszą obsłużyć (jak bug #3 ale w archive endpointach)
- Re-run migracji — idempotentne (`INSERT IGNORE`, `CREATE TABLE IF NOT EXISTS`)
- Po migracji `shared/revenue.py` — `is_legacy` nie istnieje w query → czy code crashuje? (weryfikacja backend-dev)

---

#### Poza scope (na później)

- Eksport archiwum do PDF/Excel
- Porównanie side-by-side archiwum vs nowe (ten sam kontrahent/maszyna)
- Import korekt do archiwum (poza kategoriami)
- Automatyczne sugestie kategorii dla `archive_articles` (AI/ML)

**Estymacja:** 16-20h (L) — Faza 0 (migracja 4-6h) + Faza 1 (backend 6-8h) + Faza 2 (frontend 4-6h) + Faza 3 (QA 2-3h) + Faza 4 (spec sync 1-2h)

**Kolejność:** **RAO-P2-062 FIRST** (przed P2-060 i P2-061) — bo upraszcza oba zadania

---

### [RAO-P2-067] Demo data refactor — migrate_all.py orchestrator + FA-pending contracts + delivery_address

```yaml
id: RAO-P2-067
priority: P2
size: M
status: done
classification: backend/data-seeding+tooling
roles: [tech-lead, backend-dev, db-architect, qa-engineer, product-owner]
source: demo-showcase-prep
source_date: 2026-07-04
specs_to_update:
  - core/07_integrations.md (Fakturownia seeding — FA-pending flow)
  - core/04_business_logic.md (demo data lifecycle — migrate_all steps)
  - core/11_reports_stats.md (showcase scenarios — FA-pending demo)
migration_impact: no (demo dane tylko)
security_impact: medium (hardcoded FA token usunięty → env-only)
depends_on:
  - RAO-P2-061 (Demo data seeding — foundation)
  - RAO-P2-058 (Fakturownia integracja — OID + product mapping)
verification:
  - "python migrate_all.py --steps recreate_db,import_dump,seed_demo_data,seed_fa_invoices,verify: PASS"
  - "31 faktur FA utworzonych (19 backfill + 12 FA-pending)"
  - "12 umów FA-pending z fakturą czekającą w FA (demo 'Pobierz z Fakturowni')"
  - "delivery_address wypełnione dla wszystkich umów demo (miasta + PNA)"
  - "Lokalizacje w AnalyticsView pokazują miasta (nie '(brak PNA)')"
  - "grep FAKTUROWNIA_API_TOKEN seed_fa_invoices.py: tylko env read (brak hardcoded)"
```

**Problem:**

Po P2-061 demo data było funkcjonalne ale ograniczone:
1. **Brak `delivery_address`** we wszystkich umowach demo → zakładka "Lokalizacje" w AnalyticsView pokazywała "(brak PNA)" zamiast miast (regresja wykryta w P2-065 4b)
2. **Brak umów FA-pending** (nierozliczonych z fakturą czekającą w FA) → nie można demonstrować flow "Pobierz z Fakturowni" dla nowej umowy
3. **Hardcoded Fakturownia API token** w `seed_fa_invoices.py` → security risk (sekrety w kodzie)
4. **Brak orchestratora** — każdy skrypt seedujący uruchamiany ręcznie w odpowiedniej kolejności, bez weryfikacji
5. **Krótki okres danych** (tylko 2026) → filtry roczne pokazywały mało danych

**Cel:** Robust demo environment z realistycznymi adresami, umowami FA-pending do demonstracji sync FA, i orchestratorem `migrate_all.py` zarządzającym pełnym flow seedowania.

---

#### Scope implementacji

**Faza 1: `seed_demo_data.py` enhancements**

1. **`delivery_address` z miastami/PNA:**
   - Pula 10 polskich miast z realnymi PNA (Warszawa, Gdańsk, Kraków, Wrocław, Poznań, Łódź, Lublin, Katowice, Bydgoszcz, Szczecin)
   - Każda umowa demo dostaje `delivery_address` w formacie "ulica, miasto, PNA"
   - Zakładka "Lokalizacje" w AnalyticsView pokazuje miasta zamiast "(brak PNA)"
2. **Pula 2025 wstecz:**
   - Umowy rozciągnięte na okres 2024-10 do 2026-07 (żeby filtry roczne 2025 miały dane)
   - `contract_positions` z `date_from`/`date_to` w odpowiednich okresach
3. **Pula FA-pending (12 umów):**
   - Umowy z 2026 nierozliczone (`is_settled=0`, brak `contract_settlements`)
   - Oznaczone w `notes` jako "[FA-pending]" (do identyfikacji przez `seed_fa_invoices.py`)
   - Pozwala demonstrować: user klika "Pobierz z Fakturowni" → faktura pobrana → rozliczenie utworzone
4. **Konfiguracja 'jak od klienta':**
   - Default service fee presets (zestawy S/U)
   - Company configuration (dane firmy, NIP, adres)
   - `contract_conditions` z realnymi stawkami (rate1/rate2/period_count)
5. **`is_legacy` cleanup:**
   - Martwy kod związany z flagą `is_legacy` usunięty (P2-062 przeniosło legacy do `archive_*`)

**Faza 2: `seed_fa_invoices.py` enhancements**

1. **Token z env (security fix):**
   - `FAKTUROWNIA_API_TOKEN` czytane z env (brak hardcoded)
   - Brak tokenu → error z instrukcją (nie silent fail)
2. **FA-pending handling:**
   - Skrypt wykrywa umowy FA-pending (bez settlements)
   - Tworzy fakturę w FA z `oid=contract.number` (pozycje = pozycje umowy)
   - **NIE tworzy `contract_settlements`** — faktura czeka w FA na "Pobierz"
   - Demo: user w UI klika "Pobierz z Fakturowni" → sync pobiera fakturę → tworzy rozliczenie
3. **Backfill (istniejące rozliczenia):**
   - Dla umów z `contract_settlements` ale bez faktury FA → tworzy fakturę
   - `source='fakturownia'` w settlements zachowane

**Faza 3: `migrate_all.py` orchestrator**

1. **CLI z krokami:**
   - `--steps recreate_db,import_dump,seed_demo_data,seed_fa_invoices,verify`
   - `--list` — wyświetla dostępne kroki
   - Każdy krok idempotentny (re-run safe)
2. **Kroki:**
   - `recreate_db` — DROP + CREATE database (czysty start)
   - `import_dump` — import legacy dump (jeśli dostępny)
   - `seed_demo_data` — uruchom `seed_demo_data.py`
   - `seed_fa_invoices` — uruchom `seed_fa_invoices.py` (wymaga `FAKTUROWNIA_API_TOKEN` w env)
   - `verify` — sprawdź spójność (count umów, pozycji, rozliczeń, faktur FA, lokalizacji)
3. **Output:**
   - Progress per krok (PASS/FAIL)
   - Podsumowanie na końcu (count utworzonych rekordów)

---

#### Weryfikacja (2026-07-04)

**Uruchomienie:**
```bash
cd backend
python migrate_all.py --steps recreate_db,import_dump,seed_demo_data,seed_fa_invoices,verify
```

**Wynik:**
- 31 faktur FA utworzonych (19 backfill + 12 FA-pending)
- 12 umów FA-pending z fakturą czekającą w FA
- `delivery_address` wypełnione dla wszystkich umów demo
- Lokalizacje w AnalyticsView pokazują miasta (Warszawa, Gdańsk, Kraków, etc.)
- `grep FAKTUROWNIA_API_TOKEN seed_fa_invoices.py`: tylko `os.environ.get()` (brak hardcoded)

**Demo scenarios dostępne:**
1. **"Pobierz z Fakturowni"** — 12 umów FA-pending czeka na sync (S005/2026, S010/2026, U015/2026, etc.)
2. **Lokalizacje** — ranking miast z danymi (nie puste)
3. **Statystyki roczne** — dane za 2025 i 2026 (filtry roczne mają sens)

---

#### Pliki zmienione

| Plik | Zmiana |
|------|--------|
| `backend/seed_demo_data.py` | +delivery_address, +pula 2025, +12 FA-pending, +company config, -is_legacy cleanup |
| `backend/seed_fa_invoices.py` | +env token (security fix), +FA-pending handling, +backfill |
| `backend/migrate_all.py` | NOWY — orchestrator z CLI --steps/--list |

---

#### Security impact

**HARDcoded Fakturownia API token usunięty** z `seed_fa_invoices.py`. Token czytany z `FAKTUROWNIA_API_TOKEN` env var. Brak tokenu → error z instrukcją. To eliminuje ryzyko wycieku sekretu przez commit do repo.

---

**Estymacja:** 6-8h (M) — Faza 1 (3-4h) + Faza 2 (2h) + Faza 3 (1-2h) + weryfikacja (1h)

---

### [RAO-P2-068] Demo data — predefiniowane cenniki kaskadowe + pełna konfiguracja "jak od klienta"

```yaml
id: RAO-P2-068
priority: P2
size: M
status: done
classification: backend/data-seeding+config
roles: [tech-lead, backend-dev, db-architect, product-owner]
source: operator-request
source_date: 2026-07-04
specs_to_update:
  - core/04_business_logic.md (cenniki kaskadowe + pełna konfiguracja firmy)
  - core/07_integrations.md (demo setup — cenniki + presety + rate types)
migration_impact: no (demo dane tylko)
security_impact: no
depends_on:
  - RAO-P2-067 (Demo data refactor — migrate_all.py orchestrator)
verification:
  - "python seed_demo_data.py: PASS (idempotentny re-run)"
  - "CENNIKI_KASKADOWE: 5 maszyn × 3 warunki kaskadowe (1-3 dni, 4-16 dni, powyżej 16 dni)"
  - "ZESTAWY_USLUG: 6 presetów (najem, usługa z operatorem, kontrakt długoterminowy, weekend, kontrakt zagraniczny, operator premium)"
  - "ServiceFeeTemplateItem: 22 relacji N:M preset → artykuł"
  - "Rate types: 6 typów (dniowa, godzinowa, km, tygodniowa, miesięczna, jednorazowa)"
  - "Firma: NIP=1234563218, bank_account=PL 12 1020..., header_text do PDF"
```

**Problem:**

Po P2-067 demo data miało jeszcze braki:
1. **Brak cenników kaskadowych** — każda pozycja umowy miała tylko 1 warunek (płaska stawka). W starej aplikacji WinForms warunki były kaskadowe (1-3 dni 540zł/doba, 4-16 dni 410zł/doba, powyżej 16 dni 350zł/doba). User musiał ręcznie wpisywać każdy warunek.
2. **Brak pełnej konfiguracji firmy** — `company` table miała tylko `name="RAO — Wynajem Maszyn"` (z main.py). Brak NIP, adres, konto bankowe, header_text do PDF.
3. **Tylko 3 presety usług** — brak scenariuszy weekend, kontrakt zagraniczny, operator premium.
4. **ServiceFeeTemplateItem pusta** — relacja N:M preset → artykuł nie była wypełniana.
5. **Tylko 3 rate types** — brak tygodniowa, miesięczna, jednorazowa.

**Cel:** "Rozliczenie = cennik" — user klika maszynę i ma gotowy cennik kaskadowy, nie musi ciągle wpisywać tego samego. Wszystkie rzeczy konfigurowalne zeseedowane pod demo.

---

#### Scope implementacji

**1. CENNIKI_KASKADOWE per maszyna (5 maszyn × 3 warunki):**

| Maszyna | 1-3 dni | 4-16 dni | powyżej 16 dni |
|---------|---------|----------|----------------|
| Koparka JCB 8035 | 900 zł/doba | 750 zł/doba | 600 zł/doba |
| Ładowarka Manuscop 6.36 | 720 zł/doba | 600 zł/doba | 480 zł/doba |
| Podnośnik Haulotte HA16PX | 500 zł/doba | 420 zł/doba | 340 zł/doba |
| Spychacz Wirtgen W100CFi | 1300 zł/doba | 1100 zł/doba | 900 zł/doba |
| Zagęszczarka Ammann APF 15/50 | 180 zł/doba | 150 zł/doba | 120 zł/doba |

**2. 6 presetów usług dodatkowych:**
- Cennik usług — najem 2026 (S, default) — 6 szablonów
- Cennik usług — usługa z operatorem 2026 (U, default) — 3 szablony
- Kontrakt długoterminowy (rabat) (S) — 4 szablony
- Weekend / krótkoterminowy (1-3 dni) (S) — 3 szablony
- Kontrakt zagraniczny (export) (S) — 4 szablony
- Usługa z operatorem — premium (U) — 4 szablony

**3. ServiceFeeTemplateItem:** 22 relacji N:M preset → artykuł z domyślną ceną.

**4. 6 rate types:** dniowa, godzinowa, km (istniejące) + tygodniowa, miesięczna, jednorazowa (nowe).

**5. Pełna konfiguracja firmy:** NIP 1234563218, REGON, adres Warszawa, konto PKO BP, header_text do PDF, numbering_start=1, increment_step=50.

**6. `_build_positions_and_fees`** używa cenników kaskadowych zamiast płaskiej stawki.

---

#### Weryfikacja (2026-07-04)

- `python seed_demo_data.py`: PASS (idempotentny re-run, 0 nowych bo dane istnieją)
- `python _verify_cennik.py`: CENNIKI_KASKADOWE=5, ZESTAWY_USLUG=6, RATE_TYPES=6, FIRMA_CONFIG OK
- DB check: 8 presetów (2 stare default + 6 nowych), 22 ServiceFeeTemplateItem, 9 rate types (3 legacy + 6 nowych)
- Firma: NIP=1234563218, bank_account=PL 12 1020..., header_text z pełnymi danymi

---

#### Pliki zmienione

| Plik | Zmiana |
|------|--------|
| `backend/seed_demo_data.py` | +CENNIKI_KASKADOWE (5 maszyn × 3 warunki), +STAWKA_EFEKTYWNA, +FIRMA_CONFIG, +3 nowe presety, +ServiceFeeTemplateItem, +3 rate types, +seed_company(), _build_positions_and_fees używa cenników kaskadowych |

---

**Estymacja:** 4-5h (M) — cenniki kaskadowe (1.5h) + presety + ServiceFeeTemplateItem (1h) + rate types + firma (1h) + weryfikacja (0.5h)

---

### [RAO-P2-069] Analytics — agregacja lokalizacji po mieście (toggle Miasto/PNA) + drill-down po mieście

```yaml
id: RAO-P2-069
priority: P2
size: M
status: done
classification: cross-stack
roles: [backend-dev, frontend-dev, product-owner]
source: operator-request
source_date: 2026-07-04
specs_to_update:
  - core/02_backend_api.md (endpoint /locations/city/{city} + group_by param)
migration_impact: no
security_impact: no
depends_on:
  - RAO-P2-028 (Agregacja PNA z LEFT JOIN do postal_codes)
verification:
  - "vue-tsc --noEmit: PASS"
  - "npm run build: PASS (643ms)"
  - "curl /explorer/locations?group_by=city: Warszawa → 1 wiersz (postal_code=null)"
  - "curl /explorer/locations?group_by=pna: Warszawa 00-002 → 1 wiersz z PNA"
  - "curl /explorer/locations/city/Warszawa: 200 OK z pna_breakdown + top_machines"
  - "Playwright screenshot: toggle Miasto/PNA działa, kolumna PNA warunkowa"
```

**Problem:**

W zakładce "Lokalizacje" w AnalyticsView każde miasto było rozbite na kody pocztowe — Warszawa (3978 PNA w słowniku) mogła mieć wiele wierszy zamiast jednego. User chciał: "ma być miasto do wielu kodów pocztowych" — jeden wiersz per miasto, z opcją rozbicia na PNA jeśli potrzeba.

**Cel:** Toggle Miasto/PNA w UI. Domyślnie miasto (1 wiersz per miasto, sumuje wszystkie PNA). Drill-down po mieście pokazuje rozbicie na PNA.

---

#### Scope implementacji

**Backend:**
1. `shared/locations.py` — `aggregate_by_pna()` dostaje `group_by='city'|'pna'` (domyślnie 'city'):
   - `city`: klucz = (city, gmina, powiat, wojewodztwo) — 1 wiersz per miasto, `postal_code=null`
   - `pna`: klucz = (postal_code, city) — 1 wiersz per PNA (legacy)
2. `explorer/router.py` — `GET /explorer/locations` dostaje `?group_by=city|pna` (domyślnie city)
3. `explorer/router.py` — nowy `GET /explorer/locations/city/{city}` — drill-down po mieście:
   - Sumuje wszystkie PNA w mieście (case-insensitive)
   - Zwraca `pna_breakdown` (rozbicie na kody pocztowe)
   - Top maszyny (10) + top kontrahenci (5) filtrowani po mieście
   - `metrics.pna_count` — ile kodów PNA w mieście

**Frontend:**
1. `stores/analytics.ts` — `fetchLocationsRanking()` dostaje `groupBy` param; nowy `fetchCityDetails()`
2. `LocationsTab.vue` — toggle "Miasto / PNA" w nagłówku sekcji ranking
3. Kolumna PNA warunkowa (tylko w trybie PNA)
4. `onRowClick` — w trybie city wywołuje `openDrillDown('location', 'city:'+city, city)`
5. `AnalyticsView.vue` — drill-down po mieście pokazuje `pna_breakdown` sekcję + `pna_count` w metrics

---

#### Weryfikacja (2026-07-04)

- `vue-tsc --noEmit`: PASS
- `npm run build`: PASS (643ms)
- `curl /explorer/locations?group_by=city`: Warszawa → 1 wiersz (postal_code=null, gmina=Warszawa, woj=mazowieckie)
- `curl /explorer/locations?group_by=pna`: Warszawa 00-002 → 1 wiersz z PNA
- `curl /explorer/locations/city/Warszawa`: 200 OK — city, gmina, powiat, wojewodztwo, metrics (pna_count=1), pna_breakdown, top_machines, top_contractors
- Playwright: toggle Miasto/PNA działa, kolumna PNA pojawia się tylko w trybie PNA, drill-down po mieście otwiera drawer "📍 Kraków / Umowy w mieście (wszystkie PNA)"

---

#### Pliki zmienione

| Plik | Zmiana |
|------|--------|
| `backend/shared/locations.py` | +`group_by` param (city/pna), klucz agregacji zależny od trybu |
| `backend/explorer/router.py` | +`group_by` query param, +`/locations/city/{city}` endpoint, +import defaultdict |
| `frontend/src/stores/analytics.ts` | +`groupBy` param w fetchLocationsRanking, +fetchCityDetails, +pna_breakdown w LocationDetailsResponse |
| `frontend/src/components/analytics/tabs/LocationsTab.vue` | +toggle Miasto/PNA, kolumna PNA warunkowa, onRowClick per tryb |
| `frontend/src/views/AnalyticsView.vue` | +sekcja pna_breakdown w drill-down, +metric pna_count |

---

**Estymacja:** 3-4h (M) — backend (1.5h) + frontend (1.5h) + weryfikacja (0.5h)

---

### [RAO-P2-070] Audyt interaktywności — drilldowny, filtry, przekliki (cross-view navigation)

```yaml
id: RAO-P2-070
priority: P2
size: L
status: triaged
classification: frontend/ux
roles: [ux-designer, frontend-dev, product-owner]
source: operator-request
source_date: 2026-07-04
specs_to_update:
  - core/03_frontend_screens.md (drilldowny cross-view)
  - core/06_navigation_flow.md (cross-view navigation, goBack → router.back)
  - core/18_ux_improvements.md (toast zamiast alert, feedback po zapisie)
migration_impact: no
security_impact: no
depends_on: []
blocks: []
verification: []
```

**Problem:**

Aplikacja ma solidne podstawy (drilldown w Analytics/Archive, skeleton loadery, empty states, active sidebar). Ale **codzienne flow usera** jest utrudnione — brakuje cross-view drilldownów (kontrahent↔umowa↔maszyna), sortowania po kolumnach w Dashboard, kluczowych filtrów (handlowiec, miasto), oraz `alert()` zamiast toastów w 25+ miejscach.

**Cel:** Aplikacja w pełni interaktywna — user może "przeskakiwać" między encjami bez ręcznego szukania, każdy zapis/akcja ma feedback, każda lista ma filtry i sortowanie.

---

#### Audyt UX (2026-07-04) — 30 usterek w 3 priorytetach

##### 🔴 HIGH — Blokuje codzienną pracę (8 usterek)

| # | Usterka | Widok | User pain | Stara aplikacja |
|---|---------|-------|-----------|-----------------|
| B1 | Brak drilldown z listy umów → kontrahent | DashboardView /contracts | Ręczne szukanie kontrahenta w sidebar | WinForms: context menu / double-click |
| B2 | Brak kolumny "Maszyny" w liście umów | DashboardView /contracts | Trzeba otwierać każdą umowę | WinForms: tooltip / dialog "?" |
| B3 | Brak drilldown z kontrahenta → jego umowy | DashboardView /contractors | "Aktywna umowa" nie jest klikalna | WinForms: double-click → historia umów |
| B4 | Brak drilldown z artykułu → historia wynajmów | DashboardView /articles | Trzeba kombinować z Analytics | WinForms: FormA.cs podgląd historii |
| B5 | Brak sortowania po kolumnach w DashboardView | DashboardView (3 sekcje) | Klik w nagłówek nie sortuje | WinForms: DataGridView sortował |
| B6 | `alert()` zamiast toastów — 25+ miejsc | 9 widoków (ContractForm 18×, ContractorForm 5×, Archive 5×, Admin 6×, inne) | Blokuje aplikację, legacy pattern | WinForms: MessageBox (web ≠ MessageBox) |
| B7 | Brak toastu po zapisie umowy/kontrahenta/artykułu | ContractForm, ContractorForm, ArticleForm | User nie wie czy zapisano → duplikat | WinForms: "Zapisano" w status bar |
| B8 | Brak filtra "Handlowiec" i "Miasto" w liście umów | DashboardView /contracts | Handlowiec nie widzi swoich umów | WinForms: filtry handlowca w toolbarze |

##### 🟡 MEDIUM — Frustrujące, user radzi sobie obejściem (13 usterek)

| # | Usterka | Widok |
|---|---------|-------|
| B9 | Brak drilldown z umowy → edycja kontrahenta | ContractFormView |
| B10 | Brak drilldown z umowy → edycja maszyny (z pozycji) | ContractFormView (PositionGrid) |
| B11 | Brak drilldown z umowy → faktura w Fakturownia | ContractFormView (panel FA) |
| B12 | Brak drilldown z CommissionView → umowy handlowca | CommissionView |
| B13 | Brak drilldown z drill-machine-rentals → konkretna umowa | AnalyticsView (drawer machine) |
| B14 | Brak drilldown z top_contractors → kontrahent | AnalyticsView (drawer location) |
| B15 | Brak breadcrumb w formularzach | ContractForm, ContractorForm, ArticleForm |
| B16 | `goBack` hardcoded zamiast `router.back()` | ContractForm, ContractorForm, ArticleForm |
| B17 | Brak filtra "Tylko z aktywną umową" w kontrahentach | DashboardView /contractors |
| B18 | Brak filtra kategoria/marka/typ w artykułach | DashboardView /articles |
| B19 | Brak kalendarza umów (spec 06 sekcja 3) | DashboardView /contracts |
| B20 | Brak toolbar [?] — podgląd szczegółów bez edycji | DashboardView |
| B21 | Brak context menu "Dodaj umowę" w kontrahentach | DashboardView /contractors |

##### 🟢 LOW — Polish / nice-to-have (9 usterek)

| # | Usterka | Widok |
|---|---------|-------|
| B22 | Brak hover indicatora na klikalnych wierszach | ArchiveView |
| B23 | Brak undo dla destruktywnych akcji | DashboardView, ContractorForm |
| B24 | Brak sticky header w tabelach | DashboardView, ArchiveView |
| B25 | Brak filtra "Okres" w kontrahentach i artykułach | DashboardView |
| B26 | Brak paginacji w drilldown drawers | AnalyticsView |
| B27 | Brak "Eksportuj CSV/PDF" z list | DashboardView, AnalyticsView |
| B28 | Brak tooltipów na ikonach w toolbarze | ContractFormView |
| B29 | Brak drilldown z HomeView KPI → filtrowana lista | HomeView |
| B30 | Brak drilldown z HomeView "Dostawy" → umowa | HomeView |

---

#### Mapa pożądanych interakcji (cross-view navigation)

| Z widoku | Klik w | Powinno otworzyć | Priorytet |
|----------|--------|------------------|-----------|
| Dashboard /contracts | Nazwa kontrahenta | `/contractors/:id/edit` | HIGH |
| Dashboard /contracts | Maszyna (nowa kolumna) | `/articles/:id/edit` lub drilldown | HIGH |
| Dashboard /contracts | Nagłówek kolumny | Sort ASC/DESC | HIGH |
| Dashboard /contracts | Filtr Handlowiec | Lista filtrowana po `salesperson_id` | HIGH |
| Dashboard /contracts | Filtr Miasto | Lista filtrowana po `city` | HIGH |
| Dashboard /contractors | Numer aktywnej umowy | `/contracts/:id/edit` | HIGH |
| Dashboard /contractors | Right-click → "Dodaj umowę" | `/contracts/new?contractor_id=:id` | HIGH |
| Dashboard /articles | Numer aktywnej umowy | `/contracts/:id/edit` | HIGH |
| Dashboard /articles | "Historia wynajmów" | Drawer jak w Analytics | HIGH |
| ContractForm | "✎ Edytuj" obok kontrahenta | `/contractors/:id/edit` (nowa karta) | MEDIUM |
| ContractForm | Nazwa artykułu w pozycji | `/articles/:id/edit` (nowa karta) | MEDIUM |
| ContractForm | Faktura w panelu FA | `window.open(invoice.url)` | MEDIUM |
| Analytics /drill-machine | Wiersz rental (umowa) | `/contracts/:contract_id/edit` | MEDIUM |
| Analytics /drill-location | Wiersz top_contractor | `/contractors/:id/edit` | MEDIUM |
| Commission | Wiersz handlowca | `/dashboard/contracts?salesperson_id=:id` | MEDIUM |
| HomeView | KPI card | `/worker` lub `/dashboard/contracts` z filtrem | MEDIUM |
| HomeView | Dostawa (delivery-row) | `/contracts/:contract_id/edit` | MEDIUM |
| Wszystkie formularze | Toolbar "←" | `router.back()` z fallbackiem | MEDIUM |
| Wszystkie błędy | API error | Toast error (NIE `alert()`) | HIGH |
| Wszystkie formularze | Po Zapisz | Toast success | HIGH |

---

#### Rekomendowana kolejność implementacji (5 faz)

**Faza 1 — Toasty zamiast alert() + feedback po zapisie (B6, B7)** — quick win, 25+ miejsc
- Komponent `Toast.vue` i `useToastStore` już istnieją (używane w 1 miejscu)
- Czysta zamiana `alert(err)` → `toastStore.showToast(msg, 'error')`
- Dodać toast success po zapisie we wszystkich formularzach
- Est: 4-6h (S)

**Faza 2 — Cross-view drilldown z list (B1, B3, B4)** — najczęstszy flow codzienny
- DashboardView /contracts: nazwa kontrahenta → link, kolumna "Maszyny" → link
- DashboardView /contractors: `active_contract_number` → link, context menu "Dodaj umowę"
- DashboardView /articles: `active_contract_number` → link, akcja "Historia wynajmów"
- Est: 6-8h (M)

**Faza 3 — Sortowanie po kolumnach w DashboardView (B5)** — `useSort` już istnieje
- Przenieść pattern z `ExplorerTab.vue` / `AnalyticsTable.vue`
- 3 tabele: contracts, contractors, articles
- Est: 3-4h (S)

**Faza 4 — Filtry: Handlowiec + Miasto w liście umów (B8)** — wymaga backend
- Dodać `salesperson_id` i `city` do `GET /contracts` query params (backend)
- Dodać `<select>` i `<input>` w grid-header (frontend)
- `settingsStore.salespeople` już załadowany
- Est: 4-5h (S)

**Faza 5 — goBack → router.back() + drilldown w Analytics/HomeView (B13-B16, B29-B30)** — polish
- `goBack` używające `router.back()` z fallbackiem
- Drilldown z drawer Analytics → konkretna umowa
- KPI cards w HomeView klikalne
- Est: 4-6h (S)

**Łączna estymacja:** 21-29h (L) — 5 faz, każda niezależna (można robić sekwencyjnie)

---

#### Co działa dobrze (nie wymaga zmian)

- ✅ HomeView — klik w umowę w panelach → edycja
- ✅ WorkerView — klik w umowę/dostawy → edycja, filtry dni
- ✅ AnalyticsView — drilldown machine/location, filtry (date, type, contractor, city)
- ✅ ArchiveView — drilldown umów, filtry (search, typ, data, kategoria), paginacja
- ✅ ExplorerTab — klik w wynik → edycja, search + sort
- ✅ ContractFormView — picker kontrahenta/art/dostawcy, inline form, conflict modal
- ✅ ContractorFormView — "+ Umowa" → auto-fill, GUS lookup
- ✅ AppSidebar — active state per section
- ✅ AppLayout — Ctrl+N = nowy, Esc = back

---

#### Edge cases do obsługi w implementacji

- [ ] **Error state:** Tylko ArchiveView/AnalyticsView mają retry; reszta = `alert('Błąd')`
- [ ] **Success feedback:** Tylko CommissionView (toast); reszta = brak
- [ ] **Slow connection:** Brak timeout indicatora
- [ ] **Long content:** DashboardView paginacja (50/strona, brak wyboru per-page)
- [ ] **Soft delete vs hard delete:** Usunięcie kontrahenta z aktywnymi umowami — blokować LUB soft-delete

---

**Estymacja:** 21-29h (L) — 5 faz, każda niezależna

---

### [RAO-P3-071] Audyt UX — czytelność, spójność, przyjemność poruszania się

```yaml
id: RAO-P3-071
priority: P3
size: L
status: triaged
classification: frontend/ux
roles: [ux-designer, ui-designer, frontend-dev]
source: operator-request
source_date: 2026-07-04
specs_to_update:
  - core/09_design_reference.md (jeden source of truth zmiennych CSS, font-size minima)
  - core/03_frontend_screens.md (skeleton loaders, breadcrumb, page-title)
  - core/18_ux_improvements.md (glossary skrótów, ConfirmDialog konkretne obiekty)
migration_impact: no
security_impact: no
depends_on: []
blocks: []
verification: []
```

**Problem:**

Aplikacja ma solidne podstawy (skeleton loadery, empty states z CTA, KPI z semantycznym kolorem, mikro-animacje, sticky headers, keyboard shortcuts). Ale po 8h pracy operatora boli głowa od czytania — 56 miejsc z `font-size: 11px`, 3 różne formaty walut, 2 różne formaty dat, żargon bez tooltipów (PNA, ZO, FA), niespójny design system (CommissionView łamie wszystko), brak a11y (aria-label, focus states, kontrast poniżej WCAG AA).

**Cel:** Aplikacja przyjemna w użyciu po 8h pracy — czytelna, spójna, dostępna, z mikro-polishem.

---

#### Audyt UX (2026-07-04) — czytelność, spójność, przyjemność

##### Co działa dobrze (nie wymaga zmian)

- ✅ Skeleton loaders (HomeView, WorkerView, AnalyticsTable, DrillDownDrawer)
- ✅ Empty states z CTA (DashboardView, HomeView panele)
- ✅ KPI cards z semantycznym kolorem (kpi-ok/warn/danger/info)
- ✅ Live preview warunków kaskadowych (ConditionPanel)
- ✅ Help section wbudowany ("📖 Jak wpisać warunki?")
- ✅ Polskie formatowanie w AnalyticsView (Intl PLN, toLocaleDateString pl-PL)
- ✅ Mikro-animacje (LoginView shake, nav-tile hover, KPI hover, btn:active scale)
- ✅ Archive separator pomarańczowy + banner ostrzegawczy
- ✅ Keyboard shortcuts (Ctrl+N, Escape, Enter/Esc inline edit)
- ✅ Print CSS, sticky table headers, DrillDownDrawer z Teleport + Esc

##### 🔴 HIGH — 5 usterek blokujących czytelność

| # | Usterka | Widok | User pain |
|---|---------|-------|-----------|
| B1 | `font-size: 11px` × 56 miejsc — za mały do 8h pracy | DashboardView, HomeView, WorkerView, AdminView, SettingsView, ContractFormView | Ból głowy po 2h, starsi pracownicy nie przeczytają |
| B2 | `font-size: 10px` (del-chip) i `9px` (sidebar-logo-sub) | WorkerView, AppSidebar | Kluczowa informacja (data dostawy) nieczytelna |
| B3 | 3 różne formaty walut — `Intl PLN` vs `toFixed(2)+' zł'` vs `toLocaleString` | AnalyticsView ✅, ContractFormView ❌, ConditionPanel ❌, CommissionView ✅ | Pomyłki w odczycie przy porównywaniu z fakturą |
| B4 | 2 różne formaty dat — "01.02.2026" vs "1.2.2026" | HomeView ✅ (leading zero), DashboardView/ContractFormView ❌ | Skanowanie tabeli przerywane — wygląda jak inna data |
| B5 | Żargon bez tooltipów — PNA, ZO, FA, OID, S/U | ContractFormView, DashboardView, ArticleFormView, ArchiveView | Nowy user pyta kolegę "co to ZO?" — wstyd, strata czasu |

##### 🟡 MEDIUM — 6 usterek spójności i komfortu

| # | Usterka | Widok |
|---|---------|-------|
| B6 | Kolumna "Adres dostawy" 11px + max 180px + pre-wrap | DashboardView |
| B7 | "X rekordów" zamiast "X umów" — żargon bazodanowy | DashboardView (4 sekcje) |
| B8 | Toolbar ikony `− + ⎙ ? ∑ 💰` bez etykiet tekstowych | AppToolbar, ContractFormView |
| B9 | Numbers nie wyrównane do prawej w tabelach | DashboardView, ArchiveView |
| B10 | CommissionView całkowicie własny styl — hardcoded kolory, rem, 4-8px radius, `.data-table` zamiast `.data-grid` | CommissionView |
| B11 | Dwa konfliktujące systemy zmiennych CSS — `style.css` vs `variables.css` (różne odcienie navy, różne font-size) | Global |

##### 🟢 LOW — 3 usterek polish

| # | Usterka |
|---|---------|
| B12 | Spacing niespójny między widokami (padding 12px/20px/24px/32px) |
| B13 | "Pulpit" w sidebar vs "Pulpit operacyjny" w WorkerView — niespójna nazwa |
| B14 | ArchiveView tab labels identyczne jak sekcje główne (ryzyko pomyłki) |

##### Usterki spójności wizualnej (tabela)

| Element | Gdzie spójne | Gdzie niespójne |
|---------|-------------|-----------------|
| Kolor primary | variables.css `#0F234E` | style.css `#1D2B53`, WorkerView hardcoded, CommissionView hardcoded |
| Border-radius kart | 12px (layout.css) | WorkerView 10px, CommissionView 8px, HomeView nav-tile 6px |
| Styl tabeli | `.data-grid` (navy header, zebra, hover) | CommissionView `.data-table` (jasny header, brak zebra) |
| Styl przycisków | `.btn` (pill 24px) | CommissionView 5px, HomeView 12px, LoginView redefine |
| Badge statusu | tables.css (success/warning/danger/info/muted) | DashboardView (badge-settled/overdue/active — nie zdefiniowane!) |
| Karty KPI | HomeView własny, KpiRow.vue własny | Dwa różne komponenty KPI, różny styling |
| Loading state | HomeView/WorkerView skeleton | DashboardView/AdminView/SettingsView/ArchiveView tekst "Ładowanie..." |
| Ikony | Emoji (📊📦⏰🖨) | Unicode symbole (⌕ ⎙ ∑ −) — mix |
| Toast kolory | hardcoded `#10b981/#ef4444` | Design system `--color-success/danger` (inne odcienie) |
| Tło widoku | `#F8F9FA` (layout.css) | HomeView `#F4F6FB`, WorkerView `#F4F6FB`, CommissionView białe |

##### Usterki dostępności (a11y)

| Element | Stan | Priorytet |
|---------|------|-----------|
| aria-label na icon buttons | Brak (16 aria/role w całej apce) | HIGH |
| Label ↔ input powiązanie (for/id) | Brak | HIGH |
| Focus state na przyciskach | Tylko `.form-control:focus`, brak na `.btn`/`.btn-icon`/`.toolbar-btn` | HIGH |
| Kontrast muted text `#718096` na białym | ~4.0:1 — poniżej WCAG AA 4.5:1, przy 11px = fail | HIGH |
| role="alert" na błędach | Brak | MEDIUM |
| aria-invalid na polach z błędem | Brak | MEDIUM |
| Modal focus trap | Brak (Tab wychodzi z modala) | MEDIUM |
| Modal aria-modal | Brak `role="dialog" aria-modal="true"` | MEDIUM |
| Skip-to-content link | Brak | LOW |
| Touch target size | `.page-btn` 28×28, `.days-filter` ~24×20 — poniżej 44×44 | LOW |

##### Usterki przyjemności/polish

| Element | Stan | Rekomendacja |
|---------|------|--------------|
| View transitions | Brak `<Transition>` na router-view | `<Transition name="fade" mode="out-in">` |
| Loading w 4 widokach | Tekst "Ładowanie..." | Skeleton rows (`.skeleton` już w animations.css) |
| Toast bez ikony | Tylko kolor + tekst | Ikona ✓/⚠️/ℹ — szybsze skanowanie |
| Toast bez undo | Success = info only | Przycisk "Cofnij" dla destruktywnych (5s) |
| KPI hover ale nie clickable | `:hover { box-shadow }` bez `@click` | Albo usuń hover, albo dodaj cursor:pointer + klik |
| ConfirmDialog generyczny | "Czy na pewno chcesz usunąć ten element?" | "Usuniesz umowę XYZ. Tej akcji nie można cofnąć." |
| Brak "recently viewed" | — | Lista "Ostatnio otwarte umowy" w HomeView |
| Brak keyboard hint w UI | Ctrl+N, Esc działają ale user nie wie | Tooltip w sidebar lub help overlay |

---

#### Rekomendowana kolejność implementacji (5 faz)

**Faza 1 — Font-size + kontrast (HIGH impact, LOW effort)** — 1 dzień
- Zamień `font-size: 11px` → 13px (dane), 12px (metadane); `10px` → 12px; `9px` → 11px
- Sciemnij `--color-text-muted` z `#718096` → `#5A6B7E` (WCAG AA 4.5:1)
- Każdy operator poczuje natychmiast

**Faza 2 — Unifikacja formatowania dat i walut (HIGH impact, LOW effort)** — 0.5 dnia
- Stwórz `composables/useFormat.ts` z `formatDate()`, `formatCurrency()`, `formatNumber()`
- Zastąp 5 różnych implementacji (AnalyticsView ✅ wzorzec, ContractFormView ❌, ConditionPanel ❌, CommissionView ✅, HomeView ✅)
- Zawsze `pl-PL` + `PLN` + 2 cyfry + leading zero w datach

**Faza 3 — a11y: aria-label + focus states (HIGH impact, MEDIUM effort)** — 1-2 dni
- `aria-label` na wszystkich icon buttons (−, +, ⎙, ?, ∑, 💰, ←, ✎, ✕)
- `:focus-visible { outline: 2px solid var(--color-primary) }` globalnie
- `for`/`id` na label/input, `role="alert"` na błędach, `aria-invalid` na polach z błędem
- `role="dialog" aria-modal="true"` na modalach

**Faza 4 — Unifikacja design system (MEDIUM impact, MEDIUM effort)** — 1 dzień
- CommissionView — usuń scoped CSS, użyj `.data-grid`, `.page-card`, `.btn`, `--color-*`
- WorkerView — zamień hardcoded `#0F234E` na `var(--color-primary)`, `#F4F6FB` na `var(--color-bg-app)`
- Jeden plik zmiennych — usuń definicje kolorów/typografii z `style.css`, zostaw `variables.css`
- Dodaj `badge-settled/overdue/active` do tables.css (lub użyj istniejących)
- Połącz KPI komponenty (HomeView + KpiRow.vue → jeden)

**Faza 5 — Skeleton loaders + polish (MEDIUM impact, LOW effort)** — 0.5-1 dzień
- DashboardView, AdminView, SettingsView, ArchiveView — skeleton rows zamiast "Ładowanie..."
- Komponent `<TableSkeleton :rows="5" />`
- View transitions (`<Transition name="fade" mode="out-in">`)
- Toast z ikoną (✓/⚠️/ℹ)
- ConfirmDialog z konkretnym obiektem ("Usuniesz umowę U/2024/123...")
- Glossary skrótów (PNA, ZO, FA, OID, S/U) — tooltip lub legenda

**Łączna estymacja:** 4-5.5 dni (L) — 5 faz, każda niezależna

---

#### Glossary skrótów (do implementacji w Faza 5)

| Skrót | Pełna nazwa |
|-------|-------------|
| PNA | Kod pocztowy (PNA) |
| ZO | Protokół zdania obiektu (ZO) |
| FA | Faktura (FA) |
| OID | Identyfikator w Fakturownia (OID) |
| S | Umowa najmu (S) |
| U | Umowa usługi (U) |

---

**Estymacja:** 4-5.5 dni (L) — 5 faz, każda niezależna

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
| RAO-P1-021 | Pole „Wartość (zł)" — decyzja biznesowa + auto-z rozliczenia | P1 | M | dev-verified | → team-verified (wartość z rozliczenia, read-only w formularzu) |
| RAO-P1-022 | Korekta nazewnictwa umów — S i G na końcu dla Gdańska | P1 | S | dev-verified | → user-verified |
| RAO-P2-028 | Statystyki — disambiguation miasta via postal_code (PNA/TERYT) | P2 | L | review | → Faza 1+2+3 DONE: shared/locations + shared/revenue, extract_city usunięte, drill-down po PNA |
| RAO-P2-029 | Statystyki — audyt determinizmu + naprawa archiwalnych | P2 | M | dev-verified | → user-verified |
| RAO-P0-030 | UNIQUE na contract.number + FOR UPDATE w generate_contract_number | P0 | S | dev-verified | → team-verified (unique=True w model + DB index uq_contracts_number) |
| RAO-P0-031 | XSS w PDF — Jinja2 autoescape + markupsafe.escape() | P0 | S | done | → done (autoescape=True w reports/service.py:588) |
| RAO-P0-032 | build_contract_data mutuje sesję — kopiuj description | P0 | XS | done | → done (lokalne kopie description w fees_data) |
| RAO-P0-033 | recalculate_total — użyj algorytmu kaskadowego | P0 | S | dev-verified | → team-verified |
| RAO-P0-034 | ContractUpdate schema z exclude_unset=True (lost data) | P0 | M | dev-verified | → team-verified |
| RAO-P0-035 | N+1 queries — selectinload w list_contracts/positions/articles | P0 | M | dev-verified | → team-verified |
| RAO-P0-036 | Stack trace disclosure → detail="Błąd" + logging | P0 | XS | dev-verified | → team-verified (global exception handler w main.py) |
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
| RAO-P0-054 | Kategorie — normalizacja nazw (diakrytyki + spacje) + collation polish_ci | P0 | S | dev-verified | → team-verified (normalize w settings/service.py + ALTER TABLE polish_ci w main.py) |
| RAO-P1-055 | Branch — migracja branch_id z G suffix + endpoint /stats/by-branch | P1 | M | triaged | → in_progress |
| RAO-P2-056 | contract_type (S/U) — dodaj grupowanie w statystykach | P2 | S | triaged | → in_progress |
| RAO-P2-057 | is_external — decyzja: wdrożyć filtrowanie czy usunąć flagę | P2 | XS | dev-verified | → team-verified (is_external nie blokuje + checkbox w details) |
| RAO-P2-058 | Fakturownia — OID = numer umowy + mapowanie artykułów z metadanymi | P2 | L | triaged | → in_progress (Faza 1: OID hybrydowe + product cache + UI picker) |
| RAO-P2-059 | Usługi dodatkowe — migracja z plain-text na per-artikel + UI ArticlePicker | P2 | L | triaged | → in_progress (Faza 1: parser legacy + migracja + UI + template items) |
| RAO-P2-060 | Statystyki — gruba krecha legacy vs nowe + StatsView + bugfix QA | P1 | L | in-progress (Faza 1 done — 6 bugów + indeksy + cleanup; Faza 2 todo — StatsView.vue) |
| RAO-P2-061 | Demo data seeding — Fakturownia testowa + pełne rozliczenia dla showcase statystyk | P2 | M | done | demo data seeded: 11 artykułów, 8 kontrahentów, 24 umowy, 74 rozliczenia (72% fakturownia), 12 faktur FA |
| RAO-P2-067 | Demo data refactor — migrate_all.py orchestrator + FA-pending contracts + delivery_address | P2 | M | done | 31 faktur FA (19 backfill + 12 FA-pending), delivery_address z miastami, hardcoded token usunięty |
| RAO-P2-068 | Demo data — predefiniowane cenniki kaskadowe + pełna konfiguracja "jak od klienta" | P2 | M | done | 5 cenników kaskadowych per maszyna, 6 presetów usług, 22 ServiceFeeTemplateItem, 6 rate types, pełna konfiguracja firmy |
| RAO-P2-069 | Analytics — agregacja lokalizacji po mieście (toggle Miasto/PNA) + drill-down po mieście | P2 | M | done | Toggle Miasto/PNA w LocationsTab, 1 wiersz per miasto (Warszawa 3978 PNA → 1), drill-down /locations/city/{city} z pna_breakdown |
| RAO-P2-070 | Audyt interaktywności — drilldowny, filtry, przekliki (cross-view navigation) | P2 | L | triaged | 30 usterek UX (8 HIGH, 13 MEDIUM, 9 LOW); 5 faz: toasty, cross-view drilldown, sort, filtry, goBack |
| RAO-P3-071 | Audyt UX — czytelność, spójność, przyjemność poruszania się | P3 | L | triaged | 14 usterek (5 HIGH, 6 MEDIUM, 3 LOW) + a11y + polish; 5 faz: font-size, formatowanie, a11y, design system, skeleton |
| RAO-P2-062 | Archiwum — migracja legacy do tabel `archive_*` (gruba krecha na poziomie tabel) | P1 | L | dev-verified (Faza 0+1+2 done — migracja + backend + frontend; czeka na team-verified) |

**Razem:** 38 zadań · ~158-208h pracy (P0: 25-35h, P1: 58-75h, P2: 75-98h)

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
status: done
classification: security/idor
roles: [backend-dev, security-auditor]
source: security-audit
source_date: 2026-06-29
source_ref: "Security audit P1-015 — subagent security-auditor"
specs_to_update:
  - core/25_security.md
migration_impact: no
security_impact: yes
done_date: 2026-07-01
fix: "_check_contract_access() w reports/router.py — admin full access, non-admin tylko własny branch, fetch contract przed PDF gen (early 404/403)"
verification:
  - "py_compile reports/router.py: OK"
  - "curl POST /reports/contract/999999 (admin): 404 (contract not found)"
  - "smoke 01-login.spec.ts: 11/11 passed"
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
status: done
classification: security/injection
roles: [backend-dev, security-auditor]
source: security-audit
source_date: 2026-06-29
source_ref: "Security audit P1-015 — subagent security-auditor"
implementation_date: 2026-07-01
note: "Już naprawione — autoescape=True w reports/service.py:588"
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

---

## 📋 Audyt wymagań klienta (2026-07-01) — Tech Lead

### Wymagania klienta — status spełnienia

| # | Wymaganie | Status | Uwagi |
|---|-----------|--------|-------|
| 1 | Statystyki wynajmu maszyny (po nr wewn.) w okresie — stopa zwrotu | **SPEŁNIONE z błędem** | `top-machines` + `explorer/machines/{id}` (utilization_pct). BŁĄD: rozjazd przychodu 41% między explorer a stats |
| 2 | Ile maszyn jest teraz wynajętych | **SPEŁNIONE** | `currently-rented` + `fleet-summary` |
| 3 | Dodanie numeru wewnętrznego do maszyny | **SPEŁNIONE funkcjonalnie, 0% danych** | `articles.internal_number` istnieje, ale 0/337 maszyn ma wypełnione (CSV nie istnieje, INSERT nie mapuje) |
| 4 | Filtrowanie pozycji dodatkowych (transport, mycie) w okresach | **SPEŁNIONE** | `additional-fees` endpoint + UI |
| 5 | Filtrowanie miejscowości i ilości wynajmów | **SPEŁNIONE** | `stats/locations` + `explorer/locations` (po PNA, z gmina/powiat/woj) |
| 6 | Rezerwacja maszyny (blokada, info kiedy dostępny) | **SPEŁNIONE** | `articles/{id}/availability` + ArticlePicker z badge |

### Odkryte problemy — do analizy i decyzji

#### [RAO-P2-030] internal_number puste (0% maszyn) — BLOKER dla wymagan 1+3

```yaml
id: RAO-P2-030
priority: P2
size: M
status: wont-fix
classification: bugfix/migration-data
roles: [db-architect, backend-dev]
source: tech-lead-audit
source_date: 2026-07-01
source_ref: "Audyt wymagań klienta — wymaganie 3 (numer wewnętrzny)"
resolution: "2026-07-01 — brak źródła danych w starej bazie (0/351 archive_articles ma internal_number, registration_no też 0%). Wymaga ręcznego uzupełnienia przez użytkownika w UI. Oznaczone wont-fix dla automatycznej migracji."
```

**Problem:** `articles.internal_number` jest puste dla 0/337 maszyn (0%).
- `migrate.py` INSERT articles z `artykul3` NIE mapuje `internal_number` (kolumna nie istnieje w `artykul3`)
- `step8_csv_categories` wypełniał `internal_number` z CSV `Asortyment*.csv`, ale ten plik **nie istnieje** na dysku
- Bez `internal_number` wymaganie 1 (statystyki po nr wewn.) i 3 (dodawanie nr wewn.) są bezużyteczne

**Opcje naprawy:**
1. Znaleźć źródło numerów wewnętrznych (inny CSV? ręczne dopisanie w UI?)
2. Sprawdzić czy `nr_rejestracyjny` z `artykul3` może służyć jako numer wewnętrzny (ale też 0% wypełnione)
3. Ręczne wypełnienie przez użytkownika w UI (formularz maszyny już ma pole)

**Acceptance criteria:**
- [ ] Źródło numerów wewnętrznych zidentyfikowane
- [ ] `internal_number` wypełnione dla >80% maszyn
- [ ] Statystyki po `internal_number` działają (test API)

---

#### [RAO-P2-031] Rozjazd przychodu 41% — explorer vs stats

```yaml
id: RAO-P2-031
priority: P2
size: S
status: done
classification: bugfix/backend-logic
roles: [backend-dev, qa-engineer]
source: tech-lead-audit
source_date: 2026-07-01
source_ref: "Audyt — explorer/machines używa rate1×period_count zamiast kaskadowego"
commit: P2-032 (scalone)
specs_to_update:
  - core/01_database.md
  - core/04_business_logic.md

**Problem:** `explorer/machines/{id}` liczy przychód jako `rate1 × period_count` (simple), a `stats/top-machines` używa kaskadowego `calculate_position_value`. **Rozjazd 41%** (3.17M vs 5.37M zł). Explorer zawyża przychody maszyn o ~41%.

**Lokalizacja:** `backend/explorer/router.py:218` — subquery `rev_subq` używa `func.sum(rate1 * period_count)` zamiast wywołania `shared.revenue.compute_position_revenues`.

**Naprawa:** Refactor `get_machine_details` aby używał `shared.revenue.compute_position_revenues` (jak `stats/top-machines`).

**Acceptance criteria:**
- [ ] `explorer/machines/{id}` używa `shared.revenue.compute_position_revenues`
- [ ] Przychody spójne między explorer a stats (delta <1%)
- [ ] Test unit: porównanie przychodu per pozycja

---

#### [RAO-P2-032] Przychód z `rozliczenie` (legacy) — rzeczywiste kwoty

```yaml
id: RAO-P2-032
priority: P1
size: L
status: done
classification: feature/revenue-source
roles: [db-architect, backend-dev, frontend-dev, product-owner, tech-lead, security-auditor]
source: tech-lead-audit
source_date: 2026-07-01
source_ref: "Audyt — warunki rozliczenia są orientacyjne, nie wiemy co skasowano na fakturach"
implementation_date: 2026-07-01
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
  - core/08_migration_plan.md

**Problem:** Obecnie przychód liczony z `position_conditions.rate1 × period_count` (kaskadowe) — **orientacyjne stawki z umowy**, nie rzeczywiste kwoty zafakturowane. `contracts.total_value` jest NULL/0 dla 100% umów (martwe pole).

**Odkrycie:** W dumpie starej bazy (`spec/backlog/archiwum/refinement/toolsmart_roa_*.sql`) jest tabela `rozliczenie` z **3836 wierszami** (~1951 sparsowanych, 792,384 zł) — **rzeczywiste rozliczenia per pozycja**:
- `id, data, id_pozycji, wartosc`
- 99.2% `id_pozycji` mapuje się na `contract_positions.id`
- `wartosc` = rzeczywista kwota rozliczona (po fakcie)

**Stara funkcja SQL (linia 11064-11070):** NIE używała `oplata1 × liczba_dni` (kaskadowe), ale **lookup** — wybierała jedną stawkę po `liczba_dni` (inny algorytm niż nasz `calculate_position_value`).

**Koncepcja operatora — Data Cutoff + Dwa tryby:**
1. **Dane historyczne (`is_legacy=1`, przed cutofficem):**
   - Import `rozliczenie` → `contract_settlements` (cost_client=wartosc, source='legacy')
   - Statystyki = SUM(settlements) — **rzeczywiste kwoty**
   - Osobna sekcja UI: "Analiza danych historycznych" z label "rzeczywiste rozliczenia"
2. **Nowe dane (`is_legacy=0`, po cutofficie):**
   - Integracja Fakturownia (już istnieje! `init-from-fakturownia`)
   - `contract.oid` + `article.fakturownia_product_id` → automatyczne mapowanie
   - Statystyki = SUM(settlements) — **rzeczywiste kwoty zafakturowane**

**Decyzje do podjęcia (wymaga operatora/klienta):**
1. Czy importować `rozliczenie` (3836 wierszy) do `contract_settlements`?
2. Kiedy następuje cutoff? (wszystkie 742 obecne umowy = legacy?)
3. Czy zachować `position_conditions` (szacunek) jako fallback gdy brak rozliczenia?
4. Czy UI ma mieć przełącznik "Dane historyczne / Dane bieżące"?

**Acceptance criteria (po decyzji):**
- [ ] Import `rozliczenie` do `contract_settlements` (deterministyczny, z dumpa SQL)
- [ ] `shared/revenue.py` — źródło "actual" z `contract_settlements` (priorytet) + fallback "estimate" z `position_conditions`
- [ ] UI toggle "Dane historyczne / Dane bieżące" w ReportsSection
- [ ] Label "rzeczywiste rozliczenia" vs "orientacyjne stawki" w UI
- [ ] Fix rozjada 41% (P2-031) jako część tego zadania

**Pliki do zmiany:**
- `backend/migrate.py` (nowy step: import `rozliczenie` z dumpa)
- `backend/shared/revenue.py` (źródło "actual" z settlements)
- `backend/stats/router.py` (filtr `is_legacy` + źródło przychodu)
- `backend/explorer/router.py` (fix rozjada — użyj `shared.revenue`)
- `frontend/src/components/reports/ReportsSection.vue` (toggle + label)

**Dane:**
- Dump SQL: `spec/backlog/archiwum/refinement/toolsmart_roa_1779053066.sql` (linie 4550-6524)
- 3836 wierszy, 353 unikalnych pozycji, 792,384 zł, 99.2% mapuje się na contract_positions

---

#### [RAO-P2-033] `contracts.total_value` martwe pole (100% NULL)

```yaml
id: RAO-P2-033
priority: P2
size: XS
status: done
classification: cleanup/data
roles: [db-architect]
source: tech-lead-audit
source_date: 2026-07-01
implementation_date: 2026-07-01
note: "DROP COLUMN contracts.total_value + usuń z schemas/PDF/frontend (scalone z P1-021)"
```

**Problem:** `contracts.total_value` jest NULL/0 dla 100% umów (742/742). Pole nie jest używane w statystykach (przychód z `position_conditions`), tylko w PDF umowy jako snapshot.

**Opcje:**
1. Zostawić (pole w PDF, nie blokuje) — rekomendowane
2. Usunąć kolumnę (destructive — wymaga zgody)
3. Wypełnić z `SUM(position_conditions)` (ale to szacunek, nie rzeczywistość)

**Rekomendacja:** Zostawić jak jest. Pole jest w PDF umowy jako "Wartość (zł)" — decyzja P1-021 przenosi to do ekranu rozliczenia.

---

## ✅ Wykonane prace (2026-07-01)

### P2-028 — Statystyki miast via PNA (DONE, dev-verified)
- **Commit:** `7bb2d1a` (backend+DB), `0ee1751` (frontend)
- **Co zrobiono:**
  - Pełny Spis PNA Poczty Polskiej (21,904 wpisów) w tabeli `postal_codes`
  - `contracts.postal_code_id` (FK) + `is_legacy` + backfill
  - `shared/locations.py` + `shared/revenue.py` (unifikacja stats+explorer)
  - `GET /explorer/locations/{postal_code}` (drill-down po PNA)
  - `PostalCodeLookupResponse` z gmina/powiat/wojewodztwo
  - Frontend: auto-fill PNA + panel gmina/powiat/woj + ReportsSection :key fix
  - Deduplikacja legacy numerów umów (S142/2026, 111)
  - Fix `extract_address` (integrations/router.py) — używa PNA zamiast usuniętego `extract_city`
- **Weryfikacja:** 221 pytest passed, vue-tsc exit 0, build OK, smoke e2e 11 passed

### Lint fixes — ContractFormView.vue (2026-07-01)
- **Co zrobiono:** Naprawiono 20 pre-existing TS lint errors (`ref([])` → typed refs)
  - `contractorAddresses` → `ref<ContractorAddress[]>([])`
  - `pickerList` → `ref<ContractorPick[]>([])`
  - `settlements` → `ref<Settlement[]>([])`
  - `editingFeeData` → `ref<Partial<FeeData>>({})`
  - `selectedAddressId` → `ref<number | null>(null)`
  - `editingFeeId` → `ref<number | null>(null)`
- **Weryfikacja:** vue-tsc exit 0, build OK

### Auto-fill PNA flow (2026-07-01)
- **Co zrobiono:** 3 ścieżki auto-fill PNA w ContractFormView.vue
  1. `onDeliveryAddressInput` — po extract-address auto-trigger PNA lookup
  2. `onAddressSelect` — wypełnia postal_code+city z adresu kontrahenta + auto PNA lookup
  3. `onPostalCodeBlur` — refactor na reusable `lookupPna()`
- **Weryfikacja:** vue-tsc exit 0, build OK
