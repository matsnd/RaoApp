# Scenariusze testowe — P1-005: Elastyczne widełki cenowe

> **Cel:** Weryfikacja funkcjonalności elastycznych widełek cenowych w ConditionPanel
> **Data:** 2026-07-08
> **Odniesienie:** spec/backlog/BACKLOG.md P1-005

---

## Scenariusz 1: Podstawowe tworzenie warunków z widełkami

**Cel:** Operator może stworzyć warunek z elastycznymi widełkami (Od-Do)

**Kroki:**
1. Zaloguj się jako admin
2. Przejdź do formularza tworzenia nowej umowy
3. Wybierz kontrahenta i artykuł (maszyna)
4. W sekcji "Warunki rozliczenia" kliknij "+ Dodaj warunek"
5. W modalu wypełnij:
   - Typ stawki: "dobowa"
   - Od (dni): 1
   - Do (dni): 3
   - Stawka 1 (zł): 540
   - Jednostka: "doba"
6. Kliknij "Zapisz"

**Expected Result:**
- Warunek zapisany poprawnie
- W tabeli warunków widoczne: Od=1, Do=3, Stawka 1=540,00 zł
- Podgląd PDF live pokazuje: "1 - 3 dni - 540,00 / doba"

---

## Scenariusz 2: Warunek "powyżej X dni" (bez pola Do)

**Cel:** Operator może stworzyć warunek "powyżej X dni" (open-ended)

**Kroki:**
1. W modalu dodawania warunku wypełnij:
   - Typ stawki: "dobowa"
   - Od (dni): 16
   - Do (dni): **puste**
   - Stawka 2 (zł): 350
   - Jednostka: "doba"
2. Kliknij "Zapisz"

**Expected Result:**
- Warunek zapisany poprawnie
- W tabeli warunków widoczne: Od=16, Do=—, Stawka 2=350,00 zł
- Podgląd PDF live pokazuje: "powyżej 16 dni - 350,00 / doba"

---

## Scenariusz 3: Walidacja ciągłości (brak luk)

**Cel:** System wykrywa luki między warunkami

**Kroki:**
1. Stwórz pierwszy warunek: Od=1, Do=3, Stawka 1=540
2. Stwórz drugi warunek: Od=5, Do=7, Stawka 1=410 (LUKA: brak dnia 4)
3. Sprawdź komunikat błędu

**Expected Result:**
- Wyświetlony komunikat: "⚠️ Luka: warunek 1-3, następny 5-7 (brak 4)"
- Wiersz z błędem ma klasę `row-error` (czerwone tło)
- Podgląd PDF live pokazuje oba warunki z luką

---

## Scenariusz 4: Walidacja ciągłości (poprawne warunki)

**Cel:** System akceptuje ciągłe warunki bez luk

**Kroki:**
1. Stwórz pierwszy warunek: Od=1, Do=3, Stawka 1=540
2. Stwórz drugi warunek: Od=4, Do=7, Stawka 1=410 (brak luki)
3. Sprawdź czy brak komunikatu błędu

**Expected Result:**
- Brak komunikatu błędu
- Podgląd PDF live pokazuje: "1 - 3 dni - 540,00 / doba" i "4 - 7 dni - 410,00 / doba"

---

## Scenariusz 5: Edycja istniejącego warunku

**Cel:** Operator może edytować warunek i zmienić widełki

**Kroki:**
1. Stwórz warunek: Od=1, Do=3, Stawka 1=540
2. Kliknij ikonę ✎ (edycja) w tabeli warunków
3. Zmień: Do=5, Stawka 1=500
4. Kliknij "Zapisz"

**Expected Result:**
- Warunek zaktualizowany: Od=1, Do=5, Stawka 1=500,00 zł
- Podgląd PDF live pokazuje: "1 - 5 dni - 500,00 / doba"

---

## Scenariusz 6: Backward compatibility (period_count)

**Cel:** Stare dane z period_count nadal działają

**Kroki:**
1. W modalu dodawania warunku wypełnij:
   - Typ stawki: "dobowa"
   - Okresy (period_count): 3 (pole zachowane dla backward compatibility)
   - Stawka 1 (zł): 540
   - Jednostka: "doba"
2. Kliknij "Zapisz"

**Expected Result:**
- Warunek zapisany poprawnie
- W tabeli warunków widoczne: Od=—, Do=—, Okresy=3
- Podgląd PDF live pokazuje: "540,00 / doba" (bez widełek)

---

## Scenariusz 7: Usuwanie warunku

**Cel:** Operator może usunąć warunek

**Kroki:**
1. Stwórz warunek: Od=1, Do=3, Stawka 1=540
2. Kliknij ikonę ✕ (usuń) w tabeli warunków
3. Potwierdź usunięcie

**Expected Result:**
- Warunek usunięty
- Tabela warunków pusta
- Podgląd PDF live ukryty

---

## Scenariusz 8: Kaskadowe warunki (3 poziomy)

**Cel:** Operator może stworzyć kaskadowe warunki (jak w starej aplikacji)

**Kroki:**
1. Stwórz pierwszy warunek: Od=1, Do=3, Stawka 1=540
2. Stwórz drugi warunek: Od=4, Do=16, Stawka 1=410
3. Stwórz trzeci warunek: Od=17, Do=puste, Stawka 2=350
4. Sprawdź podgląd PDF live

**Expected Result:**
- 3 warunki zapisane poprawnie
- Brak komunikatu błędu (ciągłość zachowana)
- Podgląd PDF live pokazuje:
  - "1 - 3 dni - 540,00 / doba"
  - "4 - 16 dni - 410,00 / doba"
  - "powyżej 17 dni - 350,00 / doba"

---

## Scenariusz 9: Walidacja Od > Do

**Cel:** System blokuje zapis gdy Od > Do

**Kroki:**
1. W modalu dodawania warunku wypełnij:
   - Od (dni): 5
   - Do (dni): 3 (Od > Do)
   - Stawka 1 (zł): 540
2. Kliknij "Zapisz"

**Expected Result:**
- Komunikat błędu: "Od musi być mniejsze lub równe Do"
- Warunek nie zapisany

---

## Scenariusz 10: Podgląd PDF live dla różnych jednostek

**Cel:** Podgląd PDF live pokazuje poprawną jednostkę

**Kroki:**
1. Stwórz warunek: Od=1, Do=2, Stawka 1=1000, Jednostka="tydzień"
2. Sprawdź podgląd PDF live

**Expected Result:**
- Podgląd PDF live pokazuje: "1 - 2 dni - 1000,00 / tydzień"

---

## Scenariusz 11: API - tworzenie warunku z period_from/period_to

**Cel:** API akceptuje period_from/period_to

**Kroki:**
1. POST `/contracts/{id}/positions/{pos_id}/conditions`
2. Body:
   ```json
   {
     "rate_type_id": 1,
     "period_from": 1,
     "period_to": 3,
     "rate1": 540,
     "billing_label": "doba"
   }
   ```

**Expected Result:**
- Status 201 Created
- Response zawiera period_from=1, period_to=3

---

## Scenariusz 12: API - migracja danych (period_count → period_from/period_to)

**Cel:** Istniejące dane z period_count są migrowane

**Kroki:**
1. Sprawdź rekordy w position_conditions z period_count (stare dane)
2. Uruchom backend (migracja w startup)
3. Sprawdź czy period_from=1, period_to=period_count

**Expected Result:**
- Stare dane mają period_from=1, period_to=period_count
- period_count zachowany (backward compatibility)

---

## Mapa scenariuszy → testy Playwright

| Scenariusz | Plik testowy | Test case |
|-------------|---------------|------------|
| 1-10 | `e2e/tests/04-contract.spec.ts` | Nowy test `P1-005 elastyczne widełki` |
| 11-12 | `backend/tests/unit/test_conditions.py` | Nowy test unit |

---

## Implementacja Playwright

```typescript
// e2e/tests/04-contract.spec.ts
test('P1-005: elastyczne widełki cenowe', async ({ page, request }) => {
  // Scenariusz 1: Podstawowe tworzenie warunków z widełkami
  await page.goto('/rao/contracts/new', { waitUntil: 'domcontentloaded' })
  await quickAddContractor(page, request)
  await quickAddArticle(page, request)
  
  // Dodaj warunek z widełkami
  await page.getByRole('button', { name: /dodaj warunek/i }).click()
  await page.locator('[data-testid="rate-type"]').selectOption('dobowa')
  await page.locator('[data-testid="period-from"]').fill('1')
  await page.locator('[data-testid="period-to"]').fill('3')
  await page.locator('[data-testid="rate1"]').fill('540')
  await page.locator('[data-testid="billing-label"]').fill('doba')
  await page.getByRole('button', { name: /zapisz/i }).click()
  
  // Sprawdź czy warunek zapisany
  await expect(page.locator('tbody tr').first()).toContainText('1')
  await expect(page.locator('tbody tr').first()).toContainText('3')
  await expect(page.locator('tbody tr').first()).toContainText('540,00')
  
  // Sprawdź podgląd PDF live
  await expect(page.locator('[data-testid="conditions-preview"]')).toContainText('1 - 3 dni')
  await expect(page.locator('[data-testid="conditions-preview"]')).toContainText('540,00 / doba')
})
```

---

## Status implementacji

- ✅ Backend: period_from/period_to dodane do modelu i schematów
- ✅ Frontend: ConditionPanel z kolumnami Od/Do
- ✅ Walidacja ciągłości: watcher gapError
- ✅ Podgląd PDF live: formatPreview funkcja
- ⏸️ Testy Playwright: do utworzenia (scenariusze powyżej)
- ⏸️ Testy unit backend: do utworzenia
