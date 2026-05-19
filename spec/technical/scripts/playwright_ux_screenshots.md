# Playwright UX Screenshots Generator

**Skrypt:** `e2e/tests/10-ux-screenshots.spec.ts`
**Data utworzenia:** 2026-05-19
**Zadanie:** RAO-P2-016

## Opis

Test Playwright który automatycznie robi screenshoty wszystkich widoków aplikacji RAO dla UX review. Screenshoty służą do weryfikacji zgodności z design systemem Toolsmart.

## Użycie

### Wymagania wstępne

1. **Uruchom serwery:**
   ```bash
   # Backend (port 8001)
   cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8001

   # Frontend (port 5174)
   cd frontend && npm run dev --port 5174
   ```

2. **Zainstaluj Playwright (jeśli nie zainstalowany):**
   ```bash
   cd e2e
   npx playwright install --with-deps chromium
   ```

### Uruchomienie testu

```bash
cd e2e
npx playwright test tests/10-ux-screenshots.spec.ts --reporter=list
```

## Wyniki

Screenshoty są zapisywane w `e2e/screenshots/ux-review/`:

### Widoki główne (4)
- `01-login-empty.png` — Formularz logowania (pusty)
- `02-login-validation-error.png` — Błąd walidacji
- `03-dashboard-empty.png` — Dashboard pusty
- `04-home-landing.png` — Home page

### Formularze CRUD (4)
- `05-contractor-form-new-empty.png` — Nowy kontrahent
- `06-contractor-form-validation.png` — Błędy walidacji
- `07-article-form-new-empty.png` — Nowy artykuł
- `08-contract-form-new-empty.png` — Nowa umowa

### Ustawienia (5)
- `09-settings-company.png` — Dane firmy
- `10-settings-salespeople.png` — Handlowcy
- `11-settings-categories.png` — Kategorie
- `12-settings-fee-presets.png` — Szablony usług
- `13-settings-fakturownia.png` — Fakturownia

### Inne (4)
- `14-change-password-empty.png` — Zmiana hasła
- `15-admin-panel.png` — Panel admin
- `16-worker-view.png` — Widok pracownika
- `17-commission-view.png` — Prowizja

**Łącznie:** 17 screenshotów

## Struktura testu

Test używa:
- `waitForBackend()` — czeka aż backend będzie dostępny
- `login()` — automatyczne logowanie dla chronionych widoków
- `page.screenshot()` — zapisuje screenshot do pliku
- Playwright headless mode — bez interfejsu przeglądarki

## Konfiguracja

- **Rozdzielczość:** 1280x720 (domyślna Playwright)
- **Format:** PNG
- **Tryb:** Headless
- **Timeout:** 15s na ładowanie strony

## Integracja z UX review

Po wykonaniu testu:
1. UX Designer przegląda screenshoty w `e2e/screenshots/ux-review/`
2. Używa checklisty z `README.md` do weryfikacji
3. Zapisuje uwagi w `NOTES.md`
4. Critical issues → backlog P1/P2
5. Minor issues → backlog P3

## Rozszerzalność

Aby dodać nowy widok do screenshotowania:
1. Dodaj nowy test case w `10-ux-screenshots.spec.ts`
2. Użyj wzorca:
   ```typescript
   test('NazwaWidoku - opis stanu', async ({ page }) => {
     await login(page)
     await page.goto('/rao/sciezka-widoku', { waitUntil: 'domcontentloaded', timeout: 15_000 })
     await page.waitForTimeout(500) // Czekaj na ładowanie
     await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'XX-nazwa.png') })
   })
   ```
3. Zaktualizuj listę w `README.md`

## Uwagi

- Test wymaga działającego backendu i frontendu
- Każde uruchomienie nadpisuje istniejące screenshoty
- Test jest deterministyczny — zawsze robi te same screenshoty
- Można użyć rao-vision MCP do automatycznej analizy AI screenshotów (kosztowne)