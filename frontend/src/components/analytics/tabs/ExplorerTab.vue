<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalyticsStore, type ExplorerResultItem } from '@/stores/analytics'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import { useSort } from '@/composables/useSort'
import { formatCurrency, formatDate } from '@/utils/format'

interface Props {
  dateFrom: string
  dateTo: string
}
const props = defineProps<Props>()

const store = useAnalyticsStore()
const router = useRouter()

const query = ref('')
const hasSearched = ref(false)

const { sortKey, sortDir, toggleSort, sortedRows } = useSort<AnalyticsRow>('amount', 'desc')

const columns: AnalyticsColumn[] = [
  { key: 'type_label', label: 'Typ', width: '90px' },
  { key: 'name', label: 'Nazwa', sortable: true },
  { key: 'internal_number', label: 'Nr wewn.', sortable: true },
  { key: 'contractor_name', label: 'Kontrahent', sortable: true },
  { key: 'date', label: 'Data', sortable: true },
  { key: 'amount', label: 'Kwota', align: 'right', sortable: true },
]

const rows = computed<AnalyticsRow[]>(() =>
  store.explorerResults.map((it: ExplorerResultItem) => ({
    id: it.id,
    article_id: it.article_id,
    type: it.type,
    type_label: it.type_label,
    name: it.name,
    internal_number: it.internal_number ?? '',
    contractor_name: it.contractor_name ?? '',
    date: it.date ?? '',
    amount: it.amount,
  })),
)

const sortedRowsView = computed(() => sortedRows(rows.value))

const summary = computed(() => store.explorerSummary)

async function search(): Promise<void> {
  const q = query.value.trim()
  if (!q) {
    hasSearched.value = false
    return
  }
  hasSearched.value = true
  await store.searchExplorer(q, props.dateFrom, props.dateTo)
}

async function onSearchInput(): Promise<void> {
  // Reset wyników gdy pole puste — bez auto-search (szukaj na Enter / klik)
  if (!query.value.trim()) {
    hasSearched.value = false
  }
}

function onRowClick(row: AnalyticsRow): void {
  const articleId = Number(row.article_id)
  if (Number.isFinite(articleId) && articleId > 0) {
    router.push(`/articles/${articleId}/edit`)
  }
}
</script>

<template>
  <div class="explorer-tab" data-testid="explorer-tab">
    <!-- Wyszukiwarka -->
    <div class="ex-search-bar" data-testid="explorer-search-bar">
      <input
        v-model="query"
        type="text"
        class="ex-input"
        placeholder="Maszyna, nr wewnętrzny, kontrahent, umowa…"
        data-testid="explorer-query"
        @keyup.enter="search"
        @input="onSearchInput"
      />
      <button
        type="button"
        class="ex-btn"
        :disabled="store.loadingExplorer || !query.trim()"
        data-testid="explorer-search-btn"
        @click="search"
      >
        {{ store.loadingExplorer ? 'Szukanie…' : 'Szukaj' }}
      </button>
    </div>

    <!-- Podsumowanie -->
    <div v-if="hasSearched && !store.loadingExplorer" class="ex-summary" data-testid="explorer-summary">
      <span>Liczba wyników: <strong>{{ summary.count }}</strong></span>
      <span>Łączny przychód: <strong>{{ formatCurrency(summary.revenue) }}</strong></span>
    </div>

    <!-- Wyniki -->
    <div class="ex-section">
      <div class="ex-section-title">Wyniki wyszukiwania ({{ rows.length }})</div>
      <AnalyticsTable
        :columns="columns"
        :rows="sortedRowsView"
        :sort-key="String(sortKey)"
        :sort-dir="sortDir"
        row-key="id"
        :clickable="true"
        :loading="store.loadingExplorer"
        @sort="toggleSort"
        @row-click="onRowClick"
      >
        <template #cell-date="{ value }">{{ formatDate(String(value)) }}</template>
        <template #cell-amount="{ value }">{{ formatCurrency(value as number) }}</template>
        <template #cell-type_label="{ value }">
          <span class="ex-type-badge">{{ value }}</span>
        </template>
        <template #empty>
          <template v-if="!hasSearched">Wpisz frazę i kliknij „Szukaj"</template>
          <template v-else>Brak wyników dla zapytania „{{ query }}"</template>
        </template>
      </AnalyticsTable>
    </div>
  </div>
</template>

<style scoped>
.explorer-tab {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  font-family: var(--font-family);
}

.ex-search-bar {
  display: flex;
  gap: var(--spacing-sm);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-md) var(--spacing-lg);
}
.ex-input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  background: var(--color-bg-white);
  transition: border-color var(--transition-fast);
}
.ex-input:focus {
  outline: none;
  border-color: var(--color-border-focus);
}
.ex-btn {
  border: 1px solid var(--color-primary);
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.ex-btn:hover:not(:disabled) {
  background: var(--color-primary-light);
  border-color: var(--color-primary-light);
}
.ex-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ex-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  padding: var(--spacing-sm) var(--spacing-md);
}
.ex-summary strong {
  color: var(--color-primary);
}

.ex-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.ex-section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}

.ex-type-badge {
  display: inline-block;
  padding: 2px var(--spacing-sm);
  background: var(--color-bg-light);
  border-radius: var(--border-radius-pill);
  font-size: var(--font-size-xs);
  color: var(--color-text-body);
}
</style>
