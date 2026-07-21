<script setup lang="ts">
/**
 * P1-205 Faza 2: Widok Dostaw — kalendarz dostaw z umów (S + U) + drill-down drawer.
 *
 * Endpoint (backend P1-205):
 *  - GET /deliveries/calendar?date_from&date_to&machine_id&contractor_id → DeliveryCalendarEvent[]
 *  - GET /contracts/{id} → pełne dane umowy (drill-down, reuse contracts store)
 *
 * Stany: loading (spinner), error (retry), empty (hint).
 * Kalendarz ZAWSZE widoczny (lessons learned z reservations: nie chować gdy brak eventów).
 * Brak CRUD — dostawy powstają przez tworzenie umowy. Context menu wyłączone.
 * Design system: wyłącznie zmienne CSS z style.css.
 */
import { computed, onMounted, ref, watch } from 'vue'
import {
  useDeliveriesStore,
  type DeliveryCalendarEvent,
} from '@/stores/deliveries'
import { useContractStore } from '@/stores/contracts'
import { useArticleStore } from '@/stores/articles'
import { useContractorStore } from '@/stores/contractors'
import { useSettingsStore } from '@/stores/settings'
import ContractorCombobox from '@/components/analytics/ContractorCombobox.vue'
import SearchCombobox from '@/components/shared/SearchCombobox.vue'
import DrillDownDrawer from '@/components/analytics/DrillDownDrawer.vue'
import ExportCsvButton, { type CsvColumn } from '@/components/analytics/ExportCsvButton.vue'
import StateMessage from '@/components/StateMessage.vue'
import { formatDate, formatCurrency } from '@/utils/format'
import { extractErrorMessage } from '@/utils/validation'

const store = useDeliveriesStore()
const contractStore = useContractStore()
const articleStore = useArticleStore()
const contractorStore = useContractorStore()
const settingsStore = useSettingsStore()

// ── Filtry ────────────────────────────────────────────────────────────────────
const filterMachineId = ref<number | null>(null)
const filterSalespersonId = ref<number | null>(null)
const filterContractorId = ref<number | null>(null)
const filterType = ref<'S' | 'U' | ''>('')

// ── Panel dnia (prawa kolumna) ────────────────────────────────────────────────
const selectedDay = ref<string | null>(null)
const showDeliveriesS = ref(true)
const showDeliveriesU = ref(true)

// ── Drill-down drawer (szczegóły umowy) ───────────────────────────────────────
const drawerOpen = ref(false)
const drawerLoading = ref(false)
const drawerError = ref<string | null>(null)
const drawerContract = ref<Record<string, unknown> | null>(null)
const drawerPositions = ref<Record<string, unknown>[]>([])

// ── Kalendarz (month view, zawsze 6 tygodni = 42 dni) ─────────────────────────
const calYear = ref(new Date().getFullYear())
const calMonth = ref(new Date().getMonth()) // 0-based

const monthLabel = computed(() => {
  const d = new Date(calYear.value, calMonth.value, 1)
  return d.toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' })
})

// Zakres dat kalendarza (pierwszy widoczny dzień → ostatni widoczny dzień)
// Fix timezone: toISOString() konwertuje do UTC, co przesuwa datę o offset strefy
// (PL latem UTC+2 → 29 czerwca 00:00 lokalnie = 28 czerwca 22:00 UTC).
// Używamy lokalnego formatowania YYYY-MM-DD zamiast toISOString().slice(0,10).
const toISODate = (d: Date): string => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
const calDateFrom = computed(() => {
  const first = new Date(calYear.value, calMonth.value, 1)
  const dow = (first.getDay() + 6) % 7 // Poniedziałek = 0
  const start = new Date(first)
  start.setDate(first.getDate() - dow)
  return toISODate(start)
})
const calDateTo = computed(() => {
  // Fix cd37e5d: Zawsze 6 tygodni (42 dni) od calDateFrom — stabilny rozmiar
  // kalendarza, nie kurczy się gdy miesiąc ma 4/5 tygodni lub jest pusty.
  const start = new Date(calDateFrom.value + 'T00:00:00')
  const end = new Date(start)
  end.setDate(start.getDate() + 41)
  return toISODate(end)
})

interface CalCell {
  date: string // ISO
  dayNum: number
  inMonth: boolean
  isToday: boolean
  events: DeliveryCalendarEvent[]
}

const WEEKDAYS = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd']

// Eventy kalendarza filtrowane po handlowcu/kontrahencie/typie (machine/contractor filtrowany w API)
// Checkboxy showDeliveriesS/showDeliveriesU filtrują zarówno kalendarz (kropki) jak i panel dnia.
const filteredCalendarEvents = computed<DeliveryCalendarEvent[]>(() => {
  let items = store.calendarEvents
  if (!showDeliveriesS.value) {
    items = items.filter((e) => e.contract_type !== 'S')
  }
  if (!showDeliveriesU.value) {
    items = items.filter((e) => e.contract_type !== 'U')
  }
  if (filterSalespersonId.value != null) {
    items = items.filter((e) => e.salesperson_id === filterSalespersonId.value)
  }
  if (filterContractorId.value != null) {
    items = items.filter((e) => e.contractor_id === filterContractorId.value)
  }
  if (filterType.value !== '') {
    items = items.filter((e) => e.contract_type === filterType.value)
  }
  return items
})

const calendarCells = computed<CalCell[]>(() => {
  const cells: CalCell[] = []
  const start = new Date(calDateFrom.value + 'T00:00:00')
  const end = new Date(calDateTo.value + 'T00:00:00')
  const todayStr = toISODate(new Date())
  const events = filteredCalendarEvents.value
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const iso = toISODate(d)
    cells.push({
      date: iso,
      dayNum: d.getDate(),
      inMonth: d.getMonth() === calMonth.value,
      isToday: iso === todayStr,
      events: events.filter((e) => e.delivery_date === iso),
    })
  }
  return cells
})

function prevMonth() {
  if (calMonth.value === 0) {
    calMonth.value = 11
    calYear.value--
  } else {
    calMonth.value--
  }
}
function nextMonth() {
  if (calMonth.value === 11) {
    calMonth.value = 0
    calYear.value++
  } else {
    calMonth.value++
  }
}
function goToday() {
  const now = new Date()
  calYear.value = now.getFullYear()
  calMonth.value = now.getMonth()
}

// Kolor kropki: S = niebieski (--color-primary), U = pomarańczowy (#E67E22)
function dotClass(e: DeliveryCalendarEvent): string {
  return e.contract_type === 'U' ? 'dot-service' : 'dot-rental'
}

// ── Lista dostaw dnia (panel boczny) ──────────────────────────────────────────
const PAGE_SIZE = 10
const visibleCount = ref(PAGE_SIZE)
const dayEvents = computed<DeliveryCalendarEvent[]>(() => {
  if (!selectedDay.value) return []
  const day = selectedDay.value
  return filteredCalendarEvents.value.filter((e) => e.delivery_date === day)
})
// Stronicowanie listy dnia — pokaż pierwsze N, reszta po "Pokaż więcej"
const visibleDayEvents = computed(() => dayEvents.value.slice(0, visibleCount.value))

const selectedDayLabel = computed(() => {
  if (!selectedDay.value) return ''
  const d = new Date(selectedDay.value + 'T00:00:00')
  const wd = d.toLocaleDateString('pl-PL', { weekday: 'short' })
  return `${selectedDay.value} (${wd})`
})

function selectDay(date: string) {
  selectedDay.value = date
  visibleCount.value = PAGE_SIZE // reset paginacji na nowy dzień
}

// ── Maszyny (do filtra) ───────────────────────────────────────────────────────
interface MachineOption {
  id: number
  name: string
  internal_number: string | null
  is_service: boolean
}

const machineOptions = ref<MachineOption[]>([])

async function loadMachines() {
  try {
    await articleStore.fetchList({ is_service: false, per_page: 200 })
    machineOptions.value = (articleStore.list as MachineOption[])
      .filter((a) => !a.is_service && !(a as { is_external?: boolean }).is_external)
      .map((a) => ({
        ...a,
        name: a.internal_number ? `${a.name} (${a.internal_number})` : a.name,
      }))
  } catch {
    machineOptions.value = []
  }
}

const contractorOptions = computed(() =>
  (contractorStore.list ?? []).map((c: { id: number; name: string }) => ({
    id: c.id,
    name: c.name,
  })),
)

const salespeopleOptions = computed(() =>
  (settingsStore.salespeople ?? []).map((sp: { id: number; name: string }) => ({
    id: sp.id,
    name: sp.name,
  })),
)

// ── Drill-down drawer (pełne dane umowy) ──────────────────────────────────────
async function openDelivery(event: DeliveryCalendarEvent) {
  drawerOpen.value = true
  drawerLoading.value = true
  drawerError.value = null
  drawerContract.value = null
  drawerPositions.value = []
  try {
    const data = await contractStore.fetchOne(event.source_id) as Record<string, unknown>
    drawerContract.value = data
    // Pobierz pozycje umowy (jeśli endpoint dostępny)
    try {
      const positions = await contractStore.fetchPositions(event.source_id) as Record<string, unknown>[]
      drawerPositions.value = positions ?? []
    } catch {
      drawerPositions.value = []
    }
  } catch (e: unknown) {
    drawerError.value = extractErrorMessage(e, 'Błąd pobierania danych umowy')
  } finally {
    drawerLoading.value = false
  }
}

function closeDrawer() {
  drawerOpen.value = false
  drawerError.value = null
}

// ── Tooltip (hover na dniu kalendarza) ────────────────────────────────────────
const tooltipDay = ref<CalCell | null>(null)
function showTooltip(cell: CalCell) {
  tooltipDay.value = cell
}
function hideTooltip() {
  tooltipDay.value = null
}

// ── Czy są dane do pokazania (dla stanów loading/error/empty) ─────────────────
const dataLoaded = ref(false)
const hasData = computed(() => dataLoaded.value)

// ── Data loading ──────────────────────────────────────────────────────────────
async function refreshData() {
  try {
    await store.fetchCalendar(
      calDateFrom.value,
      calDateTo.value,
      filterMachineId.value ?? undefined,
      filterContractorId.value ?? undefined,
    )
  } finally {
    dataLoaded.value = true
  }
}

async function retry() {
  await refreshData()
}

// Watch: zmiana miesiąca / filtru maszyny/kontrahenta → reload kalendarza
watch([calYear, calMonth, filterMachineId, filterContractorId], () => {
  store.fetchCalendar(
    calDateFrom.value,
    calDateTo.value,
    filterMachineId.value ?? undefined,
    filterContractorId.value ?? undefined,
  )
})

// ── Eksport CSV ───────────────────────────────────────────────────────────────
const csvColumns: CsvColumn[] = [
  { key: 'contract_number', label: 'Numer umowy' },
  { key: 'contract_type', label: 'Typ', format: (v: unknown) => (v === 'U' ? 'Usługa' : 'Najem') },
  { key: 'machine_name', label: 'Maszyna' },
  { key: 'internal_number', label: 'Nr wewn.' },
  { key: 'contractor_name', label: 'Kontrahent' },
  { key: 'delivery_date', label: 'Data dostawy', format: (v: unknown) => formatDate(v as string) },
  { key: 'delivery_address', label: 'Adres dostawy' },
  { key: 'city', label: 'Miasto' },
  { key: 'salesperson_name', label: 'Handlowiec' },
]

const csvRows = computed(() =>
  filteredCalendarEvents.value.map((e) => ({
    contract_number: e.contract_number,
    contract_type: e.contract_type,
    machine_name: e.machine_name ?? '',
    internal_number: e.internal_number ?? '',
    contractor_name: e.contractor_name,
    delivery_date: e.delivery_date,
    delivery_address: e.delivery_address ?? '',
    city: e.city ?? '',
    salesperson_name: e.salesperson_name ?? '',
  })),
)

// ── Helpery do drill-down ─────────────────────────────────────────────────────
function contractTypeLabel(t: unknown): string {
  return t === 'U' ? 'Usługa' : 'Najem'
}

function drawerPositionsTotal(): string {
  const total = drawerPositions.value.reduce((sum, p) => {
    const conditions = (p.conditions as Record<string, unknown>[]) ?? []
    return sum + conditions.reduce((s, c) => {
      const r1 = parseFloat(String(c.rate1 ?? '0'))
      const r2 = parseFloat(String(c.rate2 ?? '0'))
      const pc = parseInt(String(c.period_count ?? '0'), 10)
      return s + (r1 + r2) * pc
    }, 0)
  }, 0)
  return formatCurrency(total)
}

onMounted(async () => {
  // Załaduj kontrahentów (combobox filtra)
  if (!contractorStore.list?.length) {
    try {
      await contractorStore.fetchList({ per_page: 500 })
    } catch {
      // ignore — filtr opcjonalny
    }
  }
  // Załaduj handlowców (filtr)
  if (!settingsStore.salespeople?.length) {
    try {
      await settingsStore.fetchSalespeople()
    } catch {
      // ignore — handlowiec opcjonalny
    }
  }
  await loadMachines()
  await refreshData()
  // Domyślnie zaznacz dzisiaj
  selectedDay.value = toISODate(new Date())
})
</script>

<template>
  <div class="deliveries-view" data-testid="deliveries-view">
    <!-- HEADER -->
    <div class="dv-header">
      <h1>Dostawy</h1>
      <ExportCsvButton
        :columns="csvColumns"
        :rows="csvRows"
        filename="dostawy.csv"
        label="Eksport CSV"
      />
    </div>

    <!-- FILTRY -->
    <div class="dv-filters">
      <div class="dv-filter-group">
        <label class="dv-filter-label">Maszyna</label>
        <SearchCombobox
          v-model="filterMachineId"
          :options="machineOptions"
          placeholder="Wszystkie"
          clear-label="Wszystkie"
          data-testid="dv-filter-machine"
        />
      </div>

      <div class="dv-filter-group">
        <label class="dv-filter-label">Handlowiec</label>
        <SearchCombobox
          v-model="filterSalespersonId"
          :options="salespeopleOptions"
          placeholder="Wszyscy"
          clear-label="Wszyscy"
          data-testid="dv-filter-salesperson"
        />
      </div>

      <div class="dv-filter-group">
        <label class="dv-filter-label">Kontrahent</label>
        <ContractorCombobox
          v-model="filterContractorId"
          :contractors="contractorOptions"
          placeholder="Wszyscy"
          data-testid="dv-filter-contractor"
        />
      </div>

      <div class="dv-filter-group">
        <label class="dv-filter-label">Typ</label>
        <select
          v-model="filterType"
          class="dv-filter-select"
          data-testid="dv-filter-type"
        >
          <option value="">Wszystkie</option>
          <option value="S">Najem (S)</option>
          <option value="U">Usługa (U)</option>
        </select>
      </div>
    </div>

    <!-- LEGENDA -->
    <div class="dv-legend">
      <span class="dv-legend-item"><span class="dv-dot dot-rental"></span> Dostawy S (najem)</span>
      <span class="dv-legend-item"><span class="dv-dot dot-service"></span> Dostawy U (usługa)</span>
    </div>

    <!-- ERROR (nad kalendarzem — kalendarz zawsze widoczny) -->
    <StateMessage
      v-if="store.error && !hasData"
      type="error"
      :message="store.error"
      action-label="Spróbuj ponownie"
      @action="retry"
    />

    <!-- LOADING (pierwsze ładowanie — przed kalendarzem) -->
    <StateMessage
      v-if="store.loading && !hasData"
      type="loading"
      message="Ładowanie dostaw…"
    />

    <!-- TREŚĆ: kalendarz (lewa) + panel dnia (prawa) — zawsze widoczny po pierwszym load -->
    <div v-if="hasData" class="dv-content">
      <!-- Kalendarz (lewa) -->
      <div class="dv-calendar" data-testid="dv-calendar">
        <div class="dv-cal-header">
          <button class="dv-cal-nav" data-testid="dv-cal-prev" @click="prevMonth">←</button>
          <span class="dv-cal-month">{{ monthLabel }}</span>
          <button class="dv-cal-nav" data-testid="dv-cal-next" @click="nextMonth">→</button>
          <button class="dv-cal-today" data-testid="dv-cal-today" @click="goToday">Dziś</button>
        </div>

        <div class="dv-cal-grid">
          <div v-for="wd in WEEKDAYS" :key="wd" class="dv-cal-dow">{{ wd }}</div>
          <div
            v-for="cell in calendarCells"
            :key="cell.date"
            :class="['dv-cal-cell', { 'dv-cell-out': !cell.inMonth, 'dv-cell-today': cell.isToday, 'dv-cell-selected': selectedDay === cell.date }]"
            data-testid="dv-cal-cell"
            @click="selectDay(cell.date)"
            @mouseenter="showTooltip(cell)"
            @mouseleave="hideTooltip"
          >
            <span class="dv-cal-daynum">{{ cell.dayNum }}</span>
            <div class="dv-cal-dots">
              <span
                v-for="(e, i) in cell.events.slice(0, 4)"
                :key="i"
                :class="['dv-dot', dotClass(e)]"
                @click.stop="openDelivery(e)"
              ></span>
              <span v-if="cell.events.length > 4" class="dv-dot-more">+{{ cell.events.length - 4 }}</span>
            </div>

            <!-- TOOLTIP -->
            <div v-if="tooltipDay === cell && cell.events.length" class="dv-tooltip">
              <div v-for="(e, i) in cell.events" :key="i" class="dv-tooltip-event">
                <span :class="['dv-dot', dotClass(e)]"></span>
                <span class="dv-tooltip-text">
                  <strong>{{ e.contract_number }}</strong>
                  <template v-if="e.machine_name"> — {{ e.machine_name }}</template>
                  <template v-if="e.internal_number"> ({{ e.internal_number }})</template>
                  <br />
                  <template v-if="e.contractor_name">{{ e.contractor_name }}</template>
                  <template v-if="e.delivery_address"><br />{{ e.delivery_address }}</template>
                  <template v-if="e.city">, {{ e.city }}</template>
                  <br />
                  <small>{{ formatDate(e.delivery_date) }}</small>
                  <small v-if="e.contract_type === 'U'"> (usługa)</small>
                  <small v-else> (najem)</small>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel dnia (prawa) -->
      <div class="dv-day-panel" data-testid="dv-day-panel">
        <div v-if="!selectedDay" class="dv-day-empty">Kliknij dzień w kalendarzu aby zobaczyć dostawy</div>
        <template v-else>
          <div class="dv-day-header">
            <h3>{{ selectedDayLabel }}</h3>
          </div>
          <div class="dv-day-filters">
            <label><input type="checkbox" v-model="showDeliveriesS" /> Dostawy S</label>
            <label><input type="checkbox" v-model="showDeliveriesU" /> Dostawy U</label>
          </div>
          <div class="dv-day-events">
            <div
              v-for="e in visibleDayEvents"
              :key="`${e.source_id}-${e.contract_type}`"
              class="dv-day-event"
              data-testid="dv-day-event"
              @click="openDelivery(e)"
            >
              <span :class="['dv-dot', dotClass(e)]"></span>
              <div>
                <strong>{{ e.contract_number }} <span class="dv-type-badge">{{ e.contract_type }}</span></strong>
                <small v-if="e.machine_name">{{ e.machine_name }}</small>
                <small v-if="e.internal_number"> ({{ e.internal_number }})</small>
                <small v-if="e.contractor_name">{{ e.contractor_name }}</small>
                <small v-if="e.delivery_address">{{ e.delivery_address }}<template v-if="e.city">, {{ e.city }}</template></small>
                <small v-if="e.salesperson_name">Handlowiec: {{ e.salesperson_name }}</small>
              </div>
            </div>
            <div v-if="dayEvents.length === 0" class="dv-day-no-events">Brak dostaw tego dnia</div>
            <button
              v-if="dayEvents.length > visibleCount"
              class="dv-day-show-more"
              data-testid="dv-day-show-more"
              @click="visibleCount += PAGE_SIZE"
            >
              Pokaż więcej ({{ dayEvents.length - visibleCount }} pozostało)
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- EMPTY (kalendarz pusty — ale widoczny, hint w panelu dnia) -->
    <StateMessage
      v-if="hasData && !store.loading && filteredCalendarEvents.length === 0"
      type="empty"
      message="Brak dostaw w wybranym zakresie. Dostawy powstają automatycznie przy tworzeniu umowy."
    />

    <!-- DRILL-DOWN DRAWER (pełne dane umowy) -->
    <DrillDownDrawer
      :open="drawerOpen"
      :title="drawerContract ? `Umowa ${String(drawerContract.number ?? '')}` : 'Umowa'"
      :subtitle="drawerContract ? String(drawerContract.contractor_name ?? '') : ''"
      :loading="drawerLoading"
      :error="drawerError ?? undefined"
      @close="closeDrawer"
    >
      <div v-if="drawerContract" class="dv-drawer-content">
        <!-- Sekcja: Dane ogólne -->
        <div class="dv-drawer-section">
          <h4>Dane ogólne</h4>
          <div class="dv-drawer-grid">
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Numer</span>
              <span class="dv-drawer-value">{{ drawerContract.number ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Typ</span>
              <span class="dv-drawer-value">{{ contractTypeLabel(drawerContract.contract_type) }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Kontrahent</span>
              <span class="dv-drawer-value">{{ drawerContract.contractor_name ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Handlowiec</span>
              <span class="dv-drawer-value">{{ drawerContract.salesperson_name ?? drawerContract.salesperson_id ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Data od</span>
              <span class="dv-drawer-value">{{ formatDate(drawerContract.date_from as string) }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Data do</span>
              <span class="dv-drawer-value">{{ formatDate(drawerContract.date_to as string) }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Status</span>
              <span class="dv-drawer-value">
                <span v-if="drawerContract.is_settled" class="dv-status dv-status-settled">Rozliczona</span>
                <span v-else class="dv-status dv-status-open">Otwarta</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Sekcja: Adres dostawy -->
        <div class="dv-drawer-section">
          <h4>Adres dostawy</h4>
          <div class="dv-drawer-grid">
            <div class="dv-drawer-field dv-drawer-field-wide">
              <span class="dv-drawer-label">Adres</span>
              <span class="dv-drawer-value">{{ drawerContract.delivery_address ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Miasto</span>
              <span class="dv-drawer-value">{{ drawerContract.city ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Kod pocztowy</span>
              <span class="dv-drawer-value">{{ drawerContract.postal_code ?? '—' }}</span>
            </div>
          </div>
        </div>

        <!-- Sekcja: Kontakt -->
        <div class="dv-drawer-section">
          <h4>Kontakt</h4>
          <div class="dv-drawer-grid">
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Osoba kontaktowa</span>
              <span class="dv-drawer-value">{{ drawerContract.contact_person1 ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Telefon</span>
              <span class="dv-drawer-value">{{ drawerContract.contact_phone1 ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Email</span>
              <span class="dv-drawer-value">{{ drawerContract.email ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Telefon firmy</span>
              <span class="dv-drawer-value">{{ drawerContract.phone ?? '—' }}</span>
            </div>
          </div>
        </div>

        <!-- Sekcja: Opłaty i warunki -->
        <div class="dv-drawer-section">
          <h4>Opłaty i warunki</h4>
          <div class="dv-drawer-grid">
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Zaliczka</span>
              <span class="dv-drawer-value">{{ formatCurrency(drawerContract.prepayment_amount as number | string) }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Dokument zaliczki</span>
              <span class="dv-drawer-value">{{ drawerContract.prepayment_document ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Dni robocze / tydz.</span>
              <span class="dv-drawer-value">{{ drawerContract.working_days_per_week ?? '—' }}</span>
            </div>
            <div class="dv-drawer-field">
              <span class="dv-drawer-label">Wartość pozycji</span>
              <span class="dv-drawer-value">{{ drawerPositionsTotal() }}</span>
            </div>
          </div>
        </div>

        <!-- Sekcja: Notatki -->
        <div v-if="drawerContract.notes_contract || drawerContract.notes_protocol" class="dv-drawer-section">
          <h4>Notatki</h4>
          <div class="dv-drawer-notes">
            <div v-if="drawerContract.notes_contract" class="dv-drawer-note">
              <span class="dv-drawer-label">Notatka umowy</span>
              <p>{{ drawerContract.notes_contract }}</p>
            </div>
            <div v-if="drawerContract.notes_protocol" class="dv-drawer-note">
              <span class="dv-drawer-label">Notatka protokołu</span>
              <p>{{ drawerContract.notes_protocol }}</p>
            </div>
          </div>
        </div>

        <!-- Sekcja: Pozycje umowy -->
        <div v-if="drawerPositions.length" class="dv-drawer-section">
          <h4>Pozycje umowy ({{ drawerPositions.length }})</h4>
          <div class="dv-drawer-positions">
            <div
              v-for="(pos, i) in drawerPositions"
              :key="i"
              class="dv-drawer-position"
            >
              <div class="dv-drawer-position-header">
                <strong>{{ pos.machine_name ?? pos.service_name ?? 'Pozycja' }}</strong>
                <span v-if="pos.internal_number"> ({{ pos.internal_number }})</span>
                <span class="dv-drawer-position-days" v-if="pos.rental_days">{{ pos.rental_days }} dni</span>
              </div>
              <div v-if="pos.conditions && (pos.conditions as Record<string, unknown>[]).length" class="dv-drawer-conditions">
                <div
                  v-for="(cond, ci) in (pos.conditions as Record<string, unknown>[])"
                  :key="ci"
                  class="dv-drawer-condition"
                >
                  <span>{{ cond.billing_label ?? cond.rate_type_name ?? 'Warunek' }}</span>
                  <span>{{ formatCurrency(cond.rate1 as number | string) }}<template v-if="cond.rate2"> / {{ formatCurrency(cond.rate2 as number | string) }}</template></span>
                  <span v-if="cond.period_count">{{ cond.period_count }} × {{ cond.period_from }}–{{ cond.period_to }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DrillDownDrawer>
  </div>
</template>

<style scoped>
.deliveries-view {
  padding: var(--spacing-6);
  font-family: var(--font-family);
  color: var(--color-text-body);
  max-width: 1400px;
  margin: 0 auto;
}

.dv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-4);
}
.dv-header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-heading);
  margin: 0;
}

/* Treść: kalendarz + panel dnia (side-by-side) */
.dv-content {
  display: flex;
  gap: var(--spacing-4);
  align-items: flex-start;
}
.dv-calendar {
  flex: 1;
  min-width: 0;
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-4);
}

/* Panel dnia (prawa) */
.dv-day-panel {
  flex: 0 0 340px;
  max-width: 400px;
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-4);
  min-height: 400px;
}
.dv-day-empty {
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--spacing-6);
  font-size: var(--font-size-sm);
}
.dv-day-header h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-3);
}
.dv-day-filters {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--color-border);
}
.dv-day-filters label {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.dv-day-events {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  max-height: 60vh;
  overflow-y: auto;
}
.dv-day-show-more {
  margin-top: var(--spacing-2);
  padding: var(--spacing-2);
  background: var(--color-bg-light);
  border: 1px dashed var(--color-border);
  border-radius: var(--border-radius-sm);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  text-align: center;
}
.dv-day-show-more:hover {
  background: var(--color-bg-card-hover);
}
.dv-day-event {
  display: flex;
  gap: var(--spacing-2);
  padding: var(--spacing-2);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  background: var(--color-bg-light);
}
.dv-day-event:hover {
  background: var(--color-bg-card-hover);
}
.dv-day-event strong {
  display: block;
  font-size: var(--font-size-sm);
}
.dv-day-event small {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.dv-type-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: var(--border-radius-sm);
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  background: var(--color-primary);
  color: var(--color-text-on-primary);
}
.dv-day-no-events {
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--spacing-4);
  font-size: var(--font-size-sm);
}

/* Filtry */
.dv-filters {
  display: flex;
  gap: var(--spacing-4);
  flex-wrap: wrap;
  align-items: flex-end;
  background: var(--color-bg-card);
  padding: var(--spacing-4);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--spacing-4);
}
.dv-filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}
.dv-filter-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.dv-filter-select {
  width: 220px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  background: var(--color-bg-white);
  box-sizing: border-box;
}
.dv-filter-select:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* Legenda */
.dv-legend {
  display: flex;
  gap: var(--spacing-5);
  margin-bottom: var(--spacing-3);
  flex-wrap: wrap;
}
.dv-legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Kalendarz — header/grid/cell */
.dv-cal-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}
.dv-cal-month {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-heading);
  text-transform: capitalize;
  min-width: 180px;
  text-align: center;
}
.dv-cal-nav {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-card);
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: var(--font-size-base);
  color: var(--color-text-body);
  transition: all 0.15s;
}
.dv-cal-nav:hover {
  background: var(--color-bg-light);
  border-color: var(--color-border-hover);
}
.dv-cal-today {
  margin-left: auto;
  padding: var(--spacing-1) var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-card);
  font-family: var(--font-family);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  color: var(--color-text-body);
}
.dv-cal-today:hover {
  background: var(--color-bg-light);
}

.dv-cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: minmax(84px, auto);
  gap: 2px;
}
.dv-cal-dow {
  text-align: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-muted);
  padding: var(--spacing-2) 0;
  text-transform: uppercase;
}
.dv-cal-cell {
  position: relative;
  min-height: 84px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-1);
  cursor: pointer;
  background: var(--color-bg-card);
  transition: background 0.15s;
}
.dv-cal-cell:hover {
  background: var(--color-bg-light);
}
.dv-cell-out {
  background: var(--color-bg-light);
  opacity: 0.6;
}
.dv-cell-today {
  border-color: var(--color-primary);
  border-width: 2px;
}
.dv-cell-selected {
  background: var(--color-bg-light);
  border-color: var(--color-primary);
  box-shadow: inset 0 0 0 1px var(--color-primary);
}
.dv-cal-daynum {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
.dv-cal-dots {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: var(--spacing-1);
  align-items: center;
}

/* Dots: S = niebieski (--color-primary), U = pomarańczowy (#E67E22) */
.dv-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  cursor: pointer;
}
.dot-rental {
  background: var(--color-primary);
}
.dot-service {
  background: #E67E22;
}
.dv-dot-more {
  font-size: 10px;
  color: var(--color-text-muted);
  font-weight: var(--font-weight-semibold);
}

/* Tooltip */
.dv-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  box-shadow: var(--shadow-modal);
  padding: var(--spacing-2) var(--spacing-3);
  z-index: 50;
  min-width: 220px;
  max-width: 300px;
  margin-bottom: 4px;
}
.dv-tooltip-event {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-1) 0;
  border-bottom: 1px solid var(--color-border);
}
.dv-tooltip-event:last-child {
  border-bottom: none;
}
.dv-tooltip-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-body);
  line-height: var(--line-height-normal);
}
.dv-tooltip-text small {
  color: var(--color-text-muted);
}

/* Drill-down drawer content */
.dv-drawer-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-5);
}
.dv-drawer-section {
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-4);
}
.dv-drawer-section:last-child {
  border-bottom: none;
}
.dv-drawer-section h4 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
  margin: 0 0 var(--spacing-3);
}
.dv-drawer-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-3);
}
.dv-drawer-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dv-drawer-field-wide {
  grid-column: 1 / -1;
}
.dv-drawer-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.dv-drawer-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
}

/* Status badges */
.dv-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--border-radius-pill);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}
.dv-status-open {
  background: var(--color-bg-light);
  color: var(--color-text-body);
  border: 1px solid var(--color-border);
}
.dv-status-settled {
  background: var(--color-success);
  color: var(--color-bg-white);
}

/* Notatki */
.dv-drawer-notes {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}
.dv-drawer-note p {
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  margin-top: var(--spacing-1);
}

/* Pozycje umowy */
.dv-drawer-positions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}
.dv-drawer-position {
  background: var(--color-bg-light);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-3);
}
.dv-drawer-position-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-2);
}
.dv-drawer-position-days {
  margin-left: auto;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.dv-drawer-conditions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}
.dv-drawer-condition {
  display: flex;
  gap: var(--spacing-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  padding: var(--spacing-1) 0;
  border-top: 1px solid var(--color-border);
}
.dv-drawer-condition span:first-child {
  flex: 1;
  color: var(--color-text-body);
  font-weight: var(--font-weight-medium);
}
</style>
