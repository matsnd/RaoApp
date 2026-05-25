# RAO Backlog — Sprint Klient 2026-05-25

> **Status:** Aktualizowany 2026-05-25 wg uwag klienta
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/`
> **Źródła uwag klienta:** `temp/uwagi klienta/` — skan PDF + screenshoty z czatu
> **Cel:** Implementacja przez agenta SWE 1.6 (zadania szczegółowe, gotowe do wykonania)

---

## ℹ️ Zasady dla agenta SWE 1.6

1. **Każde zadanie zawiera:**
   - Konkretny plik (ścieżka absolutna) i numer linii do zmiany
   - Dokładny opis `old → new` gdy to możliwe
   - Acceptance criteria z checkboxami
   - Weryfikacja wizualna PDF / smoke E2E
2. **Status flow:** `triaged → in-progress → review → done`
3. **Po każdej zmianie → smoke test:** `cd e2e; npx playwright test tests/01-login.spec.ts`
4. **Po zakończeniu zadania → lokalny commit** (patrz `AGENTS.md`)
5. **Spec sync:** każda zmiana funkcjonalna → update odpowiedniego pliku w `spec/core/`

---

## 🚨 P0 — Production Blockers
*(brak)*

---

## 🔴 P1 — Must-Have (uwagi klienta z 2026-05-25)

### [RAO-P1-001] PDF Umowa — duplikacja adresu dostawy w polu "na budowie"

```yaml
id: RAO-P1-001
priority: P1
size: XS
status: triaged
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "Scan2026-05-25_125656.pdf strona 1 (NIE przy 'na budowie'), zrzut 223652.png pkt 1"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** *„Na umowie żeby nie pokazywał się adres w tym miejscu gdzie zaznaczyłam"* — chodzi o pole `na budowie:` w sekcji „uzupełnij", które obecnie zawiera duplikat `contract.delivery_address` (już wyświetlony wyżej w `info-col` jako „Adres dostawy").

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract_u.html` linia 150-153 — `<tr><td>na budowie:</td><td colspan="3" class="fill-wide">{{ contract.delivery_address or '' }}</td></tr>`
- `backend/reports/templates/contract.html` — analogiczna sekcja (znajdź ten sam wzór)

**Acceptance criteria (DoD):**

**Backend:**
- [ ] W `contract_u.html` linia 150-153: zmień `<td colspan="3" class="fill-wide">{{ contract.delivery_address or '' }}</td>` na `<td colspan="3" class="fill-wide"></td>` (puste pole do ręcznego dopisania notatki)
- [ ] W `contract.html` analogiczna zmiana

**Test:**
- [ ] Wygeneruj PDF: `POST /contracts/{id}/pdf` dla istniejącej umowy z `delivery_address`
- [ ] Sprawdź wizualnie: adres dostawy widoczny tylko raz (w `info-col` przy „Adres dostawy")
- [ ] Pole „na budowie" jest puste (gotowe do ręcznego dopisania)

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — note „pole 'na budowie' nie duplikuje adresu dostawy"

**Pliki do zmiany:** `backend/reports/templates/contract_u.html`, `backend/reports/templates/contract.html`
**Estimate:** 15 min (XS)

---

### [RAO-P1-002] PDF Umowa — "Dni pracy/tydzień" → "Ilość dni pracy"

```yaml
id: RAO-P1-002
priority: P1
size: XS
status: review
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "Scan2026-05-25_125656.pdf strona 1 (ręczna adnotacja 'ilość dni pracy: 6')"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** Na skanie strona 1 — w boksie „uwagi" (prawa kolumna obok przedmiotu najmu) klient wykreślił `Dni pracy/tydzień: 6 dni` i napisał ręcznie `Ilość dni pracy: 6`. Słowo "tydzień" jest mylące — chodzi o łączną ilość dni pracy w okresie umowy.

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract_u.html` linia 223:
  ```html
  <p style="margin:0 0 4px 0;"><strong>Dni pracy/tydzień:</strong> {% if contract.working_days_per_week %}{{ contract.working_days_per_week }}{% else %}5{% endif %} dni.</p>
  ```
- `backend/reports/templates/contract.html` — analogiczna linia (znajdź `Dni pracy/tydzień`)

**Acceptance criteria (DoD):**

**Backend:**
- [ ] Zmień w obu szablonach: `<strong>Dni pracy/tydzień:</strong>` → `<strong>Ilość dni pracy:</strong>`
- [ ] Zmień default `{% else %}5{% endif %}` → `{% else %}6{% endif %}` (klient chce 6 jako default)
- [ ] Po wartości zostaw `dni.` (np. "Ilość dni pracy: 6 dni.")

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — note o zmianie etykiety

**Pliki do zmiany:** `backend/reports/templates/contract_u.html` (linia 223), `backend/reports/templates/contract.html` (analogiczna)
**Estimate:** 5 min (XS)

---

### [RAO-P1-003] PDF Umowa — "*ceny netto" na samym dole strony 1

```yaml
id: RAO-P1-003
priority: P1
size: S
status: triaged
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "Scan2026-05-25_125656.pdf strona 1 (strzałka w dół), zrzut 223706.png pkt 6"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** *„*ceny podane na umowie - żeby były na dole na umowie"*

Obecnie w `contract_u.html` (linia 252-256) blok `footer-legal` znajduje się POD podpisami, ale klient zaznaczył strzałką w dół że ma być wyraźnie na **samym dole strony**. Treść jest, ale jest słabo widoczna.

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract_u.html` linia 252-256 — `<div class="footer-legal">` zawiera `<strong>*ceny podane na umowie są cenami netto</strong>`
- `backend/reports/templates/contract.html` — analogiczna sekcja

**Acceptance criteria (DoD):**

**Backend (CSS w obu szablonach):**
- [ ] Zwiększ widoczność `.footer-legal`:
  - `font-size: 9px` (było 8px)
  - `border-top: 1px solid #aaa; padding-top: 8px; margin-top: 16px;`
  - `page-break-after: avoid` (żeby nie wciągało na stronę OWN)
- [ ] Pierwsza linia `*ceny podane na umowie są cenami netto`:
  - Pogrub: `<strong>` już jest, dodaj inline style: `style="font-size: 11px; color: #c00; display: block; margin-bottom: 4px;"`

**Test:**
- [ ] Wygeneruj PDF — `footer-legal` jest widoczny na dole strony 1
- [ ] Tekst "*ceny netto" jest pogrubiony i czerwony
- [ ] Strona 2 to nadal OWN (page-break OK)

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — note o pozycjonowaniu *ceny netto

**Pliki do zmiany:** `backend/reports/templates/contract_u.html`, `backend/reports/templates/contract.html`
**Estimate:** 30 min (S)

---

### [RAO-P1-004] PDF Umowa Usługi (typ U) — usuń sekcję "Cennik usług dodatkowych"

```yaml
id: RAO-P1-004
priority: P1
size: S
status: triaged
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 223710.png — 'umowa usługi: tutaj nie dodajemy takich informacji jak tankowanie czyszczenie itp.', potwierdzone OWN w spec/reference_reports/own/ownU.pdf vs ownA.pdf"
specs_to_update:
  - core/11_reports_stats.md
  - core/04_business_logic.md
migration_impact: no
security_impact: none
verification:
  - "spec/reference_reports/own/ownA.pdf (NAJM typu S) — § 3 pkt 8 wymienia opłaty za czyszczenie/transport/serwis ✅ CENNIK POTRZEBNY"
  - "spec/reference_reports/own/ownU.pdf (USŁUGA typu U) — § 2 'Najem urządzenia z operatorem' — BRAK paragrafu o transporcie/tankowaniu/czyszczeniu ✅ KLIENT MA RACJĘ"
```

**Problem (cytat klienta):** *„umowa usługi: tutaj nie dodajemy takich informacji jak tankowanie czyszczenie itp."*

**⚠️ UWAGA — mapping typów w aplikacji (z kodu `backend/contracts/service.py:149`):**
- `contract_type = 'S'` → **Umowa NAJMU** → szablon `contract.html`
- `contract_type = 'U'` → **Umowa USŁUGI** (z operatorem) → szablon `contract_u.html`

**Uzasadnienie biznesowe (potwierdzone OWN w `spec/reference_reports/own/`):**
- **Umowa najmu (S)** — klient sam obsługuje maszynę, więc płaci za transport/tankowanie/czyszczenie po używaniu. OWN umowy najmu (`ownA.pdf`) § 3 pkt 8 to potwierdza.
- **Umowa usługi (U)** — Toolsmart wykonuje pracę z operatorem, więc koszty operacyjne (transport, paliwo) są wewnętrzne. OWN umowy usługi (`ownU.pdf`) NIE zawiera paragrafu o tych opłatach.

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract_u.html` linia 191-210 — blok `{% if fees %}<div ...>Cennik usług dodatkowych:</div>...<table class="pos">...{% endif %}`
- `backend/reports/templates/contract.html` linia 207-216 — analogiczna sekcja `<table class="inne">` z "Inne usługi" — **NIE ZMIENIAĆ** (klient chce żeby zostało dla typu S najmu)

**Acceptance criteria (DoD):**

**Backend:**
- [ ] W `backend/reports/templates/contract_u.html` **USUŃ** cały blok od linii 191 do 210:
  ```jinja
  <!-- FEES -->
  {% if fees %}
  <div style="font-size:9.5px;font-weight:bold;margin:8px 0 3px;">Cennik usług dodatkowych:</div>
  <table class="pos">
    <thead>
      <tr><th style="text-align:left;">usługa</th><th style="width:130px;">stawka</th><th style="width:60px;">j.m.</th></tr>
    </thead>
    <tbody>
    {% for f in fees %}
    {% if f.is_active %}
    <tr>
      <td>{{ f.name }}{% if f.description %} ({{ f.description }}){% endif %}</td>
      <td>{% if f.amount_from %}{{ f.amount_from | money_plain }}{% endif %}{% if f.amount_to %} - {{ f.amount_to | money_plain }}{% endif %}</td>
      <td>{{ f.unit or '' }}</td>
    </tr>
    {% endif %}
    {% endfor %}
    </tbody>
  </table>
  {% endif %}
  ```
- [ ] Powód: szablon `contract_u.html` jest renderowany TYLKO dla typu U (mapping w `backend/reports/service.py:542-547`), więc usunięcie bloku jest bezpieczne — nie potrzeba warunku `{% if contract_type == 'U' %}`.
- [ ] **NIE ZMIENIAĆ** `backend/reports/templates/contract.html` — sekcja "Inne usługi" (linia 207-216) ma zostać (klient chce ją dla typu S).

**Opcjonalne (decyzja klienta):**
- [ ] Sprawdź czy w bazie `service_fee_templates` istnieją rekordy z `contract_type = 'U'`. Jeśli tak — można je deaktywować (`is_active = false`) lub zostawić (są niewidoczne w PDF, ale mogą być używane do innych celów).
- [ ] `backend/contracts/service.py::copy_fee_templates` linia 25-32 — funkcja nadal może kopiować `ContractServiceFee` dla umowy U (do bazy), ale w PDF się nie pokażą. Można rozważyć skip kopiowania dla typu U: `if contract_type == 'U': return`.

**Test:**
- [ ] Wygeneruj PDF dla umowy **typu S** (najem) → cennik "Inne usługi" widoczny ✅
- [ ] Wygeneruj PDF dla umowy **typu U** (usługa) → cennik "Cennik usług dodatkowych" **NIE** widoczny ✅
- [ ] Smoke E2E (`04-contract.spec.ts`) nadal przechodzi

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — note „contract_u.html bez cennika dodatkowego"
- [ ] `spec/core/04_business_logic.md` — różnice umowa S (najem) vs U (usługa) + dlaczego cennik tylko dla S

**Pliki do zmiany:**
- `backend/reports/templates/contract_u.html` (USUNIĘCIE linii 191-210)
- Opcjonalnie: `backend/contracts/service.py` (skip copy_fee_templates dla typu U)

**Estimate:** 30 min (S) — głównie weryfikacja typu w PDF i smoke E2E

---

### [RAO-P1-005] PDF Protokół — brakuje pola "nr tel" w boksie kontaktu

```yaml
id: RAO-P1-005
priority: P1
size: S
status: triaged
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 223652.png 'wpisałam numer tel. a na protokole się on nie pojawia', Scan...pdf strona 4 (adnotacja 'nr tel:'), zrzut 223706.png Protokół pkt 1"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** *„wpisałam numer tel. a na protokole się on nie pojawia"* + na skanie protokołu klient dopisał ręcznie `nr tel:` przy boksie „osoba upoważniona do odbioru przedmiotu najmu".

**Analiza:**
- `contract.contact_phone1` jest zapisywane w formularzu umowy (DB OK)
- W `protocol_zo.html` linia 128-129 wyświetla `{{ contract.contact_person1 }}{% if contract.contact_phone1 %}, tel. {{ contract.contact_phone1 }}{% endif %}` — to **inline**, więc gdy numeru NIE ma w bazie, nie pojawia się żadna sugestia że tu powinien być
- Klient chce widzieć etykietę `nr tel:` osobno, nawet gdy puste

**Lokalizacja w kodzie:**
- `backend/reports/templates/protocol_zo.html` linia 124-131 (boks „osoba upoważniona")
- `backend/reports/templates/protocol_zo_u.html` linia 113-128 (analogicznie)
- `backend/reports/templates/protocol_zo_nodata.html`, `protocol_zo_nodata_u.html` — wszystkie 4 szablony

**Acceptance criteria (DoD):**

**Backend (zmień we wszystkich 4 szablonach protokołu):**
- [ ] Zamień zawartość boksu „osoba upoważniona" na strukturalny układ:
  ```html
  <div class="box-inner">
    <div class="box-label">osoba upoważniona do odbioru przedmiotu najmu</div>
    {% if contract.contact_person1 %}{{ contract.contact_person1 }}{% endif %}
    <div style="margin-top: 4px; font-size: 9px;">
      <strong>nr tel:</strong> {{ contract.contact_phone1 or '' }}
    </div>
  </div>
  ```
- [ ] Zachowaj fallback gdy `contact_phone1` jest puste — pokaż etykietę "nr tel:" bez wartości

**Test:**
- [ ] Wygeneruj protokół dla umowy z wypełnionym `contact_phone1` → telefon widoczny
- [ ] Wygeneruj protokół bez `contact_phone1` → etykieta "nr tel:" widoczna z pustym polem
- [ ] Sprawdź wszystkie 4 typy protokołów

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — wymiana boksu „osoba upoważniona"

**Pliki do zmiany:** `backend/reports/templates/protocol_zo.html`, `backend/reports/templates/protocol_zo_u.html`, `backend/reports/templates/protocol_zo_nodata.html`, `backend/reports/templates/protocol_zo_nodata_u.html`
**Estimate:** 45 min (S)

---

### [RAO-P1-006] PDF Protokół — większa tabela "Przy wydaniu / Przy odbiorze"

```yaml
id: RAO-P1-006
priority: P1
size: S
status: triaged
classification: bugfix/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "Scan...pdf strona 4 (adnotacja '↓ większe' przy tabeli)"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** Na skanie protokołu klient zaznaczył strzałką w dół `większe` obok tabeli „Przy wydaniu / Przy odbiorze". Tabela ma być wyraźnie większa (wyższe wiersze, większy font) — żeby było łatwiej wypełniać ręcznie.

**UWAGA:** Klient też w pkt 2 zrzutu 223706.png napisał "tabelki mniejsze" — chodzi o **inne** tabelki (dolna sekcja zwrotu, patrz RAO-P1-007). Ta tabela PWO ma być **większa**.

**Lokalizacja w kodzie:**
- `backend/reports/templates/protocol_zo.html` linia 169-192 — `<div class="pwo-section">` z `table.pwo`
- CSS: linia 65-72 — `table.pwo td { ... height: 20px; ... }`

**Acceptance criteria (DoD):**

**Backend (CSS w protocol_zo.html):**
- [ ] Zwiększ wysokość wierszy `table.pwo td` z `height: 20px` na `height: 32px`
- [ ] Zwiększ `font-size` tabeli z `8.5px` na `10px` (`table.pwo`)
- [ ] Zwiększ `font-size` etykiet (`td.pwo-label`) z `8.5px` na `10px`
- [ ] Wiersz „Uwagi" (`tr.pwo-uwagi td`) — zwiększ z `height: 36px` na `height: 60px`
- [ ] Padding komórek z `2px 5px` na `5px 8px`

**Test:**
- [ ] Wygeneruj protokół — tabela wyraźnie większa, łatwa do wypełnienia ręcznie
- [ ] Sprawdź czy nie powoduje page-overflow (jeśli tak — zmniejsz inne marginesy lub spróbuj height 28px zamiast 32px)

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — wymiar tabeli PWO

**Pliki do zmiany:** `backend/reports/templates/protocol_zo.html` (CSS linia 65-72)
**Estimate:** 30 min (S)

---

### [RAO-P1-007] PDF Protokół — połącz 3 tabelki dolne w 1 dużą tabelę "uwagi"

```yaml
id: RAO-P1-007
priority: P1
size: M
status: triaged
classification: refactor/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 223706.png Protokół pkt 4 'na protokole jest tabela na samym dole dane zwrotu ilość dni - tak naprawdę zróbmy z tego 1 dużą tabelkę na uwagi'"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** *„na protokole jest tabela na samym dole dane zwrotu ilość dni - tak naprawdę zróbmy z tego 1 duża tabelka na uwagi :)"*

Na dole protokołu są obecnie 3 elementy do połączenia:
1. Tabela 1 wiersz × 3 kolumny: `dane zwrotu przedmiotu najmu | ilość dni | kaucja zwrócono w wysokości`
2. Pusty box `uwagi`
3. Notatka „Ogólna weryfikacja maszyny..."

Klient chce **1 dużą tabelę "uwagi"** (jedno duże pole tekstowe).

**Lokalizacja w kodzie:**
- `backend/reports/templates/protocol_zo.html` linia 209-238 — sekcja `<div class="bottom-section">`

**Acceptance criteria (DoD):**

**Backend (protocol_zo.html linia 213-220):**
- [ ] Usuń `<table class="return-table">...</table>` (3 kolumny: dane zwrotu / ilość dni / kaucja)
- [ ] Zamień `<div class="ret-uwagi">uwagi</div>` na większy box:
  ```html
  <div class="big-uwagi">
    <div class="box-label" style="font-size:9px;color:#888;margin-bottom:6px;">uwagi do zwrotu</div>
  </div>
  ```
- [ ] Dodaj CSS dla `.big-uwagi`:
  ```css
  .big-uwagi { border: 1px solid #aaa; padding: 10px 12px; font-size: 10px; min-height: 140px; color: #888; }
  ```
- [ ] Zachowaj `<div class="note-line">Ogólna weryfikacja maszyny...</div>` poniżej
- [ ] Zachowaj sekcję `RETURN SIGNATURES`

**Test:**
- [ ] Wygeneruj protokół — na dole 1 duża pusta tabela „uwagi do zwrotu" (do ręcznego wypełnienia)
- [ ] Tabela 3 kolumnowa zniknęła
- [ ] Podpisy nadal są na końcu

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — struktura dolnej sekcji protokołu

**Pliki do zmiany:** `backend/reports/templates/protocol_zo.html` (linia 209-238)
**Estimate:** 1.5h (M)

---

### [RAO-P1-008] Format opisu warunku kaskadowego rozliczenia — jak w starej aplikacji

```yaml
id: RAO-P1-008
priority: P1
size: M
status: triaged
classification: feature/refactor
roles: [frontend-dev, backend-dev]
source: client-request + legacy-app-reference
source_date: 2026-05-25
source_ref: "temp/uwagi klienta/stary_format.png, C:/projects/repos/AppRao/rao/FormW.cs linia 690-750"
specs_to_update:
  - core/03_frontend_screens.md
  - core/04_business_logic.md
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem:** Stara aplikacja WinForms wyświetlała opis warunku rozliczenia w czytelnym formacie kaskadowym (tiered rates). Nowa aplikacja generuje obecnie nieprzejrzysty opis. Klient pyta: *„Proszę podpowiedz mi jak mam wstawiać kwoty - rozliczenie? w umowie?"*

**Format docelowy (z `temp/uwagi klienta/stary_format.png`):**
```
Rozliczenie
1 - 3 dni - 540,00 / doba
4 - 16 dni - 410,00 / doba
powyżej 16 dni - 350,00 / doba
```

**Mapping na model danych (`backend/contracts/models.py::PositionCondition`):**

Każdy warunek (condition) ma pola: `rate_type_id`, `rate1`, `rate2`, `period_count`, `billing_label`, `minimum`, `description`.

Dla powyższego przykładu (3 warunki w jednej pozycji):
| # | period_count | rate1 | rate2 | billing_label | rate_type |
|---|--------------|-------|-------|---------------|-----------|
| 1 | 3            | 540   | NULL  | doba          | kaskadowa |
| 2 | 16           | 410   | NULL  | doba          | kaskadowa |
| 3 | NULL         | NULL  | 350   | doba          | kaskadowa (powyżej) |

Lub alternatywnie (decyzja w trakcie implementacji):
| # | period_count | rate1 | rate2 | billing_label |
|---|--------------|-------|-------|---------------|
| 1 | 3            | 540   | NULL  | doba          |
| 2 | 16           | 410   | 350   | doba          | (rate2 = "powyżej") |

**Logika z starej aplikacji `FormW.cs` linia 690-750 (referencja):**
```csharp
// id_stawki = "2" (cascading rate):
// Pierwszy warunek: "do {ile} dni - {oplata1}zł / doba"
// Ostatni warunek z cbdo.Checked: "powyżej {ile} dni - {oplata2}zł / doba"
```

**Acceptance criteria (DoD):**

**Backend — helper formatujący:**
- [ ] Dodaj funkcję w `backend/contracts/service.py`:
  ```python
  def format_position_conditions_cascading(conditions: list[PositionCondition]) -> str:
      """Buduje opis kaskadowych warunków rozliczenia jak w starej aplikacji WinForms.
      
      Przykład wyjścia (3 warunki):
        1 - 3 dni - 540,00 / doba
        4 - 16 dni - 410,00 / doba
        powyżej 16 dni - 350,00 / doba
      """
      # 1. Sortuj warunki rosnąco po period_count (NULL na końcu)
      sorted_conds = sorted(
          conditions,
          key=lambda c: (c.period_count is None, c.period_count or 0)
      )
      lines = []
      prev_period = 0
      for i, c in enumerate(sorted_conds):
          label = c.billing_label or 'doba'
          if c.period_count is not None and c.rate1 is not None:
              # Zakres dni
              start = prev_period + 1
              end = c.period_count
              if start == end:
                  range_text = f"{start} {label}"
              else:
                  range_text = f"{start} - {end} {label[:-1]}i"  # "doba" → "doby/dni" — uproszczenie
              # Polski format kwoty (przecinek dziesiętny)
              rate_text = f"{c.rate1:.2f}".replace('.', ',')
              lines.append(f"{range_text} - {rate_text} / {label}")
              prev_period = c.period_count
          elif c.rate2 is not None and prev_period > 0:
              # Linia "powyżej"
              rate_text = f"{c.rate2:.2f}".replace('.', ',')
              lines.append(f"powyżej {prev_period} {label[:-1]}i - {rate_text} / {label}")
      return '\n'.join(lines)
  ```
- [ ] **Edge cases:**
  - Pusty list → ""
  - 1 warunek bez `period_count` → użyj `description` (legacy fallback)
  - Tylko `rate2` bez poprzedniego — zignoruj
  - Polska fleksja "doba"/"dni" — w 1. wersji uprość: jeśli `billing_label='doba'` użyj `'dni'` w zakresie, `'doba'` w stawce. Można później dodać helper `pluralize_pl(label, count)`.

**Backend — test jednostkowy:**
- [ ] Dodaj `backend/tests/unit/test_format_conditions.py`:
  ```python
  def test_cascading_3_conditions_matches_old_app():
      conditions = [
          MockCondition(period_count=3, rate1=540, rate2=None, billing_label='doba'),
          MockCondition(period_count=16, rate1=410, rate2=None, billing_label='doba'),
          MockCondition(period_count=None, rate1=None, rate2=350, billing_label='doba'),
      ]
      result = format_position_conditions_cascading(conditions)
      expected = (
          "1 - 3 dni - 540,00 / doba\n"
          "4 - 16 dni - 410,00 / doba\n"
          "powyżej 16 dni - 350,00 / doba"
      )
      assert result == expected
  ```

**Backend — użycie w PDF:**
- [ ] `backend/reports/service.py` — przy budowie kontekstu dla template, dla każdej pozycji wywołaj `format_position_conditions_cascading(position.conditions)` i przekaż jako `p.conditions_text`
- [ ] `backend/reports/templates/contract_u.html` linia 184: `<div class="cond">{{ p.conditions_text }}</div>` — CSS `.cond` ma już `white-space: pre-line` (linia 50) ✓

**Frontend — preview w formularzu warunku:**
- [ ] `frontend/src/components/contracts/ConditionPanel.vue` — refactor `buildAutoDescription()` (linia 151-167):
  - **Opcja A (preferowana):** wywołuj backend endpoint `GET /contracts/{contract_id}/positions/{position_id}/preview-conditions` zwracający string preview po zmianie formularza (debounce 500ms)
  - **Opcja B:** zaimplementuj tę samą logikę w JS (duplikacja kodu — gorsze)
- [ ] Wyświetl preview pod formularzem warunku w komponencie (read-only `<pre>` z białym tłem)

**Backend — nowy endpoint preview (Opcja A):**
- [ ] `backend/contracts/router.py` — dodaj:
  ```python
  @router.post("/contracts/{contract_id}/positions/{position_id}/conditions/preview")
  async def preview_conditions(
      contract_id: int,
      position_id: int,
      conditions: list[ConditionIn],  # tymczasowa lista z formularza
      db: AsyncSession = Depends(get_db),
      user: User = Depends(get_current_user),
  ) -> dict:
      """Zwraca preview tekstowy warunków bez zapisywania."""
      text = format_position_conditions_cascading([
          PositionCondition(**c.dict()) for c in conditions
      ])
      return {"preview": text}
  ```

**Spec:**
- [ ] `spec/core/04_business_logic.md` — algorytm formatowania kaskadowego (z dokładnym mappingiem i przykładem)
- [ ] `spec/core/03_frontend_screens.md` — opis ConditionPanel z preview
- [ ] `spec/core/11_reports_stats.md` — format warunków w PDF
- [ ] Skopiuj `temp/uwagi klienta/stary_format.png` do `spec/core/assets/stary_format_rozliczenie.png` (już skopiowane w `spec/backlog/stary_format_rozliczenie.png`)

**Pliki do zmiany:**
- `backend/contracts/service.py` (nowy helper)
- `backend/contracts/router.py` (nowy endpoint preview)
- `backend/reports/service.py` (użyj helper przy budowie `conditions_text`)
- `backend/tests/unit/test_format_conditions.py` (nowy)
- `frontend/src/components/contracts/ConditionPanel.vue` (linia 151-167 - refactor + preview)
- `frontend/src/stores/contracts.ts` (dodaj akcję `previewConditions`)
- `spec/core/assets/stary_format_rozliczenie.png` (referencja wizualna)

**Estimate:** 3-4h (M) — najważniejsze zadanie dla UX klienta

---

### [RAO-P1-009] Wymiana pieczątki firmy w dokumentach PDF (nowa wersja)

```yaml
id: RAO-P1-009
priority: P1
size: XS
status: triaged
classification: maintenance
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 223658.png pkt 5 'pieczątka do poprawy' + obrazek pieczątki"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** *„pieczątka do poprawy"* — klient przesłał nową wersję pieczątki z czterema liniami:
```
Toolsmart Sp. z o.o.
ul. Kłobucka 6B/103, 02-699 Warszawa
NIP 9512598092, Regon 528847124
KRS 0001109942
[podpis]
```

**Lokalizacja w kodzie:**
- `backend/reports/assets/protocol_stamp.png` (27856 bytes) — używana w protokołach przez `stamp_src` (`backend/reports/service.py` linia 573)
- `backend/reports/assets/company_stamp.jpg` (12275 bytes) — stary plik (nieużywany)
- `backend/reports/assets/company_stamp_fixed.jpg` (4304 bytes) — używana w umowach (`contract_u.html` linia 242, 316, `contract.html` linia 242, 387)

**Acceptance criteria (DoD):**

**Plik graficzny:**
- [ ] Klient ma przesłać oryginalny plik PNG (przezroczyste tło, wysoka rozdzielczość)
- [ ] Wymiar finalny: 360×140px (2× dla 180×70px @ retina) lub 720×280px @ 4×
- [ ] Format: PNG z przezroczystym tłem
- [ ] **TYMCZASOWO:** użyj obrazka z `temp/uwagi klienta/Zrzut ekranu 2026-05-25 223658.png` (crop dolnej części) — wystarcza do testów

**Backend:**
- [ ] Zamień `backend/reports/assets/protocol_stamp.png` na nową wersję
- [ ] Zamień `backend/reports/assets/company_stamp_fixed.jpg` na nową wersję:
  - **Opcja A:** skonwertuj PNG→JPG z białym tłem (Pillow: `Image.open('new.png').convert('RGB').save('company_stamp_fixed.jpg', quality=95)`)
  - **Opcja B (preferowane):** zmień szablony `contract.html`/`contract_u.html` żeby używały tego samego PNG co protokoły (jednolite source of truth):
    - `contract_u.html` linia 242, 316: `<img src="../assets/company_stamp_fixed.jpg"` → `<img src="../assets/protocol_stamp.png"`
    - `contract.html` linia 242, 387: analogicznie
- [ ] Sprawdź też `deployment/backend/reports/assets/` — jeśli istnieją te same pliki, zamień również
- [ ] Skasuj nieużywany `company_stamp.jpg`

**Test:**
- [ ] Wygeneruj PDF umowy → pieczątka widoczna w stopce
- [ ] Wygeneruj PDF protokołu (oba sekcje wydania i zwrotu) → pieczątka widoczna
- [ ] Sprawdź ostrość pieczątki przy zoomie 200%

**Weryfikacja danych firmy:**
- [ ] Sprawdź czy dane w bazie `company` są aktualne (porównaj z pieczątką):
  - NIP: 9512598092
  - Regon: 528847124
  - KRS: 0001109942 ⚠️ **KRS NIE istnieje obecnie w modelu `Company`** w `backend/settings/models.py` — jeśli klient chce go widzieć w nagłówku PDF, dodaj kolumnę `krs VARCHAR(20) NULL` (migracja `ALTER TABLE company ADD COLUMN IF NOT EXISTS krs VARCHAR(20)`)
  - Adres: ul. Kłobucka 6B/103, 02-699 Warszawa

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — nota o nowej pieczątce + ścieżki plików
- [ ] `spec/core/01_database.md` — dodaj kolumnę `krs` do `company` (jeśli implementowane)

**Pliki do zmiany:**
- `backend/reports/assets/protocol_stamp.png` (zamiana)
- `backend/reports/assets/company_stamp_fixed.jpg` (zamiana LUB usunięcie + użycie PNG)
- `backend/reports/templates/contract.html` (opcja B)
- `backend/reports/templates/contract_u.html` (opcja B)
- `deployment/backend/reports/assets/*` (sync)

**Estimate:** 30 min (XS) — głównie czeka na finalny plik graficzny od klienta

---

### [RAO-P1-011] [SPIKE] Walidacja wielokrotnego dodania tej samej maszyny + ostrzeżenie o zajętej maszynie

```yaml
id: RAO-P1-011
priority: P1
size: S
status: triaged
classification: spike/research
roles: [backend-dev, frontend-dev, qa-engineer]
source: client-request
source_date: 2026-05-25
source_ref: "pytania klienta z czatu (2026-05-25 23:07)"
specs_to_update:
  - core/04_business_logic.md
  - core/01_database.md
  - core/03_frontend_screens.md
migration_impact: tbd
security_impact: none
```

**Pytania klienta:**
1. *„Czy można dodać w jednej umowie maszyne external 5 razy np.?"*
2. *„Czy maszyna która jest używana będzie wyskakiwał monit z ostrzeżeniem i świadomym ponownym wybraniem już teoretycznie pożyczonej umowy?"*

**Cel spike-u:**
Zrozumieć obecny stan, zaproponować rozwiązanie (decyzja biznesowa + techniczna), dopiero wtedy zaplanować implementację jako osobne tasky.

---

#### Pytanie 1: Wielokrotne dodanie tej samej maszyny do umowy

**Analiza stanu obecnego (kod):**
- `backend/contracts/models.py::ContractPosition` — pole `article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)`
- **NIE MA `UniqueConstraint(contract_id, article_id)`** → technicznie można dodać tę samą maszynę N razy do tej samej umowy
- `Article.is_external` (bool) — odróżnia maszyny zewnętrzne (podnajem) od własnej floty
- Brak walidacji w `backend/contracts/service.py` przy `add_position` / `update_position`

**Pytania do biznesu (decyzja klienta — Toolsmart):**
- [ ] **Czy duplikat ma sens biznesowy?** Scenariusze:
  - **TAK (np. external):** Ten sam typ maszyny wynajęty 5× od różnych dostawców = 5 pozycji w umowie, każda z innym numerem seryjnym/cenniku. *Wymaga dodania pola `external_owner` lub `external_serial` per position.*
  - **TAK (taka sama maszyna własna):** Klient chce wynająć 5 jednakowych młotów udarowych. Wtedy lepiej: 1 pozycja z `quantity=5` (już jest pole `quantity` w `ContractPosition`!) — to jest preferowane rozwiązanie z punktu widzenia UX/danych.
  - **NIE (maszyna unikalna):** Maszyna z numerem seryjnym = unikat, nie może być na tej samej umowie 2×.
- [ ] **Czy rozróżnić zachowanie dla `is_external=true` vs `is_external=false`?**
  - Maszyna własna (numer seryjny) — UNIQUE per umowa (max 1 pozycja, ale z `quantity > 1`)
  - Maszyna external (typ + dostawca) — można 5× (różni dostawcy, różne ceny)

**Proponowane warianty rozwiązania (do wyboru przez klienta):**

**Wariant A: Strict UNIQUE per umowa (maszyny własne)**
- Dodaj unique constraint w bazie: `UNIQUE(contract_id, article_id) WHERE is_external = false`
- Maszyny external: bez constraint
- Frontend: jeśli dodaję maszynę własną która już jest w umowie → blokada + komunikat „Ta maszyna jest już w tej umowie. Zmień ilość w istniejącej pozycji."
- **Plus:** Spójność danych, jasne zasady
- **Minus:** Wymaga migracji + obsługa w frontendzie (gdzie pokazać `quantity`)

**Wariant B: Pozwól na duplikaty zawsze, ale ostrzeż**
- Brak unique constraint
- Frontend: warning toast „Maszyna {name} już jest w tej umowie (pozycja #3). Dodaję jako nową pozycję?" → user klika OK
- **Plus:** Elastyczność (np. ten sam młot dwie różne ceny w jednej umowie)
- **Minus:** Łatwo o pomyłkę, dane mniej spójne

**Wariant C: Hybryda — własne strict, external dozwolone z ostrzeżeniem**
- UNIQUE constraint tylko dla `is_external = false`
- Warning dla `is_external = true`
- **Plus:** Najbliżej rzeczywistości biznesowej (external = typ, własne = unikat)
- **Minus:** Najbardziej skomplikowane technicznie

---

#### Pytanie 2: Ostrzeżenie gdy maszyna jest aktualnie pożyczona w innej umowie

**Analiza stanu obecnego (kod):**
- Brak pola `is_currently_rented` lub `rental_status` w `Article`
- Brak walidacji w `add_position` że maszyna nie jest aktualnie wynajęta
- **Aktualnie:** żaden monit się nie wyświetli — można wpisać tę samą maszynę do 5 umów z nachodzącymi datami

**Co znaczy „aktualnie pożyczona"?**
Maszyna jest pożyczona, gdy istnieje umowa spełniająca WSZYSTKIE warunki:
- `Contract.is_settled = false` (nierozliczona)
- `Contract.date_from <= NOW() <= Contract.date_to` (okres aktualny)
- Maszyna jest pozycją w tej umowie

LUB lepiej: gdy okresy się nakładają z planowaną nową umową:
- Nowa umowa ma `date_from = X`, `date_to = Y`
- Sprawdź czy maszyna jest w innej umowie której okres `[date_from, date_to]` ma część wspólną z `[X, Y]`

**Proponowane rozwiązanie (do dyskusji):**

**Krok 1: Backend endpoint do sprawdzenia konfliktu**
- [ ] Dodaj `GET /articles/{article_id}/conflicts?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&exclude_contract_id={id}`
- Zwraca: `[{contract_id, contract_number, date_from, date_to, contractor_name}]`
- Implementacja:
  ```python
  async def find_article_conflicts(
      db, article_id: int, date_from: date, date_to: date, exclude_contract_id: int | None = None
  ) -> list[ConflictInfo]:
      query = select(Contract, ContractPosition).join(ContractPosition).where(
          ContractPosition.article_id == article_id,
          Contract.is_settled == False,
          # Okresy się nakładają jeśli: contract.date_from <= date_to AND contract.date_to >= date_from
          Contract.date_from <= date_to,
          Contract.date_to >= date_from,
      )
      if exclude_contract_id:
          query = query.where(Contract.id != exclude_contract_id)
      result = await db.execute(query)
      return [...]
  ```

**Krok 2: Frontend — warning modal**
- [ ] W `ArticlePicker.vue` po wyborze artykułu → wywołaj `GET /articles/{id}/conflicts` z aktualnymi datami umowy
- [ ] Jeśli są konflikty → pokaż modal:
  ```
  ⚠️ Uwaga: Maszyna {name} jest już w innych umowach w tym okresie:
  
  • Umowa S123/2026 (Cegro Sp. z o.o.) — 23.05 do 02.06.2026
  • Umowa S130/2026 (Bud-Mat) — 28.05 do 05.06.2026
  
  Czy na pewno chcesz dodać tę maszynę do bieżącej umowy?
  
  [ Anuluj ]    [ Tak, dodaj świadomie ]
  ```
- [ ] Po kliknięciu „Tak, dodaj świadomie" → kontynuuj normalnie + zaloguj `audit_log` (kto, kiedy, którą umowę pominął)

**Krok 3: Audit log (opcjonalne)**
- [ ] Tabela `position_conflict_overrides` (id, user_id, contract_id, article_id, conflicting_contract_ids, timestamp)
- [ ] W przyszłości można generować raport „świadome konflikty" dla admina

---

#### Acceptance criteria (spike — research only, NIE implementacja)

**Deliverables (output dokumentu):**
- [ ] Decyzja biznesowa od klienta: Wariant A / B / C dla pytania 1
- [ ] Decyzja biznesowa: jaki próg nakładania okresów (cały okres / >50% / dowolny dzień)
- [ ] Decyzja: blokować czy ostrzec (modal z ✓)
- [ ] Dokument w `spec/core/04_business_logic.md` sekcja „Walidacja duplikatów + konfliktów rental"
- [ ] Nowy backlog item P1 (lub P2 zależnie od decyzji) z konkretnymi zmianami:
  - Migration (jeśli unique constraint)
  - Backend endpoint
  - Frontend modal
  - E2E test

**Test scenariusze (do weryfikacji przed implementacją):**
- [ ] Scenariusz 1: dodaj maszynę external `X` 5× do umowy → obecnie działa, sprawdź czy jest sens biznesowy
- [ ] Scenariusz 2: maszyna `Y` w aktywnej umowie A (date_from=20.05, date_to=30.05). Próbuj dodać do nowej umowy B (date_from=25.05, date_to=10.06) → obecnie brak ostrzeżenia
- [ ] Scenariusz 3: maszyna `Y` w umowie rozliczonej (`is_settled=true`) — czy to liczy się jako konflikt? (najprawdopodobniej NIE)

**Czas spike:** 2-3h (analiza + dokument + rozmowa z klientem)

---

#### Pliki do przeczytania (research)

- `backend/articles/models.py` (linia 33: `is_external`)
- `backend/contracts/models.py` (linia 58-80: `ContractPosition` — brak unique)
- `backend/contracts/service.py` — funkcja `add_position` / `update_position`
- `backend/contracts/router.py` — endpointy positions
- `frontend/src/views/ContractFormView.vue` — gdzie się dodaje pozycje
- `frontend/src/components/contracts/ArticlePicker.vue` — picker maszyn

**Estimate:** 2-3h spike (research + 1 dokument decyzyjny dla klienta)

---

### [RAO-P1-010] Weryfikacja numeru telefonu w nagłówku PDF (klient zgłosił 888 992 017)

```yaml
id: RAO-P1-010
priority: P1
size: XS
status: triaged
classification: bugfix/data-quality
roles: [backend-dev, db-agent]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 223710.png 'tutaj jest bład zły numer 888 992 017 / powinien być 888 992 015'"
specs_to_update:
  - core/01_database.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** *„tutaj jest bład zły numer 888 992 017 / powinien być 888 992 015"*

**Analiza statyczna kodu:**
- Wszystkie szablony Jinja w `backend/reports/templates/*.html` mają hardcoded `+48 888 992 015` (POPRAWNY)
- W kodzie Pythona NIE MA wzmianki o `888 992 017`
- Możliwe źródło:
  1. **Najprawdopodobniej:** produkcja ma starą wersję szablonu lub stare dane w `company.header_text`
  2. Klient widział PDF wygenerowany przed ostatnią poprawką
  3. Pole `company.header_text` w bazie zawiera stary numer

**Acceptance criteria (DoD):**

**Weryfikacja:**
- [ ] Wykonaj `SELECT id, header_text FROM company` na produkcji
- [ ] Sprawdź deployment na produkcji (toolsmart.pl/rao) — czy szablony mają aktualną wersję
- [ ] Sprawdź `frontend/src/views/SettingsView.vue` — czy nigdzie nie jest pre-wypełnione `888 992 017`

**Naprawa (jeśli znaleziono źródło):**
- [ ] Jeśli `company.header_text` zawiera stary numer:
  ```sql
  UPDATE company SET header_text = REPLACE(header_text, '888 992 017', '888 992 015');
  ```
- [ ] Jeśli to deployment — wgraj aktualne szablony

**Test:**
- [ ] Wygeneruj PDF na lokalnym backendzie → numer `888 992 015`
- [ ] Wygeneruj PDF na produkcji → numer `888 992 015`

**Spec:**
- [ ] `spec/core/01_database.md` — nota o weryfikacji `company.header_text`

**Pliki do zmiany:** SQL `UPDATE company...` (jeśli potrzebne), ewentualnie deployment templates
**Estimate:** 15 min (XS)

---

### [RAO-P1-012] PDF OWN — ujednolicenie wcięć w listach numerowanych (klient: "nic nie wystaje")

```yaml
id: RAO-P1-012
priority: P1
size: M
status: triaged
classification: bugfix/pdf/visual
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "klient bardzo restrykcyjny dot. OWN. Analiza docx w spec/archive/reference_reports/own/ownA.docx + ownU.docx wykazała hanging indenty 12.7mm/19.05mm"
specs_to_update:
  - core/11_reports_stats.md
  - core/09_design_reference.md
migration_impact: no
security_impact: none
verification:
  - "Analiza ownA.docx (Python python-docx): pierwsze paragrafy definicji L=0mm, listy numerowane left=720 twips (12.7mm), hanging=360 twips (6.35mm), sub-listy left=1080 twips (19.05mm)"
  - "Obecnie w contract.html: .own-num padding-left:14px (≈3.7mm) text-indent:-14px — ZA MAŁE wcięcie, niezgodne z docx"
  - "W docx klienta sub-listy są niespójne (różne abstractNumId: 9 / 10 / 11 — od left=720 do 1440 twips), więc agent ma uporządkować JEDNĄ SPÓJNĄ regułę dla wszystkich sub-list"
```

**Problem (cytat klienta):** *„klient ma fisia żeby wszystkie wcięcia były równe i nic nie wystawało"*

Klient wymaga aby w OWN (strona/-y z Ogólnymi Warunkami Najmu):
1. **Wszystkie główne numerowane punkty** (`1. 2. 3. ... 17.`) były wyrównane w **tej samej pionowej linii** (numer w pionie + tekst zaczynał się w pionie)
2. **Wszystkie sub-litery** (`a) b) c)` lub `a. b. c.`) były wyrównane w **innej, głębszej pionowej linii**
3. **Numery dwucyfrowe** (`10.`, `11.`, `17.`) nie wystawały na lewo poza linię numerów jednocyfrowych
4. **Kontynuacja tekstu w drugiej linii** akapitu wyrównana z pierwszą literą tekstu (nie z numerem) — czyli prawdziwy hanging indent

---

#### Analiza obecnego stanu

**Obecne CSS w `backend/reports/templates/contract.html` (linia 86-87):**
```css
.own-num        { margin: 1px 0 0; padding-left: 14px; text-indent: -14px; font-size: 7pt; line-height: 1.1; text-align: justify; }
.own-num-indent { margin: 0 0 0;   padding-left: 22px; text-indent: -14px; font-size: 7pt; line-height: 1.1; text-align: justify; }
```

**Obecne CSS w `backend/reports/templates/contract_u.html` (linia 73-74):**
```css
.own-num        { margin: 4px 0 4px; padding-left: 0; text-indent: -14px; padding-left: 14px; font-size: 7.5pt; ... }
.own-num-indent { margin: 3px 0 3px; padding-left: 22px; text-indent: -14px; font-size: 7.5pt; ... }
```

**Problemy:**
1. Wartości w `px` (14px ≈ 3.7mm) zamiast `mm` — niespójne z docx klienta (12.7mm)
2. `text-indent: -14px` (≈-3.7mm) za małe → **numery dwucyfrowe `10.` `11.` `17.` wystają na lewo** (4 znaki vs 3.7mm)
3. Niespójność między `contract.html` (font 7pt) i `contract_u.html` (font 7.5pt)
4. `padding-left` zdublowane w `contract_u.html` linia 73 (`padding-left: 0; padding-left: 14px`) — szum CSS
5. Brak `text-align: justify` ustawionego konsekwentnie

---

#### Analiza docx klienta (`spec/archive/reference_reports/own/ownA.docx`)

**Margines strony:** left=12.51mm, right=12.7mm, top=10mm, bottom=5.01mm

**Wcięcia paragrafów (z `numbering.xml`):**

| Element | numId | abstractId | left (twips) | left (mm) | hanging (twips) | hanging (mm) | Uwagi |
|---------|-------|------------|--------------|-----------|-----------------|--------------|-------|
| §1 definicje (akapit normal) | - | - | 0 | 0mm | - | - | Bez wcięcia |
| §2 punkty 1-15 | 5 | 7 | 720 | **12.7mm** | 360 | **6.35mm** | Decimal `%1.` |
| §3 punkty 1-8 | 6 | 13 | 720 | **12.7mm** | 360 | **6.35mm** | Decimal `%1.` |
| §3 pkt 8 sub-listy a)-d) | 7 | 9 | **1080** | **19.05mm** | 360 | **6.35mm** | lowerLetter `%1)` |
| §4 punkty 1-17 | 8 | 14 | 720 | **12.7mm** | 360 | **6.35mm** | Decimal `%1.` |
| §4 pkt 10 sub-listy a)-c) | 13 | 10 | **1440** | **25.4mm** | 360 | **6.35mm** | ⚠️ NIESPÓJNE z §3 |
| §5 punkty 1-9 | 9 | 3 | 720 | **12.7mm** | 360 | **6.35mm** | Decimal `%1.` |
| §6 lista a-d (bez numeru) | 11 | 11 | **720** | **12.7mm** | 360 | **6.35mm** | ⚠️ NIESPÓJNE — sub-listy spłaszczone |
| §7 punkty 1-5 | - | - | 720 | **12.7mm** | 360 | **6.35mm** | Decimal `%1.` |

**Kluczowy wniosek:** W oryginalnym docx klienta sub-listy mają **różne wcięcia** (1080 vs 1440 twips). Klient widzi tę niespójność w wygenerowanym PDF i się denerwuje. **Agent ma uporządkować jedną spójną regułę** dla wszystkich sub-list.

---

#### Acceptance criteria (DoD)

**1. Ujednolicone CSS dla OWN (do zastosowania w `contract.html` ORAZ `contract_u.html`):**

Zastąp obecne `.own-num` i `.own-num-indent` przez:

```css
/* OWN — hanging indent ujednolicony, zgodny z docx klienta */
/* Poziom 0 (definicje §1) — bez wcięcia, tylko zwykły akapit */
p.ot {
  font-size: 7.5pt;
  margin: 1px 0;
  text-align: justify;
  line-height: 1.15;
  padding-left: 0;
  text-indent: 0;
}
p.ot strong { font-size: 7.5pt; }

/* Poziom 1 — główne numerowane punkty (1. 2. ... 17.) */
/* Numer "wisi" na lewo na pozycji 0mm, tekst zaczyna się na 7mm */
.own-num {
  font-size: 7.5pt;
  margin: 2px 0;
  padding-left: 7mm;      /* tekst zaczyna od 7mm */
  text-indent: -7mm;      /* numer wisi na -7mm = na pozycji 0mm (lewa krawędź akapitu) */
  line-height: 1.15;
  text-align: justify;
}

/* Poziom 2 — sub-listy a) b) c) lub a. b. c. */
/* Litera "wisi" na pozycji 7mm (równo z tekstem poziomu 1), tekst zaczyna się na 13mm */
.own-num-indent {
  font-size: 7.5pt;
  margin: 2px 0;
  padding-left: 13mm;     /* tekst sub-listy zaczyna od 13mm */
  text-indent: -6mm;      /* litera wisi na -6mm = na pozycji 7mm (równo z tekstem .own-num !) */
  line-height: 1.15;
  text-align: justify;
}

/* Tytuły paragrafów (§ 1, § 2 ...) — wyśrodkowane */
.own-par {
  font-size: 10pt;
  font-weight: bold;
  text-align: center;
  margin: 6px 0 1px 0;
}
.own-sub {
  font-size: 9pt;
  font-weight: bold;
  text-align: center;
  margin: 0 0 5px 0;
}
```

**Pionowa logika wyrównania (klient to widzi i tego pilnuje):**
```
| 0mm    | 7mm                                       | 13mm     |
|--------|-------------------------------------------|----------|
| 1.     | Tekst głównego punktu                     |          |
|        | kontynuacja w drugiej linii bez wcięcia   |          |
| 2.     | Tekst                                     |          |
|        |          a)                               | Tekst sub-listy |
|        |          b)                               | Tekst    |
|        |          c)                               | Tekst    |
| 10.    | Tekst (dwucyfrowy numer NIE wystaje)      |          |
| 17.    | Tekst                                     |          |
```

**2. Zastosowanie zmian:**

- [ ] **`backend/reports/templates/contract.html`** (umowa najmu typ S):
  - [ ] Linia 84-87: zastąp obecne CSS dla `p.ot`, `.own-num`, `.own-num-indent`, `.own-par`, `.own-sub` powyższymi wartościami
  - [ ] Usuń zdublowane `padding-left` jeśli istnieje
  - [ ] Sprawdź czy `font-size: 7pt` (obecnie) → zmień na `7.5pt` (spójność z `contract_u.html`)
- [ ] **`backend/reports/templates/contract_u.html`** (umowa usługi typ U):
  - [ ] Linia 71-74: zastąp CSS analogicznie
  - [ ] Usuń `padding-left: 0; padding-left: 14px` (zdublowane)
- [ ] **Sprawdź użycie klas w treści OWN** (`contract.html` linia 264-380, `contract_u.html` linia 260+):
  - [ ] Wszystkie `<p class="own-num">1. ...` mają numer **na początku tekstu** (nie ma `<li>` ani `<ol>`)
  - [ ] Wszystkie `<p class="own-num-indent">a) ...` analogicznie
  - [ ] **NIE** używaj `<ol type="1">` ani `<ol type="a">` — agent ma zachować obecny układ z numerem manualnym wpisanym w tekście, tylko poprawić CSS

**3. Weryfikacja wizualna (KRYTYCZNA — klient sprawdzi to wzrokiem):**

- [ ] Wygeneruj PDF dla istniejącej umowy typu S → otwórz w przeglądarce / podglądzie
- [ ] **Test 1 — wyrównanie numerów jednocyfrowych:** Punkty `1.`, `2.`, ..., `9.` w §2/§3/§4/§5 muszą zaczynać się dokładnie w tej samej pionowej linii (cyfra na poziomie 0mm relatywnie do akapitu)
- [ ] **Test 2 — wyrównanie numerów dwucyfrowych:** Punkty `10.`, `11.`, ..., `17.` w §4 muszą **też** zaczynać się w tej samej pionowej linii (kropka po numerze może wystawać minimalnie, ale cyfra "1" musi być na poziomie 0mm)
- [ ] **Test 3 — wyrównanie kontynuacji tekstu:** Druga linia akapitu (gdy tekst się zawija) musi zaczynać się dokładnie na 7mm (pod pierwszą literą tekstu, NIE pod numerem)
- [ ] **Test 4 — wyrównanie sub-list:** Litery `a)`, `b)`, `c)`, `d)` w §3 pkt 8 oraz §4 pkt 10 muszą zaczynać się w tej samej pionowej linii (na poziomie 7mm) — TA SAMA linia co tekst głównych punktów
- [ ] **Test 5 — kontynuacja tekstu sub-listy:** Druga linia sub-listy zaczyna się na 13mm (pod pierwszą literą tekstu sub-listy)
- [ ] **Test 6 — analogicznie dla `contract_u.html`** (umowa usługi)
- [ ] **Test 7 — porównanie wizualne** z `spec/archive/reference_reports/own/ownA.pdf` (otwórz oba PDF obok siebie) — wcięcia powinny wyglądać RÓWNIEJ niż w docx klienta (bo my unifikujemy 1080/1440 do jednej wartości 13mm)

**4. Edge cases do sprawdzenia:**

- [ ] §1 Definicje — paragrafy z bold prefixem (`<strong>Ogólne Warunki Najmu</strong>`) — mają być bez wcięcia (klasa `.ot`, NIE `.own-num`)
- [ ] §6 (`contract.html` linia 365-371) — lista `a. b. c. d.` po wstępie `Wynajmujący może rozwiązać Umowę Najmu...` — agent ma to ZACHOWAĆ jako `.own-num-indent` (nie zmienia logiki, tylko CSS)
- [ ] Numery z kropką (`1.`) vs nawiasem (`a)`) — obie formy mają działać z tym samym CSS (bo to tekst, nie list-style)

**5. Nie zmieniaj:**
- [ ] Treści OWN (paragrafy prawne) — tylko CSS
- [ ] Struktury HTML (`<table class="own-table">`, `<td>` kolumny lewa/prawa)
- [ ] `.own-page` padding (6mm 12mm) — zostaje
- [ ] Nagłówków `<div class="own-title">`, `<div class="own-par">`, `<div class="own-sub">` — tylko poprawiamy CSS dla nich (margins/spacing)

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — sekcja "OWN: hanging indent" z dokładną tabelą wartości CSS
- [ ] `spec/core/09_design_reference.md` — zmienne CSS dla OWN (rozważ wprowadzenie `--own-indent-1: 7mm; --own-indent-2: 13mm;`)

**Pliki do zmiany:**
- `backend/reports/templates/contract.html` (CSS linia 84-87)
- `backend/reports/templates/contract_u.html` (CSS linia 71-74)
- `spec/core/11_reports_stats.md` (dokumentacja)
- `spec/core/09_design_reference.md` (zmienne)

**Materiał referencyjny:**
- `spec/archive/reference_reports/own/ownA.docx` (oryginalny docx klienta — umowa najmu)
- `spec/archive/reference_reports/own/ownU.docx` (oryginalny docx klienta — umowa usługi)
- `spec/archive/reference_reports/own/ownA.pdf` (zrenderowany PDF z docx — to widzi klient na druku)
- `spec/archive/reference_reports/own/ownU.pdf`
- `temp/own_analysis.txt` (output analizy python-docx — szczegółowe wartości twipsów per paragraf)

**Estimate:** 1-2h (M) — głównie iteracja wizualna z porównaniem z PDF klienta. Klient prawdopodobnie odeśle to do poprawki kilka razy, więc proszę uważać na detale (klient ma "fisia" 😉).

---

## 🟡 P2 — Should-Have

### [RAO-P2-001] PDF Umowa NAJMU (typ S) — sekcja "Inne usługi" w określonej kolejności i formacie

```yaml
id: RAO-P2-001
priority: P2
size: M
status: triaged
classification: feature/pdf
roles: [backend-dev, db-agent]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 223658.png pkt 3 — pełna lista usług z cenami"
specs_to_update:
  - core/11_reports_stats.md
  - core/04_business_logic.md
migration_impact: yes
security_impact: none
```

**Problem (cytat klienta):** *„Inne usługi musi być jak teraz jest na umowie i w tej kolejności również:"*

**Wymagana lista i kolejność:**
1. Transport: 500.00 zł / dostawa / 500.00 zł odbiór
2. Czyszczenie maszyny po wynajmie (zabrudzenia drobne): 150.00 zł - 400.00 zł
3. Czyszczenie maszyny po wynajmie (zabrudzenia trudnościeralne): 400.00 zł - 1500.00 zł
4. Usługa tankowania: 200.00 zł (plus koszt paliwa)
5. Ponadnormatywny przestój transportu: 200.00 zł / h - 300.00 zł / h
6. Nieuzasadnione wezwanie serwisowe: 280.00 zł (plus transport)

**Analiza:**
- Obecnie w `contract_u.html` linia 192-210 cennik pochodzi z `fees` (`ServiceFeeTemplate`)
- Klient chce konkretne wartości i kolejność jako **domyślne dla wszystkich umów najmu**

**Acceptance criteria (DoD):**

**DB (seed/migration):**
- [ ] **UWAGA:** Mapping typów w aplikacji RAO: `'S' = NAJEM` (`contract.html`), `'U' = USŁUGA` (`contract_u.html`). Cennik usług dodatkowych dotyczy **WYŁĄCZNIE typu S (najem)** — patrz RAO-P1-004 dla uzasadnienia.
- [ ] W `backend/main.py` startup migrations dodaj seed:
  ```python
  async def seed_default_fees_for_S():
      """Idempotentny seed cennika usług dodatkowych dla umów typu S (NAJEM)."""
      async with AsyncSessionLocal() as db:
          existing = await db.execute(
              select(FeePresetGroup).where(
                  FeePresetGroup.contract_type == 'S',
                  FeePresetGroup.is_default == True
              )
          )
          if existing.scalar_one_or_none():
              return  # Już istnieje
          
          group = FeePresetGroup(
              name='Standardowe usługi NAJMU',
              contract_type='S',
              is_default=True,
              sort_order=0,
              company_id=1,
          )
          db.add(group)
          await db.flush()
          
          templates = [
              ServiceFeeTemplate(preset_id=group.id, contract_type='S', sort_order=1,
                  name='Transport', description='dostawa / odbiór',
                  amount_from=500, amount_to=500, unit='zł', is_active=True, company_id=1),
              ServiceFeeTemplate(preset_id=group.id, contract_type='S', sort_order=2,
                  name='Czyszczenie maszyny po wynajmie', description='zabrudzenia drobne',
                  amount_from=150, amount_to=400, unit='zł', is_active=True, company_id=1),
              ServiceFeeTemplate(preset_id=group.id, contract_type='S', sort_order=3,
                  name='Czyszczenie maszyny po wynajmie', description='zabrudzenia trudnościeralne',
                  amount_from=400, amount_to=1500, unit='zł', is_active=True, company_id=1),
              ServiceFeeTemplate(preset_id=group.id, contract_type='S', sort_order=4,
                  name='Usługa tankowania', description='plus koszt paliwa',
                  amount_from=200, amount_to=None, unit='zł', is_active=True, company_id=1),
              ServiceFeeTemplate(preset_id=group.id, contract_type='S', sort_order=5,
                  name='Ponadnormatywny przestój transportu', description=None,
                  amount_from=200, amount_to=300, unit='zł/h', is_active=True, company_id=1),
              ServiceFeeTemplate(preset_id=group.id, contract_type='S', sort_order=6,
                  name='Nieuzasadnione wezwanie serwisowe', description='plus transport',
                  amount_from=280, amount_to=None, unit='zł', is_active=True, company_id=1),
          ]
          db.add_all(templates)
          await db.commit()
  ```
- [ ] Wywołaj `await seed_default_fees_for_S()` w `@app.on_event("startup")`

**Backend (renderowanie):**
- [ ] `backend/reports/service.py` — kontekst dla template: `fees` musi pochodzić z domyślnego presetu dla typu umowy, sortowane po `sort_order`
- [ ] Jeśli umowa ma override → użyj override; inaczej → preset

**Test:**
- [ ] Restart backendu → seed wykonany (sprawdź `SELECT * FROM service_fee_templates WHERE preset_id IN (SELECT id FROM fee_preset_groups WHERE contract_type='S')`)
- [ ] Drugi restart → seed nie duplikuje (idempotentność)
- [ ] Wygeneruj PDF umowy typu **S** (najem) → 6 pozycji w wymaganej kolejności w sekcji "Inne usługi"
- [ ] Wygeneruj PDF umowy typu U (usługa) → sekcja "Cennik usług dodatkowych" NIE występuje (po RAO-P1-004)

**Spec:**
- [ ] `spec/core/04_business_logic.md` — domyślne stawki dla typu S (najem)
- [ ] `spec/core/11_reports_stats.md` — kolejność i format cennika
- [ ] `spec/core/01_database.md` — seed data

**Pliki do zmiany:**
- `backend/main.py` (startup seed)
- `backend/reports/service.py` (logika fees per type)

**Estimate:** 3-4h (M)

---

### [RAO-P2-002] PDF Umowa — sekcja "Uwagi" w określonej kolejności

```yaml
id: RAO-P2-002
priority: P2
size: S
status: triaged
classification: feature/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 223658.png pkt 4 — lista uwag"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** *„Uwagi również muszą być tak jak są na umowie:"*
- Doba wynajmu obejmuje 1 dzień kalendarzowy (do 8 godz. pracy jednego dnia)
- Zgłoszenie zwrotu urządzenia: pisemnie, min. z jednodniowym wyprzedzeniem
- Ilość dni pracy w tygodniu: 6
- dokumentacja zdjęciowa: wykonano

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract_u.html` linia 217-225 — fallback gdy `contract.notes` puste
- `backend/reports/templates/contract.html` — analogiczna sekcja

**Acceptance criteria (DoD):**

**Backend (oba szablony):**
- [ ] Zmień default block:
  ```jinja
  {% else %}
  <p style="margin:0 0 4px 0;"><strong>Doba wynajmu:</strong> obejmuje 1 dzień kalendarzowy (do 8 godz. pracy jednego dnia).</p>
  <p style="margin:0 0 4px 0;"><strong>Zgłoszenie zwrotu urządzenia:</strong> pisemnie, min. z jednodniowym wyprzedzeniem.</p>
  <p style="margin:0 0 4px 0;"><strong>Ilość dni pracy w tygodniu:</strong> {% if contract.working_days_per_week %}{{ contract.working_days_per_week }}{% else %}6{% endif %}.</p>
  <p style="margin:0;"><strong>Dokumentacja zdjęciowa:</strong> wykonano.</p>
  {% endif %}
  ```

**Test:**
- [ ] Wygeneruj PDF dla umowy bez `notes` → 4 podpunkty w wymaganym formacie
- [ ] Wygeneruj PDF dla umowy z `notes` → custom notes (niezmienione)

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — domyślne uwagi

**Pliki do zmiany:** `backend/reports/templates/contract_u.html` (linia 217-225), `backend/reports/templates/contract.html`
**Estimate:** 30 min (S)

---

### [RAO-P2-003] PDF Umowa — mniejsze tabelki i mniejszy opis (kompaktniejszy layout)

```yaml
id: RAO-P2-003
priority: P2
size: M
status: triaged
classification: ux/pdf
roles: [backend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "Scan...pdf strona 1 ('mniejsze' przy tabeli + 'do poprawy' przy 'Inne usługi'), zrzut 223652.png pkt 2 'Opis mniejszy'"
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):**
- Tabela „Przedmiot najmu" jest za duża
- „Inne usługi" za duża
- Główny opis (uwagi obok przedmiotu) za duży

**Lokalizacja w kodzie:**
- `backend/reports/templates/contract_u.html` linia 47-50 — CSS `table.pos`
- Linia 56 — `.bottom-box`

**Acceptance criteria (DoD):**

**Backend (CSS w `contract_u.html` i `contract.html`):**
- [ ] `table.pos` — `font-size` z `9px` na `8.5px`
- [ ] `table.pos td` — `padding` z `4px 5px` na `2px 4px`
- [ ] `table.pos th` — `padding` z `3px 5px` na `2px 4px`
- [ ] `.bottom-box` (uwagi) — `font-size` z `9px` na `8px`, `padding` z `5px 8px` na `4px 6px`, `line-height` z `1.45` na `1.3`
- [ ] `.cond` — z `9px` na `8.5px`

**Test:**
- [ ] Wygeneruj PDF — wszystkie tabelki i opisy wyraźnie kompaktniejsze
- [ ] Sprawdź czytelność (font-size ≥ 8px)
- [ ] Sprawdź alignment/overflow

**Spec:**
- [ ] `spec/core/11_reports_stats.md` — wymiary fontów w PDF umowy

**Pliki do zmiany:** `backend/reports/templates/contract_u.html` (CSS), `backend/reports/templates/contract.html` (CSS)
**Estimate:** 1-2h (M)

---

### [RAO-P2-004] Frontend formularz umowy — wybór okresu przez kalendarz + ilość dni

```yaml
id: RAO-P2-004
priority: P2
size: M
status: triaged
classification: feature/ux
roles: [frontend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 224827.png pkt 1 'Wybór okresu umowy - w jakiś inny sposób np. zaznaczenie 25.05.2026 daty na kalendarzu i wpisaniu ile dni mniej więcej?'"
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** Obecny picker dat (`DateRangePicker` — `date_from` + `date_to`) jest niepraktyczny. Klient woli: kliknąć datę startową + wpisać ilość dni (auto-oblicza datę końcową).

**Lokalizacja w kodzie:**
- `frontend/src/components/shared/DateRangePicker.vue`
- `frontend/src/views/ContractFormView.vue` — używa DateRangePicker

**Acceptance criteria (DoD):**

**Frontend:**
- [ ] Utwórz `frontend/src/components/shared/ContractPeriodPicker.vue`:
  - Input 1: data startowa (`date_from`) — single date picker
  - Input 2: ilość dni (`days`) — number input (`min=1`)
  - Computed: `date_to = date_from + (days - 1) days`
  - Wyświetl pod inputem: `"Okres umowy: {date_from_pl} – {date_to_pl}"`
- [ ] Komponent emit-uje `date_from` i `date_to` (kompatybilność)
- [ ] Mount z istniejącymi danymi: oblicz `days = (date_to - date_from).days + 1`

**Integracja:**
- [ ] `ContractFormView.vue` — zastąp `DateRangePicker` przez `ContractPeriodPicker`

**Test:**
- [ ] Smoke E2E (`04-contract.spec.ts`): utwórz umowę z `date_from=25.05.2026`, `days=10` → `date_to=03.06.2026`

**Spec:**
- [ ] `spec/core/03_frontend_screens.md` — nowy komponent

**Pliki do zmiany:**
- `frontend/src/components/shared/ContractPeriodPicker.vue` (nowy)
- `frontend/src/views/ContractFormView.vue` (integracja)

**Estimate:** 3-4h (M)

---

### [RAO-P2-005] Frontend — dodawanie kontrahenta inline z formularza umowy

```yaml
id: RAO-P2-005
priority: P2
size: M
status: triaged
classification: feature/ux
roles: [frontend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 224827.png pkt 2 'wybór kontrahenta - wszystko ok jak jest w bazie a jak nie ma? ułatwiłoby gdyby na tym etapie można byłoby go dodać'"
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** Gdy kontrahenta nie ma w bazie, użytkownik musi wyjść z formularza umowy, dodać go, wrócić. Klient chce: w pickerze przycisk „➕ Dodaj nowego" → modal z formularzem.

**Lokalizacja w kodzie:**
- Sprawdź `frontend/src/views/ContractFormView.vue` — komponent pickera kontrahenta (może być inline lub osobny)
- Reuzywalna logika z `frontend/src/views/contractors/ContractorFormView.vue`

**Acceptance criteria (DoD):**

**Frontend:**
- [ ] W pickerze kontrahenta dodaj przycisk „➕ Dodaj nowego kontrahenta" (prominentny CTA gdy search nie zwraca wyników)
- [ ] Klik otwiera modal `ContractorQuickAddModal.vue` z minimalnym formularzem:
  - NIP (z możliwością auto-pobrania z GUS — `POST /integrations/gus/lookup`)
  - Nazwa
  - Adres (street, postal_code, city)
  - Email
  - Telefon
- [ ] Po `POST /contractors` → automatycznie wybierz kontrahenta w pickerze + zamknij modal
- [ ] Toast: „Kontrahent {name} utworzony i wybrany"

**Backend (weryfikacja):**
- [ ] Endpoint `POST /contractors` — sprawdź czy zwraca pełny obiekt. Jeśli nie — zaktualizuj response.

**Test:**
- [ ] Smoke E2E: w formularzu umowy → „Dodaj kontrahenta" → wypełnij modal → kontrahent automatycznie wybrany

**Spec:**
- [ ] `spec/core/03_frontend_screens.md` — opis QuickAdd modal

**Pliki do zmiany:**
- `frontend/src/components/contractors/ContractorQuickAddModal.vue` (nowy)
- `frontend/src/views/ContractFormView.vue` (integracja przycisku)
- `frontend/src/stores/contractors.ts` (jeśli wymagane)

**Estimate:** 3-4h (M)

---

### [RAO-P2-006] Frontend — dodawanie artykułu inline z formularza umowy

```yaml
id: RAO-P2-006
priority: P2
size: M
status: triaged
classification: feature/ux
roles: [frontend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 224827.png pkt 3 'i tak samo z artykułami też żeby była możliwość dodania na bieżąco jakieś maszyny gdyby nie było'"
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** Analogicznie do P2-005, ale dla artykułów (maszyn).

**Lokalizacja w kodzie:**
- `frontend/src/components/contracts/ArticlePicker.vue` (lub podobny)

**Acceptance criteria (DoD):**

**Frontend:**
- [ ] W `ArticlePicker.vue` dodaj przycisk „➕ Dodaj nową maszynę"
- [ ] Klik otwiera modal `ArticleQuickAddModal.vue`:
  - Nazwa
  - Kategoria (dropdown z `Category`)
  - Numer seryjny (opcjonalne)
  - Wartość odtworzeniowa (opcjonalne)
  - Domyślna stawka dobowa (opcjonalne)
- [ ] Po `POST /articles` → automatycznie wybierz w pickerze + zamknij modal
- [ ] Toast

**Backend (weryfikacja):**
- [ ] `POST /articles` zwraca pełny obiekt

**Test:**
- [ ] Smoke E2E

**Spec:**
- [ ] `spec/core/03_frontend_screens.md`

**Pliki do zmiany:**
- `frontend/src/components/articles/ArticleQuickAddModal.vue` (nowy)
- `frontend/src/components/contracts/ArticlePicker.vue` (modyfikacja)

**Estimate:** 3-4h (M)

---

### [RAO-P2-007] Frontend — pomoc/preview jak wpisywać kwoty rozliczenia

```yaml
id: RAO-P2-007
priority: P2
size: S
status: triaged
classification: feature/ux
roles: [frontend-dev]
source: client-request
source_date: 2026-05-25
source_ref: "zrzut 224827.png pkt 4 'Proszę podpowiedź mi jak mam wstawiać kwoty - rozliczenie? w umowie?'"
depends_on: [RAO-P1-008]
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: none
```

**Problem (cytat klienta):** Klient nie wie jak wpisywać kwoty rozliczenia. Po implementacji P1-008 (format kaskadowy) — dodaj UX pomocniczy.

**Acceptance criteria (DoD):**

**Frontend (`ConditionPanel.vue`):**
- [ ] Dodaj nad sekcją warunków accordion „📖 Jak wpisać warunki rozliczenia?":
  ```
  Przykład — koparka z kaskadową stawką dobową (jak w starej aplikacji):
  
  Warunek 1: rate_type="dobowa", rate1=540, period_count=3, billing_label="doba"
    → preview: "1 - 3 dni - 540,00 / doba"
    
  Warunek 2: rate_type="dobowa", rate1=410, period_count=16, billing_label="doba"
    → preview: "4 - 16 dni - 410,00 / doba"
    
  Warunek 3: rate_type="dobowa", rate2=350, billing_label="doba" (bez period_count)
    → preview: "powyżej 16 dni - 350,00 / doba"
  ```
- [ ] Dodaj live-preview pod formularzem warunku — wyświetl wynik `format_position_conditions_cascading()` przez endpoint `/conditions/preview` (z P1-008)
- [ ] Tooltip przy polu `rate2` z wyjaśnieniem „ostatni warunek (powyżej) — pozostaw period_count puste"

**Spec:**
- [ ] `spec/core/03_frontend_screens.md` — UX pomocy w ConditionPanel

**Pliki do zmiany:** `frontend/src/components/contracts/ConditionPanel.vue`
**Estimate:** 1-2h (S)

---

## 🟢 P3 — Nice-to-Have
*(brak)*

---

## 📋 Tabela TL;DR

| ID | Tytuł | Źródło | P | Est. | Status |
|----|-------|--------|---|------|--------|
| RAO-P1-001 | PDF Umowa — usunąć duplikat "na budowie" | klient skan + czat | P1 | XS | triaged |
| RAO-P1-002 | PDF Umowa — "Dni pracy/tydzień" → "Ilość dni pracy" | klient skan | P1 | XS | triaged |
| RAO-P1-003 | PDF Umowa — "*ceny netto" wyraźnie na dole | klient skan | P1 | S | triaged |
| RAO-P1-004 | PDF Umowa U (usługa) — usuń cennik dodatkowy | klient czat + OWN ref | P1 | S | triaged |
| RAO-P1-005 | PDF Protokół — etykieta "nr tel" w boksie kontaktu | klient skan + czat | P1 | S | triaged |
| RAO-P1-006 | PDF Protokół — większa tabela "Przy wydaniu/odbiorze" | klient skan | P1 | S | triaged |
| RAO-P1-007 | PDF Protokół — 1 duża tabela "uwagi" zamiast 3 | klient czat | P1 | M | triaged |
| RAO-P1-008 | Format kaskadowy warunków rozliczenia (jak stara app) | klient + legacy | P1 | M | triaged |
| RAO-P1-009 | Wymiana pieczątki firmy w PDF | klient czat | P1 | XS | triaged |
| RAO-P1-010 | Weryfikacja numeru telefonu w nagłówku | klient czat | P1 | XS | triaged |
| RAO-P1-011 | **[SPIKE]** Walidacja duplikatu maszyny + ostrzeżenie o konflikcie wynajmu | klient czat | P1 | S | triaged |
| RAO-P1-012 | PDF OWN — ujednolicenie wcięć w listach (klient: "nic nie wystaje") | klient + docx ref | P1 | M | triaged |
| RAO-P2-001 | PDF Umowa NAJMU (S) — domyślny cennik dodatkowy (6 pozycji) | klient czat | P2 | M | triaged |
| RAO-P2-002 | PDF Umowa — domyślne uwagi (4 podpunkty) | klient czat | P2 | S | triaged |
| RAO-P2-003 | PDF Umowa — kompaktniejszy layout | klient skan + czat | P2 | M | triaged |
| RAO-P2-004 | Frontend — okres umowy przez kalendarz + dni | klient czat | P2 | M | triaged |
| RAO-P2-005 | Frontend — inline add kontrahenta | klient czat | P2 | M | triaged |
| RAO-P2-006 | Frontend — inline add artykułu | klient czat | P2 | M | triaged |
| RAO-P2-007 | Frontend — pomoc UX jak wpisywać warunki | klient czat | P2 | S | triaged |

**Razem:** 19 zadań (w tym 1 spike) · ~29-37h pracy

---

## 🗂️ Materiały referencyjne dla agenta

**Lokalizacje plików klienta (źródło prawdy):**
- `temp/uwagi klienta/Scan2026-05-25_125656.pdf` — 4-stronicowy skan umowy + protokołu z odręcznymi adnotacjami
- `temp/uwagi klienta/Zrzut ekranu 2026-05-25 223652.png` — punkty 1-2 (czat)
- `temp/uwagi klienta/Zrzut ekranu 2026-05-25 223658.png` — punkty 3-5 + obrazek pieczątki (czat)
- `temp/uwagi klienta/Zrzut ekranu 2026-05-25 223706.png` — punkt 6 + protokół 1-4 (czat)
- `temp/uwagi klienta/Zrzut ekranu 2026-05-25 223710.png` — umowa usługi + protokół + telefon (czat)
- `temp/uwagi klienta/Zrzut ekranu 2026-05-25 224827.png` — UX formularz umowy 1-4 (czat)
- `temp/uwagi klienta/stary_format.png` → skopiowane do `spec/backlog/stary_format_rozliczenie.png` — referencja formatu kaskadowego z starej aplikacji
- `temp/uwagi klienta/pdf_pages/page_*.png` — strony PDF jako obrazy (do przeglądania w IDE)

**Stara aplikacja WinForms (referencja):**
- `C:\projects\repos\AppRao\rao\FormW.cs` linia 690-750 — algorytm formatowania warunków kaskadowych
- Spojrzeć też na `FormW.cs` linia 1230-1310 dla edge cases

**Aktualne szablony PDF:**
- `backend/reports/templates/contract_u.html` — umowa (najem U + usługa S)
- `backend/reports/templates/contract.html` — umowa (alternatywny wariant)
- `backend/reports/templates/protocol_zo.html` — protokół zdawczo-odbiorczy
- `backend/reports/templates/protocol_zo_u.html` — protokół wykonania usługi
- `backend/reports/templates/protocol_zo_nodata*.html` — warianty bez danych
