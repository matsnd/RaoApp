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
│   │   ├── usePagination.js         # Pagination helper
│   │   └── useFileDownload.js       # Pobieranie blob jako pliku przez <a download> (RAO-P2-018)
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

**Toolbar (górna belka):**

Przyciski toolbar (v-if="isEdit" = tylko przy edycji):
- ← — powrót do Dashboard
- ⎙ — Drukuj PDF (generateReport('contract'))
- 📄 — Protokół ZO (generateReport('protocol_zo'))
- ∑ — Przelicz wartość (recalcTotal)
- 💰 — Pobierz koszty z Fakturownia (handleFakturownia, mock data, active)
- [Zapisz] — button btn-primary btn-sm

**Fakturownia Integration (placeholder z mock data):**
- Przycisk 💰 aktywny, wywołuje handleFakturownia()
- Fakturownia store wywołuje backend API `/fakturownia/invoices?oid=`
- Backend client zwraca mock data (Koparka CAT 320 + Transport, 12400 zł)
- Alert z wynikami: liczba faktur i łączna kwota
- Backend mock mode: client.py zwraca sample data bez wywoływania zewnętrznego API
- Przygotowanie UI pod pełną integrację RAO-P2-012

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
│ RAO-P2-005: [>>geo] wywołuje POST /integrations/geocode (Nominatim) │ │ ...                 ││
│ Wynik geokodowania (latitude/longitude) zapisywany do formularza │ │ ...                 ││
│ Współrzędne [latitude, longitude - auto z geokoding] │ └─────────────────────┘│
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

> **RAO-P1-023 (2026-05-20):** Usunięto kolumnę "Rezerwacja" (stary system RAO-P1-015).
> Dostępność bazuje wyłącznie na datach umów przez `GET /articles/{id}/availability`.
> Dodano modal konfliktu przy wyborze zajętej maszyny.

```
Layout (modal wbudowany w ContractFormView.vue):

┌──────────────────────────────────────────────────────┐
│ [szukaj ________________________________________]    │
│ ┌────────────────────────────────────────────────┐   │
│ │ Nazwa │Nr rej.│Marka│Typ    │Dostępność│Akcje │   │
│ │ Kop.  │KAT-5 │CAT  │Sprzęt │🟢 Wolny  │ [⧉] │   │
│ │ Dźwig │DZW-12│Lieb.│Sprzęt │🔴 Zajęty │ [⧉] │   │
│ └────────────────────────────────────────────────┘   │
│ • Dostępność sprawdzana przez checkAvailability()    │
│   z exclude_contract_id przy edycji umowy            │
│ • [⧉] = duplikuj artykuł bezpośrednio do umowy      │
│                                                      │
│ [Anuluj]                                             │
└──────────────────────────────────────────────────────┘
```

**Conflict modal (RAO-P1-023)** — pojawia się gdy `is_available === false`:
```
┌──────────────────────────────────────────────────────┐
│ ⚠️ Maszyna zajęta                                    │
│ "Koparka 320" jest przypisana do:                    │
│ • Umowa S001/2026 — Firma XYZ (01.03 – 31.05.2026)  │
│                                                      │
│ [Anuluj]                    [Mimo to dodaj]          │
└──────────────────────────────────────────────────────┘
```

**Logika selectArticle():**
1. Brak dat umowy / artykuł-usługa → zamknij picker, dodaj bez sprawdzania
2. `checkAvailability()` → `is_available: true` → zamknij picker normalnie
3. `checkAvailability()` → `is_available: false` → pokaż conflict modal (picker zostaje otwarty)
4. [Mimo to dodaj] → zamknij oba (modal + picker), dodaj artykuł
5. [Anuluj] → zamknij tylko modal, picker pozostaje otwarty

**State (refs):** `showConflictModal`, `conflictList: ConflictingContract[]`, `pendingArticle: ArticlePickerItem | null`

**API:** `GET /articles/{id}/availability?date_from&date_to&exclude_contract_id` (opcjonalny param przy edycji)

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

**Zakładki:** Dane firmy | Handlowcy | Kategorie | Typy stawek | Zestawy usług | Fakturownia | Folder RAO


> **RAO-P2-019 (2026-05-30):** Zakl. Kategorie zastapiona drzewiastym widokiem: flatCategoryTree computed, fetchCategoriesTree() w store, inline edit, cascade subcat, addingSubcatParentId dla inline add.


> **RAO-P1-023 (2026-05-20):** Usunięto zakładkę "Rezerwacje maszyn" (RAO-P1-015).
> `ReservationsPanel.vue` i `ReservationsView.vue` zostały usunięte — ręczne rezerwacje zastąpione
> automatycznym sprawdzaniem konfliktów z dat umów (`GET /articles/{id}/availability`).

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

### Numer wewnętrzny maszyny (RAO-P2-008)

Pole `internal_number` jest w pełni zaimplementowane:

**Formularz artykułu (ArticleFormView.vue):**
- Pole input `internal_number` w formularzu edycji/nowego artykułu

**Article picker (ArticlePicker.vue):**
- Wyszukiwanie po `internal_number` (case-insensitive)
- Wyświetlanie `[nr wewnętrzny]` w wynikach wyszukiwania

**Raporty (ReportsSection.vue):**
- Kolumna "Nr wewnętrzny" w tabeli "Maszyny aktualnie wynajęte"
- Kolumna "Nr wewnętrzny" w tabeli wyników eksploratora
- Wyświetlanie `[nr wewnętrzny]` w wynikach wyszukiwania maszyn

**Backend (stats/router.py):**
- Parametr `internal_number` w endpointach:
  - `GET /stats/fleet-summary?internal_number=<str>`
  - `GET /stats/top-machines?internal_number=<str>`
  - `GET /stats/locations?internal_number=<str>`
  - `GET /stats/by-category?internal_number=<str>`
- Filtrowanie wyników po numerze wewnętrznym

### Statystyki per maszyna (RAO-P2-009)

**Backend:**
- Endpoint `/explorer/machines/{article_id}` z parametrami `date_from`, `date_to`
- Zwraca metryki: total_revenue, total_days, avg_daily, utilization_pct
- Zwraca historię wynajmów: rentals[] z contract_number, contractor_name, dates, days, revenue

**Frontend (ReportsSection.vue):**
- Zakładka "Maszyny" w Explorer tab
- Wyszukiwanie maszyny po nazwie lub nr wewnętrznym
- Panel szczegółów maszyny z metrykami:
  - Przychód w okresie
  - Dni wynajmu
  - Średni przychód/dzień
  - Wykorzystanie (%)
- Tabela historia wynajmów (umowa, kontrahent, daty, dni, kwota)

### Filtrowanie pozycji umowy po typie (RAO-P2-010)

**Backend (stats/router.py):**
- Endpoint `/stats/positions` z parametrami `type=machines|services|all`, `date_from`, `date_to`
- Zwraca `PositionStatsResponse` z:
  - total_revenue, total_machines_revenue, total_services_revenue
  - items[]: pozycje zagregowane per article (article_id, article_name, internal_number, is_service, category_main, revenue, rented_days, contracts_count, times_billed)

**Frontend (ReportsSection.vue):**
- Filtr "Typ pozycji" w sub-tab "Ogólne" (Analiza historyczna):
  - Pills: Wszystkie | Maszyny | Usługi
  - `v-if="historySubTab === 'general'"`
- Tabela pozycji z kolumnami: Nazwa, Nr wewnętrzny, Kategoria, Przychód, Dni, Umów, Razy
- Summary: Maszyny: X zł, Usługi: Y zł (zawsze widoczne, niezależnie od filtra)
- Store: `statsStore.positionsData` + `fetchPositions(type, from, to)`

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

---

## Folder dokumentów RAO (RAO-P3-013)

### SettingsView — sekcja Folder RAO

**Tab:** "Folder RAO" w SettingsView

**Cel:** Użytkownik raz wybiera folder na dysku — kolejne pobrania PDF trafiają automatycznie do podfolderów bez dialogu przeglądarki.

**Obsługiwane przeglądarki:** Chrome 86+, Edge 86+. Firefox i Safari — automatyczny fallback na `<a download>`.

**Subfoldery:**
- `Umowy/` — umowy (S_xxx, U_xxx)
- `Protokoly/` — protokoły ZO (PZO_xxx)
- `Zestawienia/` — raporty i zestawienia

**UI:**
- Informacja o obsłudze API przez przeglądarkę (`folderApiSupported`)
- Karta ze statusem aktualnego folderu (📁 ikona + nazwa / "Brak folderu")
- Przycisk "Wybierz folder RAO" / "Zmień folder" (`handlePickFolder`)
- Przycisk "Usuń konfigurację" (tylko gdy folder ustawiony, `handleClearFolder`)
- Komunikat sukcesu/błędu z auto-ukryciem po 5s

**Composables:**
- `useTargetFolder.js` — File System Access API + IndexedDB (`idb` lib)
  - `isSupported()` — feature detection
  - `pickFolder()` — dialog wyboru + zapis do IndexedDB
  - `saveToSubfolder(blob, filename, subfolder)` — zapis pliku
  - `verifyPermission(handle)` — sprawdzenie/prośba o permission
  - `clearStoredHandle()` — usunięcie handle z IndexedDB
- `useFileDownload.js` — rozszerzone o `saveToFolder(blob, cd, fallback, docType)`
  - Próbuje `saveToSubfolder` → jeśli false → fallback `downloadBlob`

**Persystencja:** `FileSystemDirectoryHandle` w IndexedDB (`rao-fs` DB, `handles` store)

---

## Integracja Fakturownia (RAO-P2-012)

### SettingsView — sekcja Fakturownia

**Tab:** "Fakturownia" w SettingsView

**Pola:**
- Toggle "Włącz integrację Fakturownia"
- Subdomena Fakturownia (text input, np. "toolsmart")
- API Token (password input, placeholder "Wklej token API")
- Aktualny token preview (tylko pierwsze 4 i ostatnie 4 znaki, np. "tk_****1234")

**Akcje:**
- "Zapisz ustawienia" — wywołuje `PUT /integrations/fakturownia/settings`
- Automatyczne fetch przy wejściu na tab (watch activeTab)
- Error handling: toast z komunikatem z backend

**Store:** `useFakturowniaStore` (stores/fakturownia.ts)

```typescript
interface FakturowniaSettings {
  id: number
  enabled: boolean
  api_token_preview: string | null
  domain_subdomain: string | null
  api_token_updated_at: string | null
  api_token_updated_by: number | null
}

async function fetchSettings()
async function updateSettings(payload: { enabled, api_token?, domain_subdomain? })
async function fetchProducts()
async function fetchInvoicesByContractId(contractId: number)
```

### ContractFormView — pole OID + guzik 💰

**Pole OID:**
- Lokalizacja: formularz danych kontraktu (po numerze umowy)
- Label: "OID (zamówienie Fakturownia)"
- Type: text input
- Placeholder: "np. 12345"
- Model: `form.oid`

**Guzik 💰:**
- Lokalizacja: toolbar (obok przycisków PDF, Protokół ZO, Przelicz)
- Widoczny tylko przy edycji umowy (`v-if="isEdit"`)
- Tooltip: "Pobierz koszty z Fakturownia"
- Akcja: `handleFakturownia()`

**Logika handleFakturownia:**
```typescript
async function handleFakturownia() {
  if (!isEdit.value) return
  if (!contractStore.current?.id) return
  await fakturowniaStore.fetchInvoicesByContractId(contractStore.current.id)
  // Alert z sumą faktur lub komunikat "Brak faktur"
}
```

**Response handling:**
- Jeśli faktury znalezione → alert z liczbą faktur i sumą
- Jeśli brak faktur → alert "Brak faktur dla tej umowy"
- Jeśli błąd → alert z komunikatem z backend (np. token nieważny)

### Store: `useStatsStore` (stores/stats.js)

| Stan | Typ | Opis |
|------|-----|------|
| `byCategoryData` | `CategoryStatsResponse \| null` | RAO-P1-017 |
| `loadingByCategory` | `boolean` | loading dla /stats/by-category |

| Funkcja | Opis |
|---------|------|
| `fetchByCategory(level, dateFrom, dateTo, includeArchival)` | GET /stats/by-category |

---

## UX/UI Improvements (RAO-P2-017)

> **Zaktualizowano:** 2026-05-19
> **Cel:** Poprawa UX/UI zgodnie z analizą wizyjną AI i design systemem Toolsmart

### LoginView.vue

**Zmiany:**
- Border-radius ustawiony na 12px dla karty, inputów i przycisku (zgodnie z `--border-radius-md`)
- Ikony w polach formularza: 👤 (login), 🔒 (password), 👁️/🙈 (show/hide password)
- Stany interaktywne: hover, focus, error z płynnymi transitionami
- Checkbox "Zapamiętaj mnie" dodany pod polami formularza
- Komunikat błędu zredesignowany: ⚠️ icon, czerwony border, większa czcionka (14px, weight 500)
- Animacja shake przy błędzie logowania
- Toggle show/hide password z ikoną
- Autofocus na pole login po błędzie

**Style:**
```css
.login-card {
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
}
.form-input {
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-border);
}
.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(29,43,83,0.1);
}
.form-input.error {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}
.btn-primary {
  background: var(--color-primary);
  border-radius: var(--border-radius-md);
}
.btn-primary:hover {
  background: var(--color-primary-dark);
}
```

### HomeView.vue (Dashboard)

**Zmiany:**
- Przyciski CTA (quick actions) w kolorze navy `#1D2B53` (`--color-primary`)
- Paleta alertów KPI zaktualizowana do CSS variables:
  - `--color-success` (ok)
  - `--color-warning` (warn)
  - `--color-error` (danger)
  - `--color-info` (info)
- Empty states z ilustracjami emoji:
  - Kończące się umowy: 📋
  - Dostawy: 🚚
  - Niewydrukowane umowy: ✅
- Wszystkie style zaktualizowane do CSS variables z design systemu Toolsmart

**Style:**
```css
.qa-primary {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
}
.qa-primary:hover {
  background: var(--color-primary-dark);
}
.kpi-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
}
.kpi-ok { border-left-color: var(--color-success); }
.kpi-warn { border-left-color: var(--color-warning); }
.kpi-danger { border-left-color: var(--color-error); }
.kpi-info { border-left-color: var(--color-info); }
```

### ContractFormView.vue

**Zmiany:**
- Pola pogrupowane w 4 sekcje/karty:
  1. **Dane podstawowe** (typ, numer, OID, okres umowy)
  2. **Kontrahent i adres dostawy** (wybór kontrahenta, adres)
  3. **Warunki finansowe** (handlowiec, oddział, wartość, przedpłata, faktura)
  4. **Kontakt i uwagi** (osoby kontaktowe, email, telefon, uwagi, opcje)
- **RAO-P3-007:** Pola `date_from`/`date_to` zastąpione komponentem `DateRangePicker.vue`
  - Biblioteka: `@vuepic/vue-datepicker`
  - Komponent: `frontend/src/components/shared/DateRangePicker.vue`
  - Tryb: range (2 kalendarze), brak time picker, locale=pl, auto-apply
  - Label: "Okres umowy (od — do) *"
  - Emity: `update:dateFrom`, `update:dateTo` → `form.date_from`, `form.date_to`
  - Walidacja: `v-if="!form.date_from"` → "Podaj datę od"
- Inline validation dla required fields (data od, kontrahent)
- Layout adresu dostawy poprawiony:
  - Select adresu w osobnym rzędzie
  - Kod pocztowy + miasto w jednym rzędzie
  - Uwagi dojazdowe w osobnym rzędzie
- Komunikaty błędów inline pod polami

**Style:**
```css
.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-heading);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.error-message {
  color: var(--color-error);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: var(--border-radius-md);
}
.field-error {
  color: var(--color-error);
  font-size: 12px;
  font-weight: 500;
}
.address-layout {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.address-row {
  display: flex;
  gap: 8px;
}
```

### style.css (Design System)

**Nowe CSS variables:**
```css
/* Error colors */
--color-error-bg: #FEF2F2;
--color-error-border: #FECACA;

/* Border radius */
--border-radius-sm: 8px;
--border-radius-md: 12px;
--border-radius-lg: 12px;
--border-radius-pill: 24px;
```

**Wszystkie style zaktualizowane do CSS variables zamiast hardcoded kolorów.**

---

## Widoki nieudokumentowane wcześniej (uzupełnienie — audit 2026-05-19)

### AdminView.vue — Panel administracyjny

**Route:** `/admin` | **requiresAdmin:** tak (tylko rola `admin`)

**Opis:** CRUD zarządzania użytkownikami systemu. Dostępny tylko dla administratorów.

**Funkcje:**
- Lista użytkowników z kolumnami: login, imię, nazwisko, rola, aktywny, ostatnie logowanie
- Dodawanie nowego użytkownika (modal z polami: login, hasło, first_name, last_name, role)
- Edycja użytkownika (modal edycji)
- Aktywacja/deaktywacja konta (PATCH `/admin/users/{id}/activate` / `/deactivate`)
- Force-reset hasła (POST `/admin/users/{id}/force-password-reset`)
- Badge: role `admin` → `badge-warning`, inne → `badge-info`

**API:** `GET /admin/users`, `POST /admin/users`, `PUT /admin/users/{id}`, `PATCH /admin/users/{id}/activate`, `PATCH /admin/users/{id}/deactivate`, `POST /admin/users/{id}/force-password-reset`

---

### CommissionView.vue — Raporty prowizji handlowców

**Route:** `/commissions` | **requiresAuth:** tak

**Opis:** Raport prowizji handlowców za zadany okres. Podsumowanie i tabela per handlowiec.

**Funkcje:**
- Filtrowanie po datach: `date_from` / `date_to` (inputy date)
- Karty podsumowania: łączny przychód, łączna prowizja, okres
- Tabela per handlowiec: nazwa, przychód, stawka %, kwota prowizji
- Przycisk "Drukuj" (window.print(), klasa `print-hide` ukrywa toolbar)

**API:** `GET /stats/commissions?date_from&date_to`

---

### WorkerView.vue — Pulpit operacyjny

**Route:** `/worker` | **requiresAuth:** tak

**Opis:** Pulpit dzienny dla operatora/pracownika. Pokazuje kluczowe informacje do codziennej pracy.

**Funkcje:**
- Kończące się umowy (filtry: 7d/14d/30d) — pobiera `GET /stats/expiring-contracts?days=N`
- Dostawy na dziś — pobiera `GET /stats/deliveries-today`
- Umowy niewydrukowane — pobiera `GET /stats/unprinted-contracts`
- Aktualne wynajmy — pobiera `GET /stats/currently-rented`
- Skeleton loading dla każdej sekcji
- Empty states z komunikatami gdy brak danych

**Layout:** Grid 2-kolumnowy, karty z ikonami emoji

---

### ChangePasswordView.vue — Zmiana hasła

**Route:** `/password` | **requiresAuth:** tak

**Opis:** Formularz zmiany własnego hasła przez zalogowanego użytkownika.

**Pola formularza:**
- `current_password` — aktualne hasło (required)
- `new_password` — nowe hasło (required, minlength: 6)
- `confirm_password` — powtórzenie nowego hasła (required)

**Walidacja:** `new_password === confirm_password` (client-side)
**API:** `PUT /auth/change-password`
**Po sukcesie:** Komunikat sukcesu inline, przycisk Anuluj → `/home`

---

### ResetPasswordView.vue — Reset hasła z tokenu

**Route:** `/reset-password?token=<token>` | **requiresAuth:** nie (publiczny)

**Opis:** Strona resetowania hasła po kliknięciu linku z emaila. Token odczytywany z query param.

**Pola formularza:**
- `new_password` — nowe hasło (required, min 6 znaków)
- `confirm_password` — powtórzenie (required)

**API:** `POST /auth/reset-password` z `{ token, new_password }`
**Po sukcesie:** Komunikat + redirect do `/login`

---

### HomeView.vue — Główna strona (KPI Dashboard)

**Route:** `/home` | **requiresAuth:** tak | **Default redirect:** `/` → `/home`

**Opis:** Główny ekran po zalogowaniu. Pokazuje kluczowe KPI i quick actions.

**KPI panele:**
- Maszyny w terenie (liczba aktywnych wynajmów)
- Kończące się umowy (w ciągu 7 dni)
- Dostawy na dziś
- Umowy niewydrukowane
- Umowy nieaktualne (edytowane po wydruku)

**Quick actions (przyciski navy `--color-primary`):**
- Nowa umowa → `/contracts/new`
- Kontrahenci → `/dashboard/contractors`
- Ustawienia → `/settings`

**Stany:** skeleton loading, empty state z emoji (📋 🚚 ✅)

**API:** `GET /stats/expiring-contracts`, `GET /stats/deliveries-today`, `GET /stats/unprinted-contracts`, `GET /stats/stale-print-contracts`, `GET /stats/currently-rented`

---

## Globalne funkcjonalności (AppLayout.vue)

### Pasek postępu NProgress (P3-010)
- Biblioteka: `nprogress` (niebieska belka `--color-accent-blue`, bez spinnera)
- Uruchamia się przy każdej zmianie trasy (`router.beforeEach` → `NProgress.start()`, `router.afterEach` → `NProgress.done()`)
- Konfiguracja: `{ showSpinner: false, speed: 300, minimum: 0.2 }`

### Keyboard shortcuts (P3-008)
- `Ctrl+N` → nowy rekord (kontekstowo: `ContractNew`, `ContractorNew`, `ArticleNew`)
- `Escape` → cofnij do poprzedniej strony (tylko gdy trasa kończy się na `/new` lub `/edit`)
- Guard: ignoruje gdy aktywny element to input/textarea/select lub gdy jest otwarte modal-overlay

---

## DashboardView — Empty state CTA (P3-009)

Puste tabele (brak rekordów) wyświetlają przycisk akcji:
- Umowy: "Brak umów — [+ Nowa umowa]" → `router.push({ name: 'ContractNew' })`
- Kontrahenci: "Brak kontrahentów — [+ Nowy kontrahent]" → `router.push({ name: 'ContractorNew' })`
- Artykuły: "Brak artykułów — [+ Nowy artykuł]" → `router.push({ name: 'ArticleNew' })`

---

## ConditionPanel — Auto-opis warunku (P3-006)

W modalu dodawania warunku:
- Przycisk `↻ auto` przy polu Opis generuje opis na podstawie: nazwa typu stawki, stawka 1 + jednostka, stawka 2, liczba okresów, minimum
- Format: `"Typ stawki, 500.00 zł/doba, do 5 dób, min. 1"`
- Watcher auto-wypełnia opis przy zmianach pól (tylko dla nowych warunków, nie dla edycji)
