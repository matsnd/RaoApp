<script setup lang="ts">
/**
 * RAO-P3 (Phase 3): Widok Rezerwacji maszyn — kalendarz + lista + modal CRUD.
 *
 * Endpointy (backend Phase 2):
 *  - GET /reservations/calendar?date_from&date_to&machine_id → CalendarEvent[]
 *  - GET /reservations/with-machines → ReservationWithMachine[]
 *  - POST /reservations, PUT /reservations/{id}, DELETE /reservations/{id}
 *
 * Stany: loading (spinner), error (retry), empty (hint + CTA).
 * Design system: wyłącznie zmienne CSS z style.css.
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  useReservationsStore,
  type CalendarEvent,
  type ReservationWithMachine,
  type ReservationPayload,
  type ReservationUpdatePayload,
} from '@/stores/reservations'
import { useArticleStore } from '@/stores/articles'
import { useContractorStore } from '@/stores/contractors'
import { useSettingsStore } from '@/stores/settings'  // P1-119: salespeople
import ContractorCombobox from '@/components/analytics/ContractorCombobox.vue'
import SearchCombobox from '@/components/shared/SearchCombobox.vue'
import StateMessage from '@/components/StateMessage.vue'
import { formatDate } from '@/utils/format'
import { extractErrorMessage } from '@/utils/validation'

const store = useReservationsStore()
const articleStore = useArticleStore()
const contractorStore = useContractorStore()
const settingsStore = useSettingsStore()  // P1-119: salespeople
const router = useRouter()

// ── Filtry ────────────────────────────────────────────────────────────────────
const filterMachineId = ref<number | null>(null)
const filterSalespersonId = ref<number | null>(null)  // P1-119+: filtr handlowca
const filterContractorId = ref<number | null>(null)

// ── Panel dnia (prawa kolumna) ────────────────────────────────────────────────
const selectedDay = ref<string | null>(null)
const showReservations = ref(true)
const showContracts = ref(true)
const contextMenu = ref<{ x: number; y: number; date: string } | null>(null)

// ── Kalendarz (month view) ────────────────────────────────────────────────────
const calYear = ref(new Date().getFullYear())
const calMonth = ref(new Date().getMonth()) // 0-based

const monthLabel = computed(() => {
  const d = new Date(calYear.value, calMonth.value, 1)
  return d.toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' })
})

// Zakres dat kalendarza (pierwszy widoczny dzień → ostatni widoczny dzień)
const calDateFrom = computed(() => {
  const first = new Date(calYear.value, calMonth.value, 1)
  const dow = (first.getDay() + 6) % 7 // Poniedziałek = 0
  const start = new Date(first)
  start.setDate(first.getDate() - dow)
  return start.toISOString().slice(0, 10)
})
const calDateTo = computed(() => {
  // Zawsze 6 tygodni (42 dni) od calDateFrom — stabilny rozmiar kalendarza,
  // nie kurczy się gdy miesiąc ma 4/5 tygodni lub jest pusty (brak eventów).
  const start = new Date(calDateFrom.value + 'T00:00:00')
  const end = new Date(start)
  end.setDate(start.getDate() + 41)
  return end.toISOString().slice(0, 10)
})

interface CalCell {
  date: string // ISO
  dayNum: number
  inMonth: boolean
  isToday: boolean
  events: CalendarEvent[]
}

const WEEKDAYS = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd']

const calendarCells = computed<CalCell[]>(() => {
  const cells: CalCell[] = []
  const start = new Date(calDateFrom.value + 'T00:00:00')
  const end = new Date(calDateTo.value + 'T00:00:00')
  const todayStr = new Date().toISOString().slice(0, 10)
  const events = filteredCalendarEvents.value
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const iso = d.toISOString().slice(0, 10)
    cells.push({
      date: iso,
      dayNum: d.getDate(),
      inMonth: d.getMonth() === calMonth.value,
      isToday: iso === todayStr,
      events: events.filter((e) => iso >= e.date_from && iso <= e.date_to),
    })
  }
  return cells
})

// Eventy kalendarza filtrowane po handlowcu/kontrahencie/typie (machine filtrowany w API)
// Checkboxy showReservations/showContracts filtrują zarówno kalendarz (kropki) jak i panel dnia.
const filteredCalendarEvents = computed<CalendarEvent[]>(() => {
  let items = store.calendarEvents
  if (!showReservations.value) {
    items = items.filter((e) => e.source !== 'reservation')
  }
  if (!showContracts.value) {
    items = items.filter((e) => e.source !== 'contract')
  }
  if (filterSalespersonId.value != null) {
    items = items.filter((e) => e.source === 'reservation' && e.salesperson_id === filterSalespersonId.value)
  }
  if (filterContractorId.value != null) {
    items = items.filter((e) => e.contractor_id === filterContractorId.value)
  }
  return items
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

// Kolor kropki event
function dotClass(e: CalendarEvent): string {
  if (e.source === 'contract') return 'dot-contract'
  return 'dot-confirmed'
}

// ── Lista rezerwacji dnia (panel boczny) ──────────────────────────────────────
const PAGE_SIZE = 10
const visibleCount = ref(PAGE_SIZE)
const dayEvents = computed<CalendarEvent[]>(() => {
  if (!selectedDay.value) return []
  const day = selectedDay.value
  return filteredCalendarEvents.value.filter(
    (e) => day >= e.date_from && day <= e.date_to,
  )
})
// P1-118: stronicowanie listy dnia — pokaż pierwsze N, reszta po "Pokaż więcej"
const visibleDayEvents = computed(() => dayEvents.value.slice(0, visibleCount.value))

const selectedDayLabel = computed(() => {
  if (!selectedDay.value) return ''
  const d = new Date(selectedDay.value + 'T00:00:00')
  const wd = d.toLocaleDateString('pl-PL', { weekday: 'short' })
  return `${selectedDay.value} (${wd})`
})

function selectDay(date: string) {
  selectedDay.value = date
  visibleCount.value = PAGE_SIZE  // P1-118: reset paginacji na nowy dzień
}

function onContextMenu(event: MouseEvent, cell: CalCell) {
  contextMenu.value = { x: event.clientX, y: event.clientY, date: cell.date }
}

function closeContextMenu() {
  contextMenu.value = null
}

function ctxAddReservation() {
  if (!contextMenu.value) return
  openCreate(contextMenu.value.date)
  closeContextMenu()
}

function ctxAddContract() {
  if (!contextMenu.value) return
  router.push({ name: 'ContractNew', query: { date: contextMenu.value.date } })
  closeContextMenu()
}

// ── Maszyny (do selecta w modalu + filtru) ───────────────────────────────────
interface MachineOption {
  id: number
  name: string
  internal_number: string | null
  is_service: boolean
}

const machineOptions = ref<MachineOption[]>([])

async function loadMachines() {
  try {
    // Tylko non-service, non-external (sprzęt aktywny)
    await articleStore.fetchList({ is_service: false, per_page: 200 })
    machineOptions.value = (articleStore.list as MachineOption[])
      .filter((a) => !a.is_service && !a.is_external)
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

// P1-119: handlowcy do selecta w modalu
const salespeopleOptions = computed(() =>
  (settingsStore.salespeople ?? []).map((sp: { id: number; name: string }) => ({
    id: sp.id,
    name: sp.name,
  })),
)

// ── Modal CRUD ────────────────────────────────────────────────────────────────
interface ModalState {
  open: boolean
  mode: 'create' | 'edit' | 'view'
  reservationId: number | null
  // contract read-only info
  contractInfo: CalendarEvent | null
  form: {
    machine_id: number | null
    contractor_id: number | null
    salesperson_id: number | null  // P1-119
    reserved_from: string
    reserved_to: string
    note: string
  }
}

const modal = ref<ModalState>({
  open: false,
  mode: 'create',
  reservationId: null,
  contractInfo: null,
  form: {
    machine_id: null,
    contractor_id: null,
    salesperson_id: null,  // P1-119
    reserved_from: '',
    reserved_to: '',
    note: '',
  },
})

const modalSaving = ref(false)
const modalError = ref<string | null>(null)
const formValid = computed(() => {
  if (modal.value.mode === 'view') return true
  const f = modal.value.form
  if (!f.machine_id) return false
  if (!f.reserved_from || !f.reserved_to) return false
  if (f.reserved_from > f.reserved_to) return false
  return true
})

function openCreate(presetDate?: string) {
  const today = presetDate || new Date().toISOString().slice(0, 10)
  modal.value = {
    open: true,
    mode: 'create',
    reservationId: null,
    contractInfo: null,
    form: {
      machine_id: filterMachineId.value,
      contractor_id: filterContractorId.value,
      salesperson_id: null,  // P1-119
      reserved_from: today,
      reserved_to: today,
      note: '',
    },
  }
  modalError.value = null
}

function openEdit(r: ReservationWithMachine | CalendarEvent) {
  // Jeśli to event z umowy (read-only)
  if ('source' in r && r.source === 'contract') {
    const ev = r as CalendarEvent
    modal.value = {
      open: true,
      mode: 'view',
      reservationId: null,
      contractInfo: ev,
      form: {
        machine_id: ev.machine_id,
        contractor_id: ev.contractor_id,
        salesperson_id: ev.salesperson_id ?? null,  // P1-119
        reserved_from: ev.date_from,
        reserved_to: ev.date_to,
        note: ev.note ?? '',
      },
    }
    modalError.value = null
    return
  }
  // Rezerwacja (edycja) — z listy (ReservationWithMachine) lub kalendarza (CalendarEvent source=reservation)
  const isList = 'reserved_from' in r
  const from = isList ? (r as ReservationWithMachine).reserved_from : (r as CalendarEvent).date_from
  const to = isList ? (r as ReservationWithMachine).reserved_to : (r as CalendarEvent).date_to
  const id = isList ? (r as ReservationWithMachine).id : (r as CalendarEvent).source_id
  modal.value = {
    open: true,
    mode: 'edit',
    reservationId: id,
    contractInfo: null,
    form: {
      machine_id: r.machine_id,
      contractor_id: r.contractor_id ?? null,
      salesperson_id: (r as any).salesperson_id ?? null,  // P1-119
      reserved_from: from,
      reserved_to: to,
      note: r.note ?? '',
    },
  }
  modalError.value = null
}

function closeModal() {
  modal.value.open = false
  modalError.value = null
}

async function saveReservation() {
  if (!formValid.value) return
  modalSaving.value = true
  modalError.value = null
  const f = modal.value.form
  try {
    if (modal.value.mode === 'create') {
      const payload: ReservationPayload = {
        machine_id: f.machine_id!,
        reserved_from: f.reserved_from,
        reserved_to: f.reserved_to,
        note: f.note || null,
        contractor_id: f.contractor_id,
        salesperson_id: f.salesperson_id,  // P1-119
      }
      await store.create(payload)
    } else if (modal.value.mode === 'edit' && modal.value.reservationId != null) {
      const payload: ReservationUpdatePayload = {
        reserved_from: f.reserved_from,
        reserved_to: f.reserved_to,
        note: f.note || null,
        contractor_id: f.contractor_id,
        salesperson_id: f.salesperson_id,  // P1-119
      }
      await store.update(modal.value.reservationId, payload)
    }
    closeModal()
    await refreshData()
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { detail?: string } } }
    if (err.response?.status === 409) {
      modalError.value = 'Konflikt: maszyna jest już zarezerwowana w tym terminie.'
    } else {
      modalError.value = extractErrorMessage(err, 'Błąd zapisu rezerwacji')
    }
  } finally {
    modalSaving.value = false
  }
}

async function deleteReservation() {
  if (modal.value.reservationId == null) return
  if (!confirm('Czy na pewno usunąć tę rezerwację?')) return
  modalSaving.value = true
  modalError.value = null
  try {
    await store.remove(modal.value.reservationId)
    closeModal()
    await refreshData()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    modalError.value = err.response?.data?.detail || 'Błąd usuwania rezerwacji'
  } finally {
    modalSaving.value = false
  }
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
const hasData = computed(() => dataLoaded.value)
const dataLoaded = ref(false)

// ── Data loading ──────────────────────────────────────────────────────────────
async function refreshData() {
  try {
    await store.fetchCalendar(calDateFrom.value, calDateTo.value, filterMachineId.value ?? undefined)
  } finally {
    dataLoaded.value = true
  }
}

async function retry() {
  await refreshData()
}

// Watch: zmiana miesiąca / filtru maszyny → reload kalendarza
watch([calYear, calMonth, filterMachineId], () => {
  store.fetchCalendar(calDateFrom.value, calDateTo.value, filterMachineId.value ?? undefined)
})

onMounted(async () => {
  // Załaduj kontrahentów (combobox filtra + modal)
  if (!contractorStore.list?.length) {
    try {
      await contractorStore.fetchList({ per_page: 500 })
    } catch {
      // ignore — filtr opcjonalny
    }
  }
  // P1-119: Załaduj handlowców (select w modalu)
  if (!settingsStore.salespeople?.length) {
    try {
      await settingsStore.fetchSalespeople()
    } catch {
      // ignore — handlowiec opcjonalny
    }
  }
  await loadMachines()
  await refreshData()
  // Domyślnie zaznacz dzisiaj (jakby użytkownik kliknął)
  selectedDay.value = new Date().toISOString().slice(0, 10)
})
</script>

<template>
  <div class="reservations-view" data-testid="reservations-view">
    <!-- HEADER -->
    <div class="rv-header">
      <h1>Rezerwacje maszyn</h1>
      <button class="btn btn-primary rv-add-btn" data-testid="rv-add-btn" @click="openCreate()">
        + Dodaj rezerwację
      </button>
    </div>

    <!-- FILTRY -->
    <div class="rv-filters">
      <div class="rv-filter-group">
        <label class="rv-filter-label">Maszyna</label>
        <SearchCombobox
          v-model="filterMachineId"
          :options="machineOptions"
          placeholder="Wszystkie"
          :clear-label="'Wszystkie'"
          data-testid="rv-filter-machine"
        />
      </div>

      <div class="rv-filter-group">
        <label class="rv-filter-label">Handlowiec</label>
        <SearchCombobox
          v-model="filterSalespersonId"
          :options="salespeopleOptions"
          placeholder="Wszyscy"
          :clear-label="'Wszyscy'"
          data-testid="rv-filter-salesperson"
        />
      </div>

      <div class="rv-filter-group">
        <label class="rv-filter-label">Kontrahent</label>
        <ContractorCombobox
          v-model="filterContractorId"
          :contractors="contractorOptions"
          placeholder="Wszyscy"
          data-testid="rv-filter-contractor"
        />
      </div>
    </div>

    <!-- LEGENDA -->
    <div class="rv-legend">
      <span class="rv-legend-item"><span class="rv-dot dot-confirmed"></span> Rezerwacja</span>
      <span class="rv-legend-item"><span class="rv-dot dot-contract"></span> Umowa</span>
    </div>

    <!-- LOADING -->
    <StateMessage
      v-if="store.loadingCalendar && !hasData"
      type="loading"
      message="Ładowanie rezerwacji…"
    />

    <!-- ERROR -->
    <StateMessage
      v-else-if="store.error && !hasData"
      type="error"
      :message="store.error"
      action-label="Spróbuj ponownie"
      @action="retry"
    />

    <!-- EMPTY -->
    <StateMessage
      v-else-if="!hasData"
      type="empty"
      message="Brak rezerwacji. Dodaj pierwszą rezerwację."
      action-label="+ Dodaj rezerwację"
      @action="openCreate()"
    />

    <!-- TREŚĆ: kalendarz (lewa) + panel dnia (prawa) -->
    <div v-else class="rv-content">
      <!-- Kalendarz (lewa) -->
      <div class="rv-calendar" data-testid="rv-calendar">
        <div class="rv-cal-header">
          <button class="rv-cal-nav" data-testid="rv-cal-prev" @click="prevMonth">←</button>
          <span class="rv-cal-month">{{ monthLabel }}</span>
          <button class="rv-cal-nav" data-testid="rv-cal-next" @click="nextMonth">→</button>
          <button class="rv-cal-today" data-testid="rv-cal-today" @click="goToday">Dziś</button>
        </div>

        <div class="rv-cal-grid">
          <div v-for="wd in WEEKDAYS" :key="wd" class="rv-cal-dow">{{ wd }}</div>
          <div
            v-for="cell in calendarCells"
            :key="cell.date"
            :class="['rv-cal-cell', { 'rv-cell-out': !cell.inMonth, 'rv-cell-today': cell.isToday, 'rv-cell-selected': selectedDay === cell.date }]"
            data-testid="rv-cal-cell"
            @click="selectDay(cell.date)"
            @contextmenu.prevent="onContextMenu($event, cell)"
            @mouseenter="showTooltip(cell)"
            @mouseleave="hideTooltip"
          >
            <span class="rv-cal-daynum">{{ cell.dayNum }}</span>
            <div class="rv-cal-dots">
              <span
                v-for="(e, i) in cell.events.slice(0, 4)"
                :key="i"
                :class="['rv-dot', dotClass(e)]"
                @click.stop="openEdit(e)"
              ></span>
              <span v-if="cell.events.length > 4" class="rv-dot-more">+{{ cell.events.length - 4 }}</span>
            </div>

            <!-- TOOLTIP -->
            <div v-if="tooltipDay === cell && cell.events.length" class="rv-tooltip">
              <div v-for="(e, i) in cell.events" :key="i" class="rv-tooltip-event">
                <span :class="['rv-dot', dotClass(e)]"></span>
                <span class="rv-tooltip-text">
                  <strong>{{ e.machine_name || e.article_name || e.internal_number || 'Maszyna' }}</strong>
                  <template v-if="e.contractor_name"> — {{ e.contractor_name }}</template>
                  <br />
                  <small>{{ formatDate(e.date_from) }} – {{ formatDate(e.date_to) }}</small>
                  <small v-if="e.source === 'contract'"> (umowa)</small>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel dnia (prawa) -->
      <div class="rv-day-panel" data-testid="rv-day-panel">
        <div v-if="!selectedDay" class="rv-day-empty">Kliknij dzień w kalendarzu aby zobaczyć rezerwacje</div>
        <template v-else>
          <div class="rv-day-header">
            <h3>{{ selectedDayLabel }}</h3>
          </div>
          <div class="rv-day-filters">
            <label><input type="checkbox" v-model="showReservations" /> Blokady rezerwacjami</label>
            <label><input type="checkbox" v-model="showContracts" /> Blokady umowami</label>
          </div>
          <div class="rv-day-events">
            <div v-for="e in visibleDayEvents" :key="`${e.source}-${e.source_id}`" class="rv-day-event" data-testid="rv-day-event" @click="openEdit(e)">
              <span :class="['rv-dot', dotClass(e)]"></span>
              <div>
                <strong>{{ e.machine_name || 'Maszyna' }}</strong>
                <small>{{ formatDate(e.date_from) }} – {{ formatDate(e.date_to) }}</small>
                <small v-if="e.contractor_name">{{ e.contractor_name }}</small>
              </div>
            </div>
            <div v-if="dayEvents.length === 0" class="rv-day-no-events">Brak blokad tego dnia</div>
            <button
              v-if="dayEvents.length > visibleCount"
              class="rv-day-show-more"
              data-testid="rv-day-show-more"
              @click="visibleCount += PAGE_SIZE"
            >
              Pokaż więcej ({{ dayEvents.length - visibleCount }} pozostało)
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Context menu -->
    <div
      v-if="contextMenu"
      class="rv-context-menu"
      data-testid="rv-context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      @click="closeContextMenu"
    >
      <button @click="ctxAddReservation">Dodaj rezerwację</button>
      <button @click="ctxAddContract">Dodaj umowę</button>
    </div>

    <!-- MODAL CRUD -->
    <div v-if="modal.open" class="modal-overlay" data-testid="rv-modal">
      <div class="modal-box rv-modal-box">
        <div class="modal-header">
          <h2 v-if="modal.mode === 'create'">Nowa rezerwacja</h2>
          <h2 v-else-if="modal.mode === 'edit'">Edycja rezerwacji</h2>
          <h2 v-else>Szczegóły umowy</h2>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>

        <div class="modal-body">
          <div v-if="modalError" class="rv-modal-error" data-testid="rv-modal-error">
            ⚠️ {{ modalError }}
          </div>

          <div v-if="modal.mode === 'view' && modal.contractInfo" class="rv-contract-info">
            <p><strong>Maszyna:</strong> {{ modal.contractInfo.machine_name || modal.contractInfo.article_name || modal.contractInfo.internal_number || '—' }}</p>
            <p><strong>Kontrahent:</strong> {{ modal.contractInfo.contractor_name || '—' }}</p>
            <p><strong>Okres:</strong> {{ formatDate(modal.contractInfo.date_from) }} – {{ formatDate(modal.contractInfo.date_to) }}</p>
            <p v-if="modal.contractInfo.note"><strong>Notatka:</strong> {{ modal.contractInfo.note }}</p>
            <p class="rv-readonly-hint">To jest umowa — edycja tylko z poziomu umowy.</p>
          </div>

          <template v-else>
            <div class="rv-form-row">
              <label class="rv-form-label">Maszyna <span class="rv-req">*</span></label>
              <SearchCombobox
                v-model="modal.form.machine_id"
                :options="machineOptions"
                placeholder="Wpisz aby wyszukać maszynę…"
                :allow-clear="false"
                clear-label="Wybierz maszynę…"
                data-testid="rv-modal-machine"
                :disabled="modalSaving"
              />
            </div>

            <div class="rv-form-row">
              <label class="rv-form-label">Handlowiec</label>
              <SearchCombobox
                v-model="modal.form.salesperson_id"
                :options="salespeopleOptions"
                placeholder="Brak (opcjonalny)"
                clear-label="Brak (opcjonalny)"
                data-testid="rv-modal-salesperson"
                :disabled="modalSaving"
              />
            </div>

            <div class="rv-form-row">
              <label class="rv-form-label">Kontrahent</label>
              <ContractorCombobox
                v-model="modal.form.contractor_id"
                :contractors="contractorOptions"
                placeholder="Brak (opcjonalny)"
                data-testid="rv-modal-contractor"
              />
            </div>

            <div class="rv-form-row rv-form-dates">
              <div>
                <label class="rv-form-label">Data od <span class="rv-req">*</span></label>
                <input
                  v-model="modal.form.reserved_from"
                  type="date"
                  class="af-input"
                  data-testid="rv-modal-from"
                  :disabled="modalSaving"
                />
              </div>
              <div>
                <label class="rv-form-label">Data do <span class="rv-req">*</span></label>
                <input
                  v-model="modal.form.reserved_to"
                  type="date"
                  class="af-input"
                  data-testid="rv-modal-to"
                  :disabled="modalSaving"
                />
              </div>
            </div>

            <div class="rv-form-row">
              <label class="rv-form-label">Notatka</label>
              <textarea
                v-model="modal.form.note"
                class="af-input rv-textarea"
                data-testid="rv-modal-note"
                rows="3"
                :disabled="modalSaving"
              ></textarea>
            </div>
          </template>
        </div>

        <div class="modal-footer">
          <button v-if="modal.mode === 'edit'" class="btn btn-danger" data-testid="rv-modal-delete" :disabled="modalSaving" @click="deleteReservation">
            Usuń
          </button>
          <div class="rv-modal-spacer"></div>
          <button class="btn btn-secondary" data-testid="rv-modal-cancel" :disabled="modalSaving" @click="closeModal">
            Anuluj
          </button>
          <button
            v-if="modal.mode !== 'view'"
            class="btn btn-primary"
            data-testid="rv-modal-save"
            :disabled="modalSaving || !formValid"
            @click="saveReservation"
          >
            {{ modalSaving ? 'Zapisywanie…' : 'Zapisz' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reservations-view {
  padding: var(--spacing-6);
  font-family: var(--font-family);
  color: var(--color-text-body);
  max-width: 1400px;
  margin: 0 auto;
}

.rv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-4);
}
.rv-header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-heading);
  margin: 0;
}
.rv-add-btn {
  padding: var(--spacing-2) var(--spacing-4);
}

/* Treść: kalendarz + panel dnia (side-by-side) */
.rv-content {
  display: flex;
  gap: var(--spacing-4);
  align-items: flex-start;
}
.rv-calendar {
  flex: 1;
  min-width: 0;
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-4);
}

/* Panel dnia (prawa) */
.rv-day-panel {
  flex: 0 0 340px;
  max-width: 400px;
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-4);
  min-height: 400px;
}
.rv-day-empty {
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--spacing-6);
  font-size: var(--font-size-sm);
}
.rv-day-header h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-3);
}
.rv-day-filters {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--color-border);
}
.rv-day-filters label {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.rv-day-events {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  max-height: 60vh;
  overflow-y: auto;
}
.rv-day-show-more {
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
.rv-day-show-more:hover {
  background: var(--color-bg-card-hover);
}
.rv-day-event {
  display: flex;
  gap: var(--spacing-2);
  padding: var(--spacing-2);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  background: var(--color-bg-light);
}
.rv-day-event:hover {
  background: var(--color-bg-card-hover);
}
.rv-day-event strong {
  display: block;
  font-size: var(--font-size-sm);
}
.rv-day-event small {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.rv-day-no-events {
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--spacing-4);
  font-size: var(--font-size-sm);
}

/* Context menu */
.rv-context-menu {
  position: fixed;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  box-shadow: var(--shadow-modal);
  z-index: 1100;
  padding: var(--spacing-1);
  min-width: 180px;
}
.rv-context-menu button {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--spacing-2) var(--spacing-3);
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  border-radius: var(--border-radius-sm);
}
.rv-context-menu button:hover {
  background: var(--color-bg-light);
}

/* Filtry */
.rv-filters {
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
.rv-filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}
.rv-filter-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.rv-filter-select {
  width: 220px;
}

/* Legenda */
.rv-legend {
  display: flex;
  gap: var(--spacing-5);
  margin-bottom: var(--spacing-3);
  flex-wrap: wrap;
}
.rv-legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Kalendarz — header/grid/cell */
.rv-cal-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}
.rv-cal-month {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-heading);
  text-transform: capitalize;
  min-width: 180px;
  text-align: center;
}
.rv-cal-nav {
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
.rv-cal-nav:hover {
  background: var(--color-bg-light);
  border-color: var(--color-border-hover);
}
.rv-cal-today {
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
.rv-cal-today:hover {
  background: var(--color-bg-light);
}

.rv-cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: minmax(84px, auto);
  gap: 2px;
}
.rv-cal-dow {
  text-align: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-muted);
  padding: var(--spacing-2) 0;
  text-transform: uppercase;
}
.rv-cal-cell {
  position: relative;
  min-height: 84px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-1);
  cursor: pointer;
  background: var(--color-bg-card);
  transition: background 0.15s;
}
.rv-cal-cell:hover {
  background: var(--color-bg-light);
}
.rv-cell-out {
  background: var(--color-bg-light);
  opacity: 0.6;
}
.rv-cell-today {
  border-color: var(--color-primary);
  border-width: 2px;
}
.rv-cell-selected {
  background: var(--color-bg-light);
  border-color: var(--color-primary);
  box-shadow: inset 0 0 0 1px var(--color-primary);
}
.rv-cal-daynum {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
.rv-cal-dots {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: var(--spacing-1);
  align-items: center;
}

/* Dots */
.rv-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  cursor: pointer;
}
.dot-confirmed {
  background: var(--color-primary);
}
/* TODO: design-reviewer — dodać --color-warning do style.css (już istnieje: --color-warning: #F59E0B) */
.dot-contract {
  background: var(--color-warning);
}
.rv-dot-more {
  font-size: 10px;
  color: var(--color-text-muted);
  font-weight: var(--font-weight-semibold);
}

/* Tooltip */
.rv-tooltip {
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
.rv-tooltip-event {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-1) 0;
  border-bottom: 1px solid var(--color-border);
}
.rv-tooltip-event:last-child {
  border-bottom: none;
}
.rv-tooltip-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-body);
  line-height: var(--line-height-normal);
}
.rv-tooltip-text small {
  color: var(--color-text-muted);
}

/* Badge */
.rv-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--border-radius-pill);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}
.rv-badge-confirmed {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.rv-modal-box {
  width: 520px;
  max-width: 92vw;
  max-height: 90vh;
  overflow-y: auto;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}
.modal-header h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-heading);
  margin: 0;
}
.modal-close {
  border: none;
  background: transparent;
  font-size: var(--font-size-md);
  cursor: pointer;
  color: var(--color-text-muted);
  padding: var(--spacing-1);
}
.modal-close:hover {
  color: var(--color-error);
}
.modal-body {
  padding: var(--spacing-5);
}
.modal-footer {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--color-border);
}
.rv-modal-spacer {
  flex: 1;
}

.rv-modal-error {
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-3);
  margin-bottom: var(--spacing-4);
  color: var(--color-error);
  font-size: var(--font-size-sm);
}

.rv-form-row {
  margin-bottom: var(--spacing-4);
}
.rv-form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
  margin-bottom: var(--spacing-1);
}
.rv-req {
  color: var(--color-error);
}
.rv-form-dates {
  display: flex;
  gap: var(--spacing-3);
}
.rv-form-dates > div {
  flex: 1;
}
.rv-textarea {
  resize: vertical;
  font-family: var(--font-family);
}

.rv-contract-info p {
  margin-bottom: var(--spacing-2);
  font-size: var(--font-size-sm);
}
.rv-readonly-hint {
  color: var(--color-text-muted);
  font-style: italic;
  font-size: var(--font-size-xs);
  margin-top: var(--spacing-3);
}
</style>
