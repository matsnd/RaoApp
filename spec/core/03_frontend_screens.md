# 03 — Frontend Screens (Vue.js 3) — Kompletna specyfikacja

> **INSTRUKCJA DLA AGENTA:** Zbuduj dokładnie te komponenty z dokładnie tymi polami i layoutem.
> Style muszą używać palety kolorów z sekcji Design System.
> Routing i nawigacja muszą być identyczne z WinForms (1:1).

## Struktura projektu

```
frontend/
├── index.html
├── vite.config.js
├── package.json
├── public/
│   └── favicon.ico
├── src/
│   ├── main.js                      # createApp, router, pinia
│   ├── App.vue                      # router-view
│   ├── assets/
│   │   └── styles/
│   │       ├── variables.css        # CSS custom properties (paleta)
│   │       ├── reset.css            # Reset + base styles
│   │       ├── layout.css           # Grid, flex, sidebar
│   │       ├── forms.css            # Input, select, button, checkbox
│   │       ├── tables.css           # DataGrid styles
│   │       └── animations.css       # Transitions, micro-animations
│   ├── router/
│   │   └── index.js                 # Routes with auth guard
│   ├── stores/
│   │   ├── auth.js                  # useAuthStore (login, token, user)
│   │   ├── contractors.js           # useContractorStore
│   │   ├── articles.js              # useArticleStore
│   │   ├── contracts.js             # useContractStore
│   │   └── settings.js              # useSettingsStore
│   ├── composables/
│   │   ├── useApi.js                # Axios instance with JWT interceptor
│   │   ├── useDebounce.js           # Debounced search
│   │   └── usePagination.js         # Pagination helper
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppSidebar.vue       # Lewy sidebar (Umowy/Kontrahenci/Artykuły/Raporty/Ustawienia)
│   │   │   ├── AppToolbar.vue       # Górny toolbar (info + ? - + przyciski)
│   │   │   └── AppLayout.vue        # Sidebar + content wrapper
│   │   ├── shared/
│   │   │   ├── DataGrid.vue         # Reusable data grid (jak WinForms DataGridView)
│   │   │   ├── SearchFilter.vue     # Search input z debounce
│   │   │   ├── CalendarGrid.vue     # Kalendarz miesięczny (tabela 7x5)
│   │   │   ├── ConfirmDialog.vue    # Modal potwierdzenia (tak/nie)
│   │   │   ├── ContextMenu.vue      # Right-click menu
│   │   │   └── DateRangePicker.vue  # Selektor dat od/do
│   │   ├── contractors/
│   │   │   ├── ContractorForm.vue   # Formularz kontrahenta
│   │   │   ├── AddressList.vue      # Lista adresów (lewa kolumna)
│   │   │   ├── AddressForm.vue      # Formularz adresu (prawa kolumna)
│   │   │   └── GusLookupButton.vue  # Przycisk GUS
│   │   ├── contracts/
│   │   │   ├── ContractForm.vue     # Duży formularz umowy
│   │   │   ├── PositionGrid.vue     # Grid pozycji z toolbar
│   │   │   ├── ConditionGrid.vue    # Grid warunków z toolbar
│   │   │   ├── ContractCalendar.vue # 2-miesięczny kalendarz
│   │   │   └── ContractorPicker.vue # Dialog wyboru kontrahenta
│   │   ├── articles/
│   │   │   ├── ArticleForm.vue      # Formularz artykułu
│   │   │   └── ArticlePicker.vue    # Dialog wyboru artykułu (FormAwybor)
│   │   └── settings/
│   │       ├── CompanyForm.vue      # Dane firmy
│   │       ├── FeesForm.vue         # Opłaty dodatkowe
│   │       ├── SalespeopleList.vue  # Lista handlowców
│   │       └── ServiceTexts.vue     # Szablony usług
│   └── views/
│       ├── LoginView.vue            # Ekran logowania
│       ├── DashboardView.vue        # Główny ekran (sidebar + content)
│       ├── ContractorFormView.vue   # Formularz kontrahenta (pełny ekran)
│       ├── ContractFormView.vue     # Formularz umowy (pełny ekran)
│       ├── ArticleFormView.vue      # Formularz artykułu (dialog)
│       ├── ConditionFormView.vue    # Warunki rozliczenia (dialog/panel)
│       └── SettingsView.vue         # Konfiguracja (pełny ekran)
```

---

## Design System (CSS Custom Properties)

> **⚠️ UWAGA:** Pełny design system z kolorami, typografią, komponentami i stylami
> znajduje się w pliku **[09_design_reference.md](./09_design_reference.md)** —
> wyekstrahowany z toolsmart.pl (wzorzec wizualny nowej aplikacji).

**Kluczowe parametry (skrócone):**

```css
/* variables.css — pełna wersja w 09_DESIGN_REFERENCE.md */
:root {
  /* === Paleta Toolsmart (Deep Navy) === */
  --color-primary: #1D2B53;          /* Sidebar, headers, buttons, table headers */
  --color-primary-dark: #141E3A;     /* Hover/active */
  --color-bg-white: #FFFFFF;         /* Główne tło */
  --color-bg-light: #F8F9FA;         /* Naprzemienne sekcje */
  --color-text-heading: #1D2B53;     /* Nagłówki */
  --color-text-body: #4A5568;        /* Tekst */
  --color-text-on-primary: #FFFFFF;  /* Na navy tle */
  --color-border: #E2E8F0;          /* Bordery kart */

  /* === Typografia: Montserrat === */
  --font-family: 'Montserrat', 'Inter', sans-serif;
  --font-size-base: 14px;
  --font-size-sm: 13px;

  /* === Layout === */
  --sidebar-width: 220px;           /* Szerszy niż WinForms */
  --navbar-height: 64px;

  /* === Styl === */
  --border-radius: 12px;            /* Zaokrąglone karty */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-card-hover: 0 10px 25px rgba(29,43,83,0.12);
}
```

---

## Routing

```javascript
// router/index.js
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard/contracts'
      },
      {
        // Dashboard z parametrem sekcji (identyczne z sidebar tabs w WinForms)
        path: 'dashboard/:section',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        props: true
        // section = 'contracts' | 'contractors' | 'articles' | 'reports' | 'settings'
      },
      {
        path: 'contractors/new',
        name: 'ContractorNew',
        component: () => import('@/views/ContractorFormView.vue')
      },
      {
        path: 'contractors/:id/edit',
        name: 'ContractorEdit',
        component: () => import('@/views/ContractorFormView.vue'),
        props: true
      },
      {
        path: 'contracts/new',
        name: 'ContractNew',
        component: () => import('@/views/ContractFormView.vue'),
        // Query: ?contractor_id=5 (opcja: z kontekstu "dodaj umowę")
      },
      {
        path: 'contracts/:id/edit',
        name: 'ContractEdit',
        component: () => import('@/views/ContractFormView.vue'),
        props: true
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue')
      }
    ]
  }
]
```

---

## Komponent: `AppSidebar.vue`

```
Layout (dokładna replika WinForms Form2 lewego panelu):

┌─────────┐
│   RAO   │  ← Logo/nazwa (row 0, h=50px)
├─────────┤
│ Umowy   │  ← sidebar-btn, aktywny = fioletowy (#534478)
├─────────┤
│ Kontra- │  ← sidebar-btn
│ henci   │
├─────────┤
│ Artyku- │  ← sidebar-btn
│ ły      │
├─────────┤
│         │  ← gap (flex-grow)
├─────────┤
│ Raporty │  ← sidebar-btn
├─────────┤
│ Ustaw.  │  ← sidebar-btn
└─────────┘
```

**Props:** `activeSection: string`
**Emits:** `@navigate(section: string)`

```vue
<template>
  <nav class="sidebar">
    <div class="sidebar-logo">RAO</div>
    <button
      v-for="item in menuItems"
      :key="item.section"
      :class="['sidebar-btn', { active: activeSection === item.section }]"
      @click="$emit('navigate', item.section)"
    >
      {{ item.label }}
    </button>
    <div class="sidebar-spacer"></div>
    <button
      :class="['sidebar-btn', { active: activeSection === 'reports' }]"
      @click="$emit('navigate', 'reports')"
    >Raporty</button>
    <button
      :class="['sidebar-btn', { active: activeSection === 'settings' }]"
      @click="$emit('navigate', 'settings')"
    >Ustawienia</button>
  </nav>
</template>

<script setup>
const menuItems = [
  { section: 'contracts', label: 'Umowy' },
  { section: 'contractors', label: 'Kontrahenci' },
  { section: 'articles', label: 'Artykuły' },
]
defineProps({ activeSection: String })
defineEmits(['navigate'])
</script>
```

**CSS:**
```css
.sidebar {
  width: var(--sidebar-width);
  background: var(--color-sidebar-bg);
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.sidebar-logo {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  font-size: var(--font-size-xl);
  font-weight: 700;
}
.sidebar-btn {
  padding: var(--spacing-lg) var(--spacing-sm);
  background: transparent;
  border: none;
  color: var(--color-white);
  cursor: pointer;
  font-size: var(--font-size-base);
  transition: background var(--transition-fast);
}
.sidebar-btn:hover { background: var(--color-sidebar-hover); }
.sidebar-btn.active { background: var(--color-sidebar-active); }
.sidebar-spacer { flex: 1; }
```

---

## Komponent: `AppToolbar.vue`

```
Layout (replika WinForms Form2 górnego paska):

┌──────────────────────────────────────────────────────┐
│ [w]   info: Umowy (123 rekordów)          [?] [-] [+]│
└──────────────────────────────────────────────────────┘
```

**Props:**
- `infoText: string` — np. "Umowy (123 rekordów)"
- `showViewButton: boolean` — przycisk `[w]` (tylko dla umów)
- `showHelpButton: boolean` — przycisk `[?]`

**Emits:**
- `@view` — podgląd (otwórz raport)
- `@help` — pokaż szczegóły
- `@remove` — usuń wybrany
- `@add` — dodaj nowy

---

## Widok: `DashboardView.vue`

```
Layout (replika WinForms Form2):

┌──────────────────────────────────────────────────────┐
│ AppToolbar: [w] info [?] [-] [+]                     │
├──────────────────────────────────────────────────────┤
│ SearchFilter: [__________________szukaj____________] │
├──────────────────────────────────────────────────────┤
│ CalendarGrid (widoczny TYLKO dla sekcji 'contracts') │
│  Pn Wt Śr Czw Pt Sb Nd    (umowy tego dnia →)       │
│  1  2  3  4   5  6  7     z kolorowaniem komórek     │
├──────────────────────────────────────────────────────┤
│ DataGrid: lista danych                               │
│  - contracts: numer, kontrahent, adres, od, do, val  │
│  - contractors: nazwa, NIP, miasto, telefon          │
│  - articles: nazwa, rejestr., kategoria, właściciel  │
├──────────────────────────────────────────────────────┤
│ (Sekcja reports): DateRangePicker + ReportCombo      │
│ (Sekcja settings): redirect to /settings             │
└──────────────────────────────────────────────────────┘
```

**State:**
```javascript
const section = ref(route.params.section || 'contracts')
const items = ref([])
const selectedItem = ref(null)
const searchText = ref('')
const calendarDate = ref(new Date())
const totalCount = ref(0)
```

**Kolumny DataGrid per sekcja:**

```javascript
const columnDefs = {
  contracts: [
    { key: 'number', label: 'Numer', width: 120 },
    { key: 'contractor_name', label: 'Kontrahent', width: 250 },
    { key: 'delivery_address', label: 'Adres', width: 200 },
    { key: 'date_from', label: 'Początek', width: 100, type: 'date' },
    { key: 'date_to', label: 'Koniec', width: 100, type: 'date' },
    { key: 'total_value', label: 'Wartość', width: 120, type: 'currency' },
    { key: 'notes', label: 'Uwagi', width: 200 },
  ],
  contractors: [
    { key: 'name', label: 'Nazwa', width: 300 },
    { key: 'nip', label: 'NIP', width: 120 },
    { key: 'city', label: 'Miejscowość', width: 150 },
    { key: 'street', label: 'Ulica', width: 150 },
    { key: 'phone1', label: 'Telefon', width: 120 },
    { key: 'active_contract_number', label: 'Umowa', width: 120 },
  ],
  articles: [
    { key: 'name', label: 'Nazwa', width: 200 },
    { key: 'registration_no', label: 'Nr rej.', width: 100 },
    { key: 'brand', label: 'Marka', width: 100 },
    { key: 'model', label: 'Model', width: 100 },
    { key: 'category_name', label: 'Kategoria', width: 150 },
    { key: 'owner_name', label: 'Właściciel', width: 200 },
    { key: 'active_contract_number', label: 'Umowa', width: 120 },
    { key: 'serial_no', label: 'Nr seryjny', width: 120 },
    { key: 'replacement_value', label: 'Wartość', width: 120, type: 'currency' },
  ],
}
```

**Context Menu per sekcja:**

```javascript
const contextMenuItems = {
  contracts: [
    { label: 'Edytuj', action: 'edit', icon: '✏️' },
    { label: 'Usuń', action: 'delete', icon: '🗑️' },
    { label: 'Wydruk → Umowa', action: 'print_contract' },
    { label: 'Wydruk → Protokół ZO', action: 'print_protocol' },
    { label: 'Wydruk → Protokół ZO bez danych', action: 'print_protocol_nodata' },
    { label: 'Wyślij email', action: 'send_email' },
    { label: 'Pliki', action: 'open_files' },
  ],
  contractors: [
    { label: 'Edytuj', action: 'edit' },
    { label: 'Usuń', action: 'delete' },
    { label: 'Dodaj umowę', action: 'add_contract' },
    { label: 'Wydruk', action: 'print' },
  ],
  articles: [
    { label: 'Pokaż', action: 'view' },
    { label: 'Usuń', action: 'delete' },
    { label: 'Duplikuj', action: 'duplicate' },
  ],
}
```

**Event Handlers (kluczowe):**

```javascript
// Double-click na wierszu → edycja
function onRowDoubleClick(item) {
  if (section.value === 'contracts') {
    router.push({ name: 'ContractEdit', params: { id: item.id } })
  } else if (section.value === 'contractors') {
    router.push({ name: 'ContractorEdit', params: { id: item.id } })
  } else if (section.value === 'articles') {
    showArticleDialog(item.id) // dialog, nie nowa strona
  }
}

// Przycisk [+] na toolbarze
function onAdd() {
  if (section.value === 'contracts') {
    router.push({ name: 'ContractNew' })
  } else if (section.value === 'contractors') {
    router.push({ name: 'ContractorNew' })
  } else if (section.value === 'articles') {
    showArticleDialog(null) // nowy
  }
}

// Przycisk [-] na toolbarze
async function onRemove() {
  if (!selectedItem.value) return
  const confirmed = await confirmDialog('Czy na pewno usunąć?')
  if (!confirmed) return
  await api.delete(`/${section.value}/${selectedItem.value.id}`)
  await loadData()
}

// Filtrowanie — client-side (identyczne z WinForms RowFilter)
const filteredItems = computed(() => {
  if (!searchText.value) return items.value
  const search = searchText.value.toLowerCase()
  return items.value.filter(item =>
    Object.values(item).some(v =>
      String(v || '').toLowerCase().includes(search)
    )
  )
})
```

---

## Widok: `ContractorFormView.vue`

**Layout (replika WinForms FormK — 2 sekcje, 50%/50%):**

```
┌──────────────────────────────────────────────────────┐
│ GroupBox "Dane kontrahenta" (50% height)              │
│ ┌──────────────────────────────────────────────────┐  │
│ │ ☐ Dostawca           [GUS] data_gus_label       │  │
│ │ Nazwa     [____________]  NIP    [__________]   │  │
│ │ Naz.krót. [____________]  REGON  [__________]   │  │
│ │ uwagi    [__textarea__]   PESEL  [__________]   │  │
│ │ tel.     [_____] email [_____]  osoba [_____]   │  │
│ │ tel2.    [_____] www   [_____]  osoba2 [____]   │  │
│ │ ścieżka  [_____]          [ Zatwierdź ]         │  │
│ └──────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│ GroupBox "Adresy" (50% height)                        │
│ ┌─────────────────┬──────────────────────────────┐   │
│ │ Lista adresów   │ Formularz wybranego adresu   │   │
│ │ ☐ Siedziba      │ ☐ siedziba ☐ domyślny       │   │
│ │ ☐ Magazyn       │ nazwa [___] ulica [___]      │   │
│ │                 │ kod [__] miasto [__]          │   │
│ │                 │ osoba [___] tel [___]         │   │
│ │                 │ [Usuń]  [Zatwierdź]          │   │
│ └─────────────────┴──────────────────────────────┘   │
│ LTT [_____] LNG [_____]  [clipboard] [maps]         │
│                                [ Nowy adres ]         │
└──────────────────────────────────────────────────────┘
```

**Reactive State:**
```javascript
const contractor = ref({
  name: '', name_short: '', nip: '', regon: '', pesel: '',
  postal_code: '', city: '', street: '', unit: '',
  notes: '', is_supplier: false, email: '',
  contact_person1: '', phone1: '', contact_person2: '', phone2: '',
  landline_phone: '', website: '', files_folder: ''
})
const addresses = ref([])
const selectedAddress = ref(null)
const isNew = computed(() => !route.params.id)
```

---

## Widok: `ContractFormView.vue`

**Layout (replika WinForms FormU4 — 4 rows):**

Dokładne rozmiary z Designer.cs:
- Row 0: 30px — belka info
- Row 1: 480px — nagłówek umowy (scrollable)
- Row 2: 200px — pozycje + warunki (split 50%/50%)
- Row 3: 30px — przycisk zapisu

Szczegółowy layout Row 1 (nagłówek):

```
┌─── Lewa kolumna (60%) ──────────────────┬─── Prawa (40%) ────────┐
│ Numer [S001/2026]  Typ [Umowa najmu ▼]  │ ┌─Kalendarz ──────────┐│
│ ☐ handlowiec [Kowalski ▼]              │ │   Marzec 2026       ││
│                                         │ │ Pn Wt Śr Czw Pt Sb ││
│ [Kontrahent] [___Firma ABC___]          │ │  1  2  3  4   5  6 ││
│ [Adres ust.] (text, opcja)              │ │ ...                 ││
│                                         │ ├─────────────────────┤│
│ ☐ Dostawa [combo adresów ▼]            │ │   Kwiecień 2026     ││
│ Adres: [ulica] [kod pocztowy] [miasto] [>>geo]   │ │ ...                 ││
│ RAO-P1-008: kod pocztowy auto-uzupełnia miasto │ │ ...                 ││
│ Współrzędne [________________]          │ └─────────────────────┘│
│                                         │                        │
│ ☐ Reprezentująca  Tel1 [________]       │ Osoba1 [____________]  │
│ ☐ Kontaktowa      Tel2 [________]       │ Tel1   [____________]  │
│                                         │ Osoba2 [____________]  │
│ Usługi dodatkowe [↺ Przywróć szablon]   │ Tel2   [____________]  │
│ ┌────────────────────────────────────┐  │ Email  [____________]  │
│ │ ☰ Transport    400zł-400zł [zł] ✅❌│  │                        │
│ │ ☰ Czyszcz.1  150zł-400zł [zł] ✅❌ │  │                        │
│ │ ☰ Tankowanie   200zł      [zł] ✅❌ │  │                        │
│ │ [+ Dodaj pozycję]                  │  │                        │
│ └────────────────────────────────────┘  │                        │
│ ┌─ Finanse ─────────────────────────┐   │ Oddział [__________▼]  │
│ │ Wartość     [    15 000,00 zł   ] │   │ Dni/tyg [6]            │
│ │ Przedpłata  [______] dok [_____] │   │                        │
│ │ Faktura     [______] dok [_____] │   │                        │
│ │ Pozostało   [    15 000,00 zł  ] │   │                        │
│ └───────────────────────────────────┘   │                        │
│ Uwagi ┌──────────────────────────┐      │                        │
│       └──────────────────────────┘      │                        │
│ ☐ Wydruk bez danych ☐ Ukryj adres dostawy na umowie (klient wpisze ręcznie) ☐ Podpisy wymagane na stronie 1 │                        │
└─────────────────────────────────────────┴────────────────────────┘
```

Row 2 (pozycje + warunki):

```
┌── Pozycje (50%) ───────────────┬── Warunki (50%) ──────────────┐
│ [?] [-] [+]                    │ [-] [+]                       │
│ ┌────────────────────────────┐ │ ┌──────────────────────────┐  │
│ │ Nazwa │Dni│ Dostawa│Dostaw.│ │ │Typ│Opis│ Ile│Op1 │Op2   │  │
│ │ Kop.  │30 │ 2026-03│      │ │ │ 2 │do 5│  5│5000│      │  │
│ └────────────────────────────┘ │ └──────────────────────────┘  │
└────────────────────────────────┴───────────────────────────────┘
```

Row 2.5 (rozliczenie umowy - RAO-P1-012):

```
┌─ Rozliczenie umowy — Koszt klienta vs Koszt firmy ─────────────────────────────┐
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │ Pozycja        │ Koszt klienta │ Koszt firmy │ Marża   │ Uwagi             │ │
│ │ Koparka 320    │ [15000.00]    │ [12000.00]  │ 3000.00 │ [____________]   │ │
│ │ Transport      │ [500.00]      │ [400.00]    │ 100.00  │ [____________]   │ │
│ │ Czyszczenie    │ [300.00]      │ [200.00]    │ 100.00  │ [____________]   │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│ Marża = koszt klienta - koszt firma (auto-calculated, green > 0, red < 0)       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Pozycje [+] otwiera `ArticlePicker.vue` (replika FormAwybor).**
**Warunki [+] otwiera `ConditionFormView.vue` (replika FormW).**

---

## Dialog: `ArticlePicker.vue`

```
Layout (replika WinForms FormAwybor):

┌──────────────────────────────────────────────────────┐
│ [szukaj ________________________________________]    │
│ ┌────────────────────────────────────────────────┐   │
│ │ Nazwa      │Nr rej.│Kategoria│Właściciel│Umowa │   │
│ │ ★Koparka 320│KAT-5 │Koparki  │RAO       │S001 │   │
│ │ Dźwig 40t  │DZW-12│Dźwigi   │RAO       │     │   │
│ └────────────────────────────────────────────────┘   │
│ ★ wiersz z Moccasin (#FFE4B5) = ma aktywną umowę    │
│                                                      │
│ Data dostawy  [2026-03-15]                           │
│ Liczba dni    [30]                                    │
│ Dostawca      [_______________▼]  (combo dostawców)  │
│                                                      │
│ [Duplikuj]              [Wybierz]  [Anuluj]          │
└──────────────────────────────────────────────────────┘
```

**Emits:** `@select({ articleId, deliveryDate, rentalDays, supplierId })`

---

## Komponent: `ServiceHourGrid.vue` (RAO-P1-014)

**Cel:** Ewidencja godzin pracy operatora dla umów typu "U" (usługa).

**Widoczność:** Tylko gdy `contract_type === 'U'` i pozycja jest wybrana.

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│ Ewidencja godzin operatora        [+ Dodaj wpis]    │
├──────────────────────────────────────────────────────┤
│ Data        │ od   │ do   │ Uwagi           │      │
│ [2026-03-15]│[08:00]│[16:00]│[Operator: Jan] │ [✕] │
│ [2026-03-16]│[08:00]│[16:00]│[Operator: Jan] │ [✕] │
└──────────────────────────────────────────────────────┘
```

**Funkcje:**
- Inline edit (data/time/notes)
- Auto-save na zmianę (change event)
- Delete button z potwierdzeniem
- Pusty state gdy brak wpisów

**Props:**
```typescript
interface Props {
  positionId: number
}
```

**Store:** `useServiceHourStore` (`frontend/src/stores/serviceHours.js`)

---

## Dialog: `ConditionFormView.vue`

```
Layout (replika WinForms FormW — 4 rows):

Row 0 (30px): [<prev] [>next] info_label  typ_stawki_combo
Row 1 (260px):
  ┌─ dane stawki ──────────────────────────────────┐
  │ Dni [30]     naliczanie [tygodniowo ▼]         │
  │              opłata za  [tydzień    ▼]         │
  │ Opis [__textarea_______________________________]│
  │                                                │
  │ Warunek [readonly_computed_text________________]│
  │                                                │
  │ [dodawanie progu] (toggle button)              │
  │ ☐ min [5] [-][+]   Okres [-] [5] [+]          │
  │                     Opłata1 [5000.00]          │
  │                ☐    Opłata2 [4000.00]          │
  │               [ Dodaj ]                        │
  └────────────────────────────────────────────────┘
Row 2 (fill):
  ┌─ warunki grid ─────────────────────────────────┐
  │ Typ│Opis       │Ile│Opłata1│Opłata2│Rozliczane│
  │ 2  │do 5 tyg   │  5│ 5000  │       │tygodniowo│
  └────────────────────────────────────────────────┘
Row 3 (30px): centered [ Zakończ ]
```

---

## Widok: `SettingsView.vue`

```
Layout (replika WinForms Konfiguracjacs — scrollable):

┌─ Dane firmy ─────────────────────────────────┐
│ Nazwa [___] Króka [___] NIP [___] REGON [___]│
│ Kod [___] Miasto [___] Ulica [___]           │
│ Nagłówek [___textarea___]                    │
│ Bank [___] Rachunek [___]                    │
│ Numeracja [1]  Folder [___]  Folder2 [___]   │
└──────────────────────────────────────────────┘
┌─ Usługi dodatkowe — Szablony ────────────────┐
│  ┌── Umowa najmu (S) ──┐ ┌── Umowa usługi (U)─┐│
│  └────────────────────┘ └───────────────────┘ │
│ (tabs przełączają widok szablonu)             │
│                                               │
│ ┌─────────────────────────────────────────┐   │
│ │☰│ Nazwa pozycji    │Od zł│Do zł│jed│ 👁 │   │
│ │─┼──────────────────┼─────┼─────┼───┼───│   │
│ │☰│ Transport        │ 400 │ 400 │zł │ ✅│   │
│ │☰│ Czyszcz. (drob.) │ 150 │ 400 │zł │ ✅│   │
│ │☰│ Czyszcz. (trudn.)│ 400 │1500 │zł │ ✅│   │
│ │☰│ Tankowanie       │ 200 │     │zł │ ✅│   │
│ │☰│ Ponadnorm. przest│ 200 │ 300 │zł/h│✅│   │
│ │☰│ Wezwanie serwis. │ 280 │     │zł │ ✅│   │
│ └─────────────────────────────────────────┘   │
│  ☰ = drag-to-reorder     👁 = toggle active   │
│  [+ Dodaj pozycję]  [🗑️ Usuń zaznaczone]       │
│                                               │
│  Podgląd tekstu (jak na umowie/PDF):          │
│  ┌─────────────────────────────────────────┐  │
│  │- Transport: 400.00 zł dostawa / odbiór  │  │
│  │- Czyszcz.: 150.00 zł - 400.00 zł        │  │
│  └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
┌─ Handlowcy ──────────────────────────────────┐
│ ┌─grid─────────────────────────────────────┐ │
│ │ Nazwa     │ Telefon   │ Aktywny          │ │
│ │ Kowalski  │ 500123456 │ ✅               │ │
│ └──────────────────────────────────────────┘ │
│ Nazwa [___]  Tel [___]  [Dodaj]              │
│ ☐ Pokaż nieaktywnych                        │
│ (context menu: toggle aktywność)             │
└──────────────────────────────────────────────┘
            [ Zapisz ]
```

---

## Komponent: `ReportsSection.vue` (sekcja Raporty)

> **Zaimplementowane:** 2026-05-18 | **RAO-P1-017**

### Tabs (główne)

| Tab | Klucz | Opis |
|-----|-------|------|
| Stan floty teraz | `live` | Donut chart + tabela aktualnie wynajętych maszyn |
| Analiza historyczna | `history` | Sub-taby: Ogólne + Kategorie |
| Eksplorator | `explorer` | Sub-taby: Wszystko / Maszyny / Usługi / Lokalizacje |

### Wizualne wyodrębnienie (RAO-P2-007)

Sekcja "Stan floty teraz" ma wizualnie wyodrębniony nagłówek z gradient tłem i lewym borderem w kolorze primary (`#1D2B53`). Subtitle jasno wskazuje że dane są "na dzień dzisiejszy — niezależne od filtrów datowych".

**CSS:**
```css
.current-status-header {
  background: linear-gradient(135deg, #f0f4ff 0%, #e8f0ff 100%);
  border-left: 4px solid var(--color-primary);
  padding: 16px 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.current-status-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
}

.current-status-subtitle {
  font-size: 13px;
  color: #718096;
  font-style: italic;
}
```

### Tab: Stan floty teraz (`live`)

- KPI cards: dostępnych maszyn, % wykorzystania floty
- Donut chart: Wynajęte vs Dostępne
- Tabela "Maszyny aktualnie wynajęte": **Maszyna | Nr wewnętrzny | Kategoria | Umowa | Kontrahent | Planowany zwrot**
  - `data-testid="live-rented-table"`
  - Kolumna `Kategoria` = `item.category_main` (RAO-P1-017)

### Tab: Analiza historyczna (`history`)

**Sub-taby:**
- `data-testid="history-subtabs"` — kontener sub-tabów
- `data-testid="history-subtab-general"` — Ogólne (dotychczasowe statystyki)
- `data-testid="history-subtab-categories"` — Kategorie (RAO-P1-017)

**Date presets** (wspólne dla obu sub-tabów):
- Ten miesiąc / Ten kwartał / Ten rok / Wszystko / 📅 Własny

#### Sub-tab: Ogólne
- KPI: przychód w okresie, top maszyna
- Bar chart: TOP 10 maszyn wg przychodu (poziomy, Chart.js)
- Tabela: usługi dodatkowe w okresie
- Tabela: lokalizacje — ranking

#### Sub-tab: Kategorie (RAO-P1-017)

```
Poziom kategorii: [Główna kategoria] [Podkategoria 1]
                   data-testid="category-level-main"  data-testid="category-level-sub1"

Loading / Error / Empty states ← OBOWIĄZKOWE

KPI row (max-width 700px):
  [Łączny przychód]  [Aktywnych kategorii]  [Dni wynajmu]

Bar chart: Kategorie wg przychodu TOP 15 (poziomy)
  canvas data-testid="category-bar-chart"

Tabela: data-testid="category-stats-table"
  Kategoria | Maszyny | Dni wynajmu | Umowy | Przychód | [bar progress]
```

**Dane z:** `GET /stats/by-category?level=main|sub1&date_from&date_to&include_archival=false`

**Store:** `statsStore.byCategoryData` (CategoryStatsResponse), `statsStore.loadingByCategory`

**Trigger ładowania kategorii:**
- Przełączenie na sub-tab Kategorie
- Zmiana poziomu (main ↔ sub1)
- Zmiana date presetu lub kliknięcie "Filtruj"

### Store: `useStatsStore` (stores/stats.js)

| Stan | Typ | Opis |
|------|-----|------|
| `byCategoryData` | `CategoryStatsResponse \| null` | RAO-P1-017 |
| `loadingByCategory` | `boolean` | loading dla /stats/by-category |

| Funkcja | Opis |
|---------|------|
| `fetchByCategory(level, dateFrom, dateTo, includeArchival)` | GET /stats/by-category |
