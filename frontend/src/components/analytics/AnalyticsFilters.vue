<script setup lang="ts">
import { computed } from 'vue'
import ContractorCombobox from '@/components/analytics/ContractorCombobox.vue'

export type ArticleTypeFilter = 'all' | 'machine' | 'service'

export interface AnalyticsFiltersValue {
  dateFrom: string
  dateTo: string
  preset: string
  articleType: ArticleTypeFilter
  contractorId: number | null
  city: string
}

interface ContractorOption {
  id: number
  name: string
}

interface Props {
  modelValue: AnalyticsFiltersValue
  contractors?: ContractorOption[]
}

const props = withDefaults(defineProps<Props>(), {
  contractors: () => [],
})

const emit = defineEmits<{
  'update:modelValue': [value: AnalyticsFiltersValue]
}>()

const presets = [
  { key: 'today', label: 'Dziś' },
  { key: 'week', label: 'Tydzień' },
  { key: 'month', label: 'Miesiąc' },
  { key: 'quarter', label: 'Kwartał' },
  { key: 'year', label: 'Rok' },
  { key: 'all', label: 'Wszystko' },
] as const

const articleTypeOptions: { value: ArticleTypeFilter; label: string }[] = [
  { value: 'all', label: 'Wszystkie' },
  { value: 'machine', label: 'Maszyny' },
  { value: 'service', label: 'Usługi' },
]

// RAO-P2-065 #5: filtr kontrahenta jako <select> (pokazuje nazwę, nie ID).
// Walidacja: Number("") = 0 → traktujemy jako "brak filtra" (null).
// Nie wysyłamy contractorId=NaN — select zawsze zwraca poprawne ID lub pusty string.
const selectedContractorId = computed({
  get: () => (props.modelValue.contractorId == null ? '' : String(props.modelValue.contractorId)),
  set: (v: string) => {
    if (v === '') {
      patch({ contractorId: null })
      return
    }
    const parsed = Number(v)
    // Walidacja: tylko poprawne liczby całkowite dodatnie trafiają do filtra.
    // "abc" / NaN / ułamki → null (brak filtra, nie wysyłamy NaN do backendu).
    if (!Number.isFinite(parsed) || !Number.isInteger(parsed) || parsed <= 0) {
      patch({ contractorId: null })
      return
    }
    patch({ contractorId: parsed })
  },
})

// RAO-P2-065 #5: empty state — czy wybrane ID istnieje na liście kontrahentów?
// (gdy lista załadowana, ale ID nie ma w opcjach → pokaż komunikat).
const contractorNotFound = computed(() => {
  const id = props.modelValue.contractorId
  if (id == null) return false
  // Jeśli lista pusta (jeszcze nie załadowana) — nie pokazuj ostrzeżenia.
  if (!props.contractors.length) return false
  return !props.contractors.some((c) => c.id === id)
})

function patch(delta: Partial<AnalyticsFiltersValue>): void {
  emit('update:modelValue', { ...props.modelValue, ...delta })
}

function selectPreset(key: string): void {
  patch({ preset: key })
}

function clearFilters(): void {
  emit('update:modelValue', {
    dateFrom: '',
    dateTo: '',
    preset: 'month',
    articleType: 'all',
    contractorId: null,
    city: '',
  })
}
</script>

<template>
  <div class="analytics-filters" data-testid="analytics-filters">
    <!-- Presets -->
    <div class="af-group">
      <span class="af-label">Okres:</span>
      <div class="af-pills">
        <button
          v-for="p in presets"
          :key="p.key"
          type="button"
          :class="['af-pill', { active: modelValue.preset === p.key }]"
          :data-testid="`preset-${p.key}`"
          @click="selectPreset(p.key)"
        >{{ p.label }}</button>
        <button
          type="button"
          :class="['af-pill', { active: modelValue.preset === 'custom' }]"
          data-testid="preset-custom"
          @click="selectPreset('custom')"
        >📅 Własny</button>
      </div>
    </div>

    <!-- Custom date range -->
    <div v-if="modelValue.preset === 'custom'" class="af-group af-custom-range" data-testid="custom-range">
      <input
        type="date"
        class="af-input af-date"
        :value="modelValue.dateFrom"
        data-testid="filter-date-from"
        @input="patch({ dateFrom: ($event.target as HTMLInputElement).value })"
      />
      <span class="af-sep">—</span>
      <input
        type="date"
        class="af-input af-date"
        :value="modelValue.dateTo"
        data-testid="filter-date-to"
        @input="patch({ dateTo: ($event.target as HTMLInputElement).value })"
      />
    </div>

    <!-- Article type -->
    <div class="af-group">
      <span class="af-label">Typ:</span>
      <select
        class="af-input af-select"
        :value="modelValue.articleType"
        data-testid="filter-article-type"
        @change="patch({ articleType: ($event.target as HTMLSelectElement).value as ArticleTypeFilter })"
      >
        <option v-for="opt in articleTypeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <!-- RAO-P0-004: Kontrahent — combobox (input + dropdown z filtrowaniem) -->
    <div class="af-group">
      <span class="af-label">Kontrahent:</span>
      <ContractorCombobox
        :model-value="modelValue.contractorId"
        :contractors="contractors"
        data-testid="filter-contractor"
        @update:model-value="patch({ contractorId: $event })"
      />
      <span
        v-if="contractorNotFound"
        class="af-contractor-warn"
        data-testid="filter-contractor-not-found"
        title="Wybrany kontrahent nie istnieje — filtr zostanie wyczyszczony"
      >
        ID {{ modelValue.contractorId }} nie istnieje
      </span>
    </div>

    <!-- City -->
    <div class="af-group">
      <span class="af-label">Miasto:</span>
      <input
        type="text"
        class="af-input"
        placeholder="Wszystkie miasta"
        :value="modelValue.city"
        data-testid="filter-city"
        @input="patch({ city: ($event.target as HTMLInputElement).value })"
      />
    </div>

    <!-- Clear -->
    <div class="af-group af-actions">
      <button
        type="button"
        class="af-clear"
        data-testid="filter-clear"
        @click="clearFilters"
      >Wyczyść</button>
    </div>
  </div>
</template>

<style scoped>
.analytics-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-md) var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  font-family: var(--font-family);
}

.af-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.af-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  white-space: nowrap;
}

.af-pills {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.af-pill {
  border: 1px solid var(--color-border);
  background: var(--color-bg-white);
  color: var(--color-text-body);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--border-radius-pill);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
}
.af-pill:hover {
  background: var(--color-bg-light);
}
.af-pill.active {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  border-color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.af-input {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  background: var(--color-bg-white);
  min-width: 140px;
  transition: border-color var(--transition-fast);
}
.af-input:focus {
  outline: none;
  border-color: var(--color-border-focus);
}
.af-select {
  min-width: 120px;
  cursor: pointer;
}
.af-contractor-warn {
  font-size: var(--font-size-xs);
  color: var(--color-warning);
  font-weight: var(--font-weight-semibold);
}
.af-date {
  min-width: 130px;
}

.af-sep {
  color: var(--color-text-muted);
}

.af-actions {
  margin-left: auto;
}

.af-clear {
  border: 1px solid var(--color-border);
  background: var(--color-bg-white);
  color: var(--color-text-body);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.af-clear:hover {
  background: var(--color-bg-light);
}
</style>
