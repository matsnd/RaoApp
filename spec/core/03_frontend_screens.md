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

**Lista artykułów — filtr archiwalny:**

- Filtr **archiwalny** (toggle checkbox w grid-header): domyślnie `Aktywne`, toggle → `Archiwalne`
- Parametr API: `archival_status=active|archival`
- Wiersz `row-archival`: szare tło `#f8fafb`, przyciemniony tekst `#718096` gdy `is_archival=true`
- Warunkowy empty state:
  - Aktywne: "Brak artykułów — + Nowy artykuł"
  - Archiwalne: "Brak artykułów archiwalnych"


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
│ ☐ Reprezentująca  Tel1 [________]       │ Reprezentowany przez [____________]  │
│ ☐ Kontaktowa      Tel2 [________]       │ Tel1   [____________]  │
│                                         │ Osoba kontaktowa      [____________]  │
│ Usługi dodatkowe [↺ Przywróć szablon]   │ Tel2   [____________]  │
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
│ │   Jeśli artykuł z mappingiem jest na umowie → automatycznie dodaje settlement z cost_client z faktury │ │
│ │   Semantyka 1:N: jeśli produkt FA jest przypisany do wielu artykułów RAO, │ │
│ │   każdy artykuł na umowie dostaje pełną wartość z faktury (multiplikacja OK) │ │
│ │                                                                                 │ │
│ │ Guzik "Pobierz z Fakturownia" jest nieaktywny jeśli Fakturownia nie jest skonfigurowana │ │
│ │ (brak enabled, domain_subdomain lub api_token_preview w ustawieniach)        │ │
│ └───────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
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

**Zakładki:** Dane firmy | Handlowcy | Kategorie | Typy stawek | Zestawy usług dodatkowych | Fakturownia | Folder RAO


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
- Pola techniczne (RAO-P1-026): `zasieg_m` (Zasięg m), `udzwig_t` (Udźwig t), `dodatki` (Dodatkowe wyposażenie)

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
[ℹ️ Banner historyczny] ← RAO-P2-021: zawsze widoczny na górze sekcji Kategorie
  data-testid="history-banner"
  "Raporty kategorii zawierają dane historyczne zaimportowane z poprzedniej aplikacji.
   Archiwalne maszyny i umowy są uwzględnianie wyłącznie w statystykach historycznych."

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

**Dane z:** `GET /stats/by-category?level=main|sub1|sub2|sub3&date_from&date_to&include_archival&category_main[]&category_sub1&category_sub2&article_type`

**Store:** `statsStore.byCategoryData` (CategoryStatsResponse), `statsStore.loadingByCategory`

**Trigger ładowania kategorii:**
- Przełączenie na sub-tab Kategorie
- Zmiana poziomu (main ↔ sub1) gdy drilldownPath.length === 0
- Zmiana date presetu lub kliknięcie "Filtruj"
- Zmiana shared filters (articleType, categoryMains, archivalState)
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
- Stan: `sharedArchivalState` (active/archival/all) → `includeArchival` computed

**RAO-P1-026: Sub-tab "📅 Historia"** (`historySubTab === 'timeline'`):
- `data-testid="timeline-panel"`
- Granularity toggle: Miesiące/Lata (`granularity: ref('month')`)
- Bar chart: `periodBarCanvas` ref, `renderPeriodBarChart()`, max 8 serii wg kategorii
- Pivot table: `pivotData` computed — wiersze=kategorie, kolumny=okresy, sumy
  - Kliknięcie kategorii → `selectPivotCategory(name)` → filtruje `sharedCategoryMains`
- Loading: `statsStore.loadingByPeriod`, Error: `errorByPeriod`, Empty state
- **Dane z:** `GET /stats/by-period?granularity&date_from&date_to&category_main[]&article_type&include_archival`

### Store: `useStatsStore` (stores/stats.js)

**RAO-P1-026 rozszerzenia:**

| Stan | Typ | Opis |
|------|-----|------|
| `loadingByPeriod` | `boolean` | loading dla /stats/by-period |
| `byPeriodData` | `ByPeriodResponse\|null` | dane historyczne per-period |
| `categoriesList` | `CategoriesListNode[]` | drzewo kategorii (dla dropdown) |

| Funkcja | Endpoint |
|---------|----------|
| `fetchByCategory(level, df, dt, includeArchival, categoryMains[], catSub1, catSub2, articleType)` | GET /stats/by-category (URLSearchParams) |
| `fetchByPeriod(granularity, df, dt, categoryMains[], articleType, includeArchival)` | GET /stats/by-period |
| `fetchCategoriesList()` | GET /stats/categories-list |

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
  1. **Dane podstawowe** (typ, numer, okres umowy)
  2. **Kontrahent i adres dostawy** (wybór kontrahenta, adres)
  3. **Warunki finansowe** (handlowiec, oddział, wartość, przedpłata, faktura)
  4. **Kontakt i uwagi** (osoby kontaktowe, email, telefon, uwagi, opcje)
- **RAO-P2-004:** Pola `date_from`/`date_to` zastąpione komponentem `ContractPeriodPicker.vue`
  - Komponent: `frontend/src/components/shared/ContractPeriodPicker.vue`
  - Input 1: `date_from` (date picker) - data rozpoczęcia umowy
  - Input 2: `days` (number input, min=1) - liczba dni trwania umowy
  - Computed: `date_to = date_from + (days - 1) days`
  - Display: "Okres umowy: {date_from_pl} – {date_to_pl}"
  - Emity: `update:dateFrom`, `update:dateTo` → `form.date_from`, `form.date_to`
  - Mount z istniejącymi danymi: `days = (date_to - date_from).days + 1`
  - Label: "Okres umowy *"
  - Walidacja: `v-if="!form.date_from"` → "Podaj datę od"
  - **2026-05-21:** Wyświetlanie dat bez godziny (format: dd.MM.yyyy - dd.MM.yyyy)
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
  - Obsługa błędów: wyświetlanie błędów z backendu (e.response?.data?.detail)
  - Pre-fill: jeśli wyszukiwany termin wygląda jak nazwa (nie jest liczbą), jest używany jako domyślna nazwa
- **RAO-P2-006:** Inline dodawanie artykułu z formularza umowy
  - W pickerze artykułów przycisk "➕ Dodaj nowy artykuł" (prominent CTA)
  - Gdy wyszukiwanie nie zwraca wyników, wyświetlany jest komunikat "Brak wyników dla {search}"
  - Przycisk otwiera modal "Nowy artykuł" z formularzem inline
  - Formularz zawiera wszystkie wymagane pola artykułu:
    - Nazwa artykułu * (required)
    - Typ artykułu (machine/vehicle/tool/service)
    - Checkbox: Artykuł jest usługą (nie sprzętem)
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
    - Nowy artykuł jest dodany do lokalnej listy articlePickerList
    - Artykuł jest automatycznie wybrany (selectArticle)
    - Modal jest zamykany
    - Formularz jest resetowany
  - Walidacja: nazwa artykułu jest wymagana
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

### ArticleFormView.vue — Formularz artykułu (RAO-P1-026)

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
- `category_id` — Kategoria (kaskadowy picker 3-poziomowy)
- `owner_id` — Właściciel/dostawca (picker kontrahentów)
- `rental_days` — Min. dni najmu
- `branch_id` — Filia (select)
- `description` — Opis (textarea)
- `notes` — Uwagi (textarea)

**Layout sekcji "Dane techniczne":**
- `zasieg_m` + `udzwig_t` — grid 2 kolumny (`form-row-2`)
- `dodatki` — pełna szerokość poniżej

**Null handling:** Puste pola number → `null` (nie `0`). Pattern: `if (!payload.x) payload.x = null`

**Edit mode:** `Object.assign(form.value, data)` automatycznie wypełnia wszystkie pola z API.

**Store:** `useArticleStore` (`stores/articles.js`) — `fetchOne`, `create`, `update`, `duplicate`

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

### Emity

| Event | Payload | Opis |
|-------|---------|------|
| `update:dateFrom` | `string \| null` | Emitowana przy zmianie daty rozpoczęcia |
| `update:dateTo` | `string \| null` | Emitowana przy zmianie daty zakończenia (przeliczanej z dni) |

### Interfejs

```
┌─────────────────────────────────────────┐
│ Data od          │ Liczba dni          │
│ [2026-05-25   ]  │ [10              ]  │
├─────────────────────────────────────────┤
│ Okres umowy: 25.05.2026 – 03.06.2026   │
└─────────────────────────────────────────┘
```

### Logika

1. **Input 1: Data od** (`date_from`)
   - Typ: `date` (native HTML5 date picker)
   - Wartość początkowa: `props.dateFrom` lub pusty string

2. **Input 2: Liczba dni** (`days`)
   - Typ: `number`, min=1
   - Wartość początkowa: obliczana z `(date_to - date_from).days + 1` przy mount
   - Walidacja: nie pozwala na wartości < 1

3. **Computed: Data do** (`date_to`)
   - Formula: `date_to = date_from + (days - 1) days`
   - Przykład: `2026-05-25 + 9 dni = 2026-05-03` (czerwiec)
   - Emitowana automatycznie przy zmianie `date_from` lub `days`

4. **Display**
   - Format: `"Okres umowy: {date_from_pl} – {date_to_pl}"`
   - Format daty PL: `dd.MM.yyyy` (np. `25.05.2026 – 03.06.2026`)
   - Widoczne tylko gdy `date_from` i `days >= 1`

### Przykład użycia (ContractFormView.vue)

```vue
<ContractPeriodPicker
  :date-from="form.date_from"
  :date-to="form.date_to"
  @update:date-from="form.date_from = $event"
  @update:date-to="form.date_to = $event"
/>
```

### Kompatybilność z API

- Komponent emituje `date_from` i `date_to` w formacie ISO (YYYY-MM-DD)
- Pełna kompatybilność z istniejącym API backendu
- Możliwość montowania z istniejącymi danymi (edycja umowy)

### Przykłady obliczeń

| date_from | days | date_to | Display |
|-----------|------|---------|---------|
| 2026-05-25 | 1 | 2026-05-25 | 25.05.2026 – 25.05.2026 |
| 2026-05-25 | 10 | 2026-06-03 | 25.05.2026 – 03.06.2026 |
| 2026-05-01 | 31 | 2026-05-31 | 01.05.2026 – 31.05.2026 |
| 2026-12-25 | 10 | 2027-01-03 | 25.12.2026 – 03.01.2027 |

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

