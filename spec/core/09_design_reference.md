# 09 — Design Reference: Toolsmart.pl

> **INSTRUKCJA DLA AGENTA:** Nowa aplikacja RAO ma wyglądać jak toolsmart.pl.
> **PRZED ROZPOCZĘCIEM BUDOWY FRONTENDU** wykonaj pełny scrape CSS z toolsmart.pl
> zgodnie z procedurą w sekcji „Scraping CSS" poniżej. Wartości w tym pliku są
> punktem wyjścia — aktualne dane ze strony mają zawsze pierwszeństwo.

---

## 0. Scraping CSS z toolsmart.pl — WYKONAJ PRZED BUDOWĄ UI

### Cel
Wyciągnąć aktualne wartości CSS (kolory, fonty, spacing, border-radius, shadows)
bezpośrednio ze strony www.toolsmart.pl używając Playwright MCP.
Zaktualizować sekcje poniżej jeśli cokolwiek się różni.

### Procedura (Playwright MCP)

```
1. Otwórz stronę:
   → mcp5_browser_navigate({ url: "https://www.toolsmart.pl" })

2. Zrób screenshot dla wizualnego odniesienia:
   → mcp5_browser_take_screenshot({ filename: "spec/toolsmart_scrape.png", fullPage: true })

3. Wyciągnij wszystkie CSS custom properties (:root variables):
   → mcp5_browser_evaluate({
       function: `() => {
         const styles = getComputedStyle(document.documentElement);
         const vars = {};
         for (const sheet of document.styleSheets) {
           try {
             for (const rule of sheet.cssRules) {
               if (rule.selectorText === ':root') {
                 rule.style.cssText.split(';').forEach(d => {
                   const [k, v] = d.split(':');
                   if (k && k.trim().startsWith('--')) vars[k.trim()] = v.trim();
                 });
               }
             }
           } catch(e) {}
         }
         return vars;
       }`
     })

4. Wyciągnij kolory tła, tekstu i border z kluczowych elementów:
   → mcp5_browser_evaluate({
       function: `() => {
         const sel = (s) => {
           const el = document.querySelector(s);
           if (!el) return null;
           const cs = getComputedStyle(el);
           return { bg: cs.backgroundColor, color: cs.color, border: cs.borderColor,
                    fontFamily: cs.fontFamily, fontSize: cs.fontSize, fontWeight: cs.fontWeight };
         };
         return {
           navbar:      sel('header, nav, .navbar, [class*="nav"]'),
           btn_primary: sel('[class*="btn-primary"], [class*="cta"], button[class*="primary"]'),
           card:        sel('[class*="card"], [class*="product"]'),
           body:        sel('body'),
           h1:          sel('h1'),
           footer:      sel('footer'),
         };
       }`
     })

5. Wyciągnij font z Google Fonts link tag:
   → mcp5_browser_evaluate({
       function: `() => [...document.querySelectorAll('link[href*="fonts.googleapis"]')]
                        .map(l => l.href)`
     })

6. Sprawdź navbar background + logo kolor:
   → mcp5_browser_evaluate({
       function: `() => {
         const nav = document.querySelector('header, nav, [class*="navbar"]');
         if (!nav) return null;
         const cs = getComputedStyle(nav);
         return { bg: cs.backgroundColor, color: cs.color, height: cs.height };
       }`
     })
```

### Co zrobić z wynikami
- Jeśli `--color-primary` różni się od `#1D2B53` → zaktualizuj sekcję „Paleta kolorów"
- Jeśli font to nie Montserrat → zaktualizuj sekcję „Typografia"  
- Jeśli border-radius kart różni się od `12px` → zaktualizuj komponenty
- Jeśli cokolwiek się zgadza — potwierdź i buduj bez zmian

### Fallback (jeśli scrape się nie uda)
Użyj wartości z sekcji poniżej — są zweryfikowane i aktualne na dzień tworzenia specyfikacji.

---

## Screenshoty referencyjne

![Toolsmart hero + navbar](file:///C:/Users/mateu/.gemini/antigravity/brain/cee607b1-9ee9-4f47-9765-9b5a8c0a77a8/toolsmart_home_1_1773511486481.png)

![Toolsmart wartości + karty](file:///C:/Users/mateu/.gemini/antigravity/brain/cee607b1-9ee9-4f47-9765-9b5a8c0a77a8/toolsmart_home_2_1773511494075.png)

![Toolsmart produkty](file:///C:/Users/mateu/.gemini/antigravity/brain/cee607b1-9ee9-4f47-9765-9b5a8c0a77a8/toolsmart_home_3_1773511500025.png)

---

## Paleta kolorów (wyekstrahowana z toolsmart.pl)

```css
:root {
  /* === PRIMARY — Deep Navy Blue === */
  --color-primary: #1D2B53;          /* Navbar text, headers, buttons, card labels */
  --color-primary-dark: #141E3A;     /* Hover/active na przyciskach, footer bg */
  --color-primary-light: #2A3F6F;    /* Lighter navy for subtle elements */

  /* === BACKGROUNDS === */
  --color-bg-white: #FFFFFF;         /* Główne tło sekcji, navbar, karty */
  --color-bg-light: #F8F9FA;         /* Tło naprzemiennych sekcji, light gray */
  --color-bg-card: #FFFFFF;          /* Tło kart */
  --color-bg-card-hover: #FCFCFE;    /* Hover na kartach */
  --color-bg-editing: #FFFBEB;       /* Warm cream tint dla wierszy w trybie inline edit */

  /* === TEXT === */
  --color-text-heading: #1D2B53;     /* Nagłówki — navy blue */
  --color-text-body: #4A5568;        /* Tekst body — ciemny szary */
  --color-text-muted: #718096;       /* Muted/secondary text */
  --color-text-on-primary: #FFFFFF;  /* Biały tekst na navy tle */

  /* === ACCENTS === */
  --color-accent-blue: #3B82F6;      /* Linki, hover, numbering circles */
  --color-border: #E2E8F0;           /* Delikatne bordery kart */
  --color-border-hover: #CBD5E1;     /* Border karty na hover */

  /* === STATUS === */
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-error-bg: #FEF2F2;
  --color-error-border: #FECACA;
  --color-info: #3B82F6;

  /* === SHADOWS === */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-card-hover: 0 10px 25px rgba(29,43,83,0.12);
  --shadow-navbar: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-button: 0 2px 4px rgba(29,43,83,0.2);
}
```

## Typografia

```css
/* Google Fonts import */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

:root {
  --font-family: 'Montserrat', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  /* Rozmiary */
  --font-size-xs: 11px;
  --font-size-sm: 13px;
  --font-size-base: 14px;
  --font-size-md: 16px;
  --font-size-lg: 20px;
  --font-size-xl: 24px;
  --font-size-xxl: 32px;
  --font-size-hero: 40px;

  /* Wagi */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --font-weight-extrabold: 800;

  /* Line height */
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.7;
}
```

## Spacing

```css
:root {
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-5: 20px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  --spacing-10: 40px;
  --spacing-12: 48px;
  --spacing-16: 64px;
}
```

> **UWAGA — dwa systemy zmiennych (RAO-P2-062 fix 2026-07-01):**
> `frontend/src/style.css` definiuje `--spacing-N` (1/2/3/4/5/6/8/10/12/16) ale **NIE jest importowany** w `main.ts`.
> Aktywne zmienne są w `frontend/src/assets/styles/variables.css` (`--spacing-xs/sm/md/lg/xl/2xl`).
> Aby uniknąć pustych wartości (0px padding/border-radius — root cause broken layout archiwum),
> `variables.css` zawiera **aliasy** mapujące stare nazwy na nowe:
> `--spacing-1` → `--spacing-xs` (4px), `--spacing-5` → 20px (dodane), itd.
> To samo dotyczy `--border-radius-md` → `--border-radius` (12px), `--color-error` → `--color-danger`.
> **Nowy kod powinien używać nazw z `variables.css`** (`--spacing-lg`, `--border-radius`), ale aliasy
> zapewniają backward-compat dla istniejących widoków.

## Border Radius

```css
:root {
  --border-radius-sm: 8px;      /* Form inputs, small elements */
  --border-radius-md: 12px;     /* Cards, panels, buttons (alias → --border-radius) */
  --border-radius-lg: 12px;     /* Large cards */
  --border-radius-pill: 24px;   /* Pill-shaped buttons */
}
```

## Komponenty UI (stylistically)

### Navbar (sticky top)
```css
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--color-bg-white);
  box-shadow: var(--shadow-navbar);
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-8);
}
.navbar-logo {
  font-family: var(--font-family);
  font-weight: var(--font-weight-extrabold);
  font-size: var(--font-size-xl);
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 2px;
}
.navbar-links a {
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-base);
  text-decoration: none;
  margin: 0 var(--spacing-4);
  transition: opacity 0.2s;
}
.navbar-links a:hover { opacity: 0.7; }
```

### CTA Button (okrągły, navy bg, biały tekst)
```css
.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  border: none;
  border-radius: 24px;              /* Pill-shaped */
  padding: 10px 28px;
  font-family: var(--font-family);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  cursor: pointer;
  box-shadow: var(--shadow-button);
  transition: all 0.2s ease;
}
.btn-primary:hover {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(29,43,83,0.3);
}
```

### Karty (białe, rounded, shadow)
```css
.card {
  background: var(--color-bg-card);
  border-radius: 12px;
  padding: var(--spacing-6);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}
.card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
  border-color: var(--color-border-hover);
}
```

### Card z navy label (jak karty produktów na toolsmart)
```css
.product-card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
}
.product-card-image {
  background: var(--color-bg-light);
  padding: var(--spacing-6);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}
.product-card-label {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  padding: var(--spacing-4) var(--spacing-6);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  text-align: center;
}
```

### Step Cards (01, 02, 03, 04 — navy bg, biały tekst)
```css
.step-card {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  border-radius: 12px;
  padding: var(--spacing-6);
  text-align: center;
  position: relative;
}
.step-card-number {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-bg-white);
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  box-shadow: var(--shadow-card);
}
.step-card-icon {
  font-size: 32px;
  margin-bottom: var(--spacing-4);
  opacity: 0.9;
}
```

### Headings
```css
h1, h2 {
  font-family: var(--font-family);
  color: var(--color-text-heading);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
}
h1 { font-size: var(--font-size-xxl); }
h2 { font-size: var(--font-size-xl); }
h3 { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); }
```

### Form Elements (aplikacja RAO)
```css
.form-input {
  width: 100%;
  padding: 10px 14px;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-white);
  color: var(--color-text-body);
  transition: border-color 0.2s;
}
.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(29,43,83,0.1);
}
.form-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-heading);
  margin-bottom: var(--spacing-1);
  display: block;
}
```

### DataGrid / Table (tabelki w aplikacji)
```css
.data-grid {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.data-grid thead th {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  padding: 12px 16px;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  text-align: left;
  border: none;
}
.data-grid tbody tr {
  background: var(--color-bg-white);
  transition: background 0.15s;
}
.data-grid tbody tr:nth-child(even) {
  background: var(--color-bg-light);
}
.data-grid tbody tr:hover {
  background: rgba(29,43,83,0.05);
}
.data-grid tbody tr.selected {
  background: rgba(29,43,83,0.1);
}
.data-grid tbody td {
  padding: 10px 16px;
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  border-bottom: 1px solid var(--color-border);
}
```

### Sidebar (nawigacja aplikacji — nowy styl Toolsmart)
```css
.sidebar {
  width: 220px;
  background: var(--color-primary);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-top: var(--spacing-6);
}
.sidebar-logo {
  padding: var(--spacing-4) var(--spacing-6);
  font-family: var(--font-family);
  font-weight: var(--font-weight-extrabold);
  font-size: var(--font-size-xl);
  color: var(--color-text-on-primary);
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: var(--spacing-8);
}
.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-6);
  color: rgba(255,255,255,0.7);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-base);
  text-decoration: none;
  border-radius: 0 8px 8px 0;
  margin-right: var(--spacing-3);
  transition: all 0.2s;
}
.sidebar-nav-item:hover {
  color: var(--color-text-on-primary);
  background: rgba(255,255,255,0.1);
}
.sidebar-nav-item.active {
  color: var(--color-text-on-primary);
  background: rgba(255,255,255,0.15);
  font-weight: var(--font-weight-semibold);
}
```

---

## Mapowanie: Toolsmart → RAO App

| Element Toolsmart | Element RAO |
|-------------------|------------|
| Sticky top navbar (#FFF, shadow) | Opcjonalnie top bar z info użytkownika |
| Deep navy sidebar/footer | **Sidebar nawigacji** (navy #1D2B53) |
| Product cards (image + navy label) | Karty maszyn w gridzie Artykułów |
| Step cards (01-04, navy bg) | Dashboard status cards |
| White cards with shadow | Formularz container |
| Pill CTA button (navy) | Wszystkie główne przyciski |
| Font Montserrat bold | Nagłówki i etykiety |
| Light gray alternating bg | Naprzemienne tło sekcji |

## Ikony SVG (RAO-P0-003/P1-006)

`components/shared/AppIcon.vue` — lekki zestaw ikon SVG (bez zależności zewnętrznych),
stroke=currentColor, 24×24 viewBox, stroke-width 2 (styl lucide).

**Zestaw:** tractor, map-pin, mail, trophy, building, **banknote**, file, chart,
calendar, search, wrench, package, layers, check-circle.

**RAO-P0-003/P1-006:** Ikona `dollar` (pionowa kreska + krzywa S — kojarzyła się z USD)
została zastąpiona neutralną ikoną `banknote` (banknot z okiem — bez symbolu waluty).
W polskiej aplikacji wynajmu maszyn symbol `$` jest niedopuszczalny; waluta zawsze
formatowana jako "zł" (`utils/format.ts → formatCurrency`).

---

## Wykresy Chart.js (vue-chartjs) — komponenty i paleta

### `components/analytics/ChartCard.vue`
Wrapper kartowy dla wykresów Chart.js używanych w tabach AnalyticsView. Opakowuje komponenty
`vue-chartjs` (Bar, Line, Doughnut) w kartę z nagłówkiem, stanami loading/empty i spójnym stylem.

**Props:**
- `title: string` — nagłówek kartowy
- `chartType: 'bar' | 'line' | 'doughnut'` — typ wykresu
- `chartData: ChartData` — dane Chart.js
- `chartOptions?: ChartOptions` — opcje (default: `defaultChartOptions` z `useChartTheme.ts`)
- `loading?: boolean`, `empty?: boolean`, `testId?: string`

**Styl:** karta z `--color-bg-card`, `--border-radius`, `--shadow-card`; canvas responsive
(maintainAspectRatio=false, auto resize).

**data-testid:** `chart-card`, `chart-card-<testId>`, `chart-canvas`, `chart-loading`, `chart-empty`.

### `composables/useChartTheme.ts`
Dostarcza paletę kolorów i bazowe opcje Chart.js spójne z design system RAO.

**Paleta kolorów chart (`chartColors`):**

| Klucz | Wartość | Odpowiednik CSS |
|-------|---------|-----------------|
| `colors.primary` | `#1D2B53` | `--color-primary` (Deep Navy) |
| `colors.info` | `#3B82F6` | `--color-info` / `--color-accent-blue` |
| `colors.success` | `#22C55E` | `--color-success` |
| `colors.warning` | `#F59E0B` | `--color-warning` |
| `colors.error` | `#EF4444` | `--color-error` |
| `colors.primaryLight` | `#2A3F6F` | `--color-primary-light` |

**Eksportowane funkcje:**
- `getChartPalette(n: number): string[]` — generuje tablicę N kolorów (cykl przez paletę dla dużych zbiorów danych).
- `defaultChartOptions: ChartOptions` — bazowe opcje: font Montserrat, grid color z `--color-border`, tooltip styling, responsive.

**Runtime:** czyta zmienne CSS z `:root` (getComputedStyle) dla spójności z aktywnym motywem.

### Wykresy w tabach AnalyticsView

| Tab | Typ wykresu | Opis |
|-----|-------------|------|
| LiveFleetTab | doughnut + bar | Dostępne vs Wynajęte + top maszyny wg dni |
| CategoriesTab | bar (horyzontalny) | Top kategorie wg metryki (Przychód/Dni/Umów) z toggle |
| MachinesTab | bar | Top 10 maszyn wg przychodu |
| PeriodRentalTab | line + bar | Trend przychodu w okresie + top kategorii |
| ServicesRegularTab | bar | Top 10 usług zwykłych wg przychodu |
| ServicesAdditionalTab | doughnut | Udział usług dodatkowych wg przychodu |
| LocationsTab | bar | Top 10 miast (zastąpił custom CSS bars) |
