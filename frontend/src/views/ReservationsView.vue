<script setup lang="ts">
/**
 * RAO-P3 (Phase 3): Widok Rezerwacji maszyn — kalendarz + lista + modal CRUD.
 *
 * Endpointy (backend Phase 2):
 *  - GET /reservations/calendar?date_from&date_to&article_id → CalendarEvent[]
 *  - GET /reservations/with-articles → ReservationWithArticle[]
 *  - POST /reservations, PUT /reservations/{id}, DELETE /reservations/{id}
 *
 * Stany: loading (spinner), error (retry), empty (hint + CTA).
 * Design system: wyłącznie zmienne CSS z style.css.
 */
import { computed, onMounted, ref, watch } from 'vue'
import {
  useReservationsStore,
  type CalendarEvent,
  type ReservationWithArticle,
  type ReservationPayload,
  type ReservationUpdatePayload,
} from '@/stores/reservations'
import { useArticleStore } from '@/stores/articles'
import { useContractorStore } from '@/stores/contractors'
import ContractorCombobox from '@/components/analytics/ContractorCombobox.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import StateMessage from '@/components/StateMessage.vue'
import { formatDate } from '@/utils/format'

const store = useReservationsStore()
const articleStore = useArticleStore()
const contractorStore = useContractorStore()

// ── Tryb widoku: kalendarz / lista ────────────────────────────────────────────
type ViewMode = 'calendar' | 'list'
const viewMode = ref<ViewMode>('calendar')

// ── Filtry ────────────────────────────────────────────────────────────────────
const filterArticleId = ref<number | null>(null)
const filterContractorId = ref<number | null>(null)
const filterStatus = ref<'all' | 'confirmed' | 'provisional'>('all')
// Zakres dat dla widoku listy
const listDateFrom = ref<string | null>(null)
const listDateTo = ref<string | null>(null)

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
  const last = new Date(calYear.value, calMonth.value + 1, 0)
  const dow = (last.getDay() + 6) % 7
  const end = new Date(last)
  end.setDate(last.getDate() + (6 - dow))
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

// Eventy kalendarza filtrowane po kontrahencie/statusie (article filtrowany w API)
const filteredCalendarEvents = computed<CalendarEvent[]>(() => {
  let items = store.calendarEvents
  if (filterContractorId.value != null) {
    items = items.filter((e) => e.contractor_id === filterContractorId.value)
  }
  if (filterStatus.value !== 'all') {
    // Umowy (source=contract) mają status=null — przy filtrze status pokaż tylko rezerwacje
    items = items.filter((e) => e.source === 'reservation' && e.status === filterStatus.value)
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
  if (e.status === 'provisional') return 'dot-provisional'
  return 'dot-confirmed'
}

// ── Lista rezerwacji ──────────────────────────────────────────────────────────
const filteredList = computed<ReservationWithArticle[]>(() => {
  let items = store.allList
  if (filterArticleId.value != null) {
    items = items.filter((r) => r.article_id === filterArticleId.value)
  }
  if (filterContractorId.value != null) {
    items = items.filter((r) => r.contractor_id === filterContractorId.value)
  }
  if (filterStatus.value !== 'all') {
    items = items.filter((r) => r.status === filterStatus.value)
  }
  if (listDateFrom.value) {
    items = items.filter((r) => r.reserved_to >= listDateFrom.value!)
  }
  if (listDateTo.value) {
    items = items.filter((r) => r.reserved_from <= listDateTo.value!)
  }
  // Sortowanie po dacie od (rosnąco)
  return [...items].sort((a, b) => a.reserved_from.localeCompare(b.reserved_from))
})

// ── Artykuły (do selecta w modalu + filtru) ───────────────────────────────────
interface ArticleOption {
  id: number
  name: string
  internal_number: string | null
  is_service: boolean
}

const articleOptions = ref<ArticleOption[]>([])

async function loadArticles() {
  try {
    // Tylko non-service, non-archival (sprzęt aktywny)
    await articleStore.fetchList({ is_service: false, archival_status: 'active', per_page: 200 })
    articleOptions.value = (articleStore.list as ArticleOption[]).filter((a) => !a.is_service && !a.is_external)
  } catch {
    articleOptions.value = []
  }
}

const contractorOptions = computed(() =>
  (contractorStore.list ?? []).map((c: { id: number; name: string }) => ({
    id: c.id,
    name: c.name,
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
    article_id: number | null
    contractor_id: number | null
    reserved_from: string
    reserved_to: string
    status: 'confirmed' | 'provisional'
    note: string
  }
}

const modal = ref<ModalState>({
  open: false,
  mode: 'create',
  reservationId: null,
  contractInfo: null,
  form: {
    article_id: null,
    contractor_id: null,
    reserved_from: '',
    reserved_to: '',
    status: 'confirmed',
    note: '',
  },
})

const modalSaving = ref(false)
const modalError = ref<string | null>(null)
const formValid = computed(() => {
  if (modal.value.mode === 'view') return true
  const f = modal.value.form
  if (!f.article_id) return false
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
      article_id: filterArticleId.value,
      contractor_id: filterContractorId.value,
      reserved_from: today,
      reserved_to: today,
      status: 'confirmed',
      note: '',
    },
  }
  modalError.value = null
}

function openEdit(r: ReservationWithArticle | CalendarEvent) {
  // Jeśli to event z umowy (read-only)
  if ('source' in r && r.source === 'contract') {
    const ev = r as CalendarEvent
    modal.value = {
      open: true,
      mode: 'view',
      reservationId: null,
      contractInfo: ev,
      form: {
        article_id: ev.article_id,
        contractor_id: ev.contractor_id,
        reserved_from: ev.date_from,
        reserved_to: ev.date_to,
        status: 'confirmed',
        note: ev.note ?? '',
      },
    }
    modalError.value = null
    return
  }
  // Rezerwacja (edycja) — z listy (ReservationWithArticle) lub kalendarza (CalendarEvent source=reservation)
  const isList = 'reserved_from' in r
  const from = isList ? (r as ReservationWithArticle).reserved_from : (r as CalendarEvent).date_from
  const to = isList ? (r as ReservationWithArticle).reserved_to : (r as CalendarEvent).date_to
  const id = isList ? (r as ReservationWithArticle).id : (r as CalendarEvent).source_id
  modal.value = {
    open: true,
    mode: 'edit',
    reservationId: id,
    contractInfo: null,
    form: {
      article_id: r.article_id,
      contractor_id: r.contractor_id ?? null,
      reserved_from: from,
      reserved_to: to,
      status: (r.status === 'provisional' ? 'provisional' : 'confirmed') as 'confirmed' | 'provisional',
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
        article_id: f.article_id!,
        reserved_from: f.reserved_from,
        reserved_to: f.reserved_to,
        note: f.note || null,
        contractor_id: f.contractor_id,
        status: f.status,
      }
      await store.create(payload)
    } else if (modal.value.mode === 'edit' && modal.value.reservationId != null) {
      const payload: ReservationUpdatePayload = {
        reserved_from: f.reserved_from,
        reserved_to: f.reserved_to,
        note: f.note || null,
        contractor_id: f.contractor_id,
        status: f.status,
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
      modalError.value = err.response?.data?.detail || 'Błąd zapisu rezerwacji'
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

// Usuń bezpośrednio z listy (z confirm, bez otwierania modalu)
async function deleteFromList(r: ReservationWithArticle) {
  if (!confirm('Czy na pewno usunąć tę rezerwację?')) return
  try {
    await store.remove(r.id)
    await refreshData()
  } catch {
    // store.remove ustawia store.error — wyświetlane przez StateMessage
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
const hasData = computed(() => {
  if (viewMode.value === 'calendar') return store.calendarEvents.length > 0
  return store.allList.length > 0
})

// ── Data loading ──────────────────────────────────────────────────────────────
async function refreshData() {
  if (viewMode.value === 'calendar') {
    await store.fetchCalendar(calDateFrom.value, calDateTo.value, filterArticleId.value ?? undefined)
  } else {
    await store.fetchAllWithArticles()
  }
}

async function retry() {
  await refreshData()
}

// Watch: zmiana miesiąca / filtru artykułu → reload kalendarza
watch([calYear, calMonth, filterArticleId], () => {
  if (viewMode.value === 'calendar') {
    store.fetchCalendar(calDateFrom.value, calDateTo.value, filterArticleId.value ?? undefined)
  }
})

// Watch: przełączenie trybu → reload odpowiednich danych
watch(viewMode, () => {
  refreshData()
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
  await loadArticles()
  await refreshData()
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

    <!-- TOGGLE: kalendarz / lista -->
    <div class="rv-view-toggle" role="group" aria-label="Tryb widoku">
      <button
        :class="['rv-toggle-btn', { active: viewMode === 'calendar' }]"
        data-testid="rv-toggle-calendar"
        @click="viewMode = 'calendar'"
      >📅 Kalendarz</button>
      <button
        :class="['rv-toggle-btn', { active: viewMode === 'list' }]"
        data-testid="rv-toggle-list"
        @click="viewMode = 'list'"
      >📋 Lista</button>
    </div>

    <!-- FILTRY -->
    <div class="rv-filters">
      <div class="rv-filter-group">
        <label class="rv-filter-label">Maszyna</label>
        <select
          v-model="filterArticleId"
          class="af-input rv-filter-select"
          data-testid="rv-filter-article"
        >
          <option :value="null">Wszystkie</option>
          <option v-for="a in articleOptions" :key="a.id" :value="a.id">
            {{ a.name }}{{ a.internal_number ? ` (${a.internal_number})` : '' }}
          </option>
        </select>
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

      <div class="rv-filter-group">
        <label class="rv-filter-label">Status</label>
        <select
          v-model="filterStatus"
          class="af-input rv-filter-select"
          data-testid="rv-filter-status"
        >
          <option value="all">Wszystkie</option>
          <option value="confirmed">Potwierdzone</option>
          <option value="provisional">Wstępne</option>
        </select>
      </div>

      <div v-if="viewMode === 'list'" class="rv-filter-group rv-filter-daterange">
        <label class="rv-filter-label">Zakres dat</label>
        <DateRangePicker
          :date-from="listDateFrom"
          :date-to="listDateTo"
          @update:date-from="listDateFrom = $event"
          @update:date-to="listDateTo = $event"
        />
      </div>
    </div>

    <!-- LEGENDA (tylko kalendarz) -->
    <div v-if="viewMode === 'calendar'" class="rv-legend">
      <span class="rv-legend-item"><span class="rv-dot dot-confirmed"></span> Rezerwacja potwierdzona</span>
      <span class="rv-legend-item"><span class="rv-dot dot-provisional"></span> Rezerwacja wstępna</span>
      <span class="rv-legend-item"><span class="rv-dot dot-contract"></span> Umowa</span>
    </div>

    <!-- LOADING -->
    <StateMessage
      v-if="(viewMode === 'calendar' ? store.loadingCalendar : store.loadingAll) && !hasData"
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

    <!-- KALENDARZ -->
    <div v-else-if="viewMode === 'calendar'" class="rv-calendar" data-testid="rv-calendar">
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
          :class="['rv-cal-cell', { 'rv-cell-out': !cell.inMonth, 'rv-cell-today': cell.isToday }]"
          data-testid="rv-cal-cell"
          @click="openCreate(cell.date)"
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
                <strong>{{ e.article_name || e.internal_number || 'Maszyna' }}</strong>
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

    <!-- LISTA -->
    <div v-else class="rv-list-section" data-testid="rv-list">
      <table class="rv-table">
        <thead>
          <tr>
            <th>Maszyna</th>
            <th>Kontrahent</th>
            <th>Od</th>
            <th>Do</th>
            <th>Status</th>
            <th>Notatka</th>
            <th class="rv-th-actions">Akcje</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filteredList" :key="r.id" data-testid="rv-list-row">
            <td>
              <div class="rv-cell-machine">
                <span>{{ r.article_name || '—' }}</span>
                <small v-if="r.internal_number" class="rv-cell-sub">{{ r.internal_number }}</small>
              </div>
            </td>
            <td>{{ r.contractor_name || '—' }}</td>
            <td>{{ formatDate(r.reserved_from) }}</td>
            <td>{{ formatDate(r.reserved_to) }}</td>
            <td>
              <span :class="['rv-badge', r.status === 'provisional' ? 'rv-badge-provisional' : 'rv-badge-confirmed']">
                {{ r.status === 'provisional' ? 'Wstępna' : 'Potwierdzona' }}
              </span>
            </td>
            <td class="rv-cell-note">{{ r.note || '—' }}</td>
            <td class="rv-cell-actions">
              <button class="rv-action-btn" title="Edytuj" data-testid="rv-edit-btn" @click="openEdit(r)">✏️</button>
              <button class="rv-action-btn" title="Usuń" data-testid="rv-delete-btn" @click="deleteFromList(r)">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="filteredList.length === 0" class="rv-list-empty">
        Brak rezerwacji pasujących do filtrów.
      </div>
    </div>

    <!-- MODAL CRUD -->
    <div v-if="modal.open" class="modal-overlay" data-testid="rv-modal" @click.self="closeModal">
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
            <p><strong>Maszyna:</strong> {{ modal.contractInfo.article_name || modal.contractInfo.internal_number || '—' }}</p>
            <p><strong>Kontrahent:</strong> {{ modal.contractInfo.contractor_name || '—' }}</p>
            <p><strong>Okres:</strong> {{ formatDate(modal.contractInfo.date_from) }} – {{ formatDate(modal.contractInfo.date_to) }}</p>
            <p v-if="modal.contractInfo.note"><strong>Notatka:</strong> {{ modal.contractInfo.note }}</p>
            <p class="rv-readonly-hint">To jest umowa — edycja tylko z poziomu umowy.</p>
          </div>

          <template v-else>
            <div class="rv-form-row">
              <label class="rv-form-label">Maszyna <span class="rv-req">*</span></label>
              <select
                v-model="modal.form.article_id"
                class="af-input"
                data-testid="rv-modal-article"
                :disabled="modalSaving"
              >
                <option :value="null" disabled>Wybierz maszynę…</option>
                <option v-for="a in articleOptions" :key="a.id" :value="a.id">
                  {{ a.name }}{{ a.internal_number ? ` (${a.internal_number})` : '' }}
                </option>
              </select>
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
              <label class="rv-form-label">Status</label>
              <select
                v-model="modal.form.status"
                class="af-input"
                data-testid="rv-modal-status"
                :disabled="modalSaving"
              >
                <option value="confirmed">Potwierdzona</option>
                <option value="provisional">Wstępna</option>
              </select>
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

/* Toggle */
.rv-view-toggle {
  display: flex;
  gap: var(--spacing-1);
  margin-bottom: var(--spacing-4);
}
.rv-toggle-btn {
  padding: var(--spacing-2) var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-card);
  color: var(--color-text-body);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all 0.15s;
}
.rv-toggle-btn.active {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  border-color: var(--color-primary);
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

/* Kalendarz */
.rv-calendar {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-4);
}
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
.dot-provisional {
  background: var(--color-primary);
  opacity: 0.5;
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

/* Lista */
.rv-list-section {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.rv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.rv-table thead th {
  text-align: left;
  padding: var(--spacing-3);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-table-header);
  color: var(--color-text-heading);
  border-bottom: 2px solid var(--color-border);
  background: var(--color-bg-light);
}
.rv-table tbody td {
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-body);
}
.rv-table tbody tr:hover {
  background: var(--color-bg-card-hover);
}
.rv-th-actions {
  width: 90px;
  text-align: center;
}
.rv-cell-machine {
  display: flex;
  flex-direction: column;
}
.rv-cell-sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.rv-cell-note {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rv-cell-actions {
  text-align: center;
  white-space: nowrap;
}
.rv-action-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-base);
  padding: var(--spacing-1);
  border-radius: var(--border-radius-sm);
  transition: background 0.15s;
}
.rv-action-btn:hover {
  background: var(--color-bg-light);
}
.rv-list-empty {
  padding: var(--spacing-6);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
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
.rv-badge-provisional {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  opacity: 0.6;
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
