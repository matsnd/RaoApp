# UX Screenshots Review — RAO-P2-016

**Data utworzenia:** 2026-05-19
**Cel:** Weryfikacja zgodności widoków RAO z design systemem Toolsmart

## Jak uruchomić screenshoty

1. **Uruchom serwery:**
   ```bash
   # Terminal 1 - Backend
   cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8001

   # Terminal 2 - Frontend
   cd frontend && npm run dev --port 5174
   ```

2. **Uruchom test screenshotów:**
   ```bash
   cd e2e
   npx playwright test tests/10-ux-screenshots.spec.ts --reporter=list
   ```

3. **Screenshoty zostaną zapisane w:** `e2e/screenshots/ux-review/`

## Lista screenshotów

### Widoki główne (3)
- `01-login-empty.png` — Formularz logowania (pusty)
- `02-login-validation-error.png` — Formularz logowania (błąd walidacji)
- `03-dashboard-empty.png` — Dashboard (brak umów)
- `04-home-landing.png` — Home page / landing

### Formularze CRUD (3)
- `05-contractor-form-new-empty.png` — Nowy kontrahent (pusty formularz)
- `06-contractor-form-validation.png` — Formularz kontrahenta (błędy walidacji)
- `07-article-form-new-empty.png` — Nowy artykuł (pusty formularz)
- `08-contract-form-new-empty.png` — Nowa umowa (pusty formularz)

### Ustawienia (5)
- `09-settings-company.png` — Ustawienia: Dane firmy
- `10-settings-salespeople.png` — Ustawienia: Handlowcy
- `11-settings-categories.png` — Ustawienia: Kategorie
- `12-settings-fee-presets.png` — Ustawienia: Szablony usług
- `13-settings-fakturownia.png` — Ustawienia: Fakturownia

### Inne (5)
- `14-change-password-empty.png` — Zmiana hasła (pusty formularz)
- `15-admin-panel.png` — Panel administracyjny
- `16-worker-view.png` — Widok pracownika
- `17-commission-view.png` — Widok prowizji

**Łącznie:** 17 screenshotów

## UX Checklist — Design System Toolsmart

Dla każdego screenshotu sprawdź:

### Kolory
- [ ] Główny kolor navy #1D2B53 używany poprawnie (nagłówki, przyciski primary)
- [ ] Kolor tła jest biały lub jasny szary
- [ ] Kolor tekstu ma odpowiedni kontrast (WCAG AA)
- [ ] Stany error używają czerwieni, warning — żółtego/pomarańczowego
- [ ] Stany success używają zieleni

### Typografia
- [ ] Font Montserrat używany poprawnie
- [ ] Hierarchy typograficzna zachowana (h1 > h2 > h3 > body)
- [ ] Rozmiary fontów zgodne z design system
- [ ] Wagi fontów (regular, medium, bold) używane zgodnie z hierarchy
- [ ] Line-height odpowiedni dla czytelności

### Spacing & Layout
- [ ] Spacing oparty na 8px grid (padding/margin: 8, 16, 24, 32px)
- [ ] Border-radius 12px na kartach i przyciskach
- [ ] Shadows zgodne z design system (subtelne, nie zbyt mocne)
- [ ] Padding w formularzach wystarczający
- [ ] Margines między sekcjami odpowiednie

### Formularze
- [ ] Labelki są nad inputami (lub obok dla inline)
- [ ] Placeholders są pomocne i nie mylące z wartościami
- [ ] Walidacja widoczna (czerwone komunikaty przy błędach)
- [ ] Przyciski mają poprawne stany (default, hover, active, disabled)
- [ ] Required fields są oznaczone (gwiazdka lub inaczej)

### Stany
- [ ] Empty states mają komunikat "Brak danych" i CTA (np. "Dodaj pierwszy element")
- [ ] Loading states mają spinner lub skeleton screen
- [ ] Error states mają komunikat błędu i akcję naprawczą (np. "Spróbuj ponownie")
- [ ] Success states mają potwierdzenie i ewentualną akcję (np. "Dodaj kolejny")

### Komponenty
- [ ] Przyciski primary mają kolor navy #1D2B53
- [ ] Przyciski secondary są szare/outline
- [ ] Karty mają shadow i border-radius 12px
- [ ] Tabele mają poprawne nagłówki i spacing
- [ ] Dropdowny/selecty mają poprawny styling

### Responsywność
- [ ] Layout działa na desktop (1920x1080)
- [ ] Layout nie jest pękany na tablet (1024x768)
- [ ] Elementy nie są ucięte na mniejszych ekranach

### Ogólne
- [ ] Interfejs wygląda profesjonalnie i spójnie
- [ ] Brak "hardcoded" wyglądów (każdy ekran zgodny z systemem)
- [ ] Brak wizualnych bugów (przeklejanie, overlap, złe alignment)
- [ ] Interfejs jest intuicyjny i łatwy w użyciu

## Proces review

1. UX Designer przegląda wszystkie screenshoty
2. Dla każdego screenshotu wypełnia checklistę powyżej
3. Zapisuje uwagi w pliku `e2e/screenshots/ux-review/NOTES.md`
4. Critical issues trafiają do backlog jako P1/P2
5. Minor issues trafiają do backlog jako P3

## Tools

- **Playwright:** Automatyzacja screenshotów
- **rao-vision MCP:** Opcjonalna analiza AI screenshotów (kosztowne, używaj tylko gdy potrzebne)
- **Figma/Design tools:** Porównanie z design systemem Toolsmart

## Uwagi

- Screenshoty są robione w headless mode (bez interfejsu przeglądarki)
- Rozdzielczość: 1280x720 (domyślna Playwright)
- Format: PNG
- Każdy uruchomienie testu nadpisuje istniejące screenshoty