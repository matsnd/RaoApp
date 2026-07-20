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
│   │   │   ├── AppSidebar.vue       # Lewy sidebar (Umowy/Kontrahenci/Maszyny/Statystyki/Prowizje/Ustawienia)
│   │   │   ├── AppToolbar.vue       # Górny toolbar (info + ? - + przyciski)
│   │   │   └── AppLayout.vue        # Sidebar + content wrapper
│   │   ├── shared/
│   │   │   ├── DataGrid.vue         # Reusable data grid (jak WinForms DataGridView)
│   │   │   ├── SearchFilter.vue     # Search input z debounce
│   │   │   ├── CalendarGrid.vue     # Kalendarz miesięczny (tabela 7x5)
│   │   │   ├── ConfirmDialog.vue    # Modal potwierdzenia (tak/nie)
│   │   │   ├── ContextMenu.vue      # Right-click menu
│   │   │   ├── DateRangePicker.vue  # Selektor dat od/do (legacy)
│   │   │   └── ContractPeriodPicker.vue # Selektor okresu umowy (data od + liczba dni)
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
        // section = 'contracts' | 'contractors' | 'articles' (DEPRECATED) | 'reports' | 'settings'
      },
      // --- Faza 4a (2026-07-11): nowe routingi machines / services / additional-services ---
      {
        path: 'machines',
        name: 'MachinesList',
        component: () => import('@/views/MachinesListView.vue')
      },
      {
        path: 'machines/new',
        name: 'MachineNew',
        component: () => import('@/views/MachineFormView.vue')
      },
      {
        path: 'machines/:id/edit',
        name: 'MachineEdit',
        component: () => import('@/views/MachineFormView.vue'),
        props: true
      },
      {
        path: 'services',
        name: 'ServicesList',
        component: () => import('@/views/ServicesListView.vue')
      },
      {
        path: 'services/new',
        name: 'ServiceNew',
        component: () => import('@/views/ServiceFormView.vue')
      },
      {
        path: 'services/:id/edit',
        name: 'ServiceEdit',
        component: () => import('@/views/ServiceFormView.vue'),
        props: true
      },
      {
        path: 'additional-services',
        name: 'AdditionalServicesList',
        component: () => import('@/views/AdditionalServicesListView.vue')
      },
      {
        path: 'additional-services/new',
        name: 'AdditionalServiceNew',
        component: () => import('@/views/AdditionalServiceFormView.vue')
      },
      {
        path: 'additional-services/:id/edit',
        name: 'AdditionalServiceEdit',
        component: () => import('@/views/AdditionalServiceFormView.vue'),
        props: true
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
│ Statys- │  ← sidebar-btn (section='analytics')
│ tyki    │
├─────────┤
│ Prowizje│  ← sidebar-btn (section='commissions')
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
      :class="['sidebar-btn', { active: activeSection === 'analytics' }]"
      @click="$emit('navigate', 'analytics')"
    >📊 Statystyki</button>
    <button
      :class="['sidebar-btn', { active: activeSection === 'commissions' }]"
      @click="$emit('navigate', 'commissions')"
    >Prowizje</button>
    <button
      :class="['sidebar-btn', { active: activeSection === 'settings' }]"
      @click="$emit('navigate', 'settings')"
    >Ustawienia</button>
  </nav>
</template>

<script setup>
// Refaktor (Faza 7, 2026-07-11): 'articles' → 'machines' (usługi/usługi dodatkowe
// mają osobne routingi /services, /additional-services — patrz AppLayout.vue handleNavigate)
const menuItems = [
  { section: 'contracts', label: 'Umowy' },
  { section: 'contractors', label: 'Kontrahenci' },
  { section: 'machines', label: 'Maszyny' },
  // { section: 'services', label: 'Usługi' },          // TODO: dodać link w sidebar
  // { section: 'additional-services', label: 'Usługi dodatkowe' }, // TODO: dodać link w sidebar
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
│  - articles: nazwa, rejestr., kategoria, właściciel  (DEPRECATED → /machines)
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
    { key: 'type', label: 'Typ', width: 80 },
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

**Lista umów — filtry i sortowanie (RAO-P2-022):**

- Sortowanie: `ORDER BY auto_number DESC` (najnowsze na górze) — po stronie backendu
- Filtr **statusu rozliczenia** (select): `Aktywne` (domyślnie, `is_settled=false`) | `Rozliczone` | `Wszystkie`
- Filtr **typ umowy**: Wszystkie typy | Umowy najmu (S) | Umowy usługi (U)
- Filtr **dat**: Data od / Data do
- Kolumna **Status**: `Aktywna` (niebieski badge) | `Przeterminowana` (czerwony) | `Rozliczona` (zielony)
- Wiersz `row-settled`: szare/wyciszone tło gdy `c.is_settled = true`

**Lista artykułów — filtr archiwalny (DEPRECATED — Faza 7 refaktor):**

> **⚠️ DEPRECATED (2026-07):** Sekcja `articles` w DashboardView jest DEPRECATED.
> Zastąpiona przez dedykowane widoki `MachinesListView.vue` (`/machines`),
> `ServicesListView.vue` (`/services`), `AdditionalServicesListView.vue` (`/additional-services`).
> Poniższe opisy pozostają jako dokumentacja legacy.
> Kolumna `is_archival` została usunięta — filtrowanie archiwalne niedostępne.


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
  articles: [  // DEPRECATED — patrz MachinesListView / ServicesListView
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
│ ☐ Reprezentująca  Tel1 [________]       │ Reprezentowany przez [____________]  │
│ ☐ Kontaktowa      Tel2 [________]       │ Tel1   [____________]  │
│                                         │ Osoba kontaktowa      [____________]  │
│ Opłaty dodatkowe [↺ Przywróć szablon]   │ Tel2   [____________]  │
│ ┌────────────────────────────────────┐  │ Email  [____________]  │
│ │ ☰ Transport    400zł-400zł [zł] ✅❌│  │                        │
│ │ ☰ Czyszcz.1  150zł-400zł [zł] ✅❌ │  │                        │
│ │ ☰ Tankowanie   200zł      [zł] ✅❌ │  │                        │
│ │ [+ Dodaj pozycję]                  │  │                        │
│ └────────────────────────────────────┘  │                        │
│ ┌─ Finanse ─────────────────────────┐   │ Oddział [__________▼]  │
│ │ Wartość z rozliczenia [read-only] │   │ Dni/tyg [6]            │
│ │ Przedpłata  [______] dok [_____] │   │                        │
│ │ Faktura     [______] dok [_____] │   │                        │
│ │ Pozostało   [    15 000,00 zł  ] │   │                        │
│ └───────────────────────────────────┘   │                        │
│ Uwagi ┌──────────────────────────┐      │                        │
│       └──────────────────────────┘      │                        │
│ ☐ Ukryj adres dostawy na umowie (klient wpisze ręcznie) ☐ Podpisy wymagane na stronie 1 │                        │
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
│ [?] [-] [+]                                                                    │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │ Pozycja        │ Koszt klienta │ Koszt firmy │ Marża   │ Uwagi             │ │
│ │ Koparka 320    │ [15000.00]    │ [12000.00]  │ 3000.00 │ [____________]   │ │
│ │ Transport      │ [500.00]      │ [400.00]    │ 100.00  │ [____________]   │ │
│ │ Czyszczenie    │ [300.00]      │ [200.00]    │ 100.00  │ [____________]   │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│ Marża = koszt klienta - koszt firma (auto-calculated, green > 0, red < 0)       │
│                                                                                 │
│ ┌─ Inicjalizacja rozliczeń ─────────────────────────────────────────────────┐ │
│ │ [📋 Pobierz z umowy]  [💰 Pobierz z Fakturownia]                          │ │
│ │                                                                                 │ │
│ │ RAO-P1-012: "Pobierz z umowy" wywołuje POST /settlements/contract/{id}/init │ │
│ │   Oblicza cost_client = unit_price * rental_days * quantity z pozycji umowy  │ │
│ │                                                                                 │ │
│ │ RAO-P2-012: "Pobierz z Fakturownia" wywołuje POST /settlements/contract/{id}/init-from-fakturownia │ │
│ │   Pobiera faktury z Fakturownia, mapuje pozycje przez fakturownia_product_id (1:N mapping) │ │
│ │   Mapowanie 3 tabel: machines, services, additional_services (refaktor Faza 7) │ │
│ │   Jeśli maszyna/usługa z mappingiem jest na umowie → automatycznie dodaje settlement z cost_client z faktury │ │
│ │   Semantyka 1:N: jeśli produkt FA jest przypisany do wielu maszyn/usług RAO, │ │
│ │   każdy z nich na umowie dostaje pełną wartość z faktury (multiplikacja OK) │ │
│ │                                                                                 │ │
│ │ Guzik "Pobierz z Fakturownia" jest nieaktywny jeśli Fakturownia nie jest skonfigurowana │ │
│ │ (brak enabled, domain_subdomain lub api_token_preview w ustawieniach)        │ │
│ └───────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Pozycje [+] otwiera `ArticlePicker.vue` (replika FormAwybor — wybór z `machines` table).**
**Warunki [+] otwiera `ConditionFormView.vue` (replika FormW).**

### RAO-P2-071: Inline editing pozycji (zero modali ustawień)

**Refactor 2026-07-05:** Usunięto modal pełnego formularza pozycji (`showPosModal`).
Pozycje umowy edytowane są wyłącznie inline w gridzie — jedynym dozwolonym modalem
dla pozycji jest `ArticlePicker` (wybór maszyny) oraz `ConflictModal` (konflikt dostępności).

**Flow dodawania pozycji:**
1. User klika `+ Dodaj pozycję` → otwiera się `ArticlePicker` (modal wyboru maszyny)
2. User wybiera maszynę → `ArticlePicker` się zamyka
3. W gridzie pojawia się nowy wiersz (`showNewPosRow`) w trybie edycji inline (podświetlony)
4. User edytuje pola inline (Tab/Enter → następna komórka)
5. Enter w ostatniej komórce LUB klik `✓` → `saveNewPosRow()` → `POST /contracts/{id}/positions`

**Flow edycji istniejącej pozycji:**
1. User klika wiersz LUB `✎` → `startEditPos(pos)` → wiersz przechodzi w tryb edit (`editingPosId`)
2. User edytuje pola inline
3. Enter LUB `✓` → `saveInlinePos()` → `PUT /contracts/{id}/positions/{posId}`
4. Esc LUB `✕` → `cancelInlinePos()` → powrót do display mode

**Pattern (skopiowany z Service Fees):**
- `editingPosId: ref<number | null>` — id edytowanej pozycji (null = brak)
- `editingPosData: ref<PosInlineData>` — bufor edycji
- `showNewPosRow: ref<boolean>` — czy pokażać wiersz "nowa pozycja"
- `newPosData: ref<PosInlineData>` — bufor nowej pozycji
- `articlePickerMode: ref<'new' | 'edit'>` — cel wyboru z ArticlePicker

**Grid pozycji — kolumny (zależne od `contract_type`):**

| Kolumna | Najem (`S`) | Usługa (`U`) | Display mode | Edit mode |
|---------|-------------|--------------|-------------|-----------|
| # | tak | tak | idx+1 | idx+1 (lub `*` dla new) |
| Maszyna / Usługa | `Maszyna` | `Usługa` | nazwa (read-only) | nazwa + `✎` → `reopenArticlePickerForEdit` |
| Typ najmu | tak | — | tekst | `<input type="text">` |
| Dni | tak | — | liczba | `<input type="number" min="0">` |
| Ilość | tak | tak | liczba | `<input type="number" min="1">` |
| Jednostka | — | tak | tekst | read-only (`godzina`) |
| Opis | — | tak | tekst | `<input type="text">` |
| Dostawca | tak | — | nazwa (read-only) | nazwa + `✎` → `openSupplierPickerForEdit` |
| Data dost. | tak | — | data PL | `<input type="date">` |
| Warunki | tak | tak | badge z licznikiem | badge (klik → `ConditionPanel`) |
| Akcje | tak | tak | `✎` edit / `✕` usuń | `✓` zapisz / `✕` anuluj |

**Empty state:** `Brak pozycji na tej umowie. [Dodaj pierwszą maszynę]` dla najmu, `Brak usług na tej umowie. [Dodaj pierwszą usługę]` dla usługi.

**Helper text nad gridem:** `Pozycje umowy` / `Usługi` + `Kliknij wiersz aby edytować • Enter = zapisz • Esc = anuluj` + `[+ Dodaj pozycję]` / `[+ Dodaj usługę]`

**Zachowane modale (dozwolone):**
- `ArticlePicker` — wybór maszyny (modal wyboru, nie ustawień)
- `ConflictModal` — konflikt dostępności maszyny (RAO-P1-023)
- `SupplierPicker` — wybór dostawcy (modal wyboru, nie ustawień)
- `ConfirmModal` — potwierdzenie usunięcia (zastępuje `confirm()`)

**Usunięte:**
- `showPosModal` — modal pełnego formularza pozycji (105 linii template)
- `posForm`, `editingPos`, `selectedArticleName`, `articleAvailability` — stan starego modala
- `savePosition()`, `editPosition()` — funkcje starego modala
- Wszystkie `alert()` i `confirm()` w komponencie → zastąpione toastami / `ConfirmModal`

**Toast system:** `useToastStore` z `@/stores/toast` — success/error/info/warning.
Auto-dismiss po 4s (error 6s). Renderowany przez `AppToast.vue` (top-right).

---

## Dialog: `ArticlePicker.vue`

> **RAO-P1-023 (2026-05-20):** Usunięto kolumnę "Rezerwacja" (stary system RAO-P1-015).
> Dostępność bazuje wyłącznie na datach umów przez `GET /machines/{id}/availability` (refaktor: było `GET /articles/{id}/availability`).
> Dodano modal konfliktu przy wyborze zajętej maszyny.
>
> **P1-126 (2026-07-13):** Picker ładuje listę **po** ustawieniu `form.contract_type` z danych edycji
> (poprzednio `onMounted` ładował `/machines` zanim `Object.assign(form.value, data)` ustawiało `contract_type='U'`,
> więc umowy usługi pokazywały sprzęt). Dodano `watch(form.value.contract_type)` i `watch(showArticlePicker)`
> odświeżające `articlePickerList` przez `loadArticlePickerList()` (endpoint `/machines` lub `/services`).
> Tabela pickera ukrywa kolumny `Nr rej.`, `Marka`, `Zewnętrzna`, `Dostępność` dla `isService` i pokazuje `Opis`.
> `ServiceListItem` zwraca `is_service=True`, `brand=None`, `registration_no=None`, `is_external=False`
> (wyrównanie kształtu z `MachineListItem`).

```
Layout (modal wbudowany w ContractFormView.vue):

┌──────────────────────────────────────────────────────┐
│ [szukaj ________________________________________]    │
│ ┌────────────────────────────────────────────────┐   │
│ │ Nazwa │Nr rej.│Marka│Typ    │Dostępność│Akcje │   │  ← S (rental)
│ │ Kop.  │KAT-5 │CAT  │Sprzęt │🟢 Wolny  │ [⧉] │   │
│ │ Dźwig │DZW-12│Lieb.│Sprzęt │🔴 Zajęty │ [⧉] │   │
│ └────────────────────────────────────────────────┘   │
│ • isService: kolumny Nr rej./Marka/Zewnętrzna/        │
│   Dostępność ukryte, zamiast nich kolumna "Opis"      │
│ • Badge Typ: "Usługa" (badge-warning) / "Sprzęt"      │
│   (badge-info) — z a.is_service                       │
│ • Dostępność sprawdzana przez checkAvailability()    │
│   z exclude_contract_id przy edycji umowy            │
│ • [⧉] = duplikuj maszynę bezpośrednio do umowy      │
│                                                      │
│ [Anuluj]                                             │
└──────────────────────────────────────────────────────┘
```

**Conflict modal (RAO-P1-023 + Phase 4)** — pojawia się gdy `is_available === false`:
```
┌──────────────────────────────────────────────────────┐
│ ⚠️ Maszyna zajęta                                    │
│ "Koparka 320" jest przypisana do:                    │
│ • Umowa S001/2026 — Firma XYZ (01.03 – 31.05.2026)  │
│ • Rezerwacja Firma XYZ (10.04 – 15.04.2026) — serwis│
│                                                      │
│ [✅ Zatwierdź i usuń rezerwacje (1)]   ← gdy rezerw.  │
│ [✅ Zatwierdź i nie usuwaj rezerwacji]  tego samego   │
│ [Mimo to dodaj]                        kontrahenta    │
│ [Anuluj]                                             │
└──────────────────────────────────────────────────────┘
```

**3 opcje akcji (Phase 4):**
- Gdy w `conflicting_reservations` są rezerwacje dla **tego samego kontrahenta** co `form.contractor_id`:
  1. **Zatwierdź i usuń rezerwacje** — `confirmAndDeleteReservations()` → `DELETE /reservations/{id}` dla każdej, potem `applySelectedArticle()`
  2. **Zatwierdź i nie usuwaj rezerwacji** — `confirmConflictSelection()` (dodaje mimo konfliktu)
- Gdy brak rezerwacji tego samego kontrahenta (lub brak rezerwacji w ogóle):
  3. **Mimo to dodaj** — `confirmConflictSelection()`
- Rezerwacje z `contractor_id === null` (bez kontrahenta) NIE są traktowane jako "tego samego kontrahenta".

**Logika selectArticle():**
1. Brak dat umowy / usługa (service_id) → zamknij picker, dodaj bez sprawdzania
2. `checkAvailability()` → `is_available: true` → zamknij picker normalnie
3. `checkAvailability()` → `is_available: false` → pokaż conflict modal (picker zostaje otwarty), populuj `conflictList` + `reservationConflictList`
4. [Zatwierdź i usuń rezerwacje] → usuń rezerwacje tego samego kontrahenta, zamknij oba, dodaj maszynę
5. [Zatwierdź / Mimo to dodaj] → zamknij oba (modal + picker), dodaj maszynę
6. [Anuluj] → zamknij tylko modal, picker pozostaje otwarty

**State (refs):** `showConflictModal`, `conflictList: ConflictingContract[]`, `reservationConflictList: ConflictingReservation[]` (z `contractor_id`/`contractor_name`), `pendingArticle: ArticlePickerItem | null` (refaktor: wybór z `machines` table)
**Computed (Phase 4):** `sameContractorReservations` (filtr po `form.contractor_id`), `hasSameContractorReservations`

**API:** `GET /machines/{id}/availability?date_from&date_to&exclude_contract_id` (opcjonalny param przy edycji), `DELETE /reservations/{id}` (opcja usuwania)

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

**Zakładki:** Dane firmy | Handlowcy | Kategorie | Typy stawek | Zestawy usług dodatkowych | Fakturownia | Foldery PDF (P2-004)

> **Placeholdery $1/$2 w opisach opłat (2026-07-12):** Wszystkie pola "Opis"/"Tekst na umowie" w:
> - Zestawach usług dodatkowych (SettingsView — szablony w presetach)
> - Formularzu usługi dodatkowej (AdditionalServiceFormView)
> - Grid opłat dodatkowych w umowie (ContractFormView)
>
> obsługują placeholdery `$1` (→ kwota od / amount_from / default_amount) i `$2` (→ kwota do / amount_to).
> Pod polem opisu wyświetla się podgląd na żywo z podmienionymi kwotami.
> Wspólna logika: `composables/useFeeDescription.ts` (`formatFeeDescription`, `FEE_DESCRIPTION_HINT`).

> **P2-004 (2026-07-11):** Nowa zakładka "Foldery PDF" — auto-zapis PDF do folderów klienta przez File System Access API (Chrome/Edge). 4 foldery: `report_main` (umowy główny), `protocol_main` (protokoły główny), `report_gdansk` (umowy Gdańsk), `protocol_gdansk` (protokoły Gdańsk). Persistencja `directoryHandle` w IndexedDB. Fallback Firefox/Safari → zwykły download. Composable: `usePdfFolders.ts`.
>
> **RAO-TECH-003 (2026-07-11):** Usunięto zakładkę "Folder RAO" (stary pojedynczy folder). Konsolidacja → "Foldery PDF" (per-oddział). Composable `useTargetFolder.js` usunięty, `useFileDownload.js` używa `usePdfFolders`.


> **RAO-P2-019 (2026-05-30):** Zakl. Kategorie zastapiona drzewiastym widokiem: flatCategoryTree computed, fetchCategoriesTree() w store, inline edit, cascade subcat, addingSubcatParentId dla inline add.


> **RAO-P1-023 (2026-05-20):** Usunięto zakładkę "Rezerwacje maszyn" (stary system RAO-P1-015).
> `ReservationsPanel.vue` zostało usunięte — ręczne rezerwacje zastąpione
> automatycznym sprawdzaniem konfliktów z dat umów (`GET /machines/{id}/availability`).
>
> **UPDATE (2026-07-11):** `ReservationsView.vue` został ponownie dodany w Phase 3 (RAO-P1-015)
> jako nowy, niezależny widok kalendarza rezerwacji (`/reservations`). Patrz sekcja poniżej.
>
> **Refaktor (Faza 7, 2026-07-11):** Rezerwacje używają `machine_id` (nie `article_id`).
> `machine_reservations` table referencjonuje `machines.id`.

```
Layout (replika WinForms Konfiguracjacs — scrollable):

┌─ Dane firmy ─────────────────────────────────┐
│ Nazwa [___] Króka [___] NIP [___] REGON [___]│
│ Kod [___] Miasto [___] Ulica [___]           │
│ Nagłówek [___textarea___]                    │
│ Bank [___] Rachunek [___]                    │
│ Numeracja [1]                                 │
└──────────────────────────────────────────────┘
┌─ Opłaty dodatkowe — Szablony ────────────────┐
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

## Komponent: `ReportsSection.vue` (sekcja Raporty) — USUNIĘTY

> **Zaimplementowane:** 2026-05-18 | **RAO-P1-017**
> **Usunięte:** 2026-07-02 (Frontend-3 cleanup) — funkcje wchłonięte przez `AnalyticsView.vue` + `stores/analytics.ts`.
> Sidebar nie emituje już `section='reports'`; `DashboardView.vue` nie renderuje sekcji `reports`.
> Route `/dashboard/reports` nie istnieje — tile w `HomeView.vue` kieruje do `/analytics`.

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

**Formularz maszyny (MachineFormView.vue):**
- Pole input `internal_number` w formularzu edycji/nowej maszyny
- Pola techniczne (RAO-P1-026): `reach_m` (Zasięg m), `capacity_t` (Udźwig t), `accessories` (Dodatkowe wyposażenie)

**Machine picker (ArticlePicker.vue — refaktor: wybór z `machines` table):**
- Wyszukiwanie po `internal_number` (case-insensitive)
- Wyświetlanie `[nr wewnętrzny]` w wynikach wyszukiwania

**Raporty (ReportsSection.vue):**
- Kolumna "Nr wewnętrzny" w tabeli "Maszyny aktualnie wynajęte"
- Kolumna "Nr wewnętrzny" w tabeli wyników eksploratora
- Wyświetlanie `[nr wewnętrzny]` w wynikach wyszukiwania maszyn

### Auto-fill PNA + panel gmina/powiat/wojewodztwo (RAO-P1-008 rozszerzenie)

**Frontend (`ContractFormView.vue`):**
- Pole "Kod pocztowy" (`postal_code`) na `@blur` wywołuje `onPostalCodeBlur()`
- Endpoint: `GET /integrations/postal-codes/{code}` → `{code, city, voivodeship, powiat, gmina}`
- Auto-fill pola "Miasto" (sugestia — pole pozostaje edytowalne, NIE read-only)
  - Pomija auto-fill jeśli użytkownik ręcznie edytował miasto (`cityManuallyEdited` flag)
- Read-only panel pod polami PNA+Miasto (widoczny tylko gdy `pnaInfo.found === true`):
  ```
  ┌─ Wypełnione z PNA 00-001 ─────────────┐
  │ Gmina: Warszawa • Powiat: Warszawa • Woj: mazowieckie │
  └─────────────────────────────────────────┘
  ```
- Loading state: spinner w polu Miasto podczas lookup (`pnaLoading` ref, klasa `.input-loading`)
- Error handling (inline, pod PNA):
  - 404 → "Nie znaleziono kodu {code} w bazie. Wpisz miasto ręcznie."
  - Inne błędy → "Nie udało się pobrać danych PNA. Wpisz miasto ręcznie."
- `data-testid`: `contract-postal-code`, `contract-city`, `pna-spinner`, `pna-error`, `pna-info-panel`
- Style wyłącznie przez zmienne CSS z `style.css` (`--color-bg-light`, `--color-border`, `--color-text-muted`, `--color-primary`, `--color-error`, `--border-radius-sm`, `--font-size-sm`, `--font-size-xs`)

### Tabela lokalizacji — kolumny gmina/powiat/wojewodztwo + composite :key

**Frontend (`ReportsSection.vue`):**
- Tabela "Lokalizacje — ranking w okresie" (sub-tab Ogólne):
  - Dodano kolumny: Gmina, Powiat, Województwo (muted, font-size-sm, klasa `.muted-cell`)
  - `:key` zmieniony z `loc.city` → `loc.postal_code || loc.city` (composite key — naprawia duplikat klucza Vue gdy wiele PNA dla jednego miasta)
- Tabela "Lokalizacje" w panelu serviceDetails (sub-tab Usługi):
  - Dodano kolumny: PNA, Gmina, Powiat, Województwo
  - `:key` zmieniony z `loc.city` → `loc.postal_code || loc.city`
- Tabela "Ranking miast" w Explorer → Lokalizacje:
  - Dodano kolumny: Gmina, Powiat, Województwo
  - Wyszukiwarka obsługuje teraz też PNA (nie tylko miasto)

### BC break: drill-down po PNA (Explorer → Lokalizacje)

**Frontend (`ReportsSection.vue`):**
- `pickLocation(loc)` przyjmuje cały obiekt (zamiast `city` string) — wydobywa `postal_code` (fallback `city`)
- `loadLocationDetails(identifier)` wywołuje `GET /explorer/locations/{postal_code}` (zamiast `/{city}`)
- Nowy ref `selectedLocationPostal` — przechowuje PNA wybranego drill-down
- Nagłówek panelu szczegółów wyświetla miasto + PNA (muted)
- Watchery `explorerPeriod` / `explorerCustomFrom` / `explorerCustomTo` reloadują po `selectedLocationPostal || selectedLocation`
- Wyszukiwarka (`onLocationSearchInput`) filtruje po `city` OR `postal_code`

**Backend (stats/router.py):**
- Parametr `internal_number` w endpointach:
  - `GET /stats/fleet-summary?internal_number=<str>`
  - `GET /stats/top-machines?internal_number=<str>`
  - `GET /stats/locations?internal_number=<str>`
  - `GET /stats/by-category?internal_number=<str>`
- Filtrowanie wyników po numerze wewnętrznym

### Statystyki per maszyna (RAO-P2-009)

**Backend:**
- Endpoint `/explorer/machines/{machine_id}` z parametrami `date_from`, `date_to` (refaktor: było `article_id`)
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
  - items[]: pozycje zagregowane per machine/service (machine_id/service_id, name, internal_number, is_service, category_main, revenue, rented_days, contracts_count, times_billed)

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
[ℹ️ Banner historyczny] ← RAO-P2-021: zawsze widoczny na górze sekcji Kategorie
  data-testid="history-banner"
  "Raporty kategorii zawierają dane historyczne zaimportowane z poprzedniej aplikacji.
   Maszyny i umowy są uwzględniane w statystykach historycznych."

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

**Dane z:** `GET /stats/by-category?level=main|sub1|sub2|sub3&date_from&date_to&category_main[]&category_sub1&category_sub2&article_type`

**Store:** `statsStore.byCategoryData` (CategoryStatsResponse), `statsStore.loadingByCategory`

**Trigger ładowania kategorii:**
- Przełączenie na sub-tab Kategorie
- Zmiana poziomu (main ↔ sub1) gdy drilldownPath.length === 0
- Zmiana date presetu lub kliknięcie "Filtruj"
- Zmiana shared filters (articleType, categoryMains)
- Kliknięcie wiersza z drilldownable kategorią

**RAO-P1-026: Drilldown (4 poziomy):**
- `drilldownPath: ref([])` — ścieżka drilldown, np. `['Wozidła', 'Wózki widłowe']`
- Kliknięcie wiersza z `categoryHasChildren(name) === true` → `drillDown(name)` → dodaje do ścieżki
- Breadcrumb nad KPI row: `Wszystkie / Wozidła / Wózki widłowe` — klikalne (drillTo)
- Level selector (main/sub1) widoczny tylko gdy `drilldownPath.length === 0`
- `sortedCategoryItems` computed z sortKey/sortDir — sortowanie po kliknięciu nagłówka ▲▼

**RAO-P1-026: Shared filter bar** (widoczny dla categories + timeline):
- Rodzaj: `sharedArticleType` (all/machine/service)
- Kategoria: multi-select dropdown z `statsStore.categoriesList`

**RAO-P1-026: Sub-tab "📅 Historia"** (`historySubTab === 'timeline'`):
- `data-testid="timeline-panel"`
- Granularity toggle: Miesiące/Lata (`granularity: ref('month')`)
- Bar chart: `periodBarCanvas` ref, `renderPeriodBarChart()`, max 8 serii wg kategorii
- Pivot table: `pivotData` computed — wiersze=kategorie, kolumny=okresy, sumy
  - Kliknięcie kategorii → `selectPivotCategory(name)` → filtruje `sharedCategoryMains`
- Loading: `statsStore.loadingByPeriod`, Error: `errorByPeriod`, Empty state
- **Dane z:** `GET /stats/by-period?granularity&date_from&date_to&category_main[]&article_type`

### Store: `useStatsStore` (stores/stats.js)

**RAO-P1-026 rozszerzenia:**

| Stan | Typ | Opis |
|------|-----|------|
| `loadingByPeriod` | `boolean` | loading dla /stats/by-period |
| `byPeriodData` | `ByPeriodResponse\|null` | dane historyczne per-period |
| `categoriesList` | `CategoriesListNode[]` | drzewo kategorii (dla dropdown) |

| Funkcja | Endpoint |
|---------|----------|
| `fetchByCategory(level, df, dt, categoryMains[], catSub1, catSub2, articleType)` | GET /stats/by-category (URLSearchParams) |
| `fetchByPeriod(granularity, df, dt, categoryMains[], articleType)` | GET /stats/by-period |
| `fetchCategoriesList()` | GET /stats/categories-list |

---

## Folder dokumentów RAO (RAO-P3-013) — ARCHIVED

> **RAO-TECH-003 (2026-07-11):** Ta sekcja została zarchiwizowana. Zakładka "Folder RAO" (pojedynczy folder) została usunięta w ramach konsolidacji z "Foldery PDF" (per-oddział, RAO-P2-004). Composable `useTargetFolder.js` usunięty. `useFileDownload.js` używa teraz `usePdfFolders.savePdf()` dla umów/protokołów, z fallback `<a download>` dla zestawień.

**Historia (archiwum):**
- ~~Tab: "Folder RAO" w SettingsView~~ — usunięta
- ~~Composable: `useTargetFolder.js`~~ — usunięty
- ~~Subfoldery: Umowy/, Protokoly/, Zestawienia/~~ — zastąpione przez 4 foldery per-oddział

Patrz: "Foldery PDF (RAO-P2-004)" poniżej dla aktualnego systemu.

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

### ContractFormView — guzik 💰 (Pobierz koszty z Fakturownia)

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
| `fetchByCategory(level, dateFrom, dateTo)` | GET /stats/by-category |

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
  1. **Dane podstawowe** (typ, numer, OID Fakturownia, okres umowy)
  2. **Kontrahent i adres dostawy** (wybór kontrahenta, adres)
  3. **Warunki finansowe** (handlowiec, oddział, wartość, przedpłata, faktura)
  4. **Kontakt i uwagi** (osoby kontaktowe, email, telefon, uwagi, opcje)
- **RAO-P2-058:** Pole `oid` (OID Fakturownia, opcjonalny)
  - Input text, placeholder "(auto = numer umowy)", pattern `[A-Za-z0-9\-/_]+`, maxlength=40
  - Help text: "Puste = użyj numeru umowy. Tylko litery, cyfry, -, /, _."
  - Backend: `oid = contract.oid if contract.oid else contract.number` (hybrydowe)
  - Walidacja backend: `^[A-Za-z0-9\-/_]+$` (OidStr Annotated type)
- **RAO-P2-004 (+ decyzja 2026-07-08):** Pola `date_from`/`date_to` zastąpione komponentem `ContractPeriodPicker.vue`
  - Komponent: `frontend/src/components/shared/ContractPeriodPicker.vue`
  - Input 1: `date_from` (date picker) - data rozpoczęcia umowy
  - Input 2: `Liczba dni` (number input, min=1) - **dni robocze** (nie kalendarzowe)
  - Przyciski 5/6/7: wybór dni roboczych w tygodniu (`working_days_per_week`)
  - Computed: `date_to` kalendarzowo z `Data od + Liczba dni roboczych + dni/tyg`
  - Display: "Okres umowy: {date_from_pl} – {date_to_pl} ({N} dni roboczych / {M} dni kalendarzowych)"
  - Emity: `update:dateFrom`, `update:dateTo` → `form.date_from`, `form.date_to`
  - `v-model:working-days-per-week` → `form.working_days_per_week`
  - Przycisk "Wpisz datę końcową": przełącza w tryb ręczny z pickiem `date_to`
  - W trybie ręcznym pole `Liczba dni` jest disabled i computed z kalendarza
  - Label: "Okres umowy *"
  - Walidacja: `v-if="!form.date_from"` → "Podaj datę od"
- **RAO-P3-007 (legacy):** Poprzednio używany `DateRangePicker.vue` (z @vuepic/vue-datepicker) - zachowany jako fallback
- **2026-05-21:** Wyświetlanie błędów walidacji
  - Błędy walidacji z backendu (Pydantic) są parsowane z tablicy JSON
  - Format: `Kod pocztowy: String should have at least 6 characters, Miasto: String should have at least 1 character`
  - Nazwy pól są mapowane na język polski (postal_code → Kod pocztowy, city → Miasto)
  - Funkcja `handleSave()` w `ContractFormView.vue` parsuje `e.response?.data?.detail`
- Inline validation dla required fields (data od, kontrahent)
- **RAO-P2-005:** Inline dodawanie kontrahenta z formularza umowy
  - W pickerze kontrahentów przycisk "➕ Dodaj nowego kontrahenta" (prominent CTA)
  - Gdy wyszukiwanie nie zwraca wyników, wyświetlany jest komunikat "Brak wyników dla {search}"
  - Przycisk otwiera modal "Nowy kontrahent" z formularzem inline
  - Formularz zawiera wszystkie wymagane pola kontrahenta:
    - Pełna nazwa * (required)
    - Nazwa skrócona
    - NIP
    - REGON, PESEL
    - Adres główny: kod pocztowy, miejscowość, ulica, nr lokalu
    - Kontakt: osoba kontaktowa 1/2, telefon 1/2, email, telefon stacjonarny
    - Uwagi
  - Po zapisie:
    - Nowy kontrahent jest dodany do lokalnej listy pickerList
    - Kontrahent jest automatycznie wybrany (selectContractor)
    - Modal jest zamykany
    - Formularz jest resetowany
  - Walidacja: nazwa kontrahenta jest wymagana
- **RAO-P1-001 (2026-07-08):** Checkbox is_external w Machine picker modal
  - Kolumna "Zewnętrzna" w tabeli wyników picker
  - Badge ✓ (is_external=true) lub — (is_external=false)
  - Backend pole `is_external` istnieje w `machines` table (refaktor: było `articles`)
- **RAO-P1-002 (2026-07-08):** Checkbox "Ręczny adres" w sekcji Adres dostawy
  - Checkbox: "Ręczny adres (wyłącz auto-fill z PNA/Nominatim)"
  - Gdy zaznaczony → pola postal_code/city disabled
  - Auto-fill z PNA/Nominatim skipowane w trybie ręcznym
  - Placeholder textarea: "Uwagi dojazdowe (opcjonalnie) — numer działki, bramka, wskazówki dojazdu"

- **RAO-P1-100 (2026-07-08):** Zmiany w sekcji "Opłaty dodatkowe", cenniku i trybie usługi
  - **Szybki wybór zestawu**
    - Najem (`contract_type === 'S'`): 2 przyciski [Diesel] [Elektryk] + dropdown z pełną listą presetów
    - Usługa (`contract_type === 'U'`): brak szybkich przycisków (tylko dropdown z presetami)
    - Przyciski wywołują `applyHardcodedFeePreset('diesel' | 'elektryk')` — usuwają obecne usługi i tworzą nowe wiersze `ContractServiceFee` przez `POST /contracts/{id}/service-fees`
    - Wspólny zestaw (najem): Transport, Czyszczenie, Tankowanie, Przestój, Wezwanie serwisowe
    - Diesel = pełny zestaw (Transport + przegląd 150 zł + czyszczenie + tankowanie + przestój + serwis); Elektryk = pełny zestaw (Transport + przegląd 35 zł + reszta). P2-007: "Wspólne" usunięte — Diesel/Elektryk są pełnymi zestawami, nie dodatkami.
    - Wspólny zestaw (usługa): Transport, Praca operatora
    - Dropdown wywołuje `applyPresetWithConfirm` → `POST /contracts/{id}/service-fees/apply-preset?preset_id={id}&replace=true`
    - Nowa umowa zaczyna z pustą sekcją usług (operator wybiera preset ręcznie)
  - **P2-002 (2026-07-11): Banner sugestii zestawu** — gdy `contractStore.current?.suggested_preset` jest nie-null ('diesel'|'electric'), banner nad sekcją "Opłaty dodatkowe" (`data-testid="suggested-preset-banner"`) sugeruje odpowiedni zestaw. **NIE auto-apply** — tylko informacja dla operatora.
    - Wszystkie przyciski/dropdown są disabled gdy `is_settled = true`
  - **Grid usług — tylko aktywne**
    - Wyświetlane są tylko pozycje z `is_active = true` (computed `activeServiceFees`)
    - Szablon ładuje wszystkie pozycje jako aktywne; operator może dezaktywować/usunąć
  - **Kolumna "Tekst na umowie (zamiast kwot)"** (zamiast "Opis")
    - Tooltip: "Jeśli wypełnione — na PDF drukuje się ten tekst zamiast kwot. Np. «Transport: odbiór własny», «wycena indywidualna»"
    - Formatowanie: `formatDescription(description, amount_from, amount_to, name)` — wszystkie kwoty w `zł`, nigdy `$`
    - Wartości kwotowe w `description` używają placeholderów `$1` (amount_from) i `$2` (amount_to) — frontend zamienia je na sformatowane kwoty z polskim separatorem tysięcy i przecinkiem (`1 200,00 zł`)
    - Przykład: `description = "$1 dostawa / $2 odbiór"` + `name = "Transport"` + `amount_from = 1200` + `amount_to = 1200` → `Transport: 1 200,00 zł dostawa / 1 200,00 zł odbiór`
    - **P1-113 (2026-07-12):** Preset data (`applyHardcodedFeePreset`) i seedy (`seed_demo_data.py`) używają `$1`/`$2` placeholderów (nie hardcoded kwot). Migracja DB podmieniająca placeholdery → hardcoded kwoty usunięta z `main.py`. Placeholdery są zachowane w DB i podmieniane w locie w UI (`formatDescription`) i PDF (`_resolve_fee_description`).
  - **Usunięto combobox artykułów-usług** — wiersze usług dodatkowych są edytowane ręcznie (nazwa, kwota od/do, jednostka, tekst na umowie)
  - **P1-120 (2026-07-12): Combobox z additional_services** — pole "Nazwa usługi" w nowym wierszu i w edycji inline jest comboboxem (select) z listy `additional_services` (ładowane w `onMounted` przez `additionalServiceStore.fetchList`). Po wyborze: `additional_service_id` = id, `name` = `display_name || name`, `amount_from` = `default_amount` (jeśli puste). Opcja "✎ własna nazwa…" przełącza na wolny tekst (`additional_service_id = null`). Z punktu widzenia usera jedyna zmiana to combobox zamiast wolnego tekstu — reszta bez zmian.
  - **Podgląd PDF live** pod gridem usług
    - Wyświetla tylko aktywne pozycje w formacie `- {name}: {description lub kwoty}`
    - Używa CSS variables, bez `v-html`
  - **Przedpłata na górze formularza**
    - Pole `prepayment_amount` edytowalne w sekcji "Warunki finansowe"
    - Pole `prepayment_document` ukryte (martwe, nie trafia na PDF)
    - RAO-P1-103: pole "Faktura (zł)" + `invoice_document` usunięte (kwoty faktur z Fakturowni)
    - "Pozostało" = `total - prepayment` (zwykły kolor tekstu, pogrubione — nie czerwony)
  - **Segmented control dni/tyg** w komponencie `ContractPeriodPicker`
    - Przyciski 5/6/7 (inline buttons)
    - Active state: `btn-primary`, inactive: `btn-secondary`
    - Decyduje ile dni w tygodniu jest roboczych (5: pn–pt, 6: pn–sb, 7: wszystkie)
    - Bindowane przez `v-model:working-days-per-week="form.working_days_per_week"` (default 6)
  - **Ukrycie nr wewnętrznego w trybie usługi (`contract_type === 'U')**
    - InlineMachineForm: pole "Nr wewnętrzny" widoczne tylko gdy `form.contract_type !== 'U'`

- **RAO-P1-100 (ConditionPanel):** Widełki cenowe, wierny podgląd PDF i podział najem/usługa
  - **Props:** `mode: 'rental' | 'service'` (lub fallback `contractType`) — steruje kolumnami, jednostką i szablonami
  - **Główne źródła warunków:** `Z ostatniej umowy`, `Zastosuj cennik`
  - **Kolumny gridu warunków (zależne od `mode`):**
    - `Od (dni)` / `Od (godz.)` dla najmu/usługi
    - `Do (dni)` / `Do (godz.)` dla najmu/usługi
    - `Stawka (zł)` — `rate1`
    - `Jednostka` — `billing_label` (`doba` dla najmu, `godzina` dla usługi)
    - `Minimum` — `minimum`
    - `Akcje` — edytuj / usuń
  - **Szablon widełek** — select **Gotowe przedziały…** z opcjami:
    - Najem: `1 - 3 dni`, `1 - 8 dni`, `1 - 2 / 3 - 5 / >5 dni`, `>3 dni`, `>8 dni`, `>16 dni`, `>20 dni`, `1 dzień`
    - Usługa: `do 2 godzin`, `do 3 godzin`, `do 8 godzin`, `0 - 2 / 3 - 8 / >8 godzin`, `każda kolejna`
    - Wywołanie dodaje jeden lub więcej wierszy warunków z uzupełnionym `period_from`/`period_to`/`period_count` i placeholderem opisu (operator wpisuje stawkę)
  - **Wierny podgląd PDF** pod tabelą warunków
    - Sortuje warunki po `period_from`, pokazuje `description` lub buduje opis jak PDF (`{od}-{do} dni/godzin - {stawka} / {jednostka}`)
    - Nigdy nie znika pól; stawki puste pokazują `0,00 zł` do uzupełnienia
  - Walidacja ciągłości przedziałów inline: `Luka: warunek X-Y, następny A-B (brak Y+1)`
  - Edycja gridu jest zablokowana gdy `is_settled = true` (w tym `select` przedziałów, inputy, akcje).

  - Obsługa błędów: wyświetlanie błędów z backendu (e.response?.data?.detail)
  - Pre-fill: jeśli wyszukiwany termin wygląda jak nazwa (nie jest liczbą), jest używany jako domyślna nazwa
- **RAO-P2-006:** Inline dodawanie maszyny z formularza umowy
  - W pickerze maszyn przycisk "➕ Dodaj nową maszynę" (prominent CTA)
  - Gdy wyszukiwanie nie zwraca wyników, wyświetlany jest komunikat "Brak wyników dla {search}"
  - Przycisk otwiera modal "Nowa maszyna" z formularzem inline
  - Formularz zawiera wszystkie wymagane pola maszyny:
    - Nazwa maszyny * (required)
    - Typ zasilania (diesel/electric/other)
    - Checkbox: Maszyna zewnętrzna (nie wliczana do floty własnej)
    - Nr wewnętrzny, Nr rejestracyjny, Nr seryjny
    - Wartość odtworzeniowa (zł)
    - Marka, Model
    - Dane techniczne: Zasięg (m), Udźwig (t), Dodatkowe wyposażenie
    - Kategoria (kaskadowa: główna → podrzędna 1 → podrzędna 2)
    - Filia
    - Min. dni najmu
    - Opis, Uwagi
  - Po zapisie:
    - Nowa maszyna jest dodana do lokalnej listy articlePickerList
    - Maszyna jest automatycznie wybrana (selectArticle)
    - Modal jest zamykany
    - Formularz jest resetowany
  - Walidacja: nazwa maszyny jest wymagana
  - Obsługa błędów: wyświetlanie błędów z backendu (e.response?.data?.detail)
  - Pre-fill: jeśli wyszukiwany termin wygląda jak nazwa (nie jest liczbą), jest używany jako domyślna nazwa
  - Pre-fill is_service: ustawiane na true jeśli typ umowy to 'U' (umowa usługi)
  - Kaskada kategorii: 3-poziomowa (główna → podrzędna 1 → podrzędna 2)
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
- Tabela per handlowiec: nazwa, marża (baza prowizji), stawka %, kwota prowizji
- Przycisk "Drukuj" (window.print(), klasa `print-hide` ukrywa toolbar)
- **P1-123 Faza 2: drill-down umów handlowca** — przycisk "Umowy →" w wierszu
  handlowca otwiera `DrillDownDrawer` (współdzielony z `AnalyticsView`) z listą
  umów: numer, kontrahent, okres, przychód (cost_client), koszt firmy
  (cost_company), zarobek (marża), stawka, prowizja. Prowizja liczona
  WYŁĄCZNIE od rzeczywistych rozliczeń — umowy bez kompletnego settlementu
  są pomijane (brak fallbacku do szacunkowego przychodu).
  KPI w nagłówku drawera: łączny przychód, koszt firmy, zarobek, prowizja.
  Zmiana zakresu dat w widoku nadrzędnym odświeża otwarty drawer.

**API:**
- `GET /stats/commissions?date_from&date_to` — lista per handlowiec
- `GET /stats/commissions/{salesperson_id}/contracts?date_from&date_to` — drill-down umów (P1-123)

---

### ArchiveView.vue — Archiwum danych historycznych (RAO-P2-062 Faza 2)

**Route:** `/archive` | **requiresAuth:** tak | **requiresAdmin:** częściowo (edycja kategorii — admin)

**Opis:** Read-only przegląd danych historycznych (legacy umowy/maszyny przeniesione do tabel `archive_*` w Fazie 0). Wartości są szacunkowe (cennik × dni), nie z systemu rozliczeń. Jedyny write to edycja kategorii (admin).

**Sidebar:** Przycisk "📦 Archiwum" w `AppSidebar.vue` — wyraźny dział główny z pomarańczowym separatorem (2px) + label "ARCHIWUM (szacunkowe)" + border-left na przycisku. Oddzielone od sekcji głównej (Umowy/Kontrahenci/Maszyny/Pulpit/Statystyki/Prowizje/Raporty) i od sekcji konta (Ustawienia/Admin/Hasło/Wyloguj).

**Banner ostrzegawczy** (góra widoku):
> ⚠️ Archiwum — dane historyczne (szacunkowe). Wartości pochodzą z cenników sprzed migracji, nie z systemu rozliczeń.

**Kreska na wartościach szacunkowych:** Wszystkie wartości szacunkowe (`.est-value`) są **przekreślone** (`text-decoration: line-through` w kolorze warning) + suffix `[szac.]` — wizualnie oddziela dane historyczne od rzeczywistych.

**4 zakładki:**

1. **Umowy** (`activeTab='contracts'`) — `GET /archive/contracts` (paginacja 50, filtry: search, contract_type S/U, date_from, date_to)
   - Grid: Numer, Typ (badge S/U), Kontrahent, Data od, Data do, Pozycji, Wartość szac. (z suffix `[szac.]`), Status (Rozliczona/Nierozliczona badge)
   - Klik wiersza → rozwija panel szczegółów: `GET /archive/contracts/{id}` (kontrahent, adres dostawy, okres, osoba kontaktowa, zaliczka, faktura szac., pozycje z warunkami, opłaty dodatkowe, rozliczenia)

2. **Maszyny** (`activeTab='articles'`) — `GET /archive/articles` (paginacja 50, filtry: search, category_id) — legacy endpoint, dane historyczne z `archive_articles`
   - Grid: Nazwa, Nr wewn., Kategoria (dropdown — `PATCH /archive/articles/{id}/category`, admin), Kontraktów count, Wartość wymiany
   - Zmiana kategorii przez `<select>` → `PATCH /archive/articles/{id}/category` z `category_id`

3. **Statystyki** (`activeTab='stats'`) — `GET /archive/stats/summary` + `/top-machines` + `/by-category` + `/by-city`
   - Filtry dat: date_from, date_to + przycisk "Odśwież"
   - Karta podsumowania: liczba umów, liczba pozycji, przychód szacunkowy
   - Top maszyny (limit 10): artykuł, kontraktów count, dni wynajmu, przychód szac. — **wiersze klikalne** (`.drill-row` z hover + ▸ strzałką), hint "Kliknij wiersz, aby zobaczyć umowy" w nagłówku
   - Per kategoria: kategoria, kontraktów, pozycji, przychód szac.
   - ROI maszyny (opcjonalne): `GET /archive/stats/machine-roi?article_id=` — przychód szac. / wartość wymiany = ROI %; przycisk "Pokaż umowy ▸" otwiera drill-down (legacy param: `article_id` — archive endpointy zachowują starą nazwę)
   - **Miasta** (limit 20): `GET /archive/stats/by-city` — miasto, kontraktów, pozycji, kodów poczt., przychód szac. — wiersze klikalne (drill-down)
   - **Drill-down drawer** (`<Teleport to="body">`, 60% szerokości, slide-in z prawej):
     - Otwierany przez `openDrillDown(type, id, name, contractsCount, days, revenue)` z wierszy Top maszyny / Miasta / przycisku ROI
     - Header: tytuł ("Umowy z maszyną: X" / "Umowy w mieście: Y") + subtitle (liczba umów, dni, przychód szac.) + przycisk ✕
     - Search bar: filtr po numerze/kontrahencie (enter / "Szukaj" / "↺" clear)
     - Tabela umów: Numer, Kontrahent, Okres, Dni, Wartość szac., Miasto (gdy type='city') — klik wiersza → `drillDownToContract(id)` (zamyka drawer, przełącza na zakładkę Umowy, otwiera szczegóły)
     - Loading (skeleton 5 wierszy pulse), Error (retry), Empty (📋 + komunikat), Footer z paginacją (50/strona)
     - Zamykanie: ✕, klik poza drawerem (overlay), **Esc** (globalny keydown listener w `onMounted`/`onUnmounted`)
     - Style w osobnym **non-scoped** `<style>` bloku (Vue 3 nie aplikuje scoped attrs do treści teleportowanej do `<body>`)
     - `reloadDrillDown()` → `archiveStore.fetchContractsForDrillDown({ article_id | city, search, date_from, date_to, page, per_page:50 })` (legacy: archive używa `article_id`)

4. **Kategorie** (`activeTab='categories'`) — `GET /archive/categories/tree` + CRUD (admin)
   - Read-only dla non-admin (drzewo kategorii bez akcji edycji/usuwania)
   - Admin: dodawanie/edycja/usuwanie kategorii (jak wcześniej)
   - Drzewo kategorii (flatten z depth indent)
   - Dodaj kategorię: `POST /archive/categories` (name, code, parent_id, level auto-z parent)
   - Edytuj: `PUT /archive/categories/{id}` (rename, code)
   - Usuń: `DELETE /archive/categories/{id}` (z confirm, tylko gdy pusta)
   - Non-admin widzi "Sekcja dostępna tylko dla administratora"

**Store:** `frontend/src/stores/archive.ts` (Pinia, composition API) — mirror endpointów `/archive/*`, typy TS zgodne z `backend/archive/schemas.py`

**Styl:** `--color-bg-light` tło, banner z `--color-warning` border-left, badge `[szac.]` przy kwotach

**API:** wszystkie endpointy pod `/rao/api/archive/*` (auth wymagany, admin dla category CRUD + article category PATCH). Archive endpointy zachowują legacy nazwy (`article_id`, `archive_articles`) — są to tabele historyczne, nie podlegające refaktorowi Fazy 7.

---

### StatsView.vue — Statystyki (RAO-P2-060 Faza 2) — USUNIĘTY

> **Usunięte:** 2026-07-02 (Frontend-3 cleanup) — funkcje wchłonięte przez `AnalyticsView.vue` + `stores/analytics.ts`.
> Route `/stats` jest teraz `redirect: '/analytics'` (backward compat dla bookmarków).
> Plik `frontend/src/stores/stats.js` usunięty (był używany wyłącznie przez StatsView i ReportsSection — oba usunięte).
> Sidebar: przycisk "📊 Statystyki" emituje `section='analytics'` → `router.push('/analytics')`.

**Route:** `/stats` → redirect `/analytics` | **requiresAuth:** tak

Następca: patrz sekcja `AnalyticsView.vue` poniżej.

---

### WorkerView.vue — Pulpit operacyjny

**Route:** `/worker` | **requiresAuth:** tak

**Opis:** Pulpit dzienny dla operatora/pracownika. Pokazuje kluczowe informacje do codziennej pracy.

**Funkcje:**
- Kończące się umowy (filtry: 7d/14d/30d) — pobiera `GET /stats/expiring-contracts?days=N`
- Dostawy na dziś — pobiera `GET /stats/deliveries-today`
- Umowy niewydrukowane — pobiera `GET /stats/unprinted-contracts`
- Nieaktualny wydruk — pobiera `GET /stats/stale-print-contracts`
- Przeterminowane umowy — pobiera `GET /stats/overdue-contracts`
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

### ArticleFormView.vue — Formularz artykułu (RAO-P1-026) — DEPRECATED (Faza 7 refaktor)

> **⚠️ DEPRECATED (2026-07):** `ArticleFormView.vue` jest DEPRECATED — zastąpiony przez
> `MachineFormView.vue` (`/machines/:id/edit`), `ServiceFormView.vue` (`/services/:id/edit`),
> `AdditionalServiceFormView.vue` (`/additional-services/:id/edit`).
> Route `/articles/new` i `/articles/:id/edit` pozostają jako backward-compat shim.
> Poniższa dokumentacja opisuje stan legacy (przed refaktor).

**Route:** `/articles/new` | `/articles/:id/edit` | **requiresAuth:** tak

**Opis:** Pełnoekranowy formularz tworzenia i edycji artykułu (maszyny/narzędzia/usługi).

**Pola formularza:**
- `name` — Nazwa artykułu * (wymagana)
- `article_type` — Typ artykułu (select: machine/vehicle/tool/service)
- `is_service` — checkbox "Artykuł jest usługą"
- `internal_number` — Nr wewnętrzny
- `registration_no` — Nr rejestracyjny
- `serial_no` — Nr seryjny
- `replacement_value` — Wartość odtworzeniowa (zł)
- `brand` — Marka
- `model` — Model
- **Sekcja "Dane techniczne"** (RAO-P1-026):
  - `zasieg_m` — Zasięg (m), number, min=0, step=0.1, opcjonalne, null gdy puste
  - `udzwig_t` — Udźwig (t), number, min=0, step=0.1, opcjonalne, null gdy puste
  - `dodatki` — Dodatkowe wyposażenie, textarea rows=3, opcjonalne, null gdy puste
  - `power_type` — Typ zasilania (select: diesel/electric/other, P2-002, `data-testid="article-power-type"`, default 'other')
- `category_id` — Kategoria (kaskadowy picker 3-poziomowy)
- `owner_id` — Właściciel/dostawca (picker kontrahentów)
- `rental_days` — Min. dni najmu
- `branch_id` — Filia (select)
- `description` — Opis (textarea)
- `notes` — Uwagi (textarea)
- **Sekcja "Integracja Fakturownia"** (RAO-P2-058):
  - `fakturownia_product_id` — Produkt Fakturownia (select z `fakturowniaStore.products`, opcjonalny, default null = brak mapowania)
  - Opcje: `— brak mapowania —` + lista produktów z FA (name + code + price_net)
  - Source: `useFakturowniaStore.fetchProducts()` → `GET /integrations/fakturownia/products` (live API call, bez cache)
  - Empty state: "Brak produktów w Fakturownia — dodaj produkty na {domain}.fakturownia.pl"
  - Error state: `fakturowniaStore.error` wyświetlany pod polem

**Layout sekcji "Dane techniczne":**
- `zasieg_m` + `udzwig_t` — grid 2 kolumny (`form-row-2`)
- `dodatki` — pełna szerokość poniżej

**Null handling:** Puste pola number → `null` (nie `0`). Pattern: `if (!payload.x) payload.x = null`

**Edit mode:** `Object.assign(form.value, data)` automatycznie wypełnia wszystkie pola z API.

**Store:** `useArticleStore` (`stores/articles.js`) — `fetchOne`, `create`, `update`, `duplicate`

> **Phase 5 (2026-07):** Sekcja "Rezerwacje maszyny" (RAO-P2-066) **usunięta** z ArticleFormView.
> Zarządzanie rezerwacjami przeniesione do osobnego widoku `ReservationsView.vue` (Phase 3 — pełny CRUD: kalendarz + lista + modal).
> Usunięto: template sekcji + modal dodawania, `useReservationsStore` import, `reservationsStore.fetchForArticle()` w `loadArticle`, refs (`showReservationModal`, `reservationSaving`, `reservationError`, `reservationForm`), computed `activeReservations`, funkcje (`openReservationForm`, `closeReservationForm`, `formatDate`, `addDay`, `saveReservation`, `deleteReservation`), CSS `.reservations-section`.

---

### MachinesListView.vue — Lista maszyn (NOWY — Faza 4a, 2026-07-11)

**Route:** `/machines` | **requiresAuth:** tak

**Opis:** Pełnoekranowa lista maszyn budowlanych (zastępuje sekcję `articles` w DashboardView dla maszyn). Tylko maszyny (`machines` table, dawniej `articles WHERE is_service=FALSE`).

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│ AppToolbar: info: Maszyny          [?] [-] [+]       │
├──────────────────────────────────────────────────────┤
│ [search...] [Kategoria ▼]                              │
├──────────────────────────────────────────────────────┤
│ DataGrid: Nazwa | Nr wew. | Nr rej. | Marka |         │
│          Kategoria | Zasilanie | Aktywna umowa       │
├──────────────────────────────────────────────────────┤
│ Empty: "Brak maszyn — [+ Nowa maszyna]"               │
└──────────────────────────────────────────────────────┘
```

**Filtry:**
- Search (nazwa, nr wewnętrzny, nr rejestracyjny)
- Kategoria (select z `categories`)

**Kolumny DataGrid:** Nazwa (sortable), Nr wew. (sortable), Nr rej. (sortable), Marka (sortable), Kategoria, Zasilanie (diesel/electric/other), Aktywna umowa

**Akcje:**
- `[+]` → `router.push({ name: 'MachineNew' })`
- Double-click → `router.push({ name: 'MachineEdit', params: { id } })`
- `[-]` → ConfirmDialog → `DELETE /machines/{id}`
- Context menu: Edytuj, Usuń, Duplikuj (`POST /machines/{id}/duplicate`)

**Store:** `useMachinesStore` (`stores/machines.js`) — `fetchList`, `remove`, `duplicate`
**API:** `GET /machines?search&category_id&page&per_page`

---

### MachineFormView.vue — Formularz maszyny (NOWY — Faza 4a, 2026-07-11)

**Route:** `/machines/new` | `/machines/:id/edit` | **requiresAuth:** tak

**Opis:** Pełnoekranowy formularz tworzenia i edycji maszyny budowlanej (zastępuje `ArticleFormView.vue` dla maszyn).

**Pola formularza:**
- `name` — Nazwa maszyny * (wymagana)
- `internal_number` — Nr wewnętrzny
- `registration_no` — Nr rejestracyjny
- `serial_no` — Nr seryjny
- `replacement_value` — Wartość odtworzeniowa (zł)
- `brand` — Marka
- `model` — Model
- **Sekcja "Dane techniczne":**
  - `reach_m` — Zasięg roboczy (m), number, min=0, step=0.1, opcjonalne
  - `capacity_t` — Udźwig (t), number, min=0, step=0.1, opcjonalne
  - `accessories` — Dodatkowe wyposażenie, textarea
  - `power_type` — Typ zasilania (select: diesel/electric/other, default 'other')
- `category_id` — Kategoria (kaskadowy picker 3-poziomowy)
- `owner_id` — Właściciel/dostawca (picker kontrahentów)
- `branch_id` — Filia (select)
- `is_external` — Checkbox "Maszyna zewnętrzna" (nie wliczana do floty własnej)
- `description` — Opis (textarea)
- `notes` — Uwagi (textarea)
- **Sekcja "Integracja Fakturownia":**
  - `fakturownia_product_id` — Produkt Fakturownia (select, opcjonalny)
- **Sekcja "Cenniki rozliczenia"** (tylko w trybie edycji):
  - Lista cenników (presetów) per-maszyna — patrz `machine_rate_presets` w `01_database.md`
  - API: `GET/POST /settings/machines/{machine_id}/rate-presets`

**Store:** `useMachinesStore` (`stores/machines.js`) — `fetchOne`, `create`, `update`, `duplicate`
**API:** `GET/POST/PUT/DELETE /machines`, `POST /machines/{id}/duplicate`

---

### ServicesListView.vue — Lista usług zwykłych (NOWY — Faza 4a, 2026-07-11)

**Route:** `/services` | **requiresAuth:** tak

**Opis:** Lista usług zwykłych (contract_type='U', dawniej `articles WHERE is_service=TRUE`).

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│ AppToolbar: info: Usługi           [?] [-] [+]       │
├──────────────────────────────────────────────────────┤
│ [search...]                                          │
├──────────────────────────────────────────────────────┤
│ DataGrid: Nazwa | Aktywna umowa                       │
├──────────────────────────────────────────────────────┤
│ Empty: "Brak usług — [+ Nowa usługa]"                 │
└──────────────────────────────────────────────────────┘
```

**Kolumny DataGrid:** Nazwa (sortable), Aktywna umowa (computed)
**P2-006 (2026-07-12):** Usunięto kolumny "Nr wew." i "Kategoria" (backend nie ma `category_id`/`branch_id` w `services`).

**Akcje:**
- `[+]` → `router.push({ name: 'ServiceNew' })`
- Double-click → `router.push({ name: 'ServiceEdit', params: { id } })`
- `[-]` → ConfirmDialog → `DELETE /services/{id}`

**Store:** `useServicesStore` (`stores/services.js`) — `fetchList`, `remove`
**API:** `GET /services?search&page&per_page`

---

### ServiceFormView.vue — Formularz usługi zwykłej (NOWY — Faza 4a, 2026-07-11)

**Route:** `/services/new` | `/services/:id/edit` | **requiresAuth:** tak

**Opis:** Formularz tworzenia i edycji usługi zwykłej (contract_type='U').

**Pola formularza:**
- `name` — Nazwa usługi * (wymagana)
- `description` — Opis (textarea)
- `notes` — Uwagi (textarea)
- **P2-006 (2026-07-12):** Usunięto pola Kategoria i Filia (backend nie ma `category_id`/`branch_id` w `services`).

**Store:** `useServicesStore` (`stores/services.js`) — `fetchOne`, `create`, `update`
**API:** `GET/POST/PUT/DELETE /services`

---

### AdditionalServicesListView.vue — Lista usług dodatkowych (NOWY — Faza 4a, 2026-07-11)

**Route:** `/additional-services` | **requiresAuth:** tak

**Opis:** Lista usług dodatkowych (katalog opłat dodatkowych: transport, czyszczenie, tankowanie itp.). Zastępuje referencję `service_fee_templates.article_id → articles`.

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│ AppToolbar: info: Usługi dodatkowe [?] [-] [+]       │
├──────────────────────────────────────────────────────┤
│ [search...]                                          │
├──────────────────────────────────────────────────────┤
│ DataGrid: Nazwa                                        │
├──────────────────────────────────────────────────────┤
│ Empty: "Brak usług dodatkowych — [+ Nowa]"            │
└──────────────────────────────────────────────────────┘
```

**Kolumny DataGrid:** Nazwa (sortable)
**P2-005 (2026-07-12):** Usunięto kolumny "Nr wew." i "Kategoria" (backend nie ma `category_id`/`branch_id` w `additional_services`). Tylko Nazwa.

**Akcje:**
- `[+]` → `router.push({ name: 'AdditionalServiceNew' })`
- Double-click → `router.push({ name: 'AdditionalServiceEdit', params: { id } })`
- `[-]` → ConfirmDialog → `DELETE /additional-services/{id}`

**Store:** `useAdditionalServicesStore` (`stores/additional_services.js`) — `fetchList`, `remove`
**API:** `GET /additional-services?search&page&per_page`

---

### AdditionalServiceFormView.vue — Formularz usługi dodatkowej (NOWY — Faza 4a, 2026-07-11)

**Route:** `/additional-services/new` | `/additional-services/:id/edit` | **requiresAuth:** tak

**Opis:** Formularz tworzenia i edycji usługi dodatkowej (katalog opłat).

**Pola formularza:**
- `name` — Nazwa * (wymagana, np. "Transport", "Czyszczenie")
- `display_name` — Nazwa na umowie (długa, opcjonalna — fallback do `name`)
- `default_amount` — Kwota domyślna (zł)
- `description` — Opis (textarea, obsługuje placeholdery `$1`/`$2` — podgląd na żywo pod polem)
- `notes` — Uwagi (textarea)
- **Sekcja "Integracja Fakturownia":**
  - `fakturownia_product_id` — Produkt Fakturownia (select, opcjonalny)

**Placeholdery $1/$2:** Opis obsługuje `$1` (→ kwota od/default_amount) i `$2` (→ kwota do).
Pod polem opisu wyświetla się podgląd na żywo z podmienionymi kwotami.
Wspólna logika: `composables/useFeeDescription.ts` (`formatFeeDescription`).

**Store:** `useAdditionalServicesStore` (`stores/additional_services.js`) — `fetchOne`, `create`, `update`
**API:** `GET/POST/PUT/DELETE /additional-services`

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
- `Ctrl+N` → nowy rekord (kontekstowo: `ContractNew`, `ContractorNew`, `MachineNew`/`ServiceNew`/`AdditionalServiceNew`)
- `Escape` → cofnij do poprzedniej strony (tylko gdy trasa kończy się na `/new` lub `/edit`)
- Guard: ignoruje gdy aktywny element to input/textarea/select lub gdy jest otwarte modal-overlay

---

## DashboardView — Empty state CTA (P3-009)

Puste tabele (brak rekordów) wyświetlają przycisk akcji:
- Umowy: "Brak umów — [+ Nowa umowa]" → `router.push({ name: 'ContractNew' })`
- Kontrahenci: "Brak kontrahentów — [+ Nowy kontrahent]" → `router.push({ name: 'ContractorNew' })`
- Artykuły: "Brak artykułów — [+ Nowy artykuł]" → `router.push({ name: 'ArticleNew' })` (DEPRECATED — patrz MachinesListView/ServicesListView)

---

## ConditionPanel — Auto-opis warunku (P3-006)

> **RAO-P2-071 (refaktor 2026-07):** Modal pełnego formularza warunków (`showCondModal`) **usunięty**. Warunki edytowane **inline w gridzie** (pattern z `ContractFormView.vue` dla pozycji). Auto-opis generowany automatycznie przy zapisie inline przez `buildAutoDescriptionFrom()`.

**Inline editing w gridzie warunków (RAO-P2-071):**
- Display mode + edit mode + new row (jak pozycje w `ContractFormView.vue`)
- `editingCondId`, `editingCondData`, `showNewCondRow`, `newCondData`
- `startEditCond` / `saveInlineCond` / `cancelInlineCond` / `saveNewCondRow` / `cancelNewCondRow`
- Enter = zapisz, Esc = anuluj (w każdym polu input)
- `addCondition()` → dodaje pusty row w trybie inline-edit (zero modali)
- Akcje: `✓` zapisz / `✕` anuluj (edit mode) • `✎` edytuj / `✕` usuń (display mode)
- `confirm()` zastąpione modalnem potwierdzenia (`confirmState`, pattern z `ContractFormView.vue`)
- Helper text nad gridem: "Kliknij wiersz aby edytować • Enter = zapisz • Esc = anuluj"
- Empty state z CTA: "Brak warunków — dodaj warunek rozliczenia" (link → `addCondition`)
- **Jedyne dozwolone użycie modala:** `showPresetPicker` (wybór cennika predefiniowanego)

**Kolumny gridu (inline editing):** Typ stawki (select) • Od (number) • Do (number) • Stawka (zł) (number) • Jednostka (text) • Minimum (number) • Akcje
- Kolumna **Stawka 2** została usunięta z UI; open-ended realizowane jest przez pustą wartość **Do**.
- Nad gridem znajduje się select **Gotowe przedziały…** z szablonami 1–2, 1–3, 1–4, 4–7, 4–8, >8, >16, >20 dni (dla najmu) oraz do 2 h, do 3 h (dla usługi). Wybór dodaje jeden wiersz warunku z uzupełnionym `period_from`/`period_to`.
- Edycja jest zablokowana gdy `isSettled = true`.

Auto-opis (PDF live preview):
- Generowany przy zapisie przez `buildAutoDescriptionFrom()` → `formatPreview()`.
- Format wierny backendowemu `format_position_conditions_cascading`: `"1 - 3 dni - 150,00 zł / doba"`, `"powyżej 16 dni - 350,00 zł / doba"`.
- Jeśli warunek ma `description`, wyświetlany jest on zamiast generowanego opisu.

---

## RAO-P1-001 — Predefiniowane cenniki warunków rozliczenia maszyn (frontend)

> **Refaktor (Faza 7, 2026-07-11):** `article_rate_presets` → `machine_rate_presets`
> (article_id → machine_id). Endpointy `/settings/articles/{article_id}/rate-presets` →
> `/settings/machines/{machine_id}/rate-presets`. Patrz `01_database.md` sekcja 11.

### 1. MachineFormView — sekcja "Cenniki rozliczenia" (CRUD)

**Lokalizacja:** `frontend/src/views/MachineFormView.vue` + `frontend/src/components/articles/RatePresetSection.vue`

**Widoczność:** Tylko w trybie edycji (`isEdit`) — maszyny nie mają flagi `is_service` (usługi w osobnej tabeli `services`). Sekcja pojawia się po sekcji "Dane techniczne".

**Funkcjonalność:**
- Lista cenników (presetów) dla tej maszyny z expand/collapse (wzorzec mirror z `fee-presets` w SettingsView)
- Każdy cennik: nazwa, badge "Domyślny", liczba warunków, przyciski: ✎ edytuj nazwę, ★ ustaw jako domyślny, ▲▼ expand, ✕ usuń
- Expand: tabela warunków (rate_type, rate1, rate2, billing_label, period_count, minimum, description) z inline edit + dodawanie wierszy
- Modal "Nowy cennik": nazwa, opis, checkbox "domyślny", tabela warunków do jednorazowego dodania (multi-row)

**Store:** `useSettingsStore` (`stores/settings.js`) — `fetchRatePresets`, `createRatePreset`, `updateRatePreset`, `deleteRatePreset`, `setDefaultRatePreset`, `addRatePresetItem`, `updateRatePresetItem`, `deleteRatePresetItem`

**API:** `GET/POST /settings/machines/{machine_id}/rate-presets`, `GET/PUT/DELETE/PATCH /settings/rate-presets/{preset_id}...` (patrz `02_backend_api.md`)

**Snapshot principle:** Po zastosowaniu w umowie warunki są kopiowane (snapshot) — edycja cenniku NIE wpływa na istniejące umowy.

### 2. ConditionPanel — "Zastosuj cennik" + "Z ostatniej umowy" (apply-preset + auto-prefill)

**Lokalizacja:** `frontend/src/components/contracts/ConditionPanel.vue`

**Nowe przyciski w nagłówku panelu warunków:**
- **📋 Zastosuj cennik** — otwiera modal picker z listą cenników maszyny (z `articleId` prop). Pre-wybiera domyślny. Checkbox "Zastąp istniejące warunki" (default true). Apply = `POST /contracts/{cid}/positions/{pid}/conditions/apply-preset` (snapshot copy, guard 409 gdy umowa rozliczona)
- **↻ Z ostatniej umowy** — auto-prefill z najnowszej umowy tej maszyny. `GET /machines/{machine_id}/last-conditions` (404 gdy brak historii → toast info). Warunki są dopisywane (nie zastępują).

**Nowy prop:** `machineId` (Number, opcjonalny) — przekazywany z `ContractFormView` przez computed `selectedPositionMachineId` (znajduje pozycję w `contractStore.positions` po `selectedPosId`).

**Store:** `useContractStore` (`stores/contracts.js`) — `applyRatePreset(contractId, posId, presetId, replace)`, `fetchLastConditionsForMachine(machineId)`

### 3. SettingsView — tab "Cenniki rozliczeń maszyn" (read-only overview)

**Lokalizacja:** `frontend/src/views/SettingsView.vue`

**Tab:** `machine-rate-presets` — label "Cenniki rozliczeń maszyn"

**Funkcjonalność (read-only):**
- Filtr tekstowy po nazwie maszyny
- Lazy-load przy aktywacji taba (watch `activeTab`)
- Pobiera wszystkie maszyny z `GET /machines?per_page=500`, następnie dla każdej `GET /settings/machines/{id}/rate-presets` (równolegle `Promise.all`)
- Pokazuje tylko maszyny, które mają ≥1 cennik
- Każda maszyna: card z nazwą, liczbą cenników, przycisk "Edytuj →" (deep-link do `/machines/{id}/edit`)
- Cenniki wyświetlone z warunkami w tabeli (rate_type, rate1, rate2, billing_label, period_count, minimum)

**Brak mutacji:** Tab jest read-only — edycja cenników odbywa się w `MachineFormView`.

---


## ConditionPanel — UX Pomoc dla warunków rozliczenia (RAO-P2-007)

> **Zaimplementowano:** 2026-05-25 | **RAO-P2-007**

**Cel:** Pomoc użytkownikowi w rozumieniu jak wpisywać warunki rozliczenia kaskadowej.

**Lokalizacja:** `frontend/src/components/contracts/ConditionPanel.vue`

### Funkcje UX

#### 1. Sekcja pomocy "Jak wpisać warunki rozliczenia?"
- Przycisk rozwijany z ikoną 📖 nad nagłówkiem "Warunki rozliczenia"
- Zawiera przykład koparki z kaskadową stawką dobową (3 warunki)
- Pokazuje mapowanie pól formularza na wynikowy format
- Przykłady:
  - Warunek 1: `rate_type="dobowa"`, `rate1=540`, `period_count=3`, `billing_label="doba"` → `"1 - 3 dni - 540,00 / doba"`
  - Warunek 2: `rate_type="dobowa"`, `rate1=410`, `period_count=16`, `billing_label="doba"` → `"4 - 16 dni - 410,00 / doba"`

---

## ConditionPanel — Elastyczne widełki cenowe (RAO-P1-005)

> **Zaimplementowano:** 2026-07-08 | **RAO-P1-005**

**Cel:** Uproszczenie wybierania widełek cenowych — operator definiuje przedziały ręcznie (np. 1-3 dni, 4-7 dni, powyżej 16).

**Lokalizacja:** `frontend/src/components/contracts/ConditionPanel.vue`

### Zmiany w tabeli warunków (inline grid)
- **Kolumny (zależne od `mode`):**
  - Najem (`mode='rental'`): `Od (dni)` • `Do (dni)` • `Stawka (zł)` (`rate1`) • `Jednostka` (`billing_label='doba'`) • `Minimum` • `Akcje`
  - Usługa (`mode='service'`): `Od (godz.)` • `Do (godz.)` • `Stawka (zł)` (`rate1`) • `Jednostka` (`billing_label='godzina'`) • `Minimum` • `Akcje`
- **Open-ended:** `rate2` jest ustawianie automatycznie przez `buildCondPayload` gdy `Do` jest puste a `Stawka` wypełniona — backend drukuje `powyżej X dni/godzin`.
- **Select "Gotowe przedziały…"** nad gridem:
  - Najem: `1 - 3 dni`, `1 - 8 dni`, `1 - 2 / 3 - 5 / >5 dni`, `>3 dni`, `>8 dni`, `>16 dni`, `>20 dni`, `1 dzień`
  - Usługa: `do 2 godzin`, `do 3 godzin`, `do 8 godzin`, `0 - 2 / 3 - 8 / >8 godzin`, `każda kolejna`
  - Wybór dodaje jeden lub więcej wierszy z `period_from`/`period_to`/`period_count` i placeholderem opisu.
- **Walidacja ciągłości:** watcher sprawdza czy są luki między warunkami (np. 1-3, następny 5-7 → błąd)
- **Podgląd PDF live:** pod tabelą wyświetla preview formatu warunków zgodny z backendem (`format_position_conditions_cascading`) i legacy:
  - Najem: `1 - 3 dni - 540,00zł / doba`, `powyżej 3 dni - 410,00zł / doba`, `230,00zł / doba` (flat, pf<=1)
  - Usługa (ryczałt, BEZ `/ unit`): `do 2 godzin - 1450,00zł` (pf=0), `3 - 8 godzin - 200,00zł`, `powyżej 8 godzin - 150,00zł`
  - Najem z `billing_label='godzina'` i pf=0 (1 przypadek w 515 legacy): `0 - 2 godzin - 1450,00zł / godzina`
- Edycja zablokowana gdy `isSettled = true`.

### Inline form
- **Pola:** "Od" / "Do" — number inputs z min=1, "Stawka (zł)" — `rate1`, "Jednostka" — `billing_label`, "Minimum" — `minimum`
- **Pole "Okresy" (period_count):** zachowane w payloadzie dla zgodności z backendem (ustawiane z `period_to` lub `null` dla open-ended)
- **Walidacja:** jeśli period_from > period_to → toast error; wymagana `rate1 > 0` przy zapisie
- Enter = zapisz, Esc = anuluj

### Funkcje walidacji
```javascript
function validateContinuity() {
  const sorted = [...conditions.value].sort((a, b) => (a.period_from || 0) - (b.period_from || 0))
  for (let i = 0; i < sorted.length - 1; i++) {
    const curr = sorted[i]
    const next = sorted[i + 1]
    if (curr.period_to && next.period_from && curr.period_to + 1 !== next.period_from) {
      gapError.value = `Luka: warunek ${curr.period_from}-${curr.period_to}, następny ${next.period_from}-${next.period_to || '∞'} (brak ${curr.period_to + 1})`
      return
    }
  }
  gapError.value = ''
}
```

### Podgląd PDF live
```javascript
function formatPreview(cond: any): string {
  if (cond.description) {
    return cond.description
      .replace(/\$1/g, formatCurrency(cond.rate1 ?? 0))
      .replace(/\$2/g, formatCurrency(cond.rate2 ?? 0))
  }
  const rate = cond.rate1 ?? cond.rate2
  const rateStr = rate ? formatCurrency(rate) : '0,00 zł'
  const unit = isService.value ? 'godzina' : (cond.billing_label || 'doba')
  const rangeUnit = getPeriodRangeUnit(unit)

  if (cond.period_from != null && cond.period_to != null) {
    const count = cond.period_to - cond.period_from + 1
    return `${cond.period_from} - ${cond.period_to} ${getPeriodLabel(count, rangeUnit)} - ${rateStr} / ${unitShort(unit)}`
  }
  if (cond.period_from != null && cond.period_to == null) {
    const count = cond.period_from - 1
    return `powyżej ${count} ${getPeriodLabel(count, rangeUnit)} - ${rateStr} / ${unitShort(unit)}`
  }
  return `${rateStr} / ${unitShort(unit)}`
}
```

### Backend changes
- **DB:** `position_conditions` — kolumny `period_from INT NULL`, `period_to INT NULL`, `period_count INT NULL`, `rate1`, `rate2`, `billing_label`
- **Schemas:** `ConditionResponse`, `ConditionCreate`, `ConditionUpdate` — dodane pola `period_from`, `period_to`, `rate1`, `rate2`, `billing_label`
- **Migration:** `ALTER TABLE position_conditions ADD COLUMN IF NOT EXISTS period_from/period_to` + `UPDATE` danych (period_from=1, period_to=period_count)
  - Warunek 3: `rate_type="dobowa"`, `rate2=350`, `billing_label="doba"` (bez `period_count`) → `"powyżej 16 dni - 350,00 / doba"`

#### 2. Tooltip dla pola "Stawka 2"
- Ikona ⓘ przy etykiecie "Stawka 2 (zł)"
- Podpowiedź: "ostatni warunek (powyżej) — pozostaw period_count puste"

#### 3. Live Preview formatu kaskadowego
- Wyświetla się w modalu dodawania/edycji warunku
- Pokazuje wynik funkcji `format_position_conditions_cascading()` z backendu (RAO-P1-008)
- Aktualizuje się na żywo przy zmianie pól formularza
- Widoczne tylko gdy wypełniono `rate1` lub `rate2`
- Format wyjściowy (frontend implementation):
  ```javascript
  function formatCascadingPreview() {
    // Sortuje warunki po period_count (NULL na końcu)
    // Buduje zakresy: "X - Y dni - stawka / jednostka"
    // Ostatni warunek: "powyżej X dni - stawka / jednostka"
  }
  ```

### Stany

| Stan | Opis |
|------|------|
| Domyślny (zwinięty) | Widoczny tylko przycisk z ikoną ▶ |
| Rozwinięty | Widoczny pełny tekst pomocy z przykładami |
| Live preview | Widoczny tylko gdy formularz ma dane |

### Style CSS

- `.help-section`: Kontener sekcji pomocy
- `.help-toggle`: Przycisk rozwijający (background: `var(--color-bg-light)`)
- `.help-content`: Treść pomocy z przykładami
- `.help-example-item`: Pojedynczy przykład z kodem
- `.field-tooltip`: Ikona ⓘ z tooltip
- `.live-preview`: Pole podglądu formatu kaskadowego (monospace)

---


---

## Komponent: `ContractPeriodPicker.vue` (RAO-P2-004)

> **Zaimplementowano:** 2026-05-21 | **RAO-P2-004**

**Cel:** Selektor okresu umowy oparty na dacie rozpoczęcia i liczbie dni (zamiast dwóch dat).

**Lokalizacja:** `frontend/src/components/shared/ContractPeriodPicker.vue`

### Props

| Prop | Typ | Opis |
|------|-----|------|
| `dateFrom` | `string \| null` | Data rozpoczęcia umowy (ISO format: YYYY-MM-DD) |
| `dateTo` | `string \| null` | Data zakończenia umowy (ISO format: YYYY-MM-DD) |
| `workingDaysPerWeek` | `number` | Ilość dni roboczych w tygodniu: `5`, `6` lub `7` (domyślnie `6`) |

### Emity

| Event | Payload | Opis |
|-------|---------|------|
| `update:dateFrom` | `string \| null` | Emitowana przy zmianie daty rozpoczęcia |
| `update:dateTo` | `string \| null` | Emitowana przy zmianie daty zakończenia |
| `update:workingDaysPerWeek` | `number` | Emitowana przy zmianie dni roboczych w tygodniu |

### Interfejs

```
┌────────────────────────────────────────────────────┐
│ Data od          │ Dni rob./tydz.                │
│ [2026-06-26   ]  │ [5] [6] [7]                   │
├────────────────────────────────────────────────────┤
│ Liczba dni │ [Wpisz datę końcową] [Data do  ]  │
│ [31        ] │                                  │
├────────────────────────────────────────────────────┤
│ Okres umowy: 26.06.2026 – 31.07.2026            │
│ (31 dni roboczych / 36 dni kalendarzowych)        │
└────────────────────────────────────────────────────┘
```

### Logika

1. **Liczba dni = dni robocze** (nie kalendarzowe).
2. **Dni robocze w tygodniu** (`workingDaysPerWeek`)
   - `5`: poniedziałek–piątek
   - `6`: poniedziałek–sobota
   - `7`: wszystkie dni tygodnia
   - Wybór przez przyciski `[5] [6] [7]` w komponencie
3. **Tryb automatyczny** (domyślny)
   - `Data do` jest obliczana kalendarzowo z `Data od + Liczba dni roboczych`
   - Dni wolne (weekendy) są pomijane przy przesuwaniu daty końcowej
   - Pole `Liczba dni` jest edytowalne
4. **Tryb ręczny** (przycisk "Wpisz datę końcową")
   - Pojawia się pole `Data do` (typ `date`)
   - Pole `Liczba dni` staje się read-only / disabled
   - Liczba dni roboczych jest liczona kalendarzowo w zadanym okresie
5. **Podsumowanie**
   - Format: `"Okres umowy: {date_from_pl} – {date_to_pl} ({N} dni roboczych / {M} dni kalendarzowych)"`
   - Pokazywane gdy są obie daty i okres ma przynajmniej 1 dzień kalendarzowy
6. **Inicjalizacja z danych (edycja umowy)**
   - Jeśli istniejące `dateTo` odpowiada obliczonemu końcowi dla zadanej liczby dni roboczych — tryb automatyczny
   - W przeciwnym razie tryb ręczny (np. data końcowa była wprowadzona ręcznie)

### Algorytmy

```ts
function addWorkingDays(startDate: Date, workingDays: number, daysPerWeek: number): Date {
  if (daysPerWeek === 7) {
    const d = new Date(startDate)
    d.setDate(d.getDate() + workingDays - 1)
    return d
  }
  const current = new Date(startDate)
  let count = 0
  while (count < workingDays) {
    const day = current.getDay()
    if (day >= 1 && day <= daysPerWeek) count++
    if (count < workingDays) current.setDate(current.getDate() + 1)
  }
  return current
}

function countWorkingDays(start: Date, end: Date, daysPerWeek: number): number {
  const current = new Date(start)
  let count = 0
  while (current <= end) {
    const day = current.getDay()
    if (daysPerWeek === 7 || (day >= 1 && day <= daysPerWeek)) count++
    current.setDate(current.getDate() + 1)
  }
  return count
}
```

### Przykład użycia (ContractFormView.vue)

```vue
<ContractPeriodPicker
  v-model:working-days-per-week="form.working_days_per_week"
  :date-from="form.date_from"
  :date-to="form.date_to"
  @update:date-from="form.date_from = $event"
  @update:date-to="form.date_to = $event"
/>
```

### Kompatybilność z API

- Komponent emituje `date_from` i `date_to` w formacie ISO (YYYY-MM-DD)
- Emituje `working_days_per_week` jako liczbę całkowitą
- Pełna kompatybilność z istniejącym API backendu
- Możliwość montowania z istniejącymi danymi (edycja umowy)

### Przykłady obliczeń

| date_from | workingDays | daysPerWeek | date_to | Display |
|-----------|-------------|-------------|---------|---------|
| 2026-06-26 | 31 | 6 | 2026-07-31 | 26.06.2026 – 31.07.2026 (31 dni roboczych / 36 dni kalendarzowych) |
| 2026-06-26 | 7 | 6 | 2026-07-02 | 26.06.2026 – 02.07.2026 (7 dni roboczych / 7 dni kalendarzowych) |
| 2026-06-26 | 31 | 5 | 2026-08-07 | 26.06.2026 – 07.08.2026 (31 dni roboczych / 43 dni kalendarzowych) |
| 2026-06-26 | 31 | 7 | 2026-07-26 | 26.06.2026 – 26.07.2026 (31 dni roboczych / 31 dni kalendarzowych) |

## RAO-P1-043: Cleanup event listenerów i timerów (memory leaks)

Każdy widok/komponent dodający `addEventListener` lub uruchamiający `setTimeout`/`setInterval` **musi** czyścić je w `onUnmounted` (lub `onBeforeUnmount`).

### Wzorzec

```ts
import { onMounted, onUnmounted } from 'vue'

let timer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  document.addEventListener('click', handleClick)        // named function!
  timer = setTimeout(() => { ... }, 1000)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClick)      // ta sama funkcja
  if (timer) clearTimeout(timer)
})
```

### Zasady

- **`addEventListener` z inline arrow function NIE działa z `removeEventListener`** — zrefaktoruj na named function.
- **Timer ID zapisany w zmiennej** — użyj tej samej zmiennej w `clearTimeout`/`clearInterval`.
- **Wiele timerów UI** (np. feedback messages 3-5s) — zbieraj w tablicy `uiTimers[]` i czyść wszystkie w `onUnmounted`.
- **Pliki bez `lang="ts"`** — używaj plain JS (`let x = null`), bez annotacji TypeScript.

### Pliki objęte fixem P1-043

| Plik | Co wyczyszczono |
|------|-----------------|
| `views/DashboardView.vue` | `document.addEventListener('click'/'keydown')` + `searchTimer` (refaktor inline arrow → `handleCtxKeydown`) |
| `views/ContractFormView.vue` | `pickerTimer`, `artTimer`, `supTimer` (dodane do istniejącego `onUnmounted`) |
| `views/ArticleFormView.vue` | `ownerTimer` (nowy `onUnmounted`) |
| `views/SettingsView.vue` | 5× `setTimeout` (feedback messages) przez `scheduleUiTimer()` + `uiTimers[]` |
| `views/LoginView.vue` | `shakeTimer` (nowy `onUnmounted`) |
| `views/ChangePasswordView.vue` | `redirectTimer` (nowy `onUnmounted`) |
| `views/ResetPasswordView.vue` | `redirectTimer` (nowy `onUnmounted`) |
| `components/reports/ReportsSection.vue` | `machineSearchTimer`, `serviceSearchTimer` (dodane do istniejącego `onBeforeUnmount`) |


## Komponenty reusable dla AnalyticsView (Frontend-1, 2026-07-01)

> Czyste komponenty dumb (bez logiki biznesowej / store / API). Używane przez przyszły
> `views/AnalyticsView.vue`. Wszystkie style przez zmienne CSS z `assets/styles/variables.css`.

### `composables/useSort.ts`
- Client-side sortowanie tabel.
- API: `useSort<T>(initialKey, initialDir='desc')` → `{ sortKey, sortDir, toggleSort, sortedRows }`
- `toggleSort(key)`: ta sama kolumna → odwróć dir; nowa kolumna → key + dir='desc'.
- `sortedRows(rows)`: nowa posortowana kopia (nie mutuje). null/undefined → na końcu.
- Obsługa: string (localeCompare 'pl'), number, boolean, Date, fallback toString.

### `components/analytics/AnalyticsTable.vue`
- Props: `columns: AnalyticsColumn[]`, `rows: AnalyticsRow[]`, `sortKey`, `sortDir`, `rowKey`, `clickable?`, `loading?`, `skeletonRows?`.
- Emits: `@sort(key)`, `@rowClick(row)`.
- Stany: loading (skeleton), empty (slot `empty`), data.
- Slot `cell-<key>` dla custom renderu komórki; sloty `loading` / `empty`.
- data-testid: `analytics-table`, `analytics-table-loading`, `analytics-table-empty`, `th-<key>`, `sort-icon-<key>`, `row-<id>`.

### `components/analytics/KpiRow.vue`
- Props: `cards: KpiCard[]` (`{ value, label, sub?, variant?, icon?, testId? }`).
- Grid auto-fit, min 180px / kartę. Varianty: default/success/accent/danger/warn → kolor wartości.
- data-testid: `kpi-row`, `kpi-card-<idx>` (lub `card.testId`).

### `components/analytics/AnalyticsFilters.vue`
- v-model: `modelValue: AnalyticsFiltersValue` (`{ dateFrom, dateTo, preset, articleType, contractorId, city }`).
- Props dodatkowe: `contractors: {id, name}[]`.
- Emits: `@update:modelValue`.
- Presets: Dziś / Tydzień / Miesiąc / Kwartał / Rok / Wszystko / Własny (pills).
- Custom range (2x input date) tylko gdy `preset='custom'`.
- Typ (select), Kontrahent (input+datalist), Miasto (text), przycisk "Wyczyść".
- data-testid: `analytics-filters`, `preset-<key>`, `preset-custom`, `custom-range`, `filter-date-from`, `filter-date-to`, `filter-article-type`, `filter-contractor`, `filter-city`, `filter-clear`.

### `components/analytics/DrillDownDrawer.vue`
- Props: `open`, `title`, `subtitle?`, `loading?`, `error?`. Emits: `@close`.
- `<Teleport to="body">` + **NON-SCOPED** `<style>` (prefiks klas `drill-` — kolizja z ArchiveView nie grozi bo klasy są globalne i identyczne semantycznie).
- Overlay rgba(0,0,0,0.4) z-index 1000; drawer 60% / min 480 / max 900px, height 100%.
- Transition `drill-fade`: slide-in z prawej (translateX 100% → 0) + fade overlay.
- Esc zamyka (window keydown listener w onMounted/onUnmounted). Click na overlay zamyka (click w drawerze stopPropagation).
- Slot default = treść; slot `footer` = np. paginacja. Blokuje scroll body gdy open.
- data-testid: `drill-overlay`, `drill-drawer`, `drill-close`, `drill-loading`, `drill-error`, `drill-footer`.

### `components/analytics/AnalyticsTabs.vue`
- Props: `tabs: AnalyticsTab[]` (`{ key, label, icon? }`), `active`. Emits: `@change(key)`.
- Pills w flex row; aktywna = bg primary + color on-primary; nieaktywna hover = bg light.
- data-testid: `analytics-tabs`, `tab-<key>`.

### `components/analytics/ChartCard.vue` (NOWY — wrapper wykresów Chart.js)
- Props: `title: string`, `chartType: 'bar' | 'line' | 'doughnut'`, `chartData: ChartData`, `chartOptions?: ChartOptions`, `loading?: boolean`, `empty?: boolean`, `testId?: string`.
- Opakowuje `vue-chartjs` komponenty (Bar, Line, Doughnut) w kartę z nagłówkiem i stanami loading/empty.
- Karta stylowana zmiennymi CSS (`--color-bg-card`, `--border-radius`, `--shadow-card`).
- Automatyczny resize (Chart.js responsive + maintainAspectRatio=false).
- data-testid: `chart-card`, `chart-card-<testId>`, `chart-canvas`, `chart-loading`, `chart-empty`.

### `composables/useChartTheme.ts` (NOWY — paleta kolorów dla Chart.js)
- Eksportuje `chartColors` obiekt z paletą spójną z design system:
  - `colors.primary` = `#1D2B53` (Deep Navy)
  - `colors.info` = `#3B82F6` (Accent Blue)
  - `colors.success` = `#22C55E`
  - `colors.warning` = `#F59E0B`
  - `colors.error` = `#EF4444`
  - `colors.primaryLight` = `#2A3F6F`
- Eksportuje `getChartPalette(n: number)` → generuje tablicę N kolorów (cykl przez paletę dla dużych zbiorów).
- Eksportuje `defaultChartOptions` — bazowe opcje Chart.js (font Montserrat, grid color z `--color-border`, tooltip styling).
- Czyta zmienne CSS z `:root` w runtime (getComputedStyle) dla spójności z motywem.

### Weryfikacja
- `npx vue-tsc --noEmit` → PASS (exit 0)
- `npm run build` → PASS (build OK)


## AnalyticsView — główny widok + 3 taby + store (Frontend-2, 2026-07-02)

> Logika biznesowa używająca komponentów z Frontend-1. Route `/analytics` (sidebar „� Statystyki").
> BEZ archiwalnych danych — tylko live contracts/articles (endpointy `/stats/*` i `/explorer/*`).

### `stores/analytics.ts` (Pinia, Composition API)
- State: `loading, loadingLive, loadingExplorer, drillLoading, drillError, summary, currentlyRented,
  topMachines, additionalFees, locations, positionsData, byCategoryData, byPeriodData, categoriesList,
  explorerResults, explorerSummary, machineDetails, locationDetails, drillDown` (ref z `open/kind/id/name/title/subtitle`).
- Getters: `liveUtilPct`, `revenueSourceClass`.
- Actions (async, axios z `@/composables/useApi`):
  - `fetchCurrentlyRented()` → GET `/stats/currently-rented`
  - `fetchSummary(dateFrom, dateTo, internalNumber?)` → GET `/stats/fleet-summary`
  - `fetchTopMachines(dateFrom, dateTo, filters?, limit=10)` → GET `/stats/top-machines` (contractor_id, city, internal_number, limit)
  - `fetchAdditionalFees(dateFrom, dateTo, contractorId?)` → GET `/stats/additional-fees`
  - `fetchLocations(dateFrom, dateTo, filters?)` → GET `/stats/locations`
  - `fetchPositions(type, dateFrom, dateTo, filters?, sortBy?, sortDir='desc')` → GET `/stats/positions`
  - `fetchByCategory(level, dateFrom, dateTo, categoryMain[], articleType)` → GET `/stats/by-category`
  - `fetchByPeriod(granularity, dateFrom, dateTo, categoryMain[], articleType)` → GET `/stats/by-period`
  - `fetchCategoriesList()` → GET `/stats/categories-list`
  - `searchExplorer(q, dateFrom, dateTo, limit=50)` → GET `/explorer/search`
  - `fetchMachineDetails(machineId, dateFrom, dateTo)` → GET `/explorer/machines/{id}`
  - `fetchLocationDetails(postalCode, dateFrom, dateTo)` → GET `/explorer/locations/{postal_code}`
  - `openDrillDown(kind, id, name, dateFrom, dateTo)` — ustawia `drillDown` ref + fetch details
    (kind='machine' → machineDetails z historią wynajmów; kind='location' → locationDetails z umowami).
  - `closeDrillDown()` — reset `drillDown` + czyszczenie `machineDetails`/`locationDetails`.
- Typy eksportowane: `FleetSummary`, `TopMachineItem`, `CurrentlyRentedResponse`, `AdditionalFeesResponse`,
  `LocationStatItem`, `PositionStatsResponse`, `CategoryStatsResponse`, `ByPeriodResponse`,
  `CategoriesListNode`, `ExplorerResultItem`, `MachineDetailsResponse`, `LocationDetailsResponse`,
  `DrillDownKind`, `DrillDownState`, `AnalyticsFiltersPayload`.

### `views/AnalyticsView.vue` (~650 linii)
- Shell z 7 zakładkami przez `AnalyticsTabs` (P1-112 kolejność + rename):
  1. `live` (🚜 Flota teraz) — domyślna taba (P1-112)
  2. `categories` (📊 Kategorie) — drill-down hierarchiczny kategorii (NOWY)
  3. `machines` (🏗️ Maszyny)
  4. `services-u` (🔧 Usługi zwykłe)
  5. `services-s` (📦 Usługi dodatkowe)
  6. `locations` (📍 Lokalizacje)
  7. `period` (📊 Rankingi wynajmu) — było "Wynajem w okresie" (P1-112 rename)
- **Filtry warunkowe (P1-112):** `AnalyticsFilters` przyjmuje prop `activeTab`:
  - `articleType` ukryte na dedykowanych tabach (machines, services-s, services-u) — tab już determinuje typ
  - `city` ukryte na tabach usług (services-s, services-u) — usługi nie mają lokalizacji
  - Wszystkie filtry ukryte na `live` (Flota teraz — dane realtime)
- **Explorer tab usunięty** (2026-07-15) — zastąpiony przez dedykowane taby Maszyny/Usługi.
- **Reservations tab usunięty z analityki** (2026-07-15, Phase A) — `ReservationsTab.vue` zostaje w repo (do przeniesienia do osobnego widoku w fazach 1-5). Import i użycie w template usunięte; typ `activeTab` zwężony.
- Współdzielony stan filtrów (`ref<AnalyticsFiltersValue>` z dateFrom/dateTo/preset/articleType/contractorId/city).
- `AnalyticsFilters` na górze — **ukryte na zakładce 'live'** (live = "teraz").
- Renderuje aktywną tabę: `<LiveFleetTab v-if="activeTab==='live'"/>` itd. (lazy mount przez `v-if`). Wszystkie taby datowe (period, locations, machines, services-s, services-u) otrzymują `:filters` prop z pełnym `AnalyticsFiltersPayload`.
- `DrillDownDrawer` na poziomie widoku (jeden, współdzielony). Treść zależna od `store.drillDown.kind`:
  - `machine` → tabela historii wynajmów (Umowa, Kontrahent, Od, Do, Dni, Kwota) + 4 KPI metrics.
  - `location` → 4 KPI metrics + Top maszyny + Top kontrahenci.
- `provide('analytics:openDrillDown', openDrillDown)` — taby injectują i wywołują przy `@rowClick`.
- Header: `<h1>Statystyki</h1>` + dzisiejsza data (toLocaleDateString 'pl-PL').
- onMounted: ładuje listę kontrahentów (datalist filtra).
- data-testid: `analytics-view`.

### `components/analytics/tabs/LiveFleetTab.vue`
- KPI row (KpiRow): Dostępne maszyny (success), Wynajęte teraz (accent), Wykorzystanie % (variant dynamiczny: ≥80 success / ≥50 accent / <50 warn).
- Utilization bar (pasek postępu — width = utilPct%).
- **Wykresy Chart.js** (vue-chartjs): doughnut (Dostępne vs Wynajęte) + bar (top maszyny wg dni wynajmu). Opakowane w `ChartCard.vue` z `useChartTheme.ts` dla spójnej palety.
- AnalyticsTable: Maszyny aktualnie wynajęte (kolumny: Maszyna [sortable], Nr wewnętrzny, Kategoria, Umowa, Kontrahent, Planowany zwrot).
  - `clickable=true`, `@rowClick` → `openDrillDown('machine', machine_id, name)`.
  - Sortowanie przez `useSort('name', 'asc')`.
- Stany: loading (`store.loadingLive`), empty (slot empty „Brak aktywnych wynajmów…"), data.
- Fetch: `store.fetchCurrentlyRented()` onMounted (tylko gdy brak danych).
- `.lf-section` — card styling (`background: var(--color-bg-card); border-radius; box-shadow; padding`) spójny z `.mt-section`/`.svc-section`/`.res-section` (od Phase A 2026-07-15 — wcześniej brak, sekcja bez tła/obramowania).
- data-testid: `live-fleet-tab`, `kpi-live-available`, `kpi-live-rented`, `kpi-live-util`, `live-util-bar`.

### `components/analytics/tabs/CategoriesTab.vue` (NOWY — drill-down hierarchiczny)
- Props: `dateFrom, dateTo, filters: AnalyticsFiltersPayload`.
- **Drill-down hierarchiczny** (main → sub1 → sub2): breadcrumb klikalny, kliknięcie wiersza kategorii z dzieciami → drill-down do kolejnego poziomu.
- KPI row: Łączny przychód, Aktywnych kategorii, Dni wynajmu.
- **Bar chart horyzontalny** (Chart.js via vue-chartjs, opakowany w `ChartCard.vue`): top kategorie wg wybranej metryki.
  - Toggle metryki (pill buttons): Przychód / Dni / Umów — przełącza sortowanie i etykiety osi.
  - Klik słupka → drill-down do kategorii (gdy ma dzieci).
- AnalyticsTable: Kategoria, Maszyny, Dni wynajmu, Umowy, Przychód (sortable, clickable → drill-down gdy `categoryHasChildren`).
- Fetch: `store.fetchByCategory(level, dateFrom, dateTo, categoryMains[], articleType)` → GET `/stats/by-category`.
- `useChartTheme.ts` dostarcza paletę kolorów spójną z design system.
- data-testid: `categories-tab`, `kpi-cat-revenue`, `kpi-cat-active`, `kpi-cat-days`, `cat-bar-chart`, `cat-metric-toggle`, `cat-table`, `cat-empty`.

### `components/analytics/tabs/PeriodRentalTab.vue`
- Props: `dateFrom, dateTo, filters: AnalyticsFiltersPayload`.
- KPI row: Przychód w okresie, Umów w okresie, Wynajętych teraz, Wykorzystanie (z `store.summary`).
- Revenue breakdown (rzeczywiste vs szacunek — gdy `revenue_actual>0` lub `revenue_estimate>0`).
- AnalyticsTable × 4:
  1. Top maszyny (#, Maszyna, Nr wewnętrzny, Przychód, Dni, Umów) — sortable: revenue/rented_days/contracts_count; clickable → drill machine.
  2. Dodatkowe opłaty (Usługa, Przychód, Razy).
  3. Lokalizacje (Miasto, Kod PNA, Wynajmów, Przychód) — clickable → drill location (po PNA).
  4. Pozycje (Nazwa, Nr wewnętrzny, Kategoria, Przychód, Dni, Umów, Razy) — sortable: article_name/internal_number/category_main/revenue/rented_days/contracts_count/times_billed.
- Sortowanie: `useSort` per tabela (topMachinesSort, positionsSort).
- **Wykresy Chart.js** (vue-chartjs, `ChartCard.vue`): line chart (trend przychodu w okresie) + bar chart (top kategorii wg przychodu). `useChartTheme.ts` dostarcza paletę.
- Fetch: `Promise.all` 5 endpointów (summary, topMachines, additionalFees, locations, positions) onMounted + watch props.
- data-testid: `period-rental-tab`, `kpi-period-revenue`, `kpi-period-contracts`, `kpi-period-rented`, `kpi-period-util`, `revenue-breakdown`.

### `components/analytics/tabs/LocationsTab.vue` (RAO-P2-065 4b, 2026-07-04)
- Props: `dateFrom, dateTo, filters?: AnalyticsFiltersPayload`. Przywrócona funkcjonalność paneli miast z legacy ReportsSection (zgubiona przy merge P2-063). `filters` przekazywane do `fetchLocationsRanking` (od Phase A 2026-07-15 — wcześniej brak, ranking ignorował kontrahenta/miasto/typ artykułu).
- Fetch: `store.fetchLocationsRanking(dateFrom, dateTo, 100, groupBy, filters)` → GET `/explorer/locations` (ranking z rollup gmina/powiat/województwo, z filtrami).
- KPI row: Lokalizacji, Wynajmów (suma), Przychód (suma, accent), Top miasto (success).
- **Wykres słupkowy (Chart.js bar, zastąpił custom CSS bars)**: top 10 miast, toggle metryki Przychód/Wynajmy (pill buttons), klik słupka → drill-down lokalizacji (gdy postal_code). Opakowany w `ChartCard.vue` z `useChartTheme.ts`.
- Wyszukiwarka miast (client-side filter po city/postal_code/gmina/powiat/wojewodztwo).
- AnalyticsTable ranking: #, Miasto, PNA, Gmina, Powiat, Województwo, Wynajmów, Przychód (sortable, slot cell-total_revenue z formatCurrency); clickable → drill location (po PNA).
- Empty state z hintem: "Lokalizacje wykrywane są z adresu dostawy umowy (kod pocztowy)".
- data-testid: `locations-tab`, `kpi-loc-count/rentals/revenue/top`, `loc-chart`, `loc-chart-revenue/rentals`, `loc-search`, `loc-ranking-table`, `loc-empty`.

### `components/analytics/tabs/MachinesTab.vue` (2026-07-15)
- Props: `dateFrom, dateTo, filters: AnalyticsFiltersPayload`.
- KPI row: Maszyn, Przychód (accent), Dni wynajmu, Top maszyna (success).
- **Wykres Chart.js** (vue-chartjs, `ChartCard.vue`): bar chart top 10 maszyn wg przychodu. `useChartTheme.ts` dostarcza paletę.
- AnalyticsTable: #, Maszyna, Nr wewnętrzny, Kategoria, Przychód, Dni, Umów, Razy (sortable, clickable → drill machine).
- Wyszukiwarka client-side (nazwa, nr wewnętrzny, kategoria).
- ExportCsvButton — eksport do CSV.
- Fetch: `store.fetchPositions('machines', dateFrom, dateTo, filters)` → GET `/stats/positions?type=machines`.
- data-testid: `machines-tab`, `kpi-machines-count/revenue/days/top`, `machines-search`, `machines-table`, `machines-empty`.

### `components/analytics/tabs/ServicesAdditionalTab.vue` (2026-07-15)
- Props: `dateFrom, dateTo, filters: AnalyticsFiltersPayload`.
- KPI row: Usług dodatkowych, Przychód (accent), Razy zafakturowane, Top usługa (success).
- **Wykres Chart.js** (vue-chartjs, `ChartCard.vue`): doughnut chart udziału usług dodatkowych wg przychodu. `useChartTheme.ts` dostarcza paletę.
- AnalyticsTable: #, Usługa dodatkowa, Kategoria, Przychód, Umów, Razy (sortable, clickable → drill service). **Kolumna "Nr wewnętrzny" usunięta** (Phase A 2026-07-15) — usługi nie mają numerów wewnętrznych (zawsze "—").
- Wyszukiwarka (nazwa, kategoria) + ExportCsvButton.
- Fetch: `store.fetchPositions('services', dateFrom, dateTo, filters, undefined, 'desc', 'S')` → GET `/stats/positions?type=services&contract_type=S`.
- data-testid: `services-additional-tab`, `kpi-svc-s-count/revenue/billed/top`, `svc-s-search`, `svc-s-table`, `svc-s-empty`.

### `components/analytics/tabs/ServicesRegularTab.vue` (2026-07-15)
- Props: `dateFrom, dateTo, filters: AnalyticsFiltersPayload`.
- KPI row: Usług zwykłych, Przychód (accent), Umów usługi, Top usługa (success).
- **Wykres Chart.js** (vue-chartjs, `ChartCard.vue`): bar chart top 10 usług zwykłych wg przychodu. `useChartTheme.ts` dostarcza paletę.
- AnalyticsTable: #, Usługa, Kategoria, Przychód, Dni, Umów, Razy (sortable, clickable → drill service). **Kolumna "Nr wewnętrzny" usunięta** (Phase A 2026-07-15) — usługi nie mają numerów wewnętrznych (zawsze "—").
- Wyszukiwarka (nazwa, kategoria) + ExportCsvButton.
- Fetch: `store.fetchPositions('all', dateFrom, dateTo, filters, undefined, 'desc', 'U')` → GET `/stats/positions?type=all&contract_type=U`.
- data-testid: `services-regular-tab`, `kpi-svc-u-count/revenue/contracts/top`, `svc-u-search`, `svc-u-table`, `svc-u-empty`.

### `components/analytics/tabs/ReservationsTab.vue` (2026-07-15) — USUNIĘTY Z ANALITYKI (Phase A 2026-07-15)
- **Plik zostaje w repo** — do przeniesienia do osobnego widoku rezerwacji w fazach 1-5. Nie jest już importowany ani renderowany w `AnalyticsView.vue`.
- Brak props — rezerwacje niezależne od dat/filtrów.
- KPI row: Rezerwacji, Aktywnych (success), Wygasłych (warn), Maszyn.
- Filter toggle: Wszystkie / Aktywne / Wygasłe.
- AnalyticsTable: Maszyna, Nr wewnętrzny, Od, Do, Dni, Status (badge), Notatka (sortable).
- Wyszukiwarka + ExportCsvButton.
- Fetch: `reservationsStore.fetchAllWithArticles()` → GET `/reservations/with-articles` (refaktor: zwraca `machine_name` zamiast `article_name`).
- data-testid: `reservations-tab`, `kpi-res-total/active/expired/machines`, `res-filter-all/active/expired`, `res-search`, `res-table`, `res-empty`.

### `components/analytics/ExportCsvButton.vue` (2026-07-15)
- Props: `columns: CsvColumn[], rows: Record<string, unknown>[], filename?, label?, disabled?`.
- Generuje CSV z BOM (UTF-8), escapuje przecinki/cudzysłowy/newline.
- Trigger: click → Blob → download link.
- data-testid: `export-csv-btn`.

### Routing / nawigacja
- `router/index.js`: dodany route `path: 'analytics'`, `name: 'Analytics'`, lazy import `AnalyticsView.vue`.
- `components/layout/AppLayout.vue`: `activeSection` rozpoznaje `/analytics`; `handleNavigate('analytics')` → `router.push('/analytics')`.
- `components/layout/AppSidebar.vue`: przycisk „📈 Analytics" (aktywny gdy `activeSection === 'analytics'`).

### Weryfikacja (Frontend-2)
- `npx vue-tsc --noEmit` → PASS (exit 0, strict + noUnusedLocals/Parameters)
- `npm run build` → PASS (chunk `AnalyticsView-*.js` ~31.7 kB / ~9.3 kB gzip; CSS `AnalyticsView-*.css` ~16 kB)

---

## ReservationsView (Phase 3, 2026-07-11; P1-111 refactor 2026-07-12)

### `views/ReservationsView.vue` (~700 linii)
- **Widok Rezerwacji maszyn** — kalendarz month-view + panel dnia + modal CRUD.
- **P1-111 (2026-07-12): Layout side-by-side** (nie toggle): kalendarz po lewej (flex: 1) + panel listy dnia po prawej (flex: 0 0 340px, max-width: 400px).
- **Kalendarz month-view** (custom CSS grid 7×5-6, BEZ biblioteki):
  - Nagłówek: miesiąc + rok (capitalize, pl-PL), przyciski ← → (poprzedni/następny miesiąc), "Dziś".
  - Komórki dni: numer dnia + kropki (colored dots) reprezentujące eventy (max 4 + "+N").
  - **Kolory kropek:** niebieski (`var(--color-primary)`) = rezerwacja; `var(--color-warning)` (#F59E0B) = umowa (source=contract).
  - **Tooltip na dniu** (hover, CSS): lista eventów — "maszyna X, kontrahent Y, data od-do" + "(umowa)" dla contract.
  - **P1-111: Lewy klik na dniu** → `selectDay(cell.date)` — wybiera dzień, panel dnia pokazuje eventy.
  - **P1-111: Prawy klik na dniu** (`@contextmenu.prevent`) → context menu: "Dodaj rezerwację" (openCreate) / "Dodaj umowę" (`router.push ContractNew query.date`).
  - Klik na kropce (event) → otwiera modal edycji (rezerwacja) lub info read-only (umowa).
  - Tydzień zaczyna się od poniedziałku (Pn-Nd).
- **P1-111: Panel listy dnia** (prawa strona, `rv-day-panel`):
  - Empty state: "Kliknij dzień w kalendarzu aby zobaczyć rezerwacje"
  - Header: wybrany dzień w formacie "2026-07-12 (sob)"
  - Checkboxes: "Blokady rezerwacjami" (`showReservations`, default true) + "Blokady umowami" (`showContracts`, default true) — filtruje listę dnia
  - Lista eventów: kropka (kolor wg source) + maszyna + daty + kontrahent. Klik → openEdit(event)
  - No-events state: "Brak blokad tego dnia"
  - **P1-118:** max-height 60vh + overflow-y auto + paginacja "Pokaż więcej" (PAGE_SIZE=10)
- **Filtry** (nad kalendarzem, kolejność: Maszyna, Handlowiec, Kontrahent):
  - Maszyna (select z maszynami — `GET /machines?per_page=200`). **P2-003:** Tylko maszyny wewnętrzne (`is_external=false`) — filtrowane frontend-side `.filter((a) => !a.is_service && !a.is_external)`.
  - Handlowiec (select, P1-119 — opcjonalny, filtruje po salesperson_id).
  - Kontrahent (`ContractorCombobox` z `components/analytics/`).
- **Modal dodawania/edycji** (kolejność pól: Maszyna, Handlowiec, Kontrahent, Daty, Notatka):
  - Pola: maszyna (select, wymagana), handlowiec (select, opcjonalny — P1-119), kontrahent (combobox, opcjonalny), data od (wymagana), data do (wymagana), notatka (textarea).
  - Walidacja: data od ≤ data do, maszyna wymagana.
  - Edycja: przycisk "Usuń" (z confirm).
  - Read-only dla umów (source=contract) — info z notką "edycja tylko z poziomu umowy".
  - Loading state (modalSaving), error state (409 konflikt → komunikat).
- **Stany:** loading (`StateMessage` type=loading), error (retry), empty ("Brak rezerwacji. Dodaj pierwszą rezerwację." + CTA).
- **Store:** `useReservationsStore()` — `fetchCalendar`, `fetchAllWithMachines`, `create`, `update`, `remove`.
- **Data loading:** onMounted → loadMachines + contractors + fetchCalendar. Watch: zmiana miesiąca/filtru maszyny → reload kalendarza.
- **Design system:** wyłącznie zmienne CSS z `style.css`. Brak hardcoded kolorów.
- data-testid: `reservations-view`, `rv-add-btn`, `rv-filter-machine`, `rv-filter-contractor`, `rv-filter-status`, `rv-calendar`, `rv-cal-prev/next/today`, `rv-cal-cell`, `rv-day-panel`, `rv-day-event`, `rv-context-menu`, `rv-modal`, `rv-modal-machine`, `rv-modal-from`, `rv-modal-to`, `rv-modal-status`, `rv-modal-note`, `rv-modal-save`, `rv-modal-delete`, `rv-modal-error`.
- **Usunięte (P1-111):** `rv-toggle-calendar`, `rv-toggle-list`, `rv-list`, `rv-list-row`, `rv-edit-btn`, `rv-delete-btn` (lista staje się panelem dnia, nie osobnym widokiem).

### `stores/reservations.ts` (rozszerzony, Phase 3)
- Interfejs `ArticleReservation`: dodano `contractor_id: number | null`, `contractor_name: string | null`, `status: string | null`.
- Interfejs `ReservationWithArticle`: dziedziczy rozszerzone `ArticleReservation`.
- Interfejs `ReservationPayload`: dodano `contractor_id?: number | null`, `status?: string | null`.
- Nowy interfejs `CalendarEvent`: `source`, `source_id`, `article_id`, `article_name`, `internal_number`, `contractor_id`, `contractor_name`, `date_from`, `date_to`, `note`, `status`.
- Nowy interfejs `ReservationUpdatePayload`: partial (`reserved_from?`, `reserved_to?`, `note?`, `contractor_id?`, `status?`).
- Nowy ref `calendarEvents: ref<CalendarEvent[]>([])`, `loadingCalendar: ref(false)`.
- Nowa metoda `fetchCalendar(dateFrom, dateTo, articleId?)` → GET `/reservations/calendar`.
- Nowa metoda `update(reservationId, payload)` → PUT `/reservations/{id}`.
- `remove` odświeża też `allList`. `reset` czyści też `calendarEvents`.

### Routing / nawigacja (Phase 3)
- `router/index.js`: dodany route `path: 'reservations'`, `name: 'Reservations'`, lazy import `ReservationsView.vue` (w children array po articles).
- `components/layout/AppLayout.vue`: `activeSection` rozpoznaje `/reservations`; `handleNavigate('reservations')` → `router.push('/reservations')`. Ctrl+N NIE otwiera formularza dla reservations (widok ma własny modal).
- `components/layout/AppSidebar.vue`: `topItems` dodany `{ section: 'reservations', label: 'Rezerwacje' }` (po articles).

### Weryfikacja (Phase 3)
- `npx vue-tsc --noEmit` → PASS (exit 0, strict + noUnusedLocals/Parameters)
- `npm run build` → PASS (chunk `ReservationsView-*.js` ~221 kB / ~65.9 kB gzip; CSS `ReservationsView-*.css` ~33.7 kB / ~6.0 kB gzip)

