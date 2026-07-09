<template>
  <div class="contract-period-picker" data-testid="contract-period-picker">
    <div class="period-inputs">
      <div class="input-group">
        <label class="input-label">Data od</label>
        <input
          v-model="dateFromInternal"
          type="date"
          class="form-control"
          data-testid="date-from"
        />
      </div>
      <div class="input-group days-input-group">
        <label class="input-label">Liczba dni</label>
        <input
          v-model.number="daysInternal"
          type="number"
          min="1"
          class="form-control"
          :readonly="manualEndDate"
          :placeholder="manualEndDate && !dateToManual ? '—' : ''"
          data-testid="days-count"
        />
      </div>
      <div class="input-group toggle-group">
        <button
          type="button"
          class="toggle-link"
          @click="toggleManualEndDate"
        >
          {{ manualEndDate ? '← Wróć do wyliczania' : 'Wpisz datę końcową ręcznie →' }}
        </button>
      </div>
      <div v-if="manualEndDate" class="input-group date-to-group">
        <label class="input-label">Data do <span class="manual-tag">(ręcznie)</span></label>
        <input
          v-model="dateToManual"
          type="date"
          class="form-control"
          :class="{ 'form-control-error': dateToError }"
          placeholder="— wybierz datę do —"
          data-testid="date-to"
        />
        <span v-if="dateToError" class="period-error">{{ dateToError }}</span>
      </div>
      <input
        v-else
        type="hidden"
        :value="effectiveDateTo"
        data-testid="date-to"
      />
    </div>

    <div
      v-if="dateFromInternal && effectiveDateTo && effectiveCalendarDays != null"
      class="period-display"
      data-testid="period-display"
    >
      <template v-if="manualEndDate">
        Okres umowy: {{ dateFromPl }} – {{ dateToPl }} (ręcznie) ({{ effectiveCalendarDays }} dni kalendarzowych)
      </template>
      <template v-else>
        Okres umowy: {{ dateFromPl }} – {{ dateToPl }} ({{ effectiveWorkingDays }} dni roboczych / {{ effectiveCalendarDays }} dni kalendarzowych)
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { formatDate } from '@/utils/format'

const props = defineProps<{
  dateFrom: string | null
  dateTo: string | null
  workingDaysPerWeek?: number
}>()

const emit = defineEmits<{
  (e: 'update:dateFrom', val: string | null): void
  (e: 'update:dateTo', val: string | null): void
  (e: 'update:workingDaysPerWeek', val: number): void
}>()

// Internal state
const dateFromInternal = ref<string>(props.dateFrom || '')
const dateToManual = ref<string>(props.dateTo || '')
const daysInput = ref<number>(1)
const manualEndDate = ref<boolean>(false)
const workingDaysPerWeekInternal = ref<number>(props.workingDaysPerWeek ?? 6)

// Parse YYYY-MM-DD to local midnight Date (avoids UTC timezone bug)
function parseLocalDate(iso: string | null): Date | null {
  if (!iso) return null
  return new Date(iso + 'T00:00:00')
}

// Format a Date as YYYY-MM-DD using LOCAL time
function toLocalISODate(d: Date): string {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

// Add working days to start (inclusive) and return the calendar end date.
// daysPerWeek: 5 (Mon-Fri), 6 (Mon-Sat), 7 (all days).
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
    if (day >= 1 && day <= daysPerWeek) {
      count++
    }
    if (count < workingDays) {
      current.setDate(current.getDate() + 1)
    }
  }
  return current
}

// Count working days between start and end (inclusive).
// daysPerWeek: 5 (Mon-Fri), 6 (Mon-Sat), 7 (all days).
function countWorkingDays(start: Date, end: Date, daysPerWeek: number): number {
  const current = new Date(start)
  let count = 0
  while (current <= end) {
    const day = current.getDay()
    if (daysPerWeek === 7 || (day >= 1 && day <= daysPerWeek)) {
      count++
    }
    current.setDate(current.getDate() + 1)
  }
  return count
}

// Calendar days between start and end (inclusive), ignoring DST by using UTC components.
function calendarDaysInPeriod(start: Date, end: Date): number {
  const startUtc = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate())
  const endUtc = Date.UTC(end.getFullYear(), end.getMonth(), end.getDate())
  return Math.floor((endUtc - startUtc) / 86400000) + 1
}

// End date computed from date_from + working days (used in automatic mode)
const dateToComputed = computed<string | null>(() => {
  if (manualEndDate.value) return null
  const start = parseLocalDate(dateFromInternal.value)
  if (!start || daysInput.value < 1) return null
  const end = addWorkingDays(start, daysInput.value, workingDaysPerWeekInternal.value)
  return toLocalISODate(end)
})

// Effective end date depending on mode
const effectiveDateTo = computed<string | null>(() =>
  manualEndDate.value ? (dateToManual.value || null) : dateToComputed.value
)

const effectiveWorkingDays = computed<number | null>(() => {
  const start = parseLocalDate(dateFromInternal.value)
  const end = parseLocalDate(effectiveDateTo.value)
  if (!start || !end || end < start) return null
  return countWorkingDays(start, end, workingDaysPerWeekInternal.value)
})

const effectiveCalendarDays = computed<number | null>(() => {
  const start = parseLocalDate(dateFromInternal.value)
  const end = parseLocalDate(effectiveDateTo.value)
  if (!start || !end || end < start) return null
  return calendarDaysInPeriod(start, end)
})

// P1-105: Walidacja — Data do < Data od (tryb awaryjny)
const dateToError = computed<string | null>(() => {
  if (!manualEndDate.value) return null
  if (!dateToManual.value || !dateFromInternal.value) return null
  const start = parseLocalDate(dateFromInternal.value)
  const end = parseLocalDate(dateToManual.value)
  if (start && end && end < start) {
    return 'Data do nie może być wcześniejsza niż data od'
  }
  return null
})

// Days field is editable in automatic mode and computed in manual mode
const daysInternal = computed<number | null>({
  get: () => (manualEndDate.value ? effectiveWorkingDays.value : daysInput.value),
  set: (val) => {
    if (manualEndDate.value) return
    const n = Number(val)
    daysInput.value = Number.isNaN(n) || n < 1 ? 1 : n
  },
})

const dateFromPl = computed(() => formatDate(dateFromInternal.value))
const dateToPl = computed(() => formatDate(effectiveDateTo.value))

function toggleManualEndDate() {
  if (!manualEndDate.value) {
    // Switch from automatic → manual: seed the manual end date from computed
    const computedTo = dateToComputed.value
    if (computedTo) {
      dateToManual.value = computedTo
    }
    manualEndDate.value = true
  } else {
    // Switch from manual → automatic: derive working days from the manual period
    const start = parseLocalDate(dateFromInternal.value)
    const end = parseLocalDate(dateToManual.value)
    if (start && end && end >= start) {
      daysInput.value = countWorkingDays(start, end, workingDaysPerWeekInternal.value)
    }
    manualEndDate.value = false
  }
}

// Set initial state from props and decide whether the existing date_to is manual
function initFromProps() {
  if (props.workingDaysPerWeek != null) {
    workingDaysPerWeekInternal.value = props.workingDaysPerWeek
  }
  if (props.dateFrom) {
    dateFromInternal.value = props.dateFrom
  }
  if (props.dateFrom && props.dateTo) {
    const start = parseLocalDate(props.dateFrom)
    const end = parseLocalDate(props.dateTo)
    if (start && end && end >= start) {
      const days = countWorkingDays(start, end, workingDaysPerWeekInternal.value)
      const recomputedEnd = addWorkingDays(start, days, workingDaysPerWeekInternal.value)
      const recomputedEndStr = toLocalISODate(recomputedEnd)
      if (recomputedEndStr === props.dateTo) {
        manualEndDate.value = false
        daysInput.value = days
      } else {
        manualEndDate.value = true
        dateToManual.value = props.dateTo
        daysInput.value = days
      }
    }
  } else if (props.dateFrom) {
    manualEndDate.value = false
    daysInput.value = 1
  } else {
    manualEndDate.value = false
    daysInput.value = 1
  }
}

initFromProps()

watch(dateFromInternal, (newVal) => {
  emit('update:dateFrom', newVal || null)
})

watch(effectiveDateTo, (newVal) => {
  emit('update:dateTo', newVal)
})

watch(workingDaysPerWeekInternal, (newVal) => {
  emit('update:workingDaysPerWeek', newVal)
})

watch(() => props.dateFrom, (newVal) => {
  if (newVal !== dateFromInternal.value) {
    dateFromInternal.value = newVal || ''
  }
})

watch(() => props.workingDaysPerWeek, (newVal) => {
  if (newVal != null && newVal !== workingDaysPerWeekInternal.value) {
    workingDaysPerWeekInternal.value = newVal
  }
})

watch(() => props.dateTo, (newTo) => {
  if (!newTo) {
    if (manualEndDate.value) {
      manualEndDate.value = false
      daysInput.value = 1
    }
    return
  }
  if (manualEndDate.value) {
    if (newTo !== dateToManual.value) {
      dateToManual.value = newTo
    }
    return
  }
  // Automatic mode: if the incoming date_to differs from computed, assume manual override
  const computedTo = dateToComputed.value
  if (newTo !== computedTo) {
    const start = parseLocalDate(dateFromInternal.value)
    const end = parseLocalDate(newTo)
    if (start && end && end >= start) {
      manualEndDate.value = true
      dateToManual.value = newTo
      daysInput.value = countWorkingDays(start, end, workingDaysPerWeekInternal.value)
    }
  }
})
</script>

<style scoped>
.contract-period-picker {
  width: 100%;
}

.period-inputs {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
  align-items: flex-start;
  flex-wrap: wrap;
}

.input-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  min-width: 120px;
}

.days-input-group {
  flex: 0 0 120px;
  min-width: 100px;
}

.toggle-group {
  flex: 0 0 auto;
  justify-content: flex-end;
  align-self: flex-end;
  padding-bottom: 6px;
}

.toggle-link {
  background: none;
  border: none;
  padding: 0;
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: underline;
  white-space: nowrap;
}

.toggle-link:hover {
  color: var(--color-primary-dark);
}

.toggle-link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--border-radius-sm);
}

.date-to-group {
  flex: 1;
  min-width: 160px;
}

.manual-tag {
  color: var(--color-text-muted);
  font-weight: var(--font-weight-normal);
  font-size: var(--font-size-xs);
}

.input-label {
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-body);
}

.form-control {
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: 6px 10px;
  color: var(--color-text-body);
  width: 100%;
  box-sizing: border-box;
  background: var(--color-bg-white);
}

.form-control:disabled {
  background: var(--color-bg-light);
  opacity: 0.8;
  cursor: not-allowed;
}

.form-control[readonly] {
  background: var(--color-bg-light);
  cursor: default;
}

.form-control:focus {
  border-color: var(--color-accent-blue);
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

/* P1-105: błąd walidacji — Data do < Data od */
.form-control-error {
  border-color: var(--color-error);
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15);
}

.form-control-error:focus {
  border-color: var(--color-error);
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.25);
}

.period-error {
  font-family: var(--font-family);
  font-size: var(--font-size-xs);
  color: var(--color-error);
  margin-top: var(--spacing-1);
}

.period-display {
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  padding: var(--spacing-1) 0;
}
</style>
