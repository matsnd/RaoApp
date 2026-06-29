<template>
  <div class="contract-period-picker">
    <div class="period-inputs">
      <div class="input-group">
        <label class="input-label">Data od</label>
        <input
          v-model="dateFromInternal"
          type="date"
          class="form-control"
          data-testid="date-from-input"
        />
      </div>
      <div class="input-group">
        <label class="input-label">Liczba dni</label>
        <input
          v-model.number="daysInternal"
          type="number"
          min="1"
          class="form-control"
          data-testid="days-input"
        />
      </div>
    </div>
    <div v-if="dateFromInternal && daysInternal >= 1" class="period-display">
      Okres umowy: {{ dateFromPl }} – {{ dateToPl }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  dateFrom: string | null
  dateTo: string | null
}>()

const emit = defineEmits<{
  (e: 'update:dateFrom', val: string | null): void
  (e: 'update:dateTo', val: string | null): void
}>()

// Internal state for date_from
const dateFromInternal = ref<string>(props.dateFrom || '')

// Internal state for days
const daysInternal = ref<number>(1)

// Format a Date as YYYY-MM-DD using LOCAL time (not UTC — avoids timezone bug)
function toLocalISODate(d: Date): string {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

// Count business days (Mon-Sat, skip Sundays) between from and to (inclusive)
function calculateDaysFromDates(from: string | null, to: string | null): number {
  if (!from || !to) return 1
  const fromDate = new Date(from + 'T00:00:00')
  const toDate = new Date(to + 'T00:00:00')
  let count = 0
  const cur = new Date(fromDate)
  while (cur <= toDate) {
    if (cur.getDay() !== 0) count++ // 0 = Sunday → skip
    cur.setDate(cur.getDate() + 1)
  }
  return count || 1
}

// Initialize days when both dates are provided on mount
if (props.dateFrom && props.dateTo) {
  daysInternal.value = calculateDaysFromDates(props.dateFrom, props.dateTo)
}

// Calculate date_to from date_from + (days - 1) business days (skip Sundays)
const dateToComputed = computed<string | null>(() => {
  if (!dateFromInternal.value || daysInternal.value < 1) return null
  const fromDate = new Date(dateFromInternal.value + 'T00:00:00')
  const toDate = new Date(fromDate)
  // day 1 = fromDate itself; add (days-1) more business days
  let added = 0
  while (added < daysInternal.value - 1) {
    toDate.setDate(toDate.getDate() + 1)
    if (toDate.getDay() !== 0) added++ // skip Sundays
  }
  return toLocalISODate(toDate)
})

// Format dates for Polish display
function formatDatePl(dateStr: string | null): string {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

const dateFromPl = computed(() => formatDatePl(dateFromInternal.value))
const dateToPl = computed(() => formatDatePl(dateToComputed.value))

// Watch date_from changes and emit
watch(dateFromInternal, (newVal) => {
  emit('update:dateFrom', newVal || null)
})

// Watch days changes and emit updated date_to
watch(daysInternal, () => {
  if (daysInternal.value < 1) {
    daysInternal.value = 1
  }
})

// Emit date_to when computed value changes
watch(dateToComputed, (newVal) => {
  emit('update:dateTo', newVal)
})

// Watch props changes (for external updates)
watch(
  () => props.dateFrom,
  (newVal) => {
    if (newVal !== dateFromInternal.value) {
      dateFromInternal.value = newVal || ''
    }
  }
)

watch(
  () => props.dateTo,
  (newTo) => {
    // Only recalculate days if we have both dates and they differ from current state
    if (newTo && dateFromInternal.value) {
      const currentToDate = dateToComputed.value
      if (newTo !== currentToDate) {
        daysInternal.value = calculateDaysFromDates(dateFromInternal.value, newTo)
      }
    }
  }
)
</script>

<style scoped>
.contract-period-picker {
  width: 100%;
}

.period-inputs {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.input-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
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

.form-control:focus {
  border-color: var(--color-accent-blue);
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.period-display {
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  padding: var(--spacing-1) 0;
}
</style>
