# Scenariusze Testowe - Sprint Klient 2026-05-25

> **Cel:** Weryfikacja wszystkich zadań zrealizowanych w Sprint Klient 2026-05-25
> **Data:** 2026-05-25
> **Status:** Przygotowanie scenariuszy przed wykonaniem testów E2E

---

## P1 Tasks - PDF Reports

### RAO-P1-001: PDF Umowa — usunąć duplikat "na budowie"

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Utwórz nową umowę z wypełnionym polem `delivery_address`
3. Wygeneruj PDF umowy (POST /contracts/{id}/pdf)
4. Otwórz PDF i sprawdź:
   - Adres dostawy widoczny tylko raz w sekcji "info-col" jako "Adres dostawy"
   - Pole "na budowie" w sekcji "uzupełnij" jest puste (gotowe do ręcznego dopisania)
   - Brak duplikatu adresu w polu "na budowie"

**Expected Result:** Adres dostawy wyświetlony tylko raz, pole "na budowie" puste

---

### RAO-P1-002: PDF Umowa — "Dni pracy/tydzień" → "Ilość dni pracy"

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Utwórz nową umowę z `working_days_per_week = 6`
3. Wygeneruj PDF umowy
4. Otwórz PDF i sprawdź sekcję "Uwagi":
   - Label: "Ilość dni pracy w tygodniu" (nie "Dni pracy/tydzień")
   - Wartość: "6" (default z pola)

**Expected Result:** Label zmieniony na "Ilość dni pracy w tygodniu", wartość poprawna

---

### RAO-P1-003: PDF Umowa — "*ceny netto" wyraźnie na dole

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Wygeneruj PDF umowy
3. Otwórz PDF i sprawdź stopkę strony 1:
   - Sekcja `.footer-legal` widoczna
   - Tekst "*ceny podane na umowie są cenami netto" jest:
     - Pogrubiony (font-weight: bold)
     - Czerwony (color: #c00)
     - Większy (font-size: 11px)
   - Sekcja ma border-top i padding-top

**Expected Result:** Tekst "*ceny netto" wyraźnie widoczny (czerwony, pogrubiony, większy)

---

### RAO-P1-004: PDF Umowa U (usługa) — usuń cennik dodatkowy

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Utwórz nową umowę typu U (usługa)
3. Wygeneruj PDF umowy (contract_u.html)
4. Otwórz PDF i sprawdź:
   - Sekcja "Cennik usług dodatkowych" NIE występuje
   - Tylko sekcja "Przedmiot umowy" jest widoczna

**Expected Result:** Brak sekcji "Cennik usług dodatkowych" w umowach typu U

---

### RAO-P1-005: PDF Protokół — etykieta "nr tel" w boksie kontaktu

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Wygeneruj protokół Z-O (protocol_zo.html, protocol_zo_u.html, protocol_zo_nodata.html)
3. Otwórz PDF i sprawdź sekcję kontaktową:
   - Kontakt osoby upoważnionej w pierwszym wierszu
   - Etykieta "nr tel:" w drugim wierszu (nawet gdy pole puste)
   - Font-size: 9px

**Expected Result:** Etykieta "nr tel:" widoczna osobno w nowym wierszu

---

### RAO-P1-006: PDF Protokół — większa tabela "Przy wydaniu/odbiorce"

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Wygeneruj protokół Z-O (protocol_zo.html)
3. Otwórz PDF i sprawdź tabelę "Przy wydaniu / Przy odbiorze":
   - Height wierszy: 32px (z 20px)
   - Font-size: 10px (z 8.5px)
   - Padding: 5px 8px (z 2px 5px)
   - Wiersz "Uwagi" height: 60px (z 36px)

**Expected Result:** Tabela większa, łatwiejsza do ręcznego wypełnienia

---

### RAO-P1-007: PDF Protokół — 1 duża tabela "uwagi" zamiast 3

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Wygeneruj protokół Z-O (protocol_zo.html)
3. Otwórz PDF i sprawdź dolną sekcję:
   - Tabela return-table (3 kolumny) USUNIĘTA
   - Div ret-uwagi zamieniony na div big-uwagi
   - big-uwagi wymiary: min-height: 140px, padding: 10px 12px, font-size: 10px
   - Notatka "Ogólna weryfikacja maszyny..." zachowana
   - Podpisy zachowane

**Expected Result:** 1 duża tabela "uwagi do zwrotu" zamiast 3 elementów

---

### RAO-P1-008: Format kaskadowy warunków rozliczenia

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Utwórz umowę z pozycją mającą 3 warunki kaskadowe:
   - Warunek 1: period_count=3, rate1=540, billing_label='doba'
   - Warunek 2: period_count=16, rate1=410, billing_label='doba'
   - Warunek 3: rate2=350, billing_label='doba' (bez period_count)
3. Wygeneruj PDF umowy
4. Otwórz PDF i sprawdź opis warunków:
   - "1 - 3 dni - 540,00 / doba"
   - "4 - 16 dni - 410,00 / doba"
   - "powyżej 16 dni - 350,00 / doba"

**Expected Result:** Format kaskadowy zgodny ze starą aplikacją WinForms

---

### RAO-P1-009: Wymiana pieczątki firmy w PDF

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Wygeneruj PDF umowy (contract.html, contract_u.html)
3. Wygeneruj PDF protokołu (protocol_zo.html)
4. Otwórz PDF i sprawdź pieczątkę:
   - W umowach: nowa pieczątka z `company_stamp_fixed.jpg`
   - W protokołach: nowa pieczątka z `protocol_stamp.png`
   - Pieczątka widoczna w stopce
   - Ostrość przy zoomie 200%

**Expected Result:** Nowa pieczątka widoczna w umowach i protokołach

---

### RAO-P1-010: Weryfikacja numeru telefonu w nagłówku

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Sprawdź wszystkie szablony PDF:
   - contract.html
   - contract_u.html
   - protocol_zo.html
   - protocol_zo_u.html
   - protocol_zo_nodata.html
3. Wyszukaj numer telefonu w nagłówku
4. Sprawdź czy numer to "+48 888 992 015"

**Expected Result:** Wszystkie szablony mają poprawny numer +48 888 992 015

---

### RAO-P1-011: [SPIKE] Walidacja duplikatu maszyny + ostrzeżenie o konflikcie wynajmu

**Scenariusz testowy (research):**
1. Przeczytaj dokumentację SPIKE w backlog
2. Sprawdź czy 3 warianty rozwiązania są opisane:
   - Wariant A: Strict UNIQUE per umowa (maszyny własne)
   - Wariant B: Pozwól na duplikaty zawsze, ale ostrzeż
   - Wariant C: Hybryda — własne strict, external dozwolone
3. Sprawdź czy endpoint do sprawdzenia konfliktu jest zaproponowany

**Expected Result:** Dokumentacja SPIKE kompletna z propozycjami rozwiązań

---

### RAO-P1-012: PDF OWN — ujednolicenie wcięć w listach

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Wygeneruj PDF umowy (contract.html, contract_u.html)
3. Otwórz PDF i sprawdź sekcję OWN:
   - Poziom 0 (p.ot): bez wcięcia
   - Poziom 1 (.own-num): padding-left: 7mm, text-indent: -7mm
   - Poziom 2 (.own-num-indent): padding-left: 13mm, text-indent: -6mm
   - Font-size: 7.5pt, line-height: 1.15, text-align: justify
   - Wszystkie numery (1-17) wyrównane pionowo

**Expected Result:** Wcięcia ujednolicone, nic nie wystaje

---

## P2 Tasks - Backend & Frontend

### RAO-P2-001: PDF Umowa NAJMU (S) — domyślny cennik dodatkowy

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Utwórz nową umowę typu S (najem)
3. Wygeneruj PDF umowy
4. Otwórz PDF i sprawdź sekcję "Inne usługi":
   - 6 pozycji w określonej kolejności:
     1. Transport (500 zł/dostawa)
     2. Czyszczenie drobne (150-400 zł)
     3. Czyszczenie trudne (400-1500 zł)
     4. Tankowanie (200 zł + paliwo)
     5. Prestój transportu (200-300 zł/h)
     6. Serwis (280 zł + transport)

**Expected Result:** 6 usług dodatkowych w wymaganej kolejności

---

### RAO-P2-002: PDF Umowa — sekcja "Uwagi" w określonej kolejności

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Utwórz nową umowę bez wypełnionego pola `notes`
3. Wygeneruj PDF umowy
4. Otwórz PDF i sprawdź sekcję "Uwagi":
   - "Doba wynajmu: obejmuje 1 dzień kalendarzowy (do 8 godz. pracy jednego dnia)"
   - "Zgłoszenie zwrotu urządzenia: pisemne, min. z jednodniowym wyprzedzeniem"
   - "Ilość dni pracy w tygodniu: 6"
   - "Dokumentacja zdjęciowa: wykonano"

**Expected Result:** 4 podpunkty w wymaganym formacie

---

### RAO-P2-003: PDF Umowa — kompaktniejszy layout

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Wygeneruj PDF umowy (contract.html, contract_u.html)
3. Otwórz PDF i sprawdź wymiary:
   - table.pos font-size: 8.5px (z 9px)
   - table.pos th/td padding: 2px 4px (z 3px 5px / 4px 5px)
   - .bottom-box/.inne-box font-size: 8px (z 9px)
   - .bottom-box/.inne-box padding: 4px 6px (z 5px 8px)
   - .bottom-box/.inne-box line-height: 1.3 (z 1.45)
   - .cond font-size: 8.5px (z 9px)

**Expected Result:** Tabelki i opisy kompaktniejsze, czytelne (≥8px)

---

### RAO-P2-004: Frontend — okres umowy przez kalendarz + dni

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Przejdź do formularza tworzenia umowy
3. Sprawdź komponent ContractPeriodPicker:
   - Input 1: data startowa (date picker)
   - Input 2: ilość dni (number input, min=1)
   - Display: "Okres umowy: {date_from_pl} – {date_to_pl}"
4. Wprowadź: date_from=25.05.2026, days=10
5. Sprawdź czy date_to=03.06.2026

**Expected Result:** Okres umowy obliczony poprawnie (10 dni = 25.05-03.06)

---

### RAO-P2-005: Frontend — inline add kontrahenta

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Przejdź do formularza tworzenia umowy
3. W pickerze kontrahenta wpisz "NieistniejącyKontrahent"
4. Sprawdź czy wyświetla się "Brak wyników dla NieistniejącyKontrahent"
5. Sprawdź czy przycisk "➕ Dodaj nowego kontrahenta" jest widoczny
6. Kliknij przycisk
7. Wypełnij formularz kontrahenta (name, NIP, address, etc.)
8. Zapisz
9. Sprawdź czy nowy kontrahent jest:
   - Dodany do listy
   - Auto-selected w pickerze
   - Modal zamknięty

**Expected Result:** Kontrahent dodany inline, auto-selected, modal zamknięty

---

### RAO-P2-006: Frontend — inline add artykułu

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Przejdź do formularza tworzenia umowy
3. W pickerze artykułu wpisz "NieistniejącyArtykuł"
4. Sprawdź czy wyświetla się "Brak wyników dla NieistniejącyArtykuł"
5. Sprawdź czy przycisk "➕ Dodaj nowy artykuł" jest widoczny
6. Kliknij przycisk
7. Wypełnij formularz artykułu (name, serial_number, category, etc.)
8. Zapisz
9. Sprawdź czy nowy artykuł jest:
   - Dodany do listy
   - Auto-selected w pickerze
   - Modal zamknięty

**Expected Result:** Artykuł dodany inline, auto-selected, modal zamknięty

---

### RAO-P2-007: Frontend — pomoc UX jak wpisywać warunki

**Scenariusz testowy:**
1. Zaloguj się jako admin
2. Przejdź do formularza tworzenia umowy
3. Sprawdź sekcję "Warunki rozliczenia":
   - Przycisk "📖 Jak wpisać warunki rozliczenia?" widoczny
   - Kliknij przycisk
   - Sprawdź czy przykład koparki z kaskadową stawką jest widoczny
4. Dodaj nowy warunek
5. Sprawdź czy tooltip przy polu "Stawka 2" jest widoczny (iⓘ)
6. Kliknij tooltip
7. Sprawdź czy tekst "ostatni warunek (powyżej) — pozostaw period_count puste" jest widoczny
8. Wypełnij warunek: rate_type="dobowa", rate1=540, period_count=3, billing_label="doba"
9. Sprawdź czy live preview pokazuje "1 - 3 dni - 540,00 / doba"

**Expected Result:** Pomoc UX widoczna, live preview działa

---

## Smoke Regression Test

### Test: 01-login.spec.ts

**Scenariusz testowy:**
1. Uruchom backend (port 8000)
2. Uruchom frontend (port 5173)
3. Uruchom test: `cd e2e && npx playwright test tests/01-login.spec.ts`
4. Sprawdź czy test przechodzi

**Expected Result:** Smoke test przechodzi (brak regresji)

---

## Summary

- **Total test scenarios:** 19 (12 P1 + 7 P2)
- **Smoke regression:** 1
- **Total:** 20 test scenarios

**Next steps:**
1. Uruchomić smoke regression test
2. Wykonać testy E2E dla każdego scenariusza
3. Zgłosić znalezione błędy
4. Przygotować raport podsumowujący
