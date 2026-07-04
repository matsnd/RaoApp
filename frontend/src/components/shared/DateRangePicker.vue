<template>
  <div style="position: relative;">
    <input
      type="text"
      :value="displayValue"
      :placeholder="placeholder"
      class="rao-datepicker-input"
      data-testid="date-range-trigger"
      @click="openPicker"
      readonly
    />
    <VueDatePicker
      ref="pickerRef"
      v-model="range"
      range
      :enable-time-picker="false"
      auto-apply
      :teleport="true"
      :month-change-on-scroll="false"
      placeholder="Data od — Data do"
      class="rao-datepicker-hidden"
      @update:model-value="onRangeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
// @ts-ignore — brak oficjalnych typów dla wszystkich propsów VueDatePicker
import { VueDatePicker } from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import { formatDate } from '@/utils/format'

const props = defineProps<{
  dateFrom: string | null
  dateTo: string | null
}>()

const emit = defineEmits<{
  (e: 'update:dateFrom', val: string | null): void
  (e: 'update:dateTo', val: string | null): void
}>()

function toISO(d: Date | null): string | null {
  if (!d) return null
  return d.toISOString().slice(0, 10)
}

function fromISO(s: string | null): Date | null {
  if (!s) return null
  return new Date(s + 'T00:00:00')
}

const range = ref<[Date | null, Date | null]>([
  fromISO(props.dateFrom),
  fromISO(props.dateTo),
])

const pickerRef = ref<InstanceType<typeof VueDatePicker> | null>(null)

watch(
  () => [props.dateFrom, props.dateTo] as [string | null, string | null],
  ([f, t]) => {
    range.value = [fromISO(f), fromISO(t)]
  },
)

function formatRange(dates: [Date | null, Date | null]): string {
  if (!dates || !dates[0] || !dates[1]) return ''
  const from = formatDate(dates[0])
  const to = formatDate(dates[1])
  return `${from} - ${to}`
}

const displayValue = computed(() => {
  return formatRange(range.value)
})

function openPicker() {
  if (pickerRef.value) {
    pickerRef.value.openMenu()
  }
}

function onRangeChange(val: [Date | null, Date | null] | null) {
  if (!val) {
    emit('update:dateFrom', null)
    emit('update:dateTo', null)
    return
  }
  emit('update:dateFrom', toISO(val[0]))
  emit('update:dateTo', toISO(val[1]))
}
</script>

<style>
/* Własny input */
.rao-datepicker-input {
  font-family: var(--font-family, 'Montserrat', sans-serif);
  font-size: var(--font-size-sm, 13px);
  border: 1px solid var(--color-border, #E2E8F0);
  border-radius: 6px;
  padding: 6px 10px;
  color: var(--color-text-body, #4A5568);
  width: 100%;
  box-sizing: border-box;
  cursor: pointer;
  background: white;
}

.rao-datepicker-input:focus {
  border-color: var(--color-accent-blue, #3B82F6);
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

/* Ukryj VueDatePicker input */
.rao-datepicker-hidden .dp__input {
  display: none !important;
}

.rao-datepicker-hidden .dp__input_wrap {
  display: none !important;
}

/* Niezbędne globalne — VueDatePicker renderuje poza shadow DOM */
.rao-datepicker {
  width: 100%;
}

/* Podświetlenie zakresu — navy primary */
.dp__range_start,
.dp__range_end {
  background: var(--color-primary, #1D2B53) !important;
  color: var(--color-text-on-primary, #ffffff) !important;
}

.dp__range_between {
  background: rgba(29, 43, 83, 0.08) !important;
}

/* Aktywny dzień */
.dp__active_date {
  background: var(--color-primary, #1D2B53) !important;
  color: var(--color-text-on-primary, #ffffff) !important;
}
</style>
