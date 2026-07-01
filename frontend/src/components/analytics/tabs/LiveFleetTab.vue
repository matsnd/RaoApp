<script setup lang="ts">
import { computed, onMounted, inject } from 'vue'
import { useAnalyticsStore, type CurrentlyRentedItem } from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import { useSort } from '@/composables/useSort'

const store = useAnalyticsStore()

// Drill-down injector (udostępniony przez AnalyticsView)
const openDrillDown = inject<(kind: 'machine' | 'location', id: number | string, name: string) => void>(
  'analytics:openDrillDown',
  () => {},
)

// Sortowanie tabeli wynajętych maszyn (po nazwie)
const { sortKey, sortDir, toggleSort, sortedRows } = useSort<AnalyticsRow>('name', 'asc')

const columns: AnalyticsColumn[] = [
  { key: 'name', label: 'Maszyna', sortable: true },
  { key: 'internal_number', label: 'Nr wewnętrzny' },
  { key: 'category_main', label: 'Kategoria' },
  { key: 'contract_number', label: 'Umowa' },
  { key: 'contractor_name', label: 'Kontrahent' },
  { key: 'return_date', label: 'Planowany zwrot' },
]

const rentedRows = computed<AnalyticsRow[]>(() => {
  const items = store.currentlyRented?.items ?? []
  return items.map((it: CurrentlyRentedItem) => ({
    article_id: it.article_id,
    name: it.name,
    internal_number: it.internal_number ?? '',
    category_main: it.category_main ?? '',
    contract_number: it.contract_number,
    contractor_name: it.contractor_name ?? '',
    return_date: it.return_date ?? '',
  }))
})

const sortedRentedRows = computed(() => sortedRows(rentedRows.value))

const kpiCards = computed<KpiCard[]>(() => {
  const cr = store.currentlyRented
  if (!cr) return []
  const available = cr.total_machines - cr.total_rented
  const utilVariant =
    cr.utilization_pct >= 80 ? 'success' : cr.utilization_pct >= 50 ? 'accent' : 'warn'
  return [
    {
      value: available,
      label: 'Dostępne maszyny',
      sub: `z ${cr.total_machines} łącznie`,
      variant: 'success',
      icon: '✅',
      testId: 'kpi-live-available',
    },
    {
      value: cr.total_rented,
      label: 'Wynajęte teraz',
      sub: 'maszyn u klientów',
      variant: 'accent',
      icon: '🚜',
      testId: 'kpi-live-rented',
    },
    {
      value: `${cr.utilization_pct}%`,
      label: 'Wykorzystanie floty',
      sub: '% maszyn u klientów teraz',
      variant: utilVariant,
      icon: '📈',
      testId: 'kpi-live-util',
    },
  ]
})

const utilPct = computed(() => store.currentlyRented?.utilization_pct ?? 0)

function formatDate(d: string): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pl-PL')
}

function onRowClick(row: AnalyticsRow): void {
  const articleId = Number(row.article_id)
  if (!Number.isFinite(articleId)) return
  openDrillDown('machine', articleId, String(row.name))
}

onMounted(() => {
  if (!store.currentlyRented) {
    store.fetchCurrentlyRented()
  }
})
</script>

<template>
  <div class="live-fleet-tab" data-testid="live-fleet-tab">
    <div v-if="store.loadingLive && !store.currentlyRented" class="lf-loading">
      Ładowanie stanu floty…
    </div>

    <template v-else-if="store.currentlyRented">
      <!-- KPI -->
      <KpiRow :cards="kpiCards" />

      <!-- Utilization bar -->
      <div class="util-bar-wrap" data-testid="live-util-bar">
        <div class="util-bar-label">
          Wykorzystanie: <strong>{{ utilPct }}%</strong>
        </div>
        <div class="util-bar-track">
          <div class="util-bar-fill" :style="{ width: utilPct + '%' }"></div>
        </div>
      </div>

      <!-- Rented machines table -->
      <div class="lf-section">
        <div class="lf-section-title">
          Maszyny aktualnie wynajęte ({{ rentedRows.length }})
        </div>
        <AnalyticsTable
          :columns="columns"
          :rows="sortedRentedRows"
          :sort-key="String(sortKey)"
          :sort-dir="sortDir"
          row-key="article_id"
          :clickable="true"
          :loading="store.loadingLive"
          @sort="toggleSort"
          @row-click="onRowClick"
        >
          <template #cell-return_date="{ value }">
            {{ formatDate(String(value)) }}
          </template>
          <template #empty>Brak aktywnych wynajmów — wszystkie maszyny dostępne</template>
        </AnalyticsTable>
      </div>
    </template>

    <div v-else class="lf-empty">Brak danych o flocie</div>
  </div>
</template>

<style scoped>
.live-fleet-tab {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  font-family: var(--font-family);
}

.lf-loading,
.lf-empty {
  padding: var(--spacing-2xl) var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
}

.util-bar-wrap {
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-md) var(--spacing-lg);
}
.util-bar-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  margin-bottom: var(--spacing-sm);
}
.util-bar-label strong {
  color: var(--color-primary);
}
.util-bar-track {
  height: 10px;
  background: var(--color-bg-light);
  border-radius: var(--border-radius-pill);
  overflow: hidden;
}
.util-bar-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--border-radius-pill);
  transition: width 0.3s ease;
}

.lf-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.lf-section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
</style>
