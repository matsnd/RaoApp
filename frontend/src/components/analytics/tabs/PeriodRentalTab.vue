<script setup lang="ts">
import { computed, inject, onMounted, watch } from 'vue'
import {
  useAnalyticsStore,
  type AnalyticsFiltersPayload,
  type TopMachineItem,
  type ServiceFeeItem,
  type LocationStatItem,
  type PositionStatItem,
} from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import { useSort } from '@/composables/useSort'

interface Props {
  dateFrom: string
  dateTo: string
  filters: AnalyticsFiltersPayload
}
const props = defineProps<Props>()

const store = useAnalyticsStore()

const openDrillDown = inject<
  (kind: 'machine' | 'location', id: number | string, name: string) => void
>('analytics:openDrillDown', () => {})

// ── Sortowanie per tabela ────────────────────────────────────────────────────
const topMachinesSort = useSort<AnalyticsRow>('revenue', 'desc')
const positionsSort = useSort<AnalyticsRow>('revenue', 'desc')

// ── Kolumny ──────────────────────────────────────────────────────────────────
const topMachinesColumns: AnalyticsColumn[] = [
  { key: 'rank', label: '#', align: 'right', width: '48px' },
  { key: 'name', label: 'Maszyna', sortable: true },
  { key: 'internal_number', label: 'Nr wewnętrzny' },
  { key: 'revenue', label: 'Przychód', align: 'right', sortable: true },
  { key: 'rented_days', label: 'Dni', align: 'right', sortable: true },
  { key: 'contracts_count', label: 'Umów', align: 'right', sortable: true },
]

const feesColumns: AnalyticsColumn[] = [
  { key: 'service_name', label: 'Usługa' },
  { key: 'total_revenue', label: 'Przychód', align: 'right' },
  { key: 'times_billed', label: 'Razy', align: 'right' },
]

const locationsColumns: AnalyticsColumn[] = [
  { key: 'city', label: 'Miasto' },
  { key: 'postal_code', label: 'Kod PNA' },
  { key: 'rentals_count', label: 'Wynajmów', align: 'right' },
  { key: 'total_revenue', label: 'Przychód', align: 'right' },
]

const positionsColumns: AnalyticsColumn[] = [
  { key: 'article_name', label: 'Nazwa', sortable: true },
  { key: 'internal_number', label: 'Nr wewnętrzny', sortable: true },
  { key: 'category_main', label: 'Kategoria', sortable: true },
  { key: 'revenue', label: 'Przychód', align: 'right', sortable: true },
  { key: 'rented_days', label: 'Dni', align: 'right', sortable: true },
  { key: 'contracts_count', label: 'Umów', align: 'right', sortable: true },
  { key: 'times_billed', label: 'Razy', align: 'right', sortable: true },
]

// ── Mapowanie danych na wiersze tabeli ───────────────────────────────────────
const topMachinesRows = computed<AnalyticsRow[]>(() =>
  store.topMachines.map((m: TopMachineItem, idx: number) => ({
    article_id: m.article_id,
    rank: idx + 1,
    name: m.name,
    internal_number: m.internal_number ?? '',
    revenue: Number(m.revenue),
    rented_days: m.rented_days,
    contracts_count: m.contracts_count,
  })),
)

const sortedTopMachinesRows = computed(() => topMachinesSort.sortedRows(topMachinesRows.value))

const feesRows = computed<AnalyticsRow[]>(() =>
  (store.additionalFees?.breakdown ?? []).map((f: ServiceFeeItem) => ({
    article_id: f.article_id,
    service_name: f.service_name,
    total_revenue: Number(f.total_revenue),
    times_billed: f.times_billed,
  })),
)

const locationsRows = computed<AnalyticsRow[]>(() =>
  store.locations.map((l: LocationStatItem) => ({
    city: l.city,
    postal_code: l.postal_code ?? '',
    rentals_count: l.rentals_count,
    total_revenue: Number(l.total_revenue),
  })),
)

const positionsRows = computed<AnalyticsRow[]>(() =>
  (store.positionsData?.items ?? []).map((p: PositionStatItem) => ({
    article_id: p.article_id,
    article_name: p.article_name,
    internal_number: p.internal_number ?? '',
    category_main: p.category_main ?? '',
    revenue: Number(p.revenue),
    rented_days: p.rented_days,
    contracts_count: p.contracts_count,
    times_billed: p.times_billed,
  })),
)

const sortedPositionsRows = computed(() => positionsSort.sortedRows(positionsRows.value))

// ── KPI ──────────────────────────────────────────────────────────────────────
const kpiCards = computed<KpiCard[]>(() => {
  const s = store.summary
  if (!s) return []
  const utilVariant =
    s.utilization_pct >= 80 ? 'success' : s.utilization_pct >= 50 ? 'accent' : 'warn'
  return [
    {
      value: formatCurrency(s.period_revenue),
      label: 'Przychód w okresie',
      sub: s.revenue_source_label ?? '',
      variant: 'accent',
      icon: '💰',
      testId: 'kpi-period-revenue',
    },
    {
      value: s.contracts_in_period,
      label: 'Umów w okresie',
      sub: 'aktywnych umów',
      icon: '📄',
      testId: 'kpi-period-contracts',
    },
    {
      value: s.total_rented,
      label: 'Wynajętych teraz',
      sub: `z ${s.total_machines} maszyn`,
      variant: 'success',
      icon: '🚜',
      testId: 'kpi-period-rented',
    },
    {
      value: `${s.utilization_pct}%`,
      label: 'Wykorzystanie',
      sub: 'floty teraz',
      variant: utilVariant,
      icon: '📈',
      testId: 'kpi-period-util',
    },
  ]
})

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatCurrency(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === '') return '0 zł'
  const n = typeof v === 'string' ? parseFloat(v) : v
  if (Number.isNaN(n)) return '0 zł'
  return n.toLocaleString('pl-PL', {
    style: 'currency',
    currency: 'PLN',
    minimumFractionDigits: 2,
  })
}

function onMachineRowClick(row: AnalyticsRow): void {
  const id = Number(row.article_id)
  if (!Number.isFinite(id)) return
  openDrillDown('machine', id, String(row.name))
}

function onLocationRowClick(row: AnalyticsRow): void {
  const pna = String(row.postal_code ?? '')
  if (!pna) return
  openDrillDown('location', pna, `${row.city} ${pna}`.trim())
}

// ── Fetch wszystkich 5 endpointów (parallel) ─────────────────────────────────
async function loadAll(): Promise<void> {
  store.loading = true
  try {
    await Promise.all([
      store.fetchSummary(props.dateFrom, props.dateTo, props.filters.internalNumber),
      store.fetchTopMachines(props.dateFrom, props.dateTo, props.filters, 10),
      store.fetchAdditionalFees(props.dateFrom, props.dateTo, props.filters.contractorId),
      store.fetchLocations(props.dateFrom, props.dateTo, props.filters),
      store.fetchPositions('all', props.dateFrom, props.dateTo, props.filters),
    ])
  } finally {
    store.loading = false
  }
}

onMounted(loadAll)
watch(
  () => [props.dateFrom, props.dateTo, props.filters.contractorId, props.filters.city, props.filters.internalNumber],
  loadAll,
)
</script>

<template>
  <div class="period-rental-tab" data-testid="period-rental-tab">
    <div v-if="store.loading && !store.summary" class="pr-loading">
      Ładowanie statystyk…
    </div>

    <template v-else-if="store.summary">
      <!-- KPI -->
      <KpiRow :cards="kpiCards" />

      <!-- Revenue breakdown (rzeczywiste vs szacunek) -->
      <div
        v-if="Number(store.summary.revenue_actual) > 0 || Number(store.summary.revenue_estimate) > 0"
        class="revenue-breakdown"
        data-testid="revenue-breakdown"
      >
        <div class="breakdown-item">
          <span class="breakdown-label">Rzeczywiste (z rozliczeń):</span>
          <span class="breakdown-value breakdown-actual">
            {{ formatCurrency(store.summary.revenue_actual) }}
          </span>
        </div>
        <div v-if="Number(store.summary.revenue_estimate) > 0" class="breakdown-item">
          <span class="breakdown-label">Szacunek (cennik):</span>
          <span class="breakdown-value breakdown-estimate">
            {{ formatCurrency(store.summary.revenue_estimate) }}
          </span>
        </div>
      </div>

      <!-- Top maszyny -->
      <div class="pr-section">
        <div class="pr-section-title">🏆 Top maszyny po przychodzie ({{ topMachinesRows.length }})</div>
        <AnalyticsTable
          :columns="topMachinesColumns"
          :rows="sortedTopMachinesRows"
          :sort-key="String(topMachinesSort.sortKey.value)"
          :sort-dir="topMachinesSort.sortDir.value"
          row-key="article_id"
          :clickable="true"
          :loading="store.loading"
          @sort="topMachinesSort.toggleSort"
          @row-click="onMachineRowClick"
        >
          <template #cell-revenue="{ value }">{{ formatCurrency(value as number) }}</template>
          <template #empty>Brak danych o top maszynach w wybranym okresie</template>
        </AnalyticsTable>
      </div>

      <!-- Dodatkowe opłaty -->
      <div class="pr-section">
        <div class="pr-section-title">💰 Pozycje dodatkowe (usługi)</div>
        <AnalyticsTable
          :columns="feesColumns"
          :rows="feesRows"
          sort-key="total_revenue"
          sort-dir="desc"
          row-key="article_id"
          :loading="store.loading"
        >
          <template #cell-total_revenue="{ value }">{{ formatCurrency(value as number) }}</template>
          <template #empty>Brak dodatkowych opłat w wybranym okresie</template>
        </AnalyticsTable>
      </div>

      <!-- Lokalizacje -->
      <div class="pr-section">
        <div class="pr-section-title">📍 Lokalizacje wynajmu</div>
        <AnalyticsTable
          :columns="locationsColumns"
          :rows="locationsRows"
          sort-key="total_revenue"
          sort-dir="desc"
          row-key="postal_code"
          :clickable="true"
          :loading="store.loading"
          @row-click="onLocationRowClick"
        >
          <template #cell-total_revenue="{ value }">{{ formatCurrency(value as number) }}</template>
          <template #empty>Brak lokalizacji w wybranym okresie</template>
        </AnalyticsTable>
      </div>

      <!-- Pozycje -->
      <div class="pr-section">
        <div class="pr-section-title">📋 Pozycje umów</div>
        <AnalyticsTable
          :columns="positionsColumns"
          :rows="sortedPositionsRows"
          :sort-key="String(positionsSort.sortKey.value)"
          :sort-dir="positionsSort.sortDir.value"
          row-key="article_id"
          :loading="store.loading"
          @sort="positionsSort.toggleSort"
        >
          <template #cell-revenue="{ value }">{{ formatCurrency(value as number) }}</template>
          <template #empty>Brak pozycji w wybranym okresie</template>
        </AnalyticsTable>
      </div>
    </template>

    <div v-else class="pr-empty">Brak danych statystyk</div>
  </div>
</template>

<style scoped>
.period-rental-tab {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  font-family: var(--font-family);
}

.pr-loading,
.pr-empty {
  padding: var(--spacing-2xl) var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
}

.revenue-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
}
.breakdown-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
}
.breakdown-label {
  color: var(--color-text-muted);
}
.breakdown-value {
  font-weight: var(--font-weight-semibold);
}
.breakdown-actual {
  color: var(--color-success);
}
.breakdown-estimate {
  color: var(--color-warning);
}

.pr-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.pr-section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
</style>
