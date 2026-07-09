# Prosty podział cenników w `ContractFormView` — KISS

> Status: propozycja UX / projekt do wykonania  
> Dotyczy: `ContractFormView.vue`, `ConditionPanel.vue`, `ContractServiceFee` grid  
> Cel: rozdzielić UX edycji cenników dla **umów najmu (S)** i **umów usługi (U)**, uprościć usługi dodatkowe do postaci zgodnej ze starą aplikacją (niezależne od artykułów).

---

## 1. Kontekst i problem

Obecnie w `ContractFormView.vue` mamy jeden wspólny układ dla obu typów umów:

- **Pozycje umowy** — grid z kolumną "Rozliczanie" (`billing_frequency`) z 6 opcjami (dziennie, tygodniowo, dwutygodniowo, miesięcznie, godzinowo, jednorazowo). Jest to mylące, bo dla umowy najmu zawsze powinno być dobowo, a dla usługi — godzinowo.
- **Warunki rozliczenia** (`ConditionPanel`) — ten sam grid kolumn dla `S` i `U`: `Typ stawki`, `Od`, `Do`, `Stawka`, `Jednostka`, `Minimum`. Operator ręcznie wpisuje `billing_label` (`doba`/`godzina`), co jest źródłem błędów.
- **Usługi dodatkowe** — grid z `article_id` + `default_price` (combobox artykułów-usług). W starej aplikacji były to proste wiersze: nazwa, kwota od/do, jednostka, tekst na umowie. Obecny model jest nadmiernie powiązany z artykułami.

### Dane z legacy PDF (potwierdzenie)

Z analizy 515 legacy PDF (`c:\Temp\legacy_pdfs\`):
- **374 umowy `_N` (najem)** — w zdecydowanej większości stawki dobowe (`zł / doba`), często kaskadowe: `1 - 3 dni - 800,00 / doba` + `powyżej 3 dni - 700,00 / doba`.
- **141 umów `_U` (usługa)** — w zdecydowanej większości stawki godzinowe: `do 8 godzin - 4700,00zł` + `każda kolejna 300,00zł`, prosta `110,00zł / godzina` lub kaskadowa `0 - 2 godzin - 1450,00 / godzina`.
- **Usługi dodatkowe** — to osobny blok tekstu (Transport, Czyszczenie, Tankowanie, Przestój, Wezwanie serwisowe) bez powiązania z artykułami.

---

## 2. Założenia projektowe

1. **Jeden typ umowy = jeden sposób rozliczania.** Nie pytamy użytkownika o `billing_frequency` / `billing_unit` — wypełnia się automatycznie.
   - `S` (najem) → `dziennie`, jednostka `doba`
   - `U` (usługa) → `godzinowo`, jednostka `godzina`
2. **KISS dla usług dodatkowych.** Usługa dodatkowa to tekst + zakres kwot + jednostka + opis na umowę. Nie łączymy jej z artykułem (`article_id`, `default_price` są ignorowane w UI, opcjonalnie do usunięcia z frontendu).
3. **Inline editing** — zachowujemy obecny pattern (kliknięcie w wiersz, Enter=zapisz, Esc=anuluj), ale grid jest prostszy.
4. **Gotowe przedziały** — nad gridem combobox z szablonami typowymi widełek.
5. **Wierny podgląd PDF** — pod gridem wyświetlamy tekst dokładnie taki, jaki trafi do PDF.

---

## 3. Sekcja A — Maszyny / Pozycje (dla `contract_type === 'S'`)

### 3.1. Grid pozycji

Kolumny:

| # | Kolumna | Typ | Uwagi |
|---|---------|-----|-------|
| 1 | `Lp.` | index | tylko do wyświetlenia |
| 2 | `Artykuł` | text | nazwa artykułu (maszyna), `is_service=false` w ArticlePicker |
| 3 | `Dni` | number | `rental_days` |
| 4 | `Ilość` | number | `quantity` |
| 6 | `Dostawca` | picker | `supplier_id` / `supplier_name` |
| 7 | `Data dost.` | date | `delivery_date` |
| 8 | `Warunki` | badge | liczba warunków, klik → rozwija `ConditionPanel` |
| 9 | `Akcje` | ikony | edytuj / usuń |

**Usuwamy kolumnę `Rozliczanie`.** Dla najmu zawsze zakładamy `billing_frequency = 'dziennie'`.

### 3.2. Grid warunków dobowych (`ConditionPanel` dla `S`)

Wyświetlany pod zaznaczoną pozycją (tak jak obecnie) lub w bocznym panelu.

Kolumny:

| # | Kolumna | Typ | Walidacja | Uwagi |
|---|---------|-----|-----------|-------|
| 1 | `Od (dni)` | number | `>= 1` | `period_from` |
| 2 | `Do (dni)` | number | `>= period_from` lub puste | `period_to` (puste = `powyżej`) |
| 3 | `Stawka (zł)` | number | `>= 0` | `rate1` |
| 4 | `Jednostka` | text readonly | — | zawsze `doba` (ukryta lub readonly) |
| 5 | `Minimum` | number | `>= 0` | `minimum` (opcjonalne) |
| 6 | `Akcje` | ikony | — | zapisz / anuluj w trybie edycji, edytuj / usuń w trybie podglądu |

**Toolbar nad gridem:**
- `Gotowe przedziały…` — combobox z opcjami:
  - `1 - 3 dni`
  - `1 - 8 dni`
  - `1 - 2 dni / 3 - 5 dni / >5`
  - `>3 dni`
  - `>8 dni`
  - `>16 dni`
  - `>20 dni`
  - `1 dzień`
- `↻ Z ostatniej umowy` — wypełnia widełki z ostatniej umowy dla tej maszyny.
- `📋 Zastosuj cennik` — modal z presetami `ArticleRatePreset`.
- `+ Dodaj warunek` — dodaje pusty wiersz inline.

**Podgląd PDF:**
```
1 - 3 dni - 150,00 zł / doba
4 - 16 dni - 410,00 zł / doba
powyżej 16 dni - 350,00 zł / doba
```

**Zachowanie:**
- Użytkownik wpisuje tylko `Od`, `Do`, `Stawka` (i opcjonalnie `Minimum`).
- `billing_label` ustawiane automatycznie na `doba`.
- `rate_type_id` ustawiamy na domyślny `RateType` dla najmu (np. "Dobowa") lub ukrywamy w UI.
- `period_count` (legacy) wyliczane z `period_to` przy zapisie.
- Walidacja ciągłości: jeśli `Do` wypełnione, następny wiersz musi zaczynać się od `Do + 1` lub być open-ended.

---

## 4. Sekcja B — Usługi (dla `contract_type === 'U'`)

### 4.1. Grid pozycji

Nagłówek sekcji: **„Usługi”** zamiast „Pozycje umowy”.

Kolumny:

| # | Kolumna | Typ | Uwagi |
|---|---------|-----|-------|
| 1 | `Lp.` | index | — |
| 2 | `Usługa` | text | nazwa artykułu (`is_service=true` w ArticlePicker) |
| 3 | `Ilość` | number | `quantity` |
| 4 | `Jednostka` | text readonly | `godzina` (lub `szt` dla innych usług) — domyślnie `godzina` |
| 5 | `Opis` | input | `description` |
| 6 | `Warunki` | badge | liczba warunków, klik → rozwija `ConditionPanel` |
| 7 | `Akcje` | ikony | edytuj / usuń |

**Usuwamy:** `Dni`, `Dostawca`, `Data dost.`, `Rozliczanie`.

Dla usługi `billing_frequency = 'godzinowo'`, `billing_unit = 'godzina'`.

### 4.2. Grid warunków godzinowych (`ConditionPanel` dla `U`)

Kolumny:

| # | Kolumna | Typ | Walidacja | Uwagi |
|---|---------|-----|-----------|-------|
| 1 | `Od (godz.)` | number | `>= 0` | `period_from` (domyślnie `0` lub `1`) |
| 2 | `Do (godz.)` | number | `>= period_from` lub puste | `period_to` (puste = `powyżej`) |
| 3 | `Stawka (zł)` | number | `>= 0` | `rate1` |
| 4 | `Jednostka` | text readonly | — | zawsze `godzina` (ukryta lub readonly) |
| 5 | `Minimum` | number | `>= 0` | `minimum` (opcjonalne) |
| 6 | `Akcje` | ikony | — | zapisz / anuluj / edytuj / usuń |

**Toolbar nad gridem:**
- `Gotowe przedziały…` — combobox z opcjami:
  - `do 2 godzin`
  - `do 3 godzin`
  - `do 8 godzin`
  - `0 - 2 / 3 - 8 / >8 godzin`
  - `każda kolejna` (dodaje wiersz z pustym `Do`)
- `↻ Z ostatniej umowy` — jeśli ta usługa była wcześniej wynajmowana, wypełnij widełki.
- `📋 Zastosuj cennik` — preset (opcjonalny, analogiczny do maszyn).
- `+ Dodaj warunek`.

**Podgląd PDF (dwa warianty, wybierany przez wypełnienie):**

Wariant kaskadowy:
```
0 - 2 godzin - 1450,00 zł / godzina
3 - 8 godzin - 2900,00 zł / godzina
powyżej 8 godzin - 400,00 zł / godzina
```

Wariant `do X + każda kolejna`:
```
do 8 godzin - 4700,00 zł
każda kolejna 300,00 zł
```

**Zachowanie:**
- `billing_label` automatycznie `godzina`.
- `rate_type_id` domyślny dla usługi (np. "Godzinowa").
- Obsługa `każda kolejna`:
  - Wiersz z `Do` wypełnionym → `do X godzin - Y zł`.
  - Wiersz z pustym `Do` (open-ended) i `Od` równym poprzedniemu `Do + 1` → `każda kolejna Z zł`.
  - W UI dopuszczamy też osobny wiersz z `Nazwa` = `każda kolejna` (opcjonalnie, aby tekst PDF był zgodny z legacy).

---

## 5. Sekcja C — Usługi dodatkowe (dla `S` i `U`)

### 5.1. Cel KISS

Wracamy do modelu zgodnego ze starą aplikacją: **niezależny tekstowy grid**.

### 5.2. Grid usług dodatkowych

Kolumny:

| # | Kolumna | Typ | Uwagi |
|---|---------|-----|-------|
| 1 | `Nazwa` | input | `name` — np. "Transport", "Czyszczenie maszyny" |
| 2 | `Kwota od` | number | `amount_from` (opcjonalna) |
| 3 | `Kwota do` | number | `amount_to` (opcjonalna) |
| 4 | `J.m.` | input | `unit` — np. `zł`, `h`, `km`, `szt` |
| 5 | `Tekst na umowie` | input | `description` — tekst widoczny w PDF |
| 6 | `Aktywna` | checkbox | `is_active` |
| 7 | `Akcje` | ikony | edytuj / usuń |

**Usuwamy:**
- combobox `— wybierz usługę z listy —` (`article_id`)
- pole `default_price`
- kolumnę `Domyślna cena`

### 5.3. Toolbar nad gridem

Dla `contract_type === 'S'`:
- `Wspólne` — wczytuje szablon wspólny (Transport, Czyszczenie, Tankowanie, Przestój, Wezwanie serwisowe).
- `Diesel` — dodaje/uszczegóławia pozycje dla maszyn diesel.
- `Elektryk` — analogicznie dla elektryków.
- `Wybierz zestaw…` — `FeePresetGroup` dla `contract_type='S'`.
- `↻ Reset` — usuwa wszystkie i wczytuje domyślny szablon.
- `+ Dodaj` — pusty wiersz inline.

Dla `contract_type === 'U'`:
- `Wspólne` — szablon dla usług (Transport, Praca operatora).
- `Wybierz zestaw…` — `FeePresetGroup` dla `contract_type='U'`.
- `↻ Reset`.
- `+ Dodaj`.

### 5.4. Podgląd PDF

Pod gridem lista aktywnych usług:
```
- Transport: 500,00 zł - dostawa / 500,00 zł - odbiór
- Czyszczenie maszyny po wynajmie (zabrudzenia drobne): 150,00 zł - 400,00 zł
- Usługa tankowania: 200,00 zł (plus koszt paliwa)
```

**Zachowanie:**
- `description` jest głównym polem tekstowym. Jeśli pusty, generujemy z `name` + `amount_from` + `amount_to` + `unit`.
- `article_id` i `default_price` są **nieużywane w UI** (zachowujemy w DB dla kompatybilności, frontend nie wysyła ich).

---

## 6. Mapowanie do obecnego modelu (minimalne zmiany)

### `ContractPosition`
- `billing_frequency` — ustawiane automatycznie:
  - `S` → `'dziennie'`
  - `U` → `'godzinowo'`
- `billing_unit` — opcjonalnie wypełniać `'doba'` / `'godzina'`.
- `rental_days` — dla `U` może być `null` (nieobowiązkowe).

### `PositionCondition`
- `billing_label` — ustawiane automatycznie:
  - `S` → `'doba'`
  - `U` → `'godzina'`
- `rate_type_id` — domyślny rate type (np. `RateType` o nazwie "Dobowa" / "Godzinowa"). Można ukryć w UI.
- `period_from` / `period_to` — mapowane 1:1 z `Od` / `Do`.
- `rate1` — `Stawka`.
- `rate2` — **nieużywane w nowym UI** (zachowane w DB dla kompatyczności z `ArticleRatePreset` z polem `rate2`). Wszystkie widełki kaskadowe reprezentowane jako osobne `PositionCondition`.
- `minimum` — opcjonalne.

### `ContractServiceFee`
- `article_id` — **nieużywane w UI** (zachowane w DB dla migracji).
- `default_price` — **nieużywane w UI**.
- `name`, `amount_from`, `amount_to`, `unit`, `description`, `is_active` — używane.
- `sort_order` — zachowane (kolejność wierszy).

---

## 7. UI flow — zmiany w `ContractFormView.vue`

### 7.1. Wybór typu umowy

Po wyborze `contract_type` (po zapisie typu niezmienny, jak obecnie):
- `S` → renderujemy sekcję A (Maszyny) + sekcję C (usługi dodatkowe z presetami S).
- `U` → renderujemy sekcję B (Usługi) + sekcję C (usługi dodatkowe z presetami U).

### 7.2. Layout sekcji

```
┌─────────────────────────────────────────────┐
│  Dane podstawowe + Kontrahent + Warunki finansowe │
├─────────────────────────────────────────────┤
│  [S] Maszyny / [U] Usługi                    │
│  + grid pozycji                               │
├─────────────────────────────────────────────┤
│  Warunki rozliczenia dla: Ładowarka teleskopowa  │
│  + grid od-do (doba lub godzina)              │
├─────────────────────────────────────────────┤
│  Usługi dodatkowe                             │
│  + prosty grid nazwa/kwota/jedn.              │
└─────────────────────────────────────────────┘
```

### 7.3. Inline editing — zachowane skróty

- Kliknięcie w wiersz → zaznaczenie.
- Podwójne kliknięcie / ikona ✎ → tryb edycji.
- `Enter` → zapisz.
- `Esc` → anuluj.
- Wiersz w trybie edycji: `background: var(--color-bg-editing)`.

---

## 8. Nowe / zmienione komponenty

| Komponent | Zmiana |
|-----------|--------|
| `ContractFormView.vue` | Usunąć kolumnę `Rozliczanie` z gridu pozycji; dodać `contract_type` warunkowanie dla nagłówków i usług dodatkowych. |
| `ConditionPanel.vue` | Rozbić na `ConditionPanelRental` (doba) i `ConditionPanelService` (godzina) lub dodać `mode` prop (`'rental'` / `'service'`). Zmienić kolumny: ukryć `Typ stawki`, `Jednostka` readonly. Dostosować gotowe przedziały. |
| `ServiceFeeGrid.vue` (nowy) | Uproszczony grid usług dodatkowych bez `article_id`/`default_price`. |
| `ArticlePicker.vue` | Filtrowanie `is_service=false` dla `S`, `is_service=true` dla `U`. |

---

## 9. Przykład końcowy — umowa najmu (S)

### Grid maszyn
| Lp. | Artykuł | Dni | Ilość | Warunki |
|-----|---------|-----|-------|---------|
| 1 | Ładowarka teleskopowa 17m | 4 | 1 | 2 |

### Grid warunków dobowych
| Od (dni) | Do (dni) | Stawka (zł) | Jednostka |
|----------|----------|-------------|-----------|
| 1 | 3 | 800,00 | doba |
| 4 | 5 | 700,00 | doba |
| 6 | — | 650,00 | doba |

### Podgląd PDF
```
1 - 3 dni - 800,00 zł / doba
4 - 5 dni - 700,00 zł / doba
powyżej 5 dni - 650,00 zł / doba
```

### Usługi dodatkowe
| Nazwa | Kwota od | Kwota do | J.m. | Tekst na umowie |
|-------|----------|----------|------|-----------------|
| Transport | 500,00 | 500,00 | zł | 500,00 zł dostawa / 500,00 zł odbiór |

---

## 10. Przykład końcowy — umowa usługi (U)

### Grid usług
| Lp. | Usługa | Ilość | Warunki |
|-----|--------|-------|---------|
| 1 | Ładowarka obrotowa 18m + przedłużki | 1 | 2 |

### Grid warunków godzinowych
| Od (godz.) | Do (godz.) | Stawka (zł) | Jednostka |
|------------|------------|-------------|-----------|
| 0 | 8 | 4700,00 | godzina |
| 9 | — | 300,00 | godzina |

### Podgląd PDF
```
do 8 godzin - 4700,00 zł
każda kolejna 300,00 zł
```

---

## 11. Definition of Done

- [ ] `ContractFormView.vue` nie pyta o `billing_frequency` w gridzie pozycji.
- [ ] `ConditionPanel` ma dwa tryby: `rental` (doba) / `service` (godzina) z predefiniowaną jednostką.
- [ ] Grid usług dodatkowych nie używa `article_id` ani `default_price` (frontend).
- [ ] Podgląd PDF dla warunków i usług dodatkowych jest wierny.
- [ ] `vue-tsc --noEmit` przechodzi.
- [ ] Smoke test `01-login.spec.ts` przechodzi.
- [ ] Spec `core/03_frontend_screens.md` zaktualizowany.
