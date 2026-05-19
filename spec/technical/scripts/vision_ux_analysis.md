# Vision AI Analysis for UX Review — RAO

> **Cel:** Dokumentacja procesu automatycznej analizy UX/UI przez MCP rao-vision
> **Data:** 2026-05-19
> **Zadanie:** RAO-P2-016 (SPIKE) + RAO-P2-017 (Poprawa UX/UI)

## Przegląd

Ten dokument opisuje jak używać MCP `rao-vision` do automatycznej analizy screenshotów UX w aplikacji RAO. Vision AI pozwala na szybką identyfikację problemów UX/UI bez ręcznego przeglądu.

## Narzędzia MCP rao-vision

### 1. `analyze_screenshot`

Analizuje istniejący screenshot UI aplikacji RAO przez Claude Vision.

**Parametry:**
- `image_path` (wymagane): Absolutna ścieżka do pliku PNG/JPG screenshota
- `question` (opcjonalne): Opcjonalne pytanie do analizy, np. "Czy formularz wygląda poprawnie?"

**Przykład użycia:**
```bash
mcp_call_tool(
  server_name="rao-vision",
  tool_name="analyze_screenshot",
  arguments={
    "image_path": "C:\\projects\\repos\\RaoApp\\e2e\\screenshots\\ux-review\\01-login-empty.png",
    "question": "Oceń ekran logowania pod kątem UX: czy pola formularza są czytelne, czy przycisk jest widoczny, czy jest odpowiedni spacing, czy kolorystyka jest spójna z design systemem Toolsmart (navy #1D2B53, Montserrat, rounded 12px). Wymień wszystkie problemy UX/UI."
  }
)
```

**Output:**
- Ocena numeryczna (np. 7/10)
- Lista problemów UX/UI z podziałem na priorytety (krytyczne, ważne, drobne)
- Rekomendacje naprawcze z przykładami kodu CSS
- Raport zapisany do pliku `*-vision-report.md`

### 2. `screenshot_and_analyze`

Robi screenshot podanego URL przez Playwright, następnie analizuje go przez Claude Vision. Wymaga działającego frontendu.

**Parametry:**
- `url` (wymagane): URL do screenshota, np. http://localhost:5173/contracts
- `question` (opcjonalne): Opcjonalne pytanie do analizy
- `output_path` (opcjonalne): Ścieżka gdzie zapisać screenshot (domyślnie: temp/screenshot-{timestamp}.png)

**Przykład użycia:**
```bash
mcp_call_tool(
  server_name="rao-vision",
  tool_name="screenshot_and_analyze",
  arguments={
    "url": "http://localhost:5174/rao/login",
    "question": "Oceń ekran logowania pod kątem UX"
  }
)
```

## Proces UX Review z Vision AI

### Krok 1: Wykonanie screenshotów

Użyj testu Playwright `e2e/tests/10-ux-screenshots.spec.ts` do wykonania screenshotów wszystkich widoków:

```bash
cd e2e
npx playwright test tests/10-ux-screenshots.spec.ts
```

Screenshoty zostaną zapisane w `e2e/screenshots/ux-review/`.

### Krok 2: Analiza vision dla kluczowych widoków

Wybierz reprezentatywny zestaw screenshotów (nie trzeba analizować wszystkich):

**Zalecany zestaw:**
- LoginView (empty state + validation error)
- DashboardView (empty state)
- ContractFormView (empty state)
- SettingsView (company data)
- Jedna lista/karta (np. contractors list)

### Krok 3: Interpretacja wyników

Vision AI zwraca:
- **Ocena numeryczna** (np. 7/10) — ogólna jakość UX/UI
- **Co jest OK** — elementy poprawne
- **Problemy do poprawy** — z podziałem na priorytety:
  - 🔴 Krytyczne — muszą być naprawione przed go-live
  - 🟡 Ważne — powinny być naprawione
  - 🟠 Drobne — nice to have

### Krok 4: Utworzenie backlog item

Na podstawie wyników vision analysis utwórz zadanie w backlogu z konkretnymi acceptance criteria:

```yaml
id: RAO-P2-017
priority: P2
size: L
status: todo
classification: frontend
roles: [frontend-dev, ui-designer, ux-designer]
depends_on: [RAO-P2-016]
```

**Acceptance criteria (przykład):**
- [ ] Border-radius karty: 12px (zamiast ~20-24px)
- [ ] Ikony w polach formularza
- [ ] Poprawa kontrastu placeholderów (WCAG AA min. 4.5:1)
- [ ] Stany interaktywne: hover, focus, error

## Przykłady analizy vision

### LoginView — Główne problemy

1. **Border-radius niezgodny z design systemem**
   - Karta: ~20-24px → powinno być 12px
   - Inputy: ~8px → powinno być 12px
   - Przycisk: ~8px → powinno być 12px

2. **Brak ikon w polach formularza**
   - Brak ikony użytkownika przy polu Login
   - Brak ikony kłódki przy polu Hasło
   - Brak ikony "pokaż/ukryj hasło" 👁️

3. **Słaby kontrast placeholderów**
   - Zbyt jasny szary, może być nieczytelny dla osób z wadami wzroku
   - Wymaga sprawdzenia WCAG AA (min. 4.5:1)

4. **Brak stanów interaktywnych**
   - Brak hover na przycisku
   - Brak focus state na inputach (outline)
   - Brak error state (czerwona ramka + komunikat)

### DashboardView — Główne problemy

1. **Niespójność kolorystyczna**
   - Przyciski CTA nie w navy #1D2B53 (wyglądają na ~#3B5BDB)
   - Ikony w różnych kolorach bez systemu

2. **Puste states bez ilustracji**
   - Brak ikony ilustracyjnej
   - Sam tekst bez wizualnego wsparcia

3. **Duplikacja informacji**
   - Te same dane wyświetlane 2x (górny pasek vs karty)

### ContractFormView — Główne problemy

1. **Brak wizualnego grupowania pól**
   - Wszystkie pola są "płaskie" — brak sekcji, kart, separatorów
   - Użytkownik nie wie, które pola są powiązane

2. **Niespójne oznaczanie pól wymaganych**
   - Tylko "Kontrahent" ma gwiazdkę (*)
   - Pozostałe wymagane pola nie są oznaczone

3. **Chaotyczny layout adresu dostawy**
   - Brak pola na ulicę/numer
   - Kod pocztowy i miasto w jednej linii z uwagami

## Optymalizacja kosztów

Vision AI jest kosztowne (~$0.01-0.03 per screenshot). Zasady optymalizacji:

1. **Analizuj tylko kluczowe widoki** — nie wszystkie 17 screenshotów
2. **Konkretne pytania** — "Czy spacing jest 16px?" vs "Czy wygląda OK?"
3. **Batch problems** — 1 screenshot z pytaniem o wszystkie problemy danego widoku
4. **Reuse screenshots** — jeśli e2e test już zrobił screenshot → analyze_screenshot

## Wzorce pytań do vision

### Dla formularzy:
```
"Oceń formularz pod kątem UX: czy layout jest czytelny, czy pola są logicznie pogrupowane, 
czy są odpowiednie etykiety i placeholdery, czy jest widoczna walidacja, czy jest odpowiedni spacing, 
czy przyciski są dobrze umieszczone. Wymień wszystkie problemy UX/UI."
```

### Dla ekranów logowania:
```
"Oceń ekran logowania pod kątem UX: czy pola formularza są czytelne, czy przycisk jest widoczny, 
czy jest odpowiedni spacing, czy kolorystyka jest spójna z design systemem Toolsmart 
(navy #1D2B53, Montserrat, rounded 12px). Wymień wszystkie problemy UX/UI."
```

### dla dashboardów:
```
"Oceń dashboard (empty state): czy layout jest czytelny, czy jest odpowiednia hierarchia informacji, 
czy nawigacja jest intuicyjna, czy jest widoczny call-to-action, czy pusty stan jest dobrze obsługiwany 
(komunikat, ikona, sugestia). Wymień wszystkie problemy UX/UI."
```

### dla komunikatów błędów:
```
"Oceń ekran z błędem walidacji: czy komunikat błędu jest czytelny, czy jest odpowiednio wyróżniony 
(kolor, pozycja), czy użytkownik wie co jest nie tak. Wymień wszystkie problemy UX/UI związane z 
wyświetlaniem błędów."
```

## Integracja z procesem QA

Vision AI powinno być używane jako **dodatek** do manualnego UX review, nie jako zamiennik:

1. **Vision AI** — szybka identyfikacja oczywistych problemów (spacing, kolory, layout)
2. **Manual review** — dogłębna analiza flow użytkownika, edge cases, accessibility
3. **Weryfikacja** — po poprawkach, ponowna analiza vision dla potwierdzenia napraw

## Przykładowy workflow

```bash
# 1. Wykonaj screenshoty
cd e2e && npx playwright test tests/10-ux-screenshots.spec.ts

# 2. Analizuj kluczowe widoki przez vision
# (używając MCP rao-vision z konkretnymi pytaniami)

# 3. Zidentyfikuj problemy i utwórz backlog item
# (dodaj RAO-P2-017 do BACKLOG.md z acceptance criteria)

# 4. Napraw problemy
# (frontend-dev + ui-designer + ux-designer)

# 5. Ponowna analiza vision po poprawkach
# (weryfikacja czy problemy zostały naprawione)
```

## Ograniczenia vision AI

- **Nie rozumie kontekstu biznesowego** — nie wie czy dany element jest wymagany przez proces
- **Nie testuje interakcji** — nie może kliknąć, wpisać tekstu, przetestować flow
- **Ograniczona wiedza o design systemie** — trzeba podać konkretne wartości (np. "navy #1D2B53")
- **Może mieć "halucynacje"** — zawsze weryfikuj manualnie krytyczne problemy

## Best practices

1. **Konkretne pytania** — im bardziej specyficzne, tym lepsze wyniki
2. **Podaj wartości design systemu** — np. "navy #1D2B53", "border-radius 12px"
3. **Pytaj o konkretne aspekty** — spacing, kolory, typografia, layout, stany
4. **Wymień priorytety** — "krytyczne", "ważne", "drobne"
5. **Zawsze weryfikuj manualnie** — vision AI to narzędzie pomocnicze, nie substytut manualnego review

## Linki

- Playwright UX screenshots: `e2e/tests/10-ux-screenshots.spec.ts`
- Screenshoty: `e2e/screenshots/ux-review/`
- MCP rao-vision: `rao-vision` server
- Backlog item: `spec/backlog/BACKLOG.md` (RAO-P2-017)
- Design system: `spec/core/09_design_reference.md`

## Historia

- **2026-05-19**: Utworzenie dokumentacji, pierwsze analizy vision (LoginView, DashboardView, ContractFormView)
- **Zadanie:** RAO-P2-016 (SPIKE) + RAO-P2-017 (Poprawa UX/UI)
- **Wynik:** 4 analizy vision, zidentyfikowano 20+ problemów UX/UI, utworzono backlog item RAO-P2-017