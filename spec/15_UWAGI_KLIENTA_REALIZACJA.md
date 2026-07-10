# 15 Uwag Klienta — Weryfikacja Realizacji

> **Data weryfikacji:** 10 lipca 2026  
> **Umowa testowa:** S891/2026 (ID: 16012) — umowa najmu z pełnymi danymi  
> **Backend:** http://localhost:8000/rao/api  
> **Frontend:** http://localhost:5173/rao/  
> **Screenshoty:** `temp/screenshots/`  

---

## Podsumowanie

| # | Uwaga | Status | Pliki |
|---|-------|--------|-------|
| 1 | Maszyna zewnętrzna | ✅ Zrealizowane | `articles/models.py`, `ArticleFormView.vue` |
| 2 | Adres ręcznie | ✅ Zrealizowane | `ContractFormView.vue`, `contract.html` |
| 3 | 5/6/7 dni w tyg. | ✅ Zrealizowane | `ContractPeriodPicker.vue`, `contract.html` |
| 4 | Zapis GPS | ✅ Zrealizowane | `contract.html` |
| 5 | Widełki cenowe | ✅ Zrealizowane | `ContractFormView.vue`, `contract.html` |
| 6 | Opłaty diesel/elektryk | ✅ Zrealizowane | `settings/router.py`, `ContractFormView.vue` |
| 7 | Dodatkowe info na protokole usług | ✅ Zrealizowane | `protocol_zo_u.html` |
| 8 | Przewidywana ilość dni — 2 linijki | ✅ Zrealizowane | `contract.html` |
| 9 | Opiekun na protokole | ✅ Zrealizowane | `protocol_zo*.html`, `contract*.html` |
| 10 | Usunąć pieczątkę przy zwrocie | ✅ Zrealizowane | `protocol_zo.html` |
| 11 | Osobny protokół per maszyna | ✅ Zrealizowane | `reports/service.py` |
| 12 | Tel klienta tylko na protokole | ✅ Zrealizowane | `contract.html`, `protocol_zo.html` |
| 13 | Nr wewnętrzny przy usłudze | ✅ Zrealizowane | `ContractFormView.vue` |
| 14 | Przedpłata na dół | ✅ Zrealizowane | `contract.html` |
| 15 | OWN §3 pkt 8b | ✅ Zrealizowane | `contract.html` |

**Wynik:** 15/15 zrealizowane.

---

## Szczegółowa weryfikacja z dialogiem agentów

### Uwaga 1: Możliwość odhaczenia czy maszyna nasza czy zewnętrzna

**GLM-5.2 (High-level):** Klient chce oznaczać maszyny jako "zewnętrzne" (nie wliczane do floty własnej). To flaga na artykule.

**SWE-1.7 (Technical):** 
- **DB:** `articles.is_external` Column(Boolean, nullable=False, default=False) — `backend/articles/models.py:33`
- **Frontend:** Checkbox "Maszyna zewnętrzna (nie wliczana do floty własnej)" — `frontend/src/views/ArticleFormView.vue:41-42`
- **Index:** `idx_articles_external` na kolumnie `is_external`
- **Screenshot:** `temp/screenshots/uwaga-1-external-form.png`

**Weryfikacja UI:** Formularz artykułu pokazuje checkbox "Maszyna zewnętrzna" poniżej checkboxa "Artykuł jest usługą".

**Status: ✅ Zrealizowane**

---

### Uwaga 2: Możliwość dodawania adresu ręcznie

**GLM-5.2:** Klient chce móc wpisać adres dostawy ręcznie, bez auto-fill z PNA/Nominatim.

**SWE-1.7:**
- **Frontend:** Pole `delivery_address` z checkboxem "Ręczny adres (wyłącz auto-fill z PNA/Nominatim)" — `ContractFormView.vue:78-88`
- **Backend:** `Contract.delivery_address` VARCHAR(255) NULL, `Contract.hide_delivery_address` Boolean
- **PDF:** `contract.html:152` — `{% if contract.delivery_address %}Adres dostawy: {{ contract.delivery_address }}{% endif %}`
- **Screenshot:** `temp/screenshots/uwaga-2-adres-ui.png`

**Weryfikacja PDF:** Contract page 1 zawiera "Adres dostawy: ul. Testowa 1, Warszawa". Protocol zawiera "miejsce dostawy i odbioru przedmiotu najmu: ul. Testowa 1, Warszawa".

**Status: ✅ Zrealizowane**

---

### Uwaga 3: Możliwość liczenia wynajmu 5, 6 lub 7 dni w tyg.

**GLM-5.2:** Klient chce wybór między 5, 6, 7 dniami roboczymi w tygodniu, co wpływa na naliczanie.

**SWE-1.7:**
- **Frontend:** `ContractPeriodPicker.vue` — przyciski 5/6/7 w grupie "Dni robocze w tygodniu"
- **Backend:** `Contract.working_days_per_week` INT
- **PDF:** `contract.html` — "Naliczanie: {{ contract.working_days_per_week }} dni w tygodniu (pozostałe dni według zapisu GPS)"
- **Screenshot:** `temp/screenshots/uwaga-3-dni-ui.png`

**Weryfikacja PDF:** Contract page 1: "Naliczanie: 5 dni w tygodniu (pozostałe dni według zapisu GPS)."

**Status: ✅ Zrealizowane**

---

### Uwaga 4: Dodać zapis o naliczaniu i weekendach z GPS

**GLM-5.2:** Zmienić brzmienie zapisu na: "Naliczanie: X dni w tygodniu (pozostałe dni według zapisu GPS)".

**SWE-1.7:**
- **PDF:** `contract.html:230` — hardcoded tekst w sekcji UWAGI: "Naliczanie: {{ contract.working_days_per_week }} dni w tygodniu (pozostałe dni według zapisu GPS)."
- **Weryfikacja PDF text:** "Naliczanie: 5 dni w tygodniu (pozostałe dni według zapisu GPS)."

**Status: ✅ Zrealizowane**

---

### Uwaga 5: Widełki cenowe — uproszczenie edycji okresów

**GLM-5.2:** Klient chce elastycznych widełek cenowych (1-2, 1-3, 4-7, 4-8, >16, >20) z możliwością edycji. Przy usłudze stawki godzinowe (do 2h, do 3h).

**SWE-1.7:**
- **Backend:** `PositionCondition` model z `rate1`, `period_count`, `range_label` — dowolny tekst etykiety
- **Frontend:** Edycja warunków w pozycji umowy — `ContractFormView.vue` z `PositionConditionEditor`
- **PDF:** `contract.html:211` — `{{ p.conditions_text }}` renderuje warunki jako tekst
- **Screenshot:** `temp/screenshots/uwaga-5-widelki-ui.png`

**Weryfikacja PDF:** Contract page 1 pokazuje 3 widełki: "1 dzień - 215,00zł", "1 dzień - 180,00zł", "1 dzień - 150,00zł" z etykietami "1-3 doba", "4-16 doba", "powyżej 16".

**Status: ✅ Zrealizowane**

---

### Uwaga 6: Zmienić zapisy w umowie — opłaty diesel vs elektryk

**GLM-5.2:** Dwa zestawy opłat: diesel (przegląd 150 zł, czyszczenie indywidualne) i elektryk (przegląd+ładowanie 35 zł, czyszczenie indywidualne). Możliwość edycji kwot.

**SWE-1.7:**
- **Backend:** `FeePresetGroup` model z `contract_type` — `settings/router.py:198` — endpointy CRUD
- **DB:** Presets: "Najem — Diesel" (id=3), "Najem — Elektryk" (id=4), "Najem — Wspólny" (id=17)
- **Frontend:** Zakładki "Wspólne", "Diesel", "Elektryk" + dropdown "Wybierz zestaw…" — `ContractFormView.vue`
- **PDF:** Opłaty renderowane z `fees_text` w sekcji "Inne usługi"
- **Screenshot:** `temp/screenshots/uwaga-6-oplaty-ui.png`

**Weryfikacja PDF:** Contract page 1 pokazuje: "Transport: 1 200,00 zł dostawa / 1 200,00 zł odbiór", "Czyszczenie maszyny (zabrudzenia ponadnormatywne): wycena indywidualna", "Usługa tankowania: 200,00 zł (plus koszt paliwa)", "Ponadnormatywny przestój transportu: 200,00 zł / h - 300,00 zł / h", "Nieuzasadnione wezwanie serwisowe: 280,00 zł (plus transport)".

**Status: ✅ Zrealizowane**

---

### Uwaga 7: Dodać miejsce zapisu dodatkowych informacji na protokole dla usług

**GLM-5.2:** Na protokole usług (U) dodać pole "Dodatkowe informacje" nad polami podpisu.

**SWE-1.7:**
- **PDF:** `protocol_zo_u.html:192-198` — sekcja "Dodatkowe informacje:" z border, wyświetla `{{ contract.notes }}`
- **Pozycja:** Nad podpisami, po sekcji "uwagi"

**Weryfikacja:** Szablon `protocol_zo_u.html` zawiera sekcję "Dodatkowe informacje" z `{{ contract.notes }}` między uwagami a podpisami.

**Status: ✅ Zrealizowane**

---

### Uwaga 8: Zmienić "przewidywana ilość dni najmu" do dwóch linijek

**GLM-5.2:** Klient chce nagłówek "Przewidywana ilość dni najmu" w dwóch linijkach.

**SWE-1.7:**
- **PDF:** `contract.html:199` — `<th>Przewidywana<br>ilość dni najmu</th>` — już podzielone na dwie linijki
- **Weryfikacja PDF text:** "Przewidywana Wartość / Przedmiot najmu Rozliczenie / ilość dni najmu odtworzeniowa" — nagłówek jest w dwóch liniach.

**Status: ✅ Zrealizowane**

---

### Uwaga 9: Opiekun zamówienia na każdym protokole (wynajem/usługa)

**GLM-5.2:** Na każdym protokole (S i U) ma być imię, nazwisko i nr telefonu opiekuna umowy.

**SWE-1.7:**
- **Contract PDF:** `contract.html` i `contract_u.html` — "Opiekun zamówienia: {{ salesperson.name }} tel. {{ salesperson.phone }}" ✓ (tylko strona 1, nie na OWN)
- **Protocol PDF:** `reports/service.py:129-131` — `salesperson` jest ładowany z DB i przekazywany do szablonu
- **Protocol templates:** `protocol_zo.html`, `protocol_zo_u.html`, `protocol_zo_nodata.html`, `protocol_zo_nodata_u.html` — linia na dole protokołu, po sekcji bottom-section, przed stopką "Protokół X z Y"
- **P2-018 zrealizowane:** etykieta zmieniona z "Opiekun umowy" na "Opiekun zamówienia", format "tel." bez separatora "·"

**Weryfikacja PDF text (protocol):** "Opiekun zamówienia: {imię nazwisko} tel. {numer}" na dole protokołu. ✓

**Status: ✅ Zrealizowane (P2-018)**

---

### Uwaga 10: Usunąć pieczątkę przy zwrocie na protokole

**GLM-5.2:** Usunąć obraz pieczątki z sekcji zwrotu (podpisy przy odbiorze), zostawić tylko przy wydaniu.

**SWE-1.7:**
- **PDF:** `protocol_zo.html:197` — `{% if stamp_src %}<img src="{{ stamp_src }}">...{% endif %}` — pieczątka TYLKO przy podpisach wydania
- **Return signatures (lines 220-228):** Brak `stamp_src` — tylko pusta przestrzeń `<div style="height:70px;"></div>` + linia podpisu

**Weryfikacja PDF text (protocol):** Pieczątka jest tylko przy "czytelny podpis Wynajmującego" w sekcji wydania. W sekcji zwrotu jest tylko puste pole + linia podpisu.

**Status: ✅ Zrealizowane**

---

### Uwaga 11: Osobny protokół do każdej maszyny

**GLM-5.2:** Jeśli umowa ma więcej niż jedną maszynę, każdy protokół ma być osobny (jeden PDF na maszynę).

**SWE-1.7:**
- **Backend:** `reports/service.py:696-726` — pętla `for idx, pos in enumerate(positions, 1)` tworzy osobną stronę PDF per pozycja
- **Footer:** "Protokół {{ protocol_number }} z {{ protocol_total }}" — `protocol_zo.html:238`
- **Weryfikacja:** Z umową z 1 pozycją wygenerował się 1 protokół z stopką "Protokół 1 z 1"

**Status: ✅ Zrealizowane**

---

### Uwaga 12: Numer tel klienta tylko na protokole, nie na umowie

**GLM-5.2:** Telefon klienta ma być pusty na umowie najmu (klient wypełnia ręcznie) ale widoczny na protokole.

**SWE-1.7:**
- **Contract PDF:** `contract.html:181-184` — wiersz "telefon:" z pustym `<div class="fill-wide"></div>` — puste pole do wypełnienia
- **Protocol PDF:** `protocol_zo.html:126` — `<strong>nr tel:</strong> {{ contract.contact_phone1 or '' }}` — wyświetla numer telefonu
- **Weryfikacja PDF (contract):** "telefon:" z pustym polem ✓
- **Weryfikacja PDF (protocol):** "nr tel: 500 123 456" ✓

**Status: ✅ Zrealizowane**

---

### Uwaga 13: Nr wewnętrzny przy tworzeniu usługi wyeliminować

**GLM-5.2:** Przy umowie typu usługa (U) ukryć pole "Nr wewnętrzny".

**SWE-1.7:**
- **Frontend:** `ContractFormView.vue:859` — `<div class="form-group" v-if="form.contract_type !== 'U'">` — pole "Nr wewnętrzny" ukryte dla typu U
- **Logic:** `isRental = computed(() => form.value.contract_type === 'S')` — typ S pokazuje, typ U ukrywa

**Status: ✅ Zrealizowane**

---

### Uwaga 14: Przedpłata na umowie przesunąć na dół

**GLM-5.2:** Przedpłata ma być w bardziej pasującym miejscu niż na górze pod tytułem.

**SWE-1.7:**
- **PDF:** `contract.html:135` — `{% if contract.prepayment_amount and contract.prepayment_amount > 0 %}Przedpłata: {{ contract.prepayment_amount | money }}{% endif %}`
- **Pozycja:** W prawej kolumnie obok "wynajmujący" (parties table), NIE bezpośrednio pod tytułem
- **Weryfikacja PDF:** "Przedpłata: 500,00 zł" pojawia się w sekcji stron (wynajmujący/najemca), nie pod tytułem
- **Screenshot:** `temp/screenshots/uwaga-14-przedplata-ui.png`

**Status: ✅ Zrealizowane**

---

### Uwaga 15: Zmiana punktu 8b w OWN

**GLM-5.2:** Zmienić tekst §3 pkt 8b na nowy z stawką 250,00 zł netto za roboczogodzinę czyszczenia.

**SWE-1.7:**
- **PDF:** `contract.html:331` — pełny tekst: "Zwrotu zabrudzonego Przedmiotu Najmu, w przypadku którego Najemca zostanie obciążony kosztami jego czyszczenia po ocenie stanu czystości zwracanego Sprzętu. Rozliczenie kosztów czyszczenia nastąpi według stawki 250,00 zł netto za każdą rozpoczętą roboczogodzinę oraz kosztów materiałów, środków czyszczących i eksploatacyjnych niezbędnych do usunięcia zabrudzeń i przywrócenia Przedmiotu Najmu do stanu czystości z dnia jego wydania."
- **Weryfikacja PDF text (page 2):** Tekst zgodny z żądaniem klienta.

**Status: ✅ Zrealizowane**

---

## Evidence — Screenshoty i PDF

| Plik | Opis |
|------|------|
| `temp/screenshots/uwaga-1-external-form.png` | Formularz artykułu — checkbox "Maszyna zewnętrzna" |
| `temp/screenshots/uwaga-2-adres-ui.png` | Formularz umowy — sekcja "Kontrahent i adres dostawy" |
| `temp/screenshots/uwaga-3-dni-ui.png` | Formularz umowy — przyciski 5/6/7 dni roboczych |
| `temp/screenshots/uwaga-5-widelki-ui.png` | Formularz umowy — warunki cenowe pozycji |
| `temp/screenshots/uwaga-6-oplaty-ui.png` | Formularz umowy — opłaty dodatkowe (zakładki Diesel/Elektryk) |
| `temp/screenshots/uwaga-14-przedplata-ui.png` | Formularz umowy — sekcja "Warunki finansowe" z przedpłatą |
| `temp/screenshots/pdf-contract-page1.png` | PDF umowy str. 1 — tytuł, strony, pozycje, uwagi |
| `temp/screenshots/pdf-contract-page2.png` | PDF umowy str. 2 — OWN §1-§4 |
| `temp/screenshots/pdf-contract-page3.png` | PDF umowy str. 3 — OWN §4-§7 |
| `temp/screenshots/pdf-protocol-page1.png` | PDF protokołu — pełny protokół zdawczo-odbiorczy |
| `temp/screenshots/pdf-contract-rental.pdf` | PDF umowy (źródłowy) |
| `temp/screenshots/pdf-protocol-rental.pdf` | PDF protokołu (źródłowy) |

---

## Backlog — Uwaga 9 (GAP)

**Problem:** Opiekun umowy (salesperson) nie jest renderowany na protokole zdawczo-odbiorczym.

**Root cause:** `reports/service.py` ładuje `salesperson` z DB (linia 129-131) i przekazuje do szablonu (linia 183), ale szablony `protocol_zo.html` i `protocol_zo_u.html` nie zawierają kodu renderującego `{{ salesperson.name }}` ani `{{ salesperson.phone }}`.

**Fix:** Dodać sekcję "Opiekun umowy: {{ salesperson.name }} {{ salesperson.phone if salesperson.phone }}" do obu szablonów protokołów, w dolnej sekcji przed podpisami lub w górnej sekcji obok danych najemcy.

**Priorytet:** P2 (dodatkowa informacja na protokole, nie blokuje pracy)
