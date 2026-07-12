<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  useAnalyticsStore,
  type AnalyticsFiltersPayload,
  type TopMachineItem,
  type ServiceFeeItem,
  type LocationStatItem,
  type PositionStatItem,
  type CategoryStatItem,
} from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import ChartCard from '@/components/analytics/ChartCard.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import AppIcon, { type AppIconName } from '@/components/shared/AppIcon.vue'
import StateMessage from '@/components/StateMessage.vue'
import { useSort } from '@/composables/useSort'
import { useChartTheme } from '@/composables/useChartTheme'
import { formatCurrency } from '@/utils/format'

interface Props {
  dateFrom: string
  dateTo: string
  filters: AnalyticsFiltersPayload
}
const props = defineProps<Props>()

const store = useAnalyticsStore()

const openDrillDown = inject<
  (kind: 'machine' | 'location' | 'service' | 'category', id: number | string, name: string, internalNumber?: string | null) => void
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
  { key: 'service_name', label: 'Usługa', clickable: true },
  { key: 'total_revenue', label: 'Przychód', align: 'right' },
  { key: 'times_billed', label: 'Razy', align: 'right' },
]

const locationsColumns: AnalyticsColumn[] = [
  { key: 'city', label: 'Miasto' },
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

// RAO-P2-065 #6: kolumny dla sekcji "Kategorie" (agregat przychodu per kategoria).
const categoriesColumns: AnalyticsColumn[] = [
  { key: 'category_name', label: 'Kategoria', sortable: true, clickable: true },
  { key: 'articles_count', label: 'Maszyn', align: 'right', sortable: true },
  { key: 'rented_days', label: 'Dni', align: 'right', sortable: true },
  { key: 'contracts_count', label: 'Umów', align: 'right', sortable: true },
  { key: 'revenue', label: 'Przychód', align: 'right', sortable: true },
]

// ── Mapowanie danych na wiersze tabeli ───────────────────────────────────────
const topMachinesRows = computed<AnalyticsRow[]>(() =>
  store.topMachines.map((m: TopMachineItem, idx: number) => ({
    machine_id: m.machine_id ?? m.article_id,
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
    service_id: f.service_id ?? f.article_id,
    service_name: f.service_name,
    total_revenue: Number(f.total_revenue),
    times_billed: f.times_billed,
  })),
)

const locationsRows = computed<AnalyticsRow[]>(() =>
  store.locations.map((l: LocationStatItem) => ({
    city: l.city,
    rentals_count: l.rentals_count,
    total_revenue: Number(l.total_revenue),
  })),
)

const positionsRows = computed<AnalyticsRow[]>(() =>
  (store.positionsData?.items ?? []).map((p: PositionStatItem) => ({
    item_id: p.is_service ? (p.service_id ?? p.article_id) : (p.machine_id ?? p.article_id),
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

// RAO-P2-065 #6: wiersze dla sekcji "Kategorie" (z /stats/by-category).
const categoriesRows = computed<AnalyticsRow[]>(() =>
  (store.byCategoryData?.items ?? []).map((c: CategoryStatItem) => ({
    category_name: c.category_name,
    articles_count: c.articles_count,
    rented_days: c.rented_days,
    contracts_count: c.contracts_count,
    revenue: Number(c.revenue),
  })),
)

const categoriesSort = useSort<AnalyticsRow>('revenue', 'desc')
const sortedCategoriesRows = computed(() => categoriesSort.sortedRows(categoriesRows.value))

// ── Chart: Line trend przychodu miesięcznego + Bar kategorii ──────────────────
const { colors, baseOptions } = useChartTheme()

// Line: przychód miesięczny (z byPeriodData, agregacja client-side)
const trendChartData = computed(() => {
  const items = store.byPeriodData?.items ?? []
  // Grupuj po period, sumuj revenue (seria __all__ lub agregacja wszystkich)
  const byPeriod: Record<string, number> = {}
  for (const item of items) {
    const p = item.period
    byPeriod[p] = (byPeriod[p] || 0) + Number(item.revenue)
  }
  const periods = Object.keys(byPeriod).sort()
  return {
    labels: periods,
    datasets: [
      {
        label: 'Przychód',
        data: periods.map((p) => byPeriod[p]),
        borderColor: colors.primary,
        backgroundColor: 'rgba(29,43,83,0.08)',
        fill: true,
        tension: 0.3,
        pointBackgroundColor: colors.info,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  }
})

const trendChartOptions = computed(() => ({
  ...baseOptions,
  scales: {
    x: {
      ...baseOptions.scales?.x,
      ticks: { ...baseOptions.scales?.x?.ticks },
    },
    y: {
      ...baseOptions.scales?.y,
      ticks: {
        ...baseOptions.scales?.y?.ticks,
        callback: (v: number | string) => {
          const n = Number(v)
          return n >= 1000 ? `${(n / 1000).toFixed(0)}k` : n
        },
      },
    },
  },
  plugins: {
    ...baseOptions.plugins,
    tooltip: {
      ...baseOptions.plugins?.tooltip,
      callbacks: {
        label: (ctx: { parsed: { y: number } }) => formatCurrency(ctx.parsed.y),
      },
    },
  },
}))

// Bar: przychód per kategoria główna
const categoryBarData = computed(() => {
  const items = [...(store.byCategoryData?.items ?? [])]
    .sort((a, b) => Number(b.revenue) - Number(a.revenue))
    .slice(0, 10)
  return {
    labels: items.map((i) => i.category_name),
    datasets: [
      {
        label: 'Przychód',
        data: items.map((i) => Number(i.revenue)),
        backgroundColor: items.map((_, i) => i === 0 ? colors.success : colors.primary),
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  }
})

const categoryBarOptions = computed(() => ({
  ...baseOptions,
  indexAxis: 'y' as const,
  scales: {
    x: {
      ...baseOptions.scales?.x,
      ticks: {
        ...baseOptions.scales?.x?.ticks,
        callback: (v: number | string) => {
          const n = Number(v)
          return n >= 1000 ? `${(n / 1000).toFixed(0)}k` : n
        },
      },
    },
    y: { ...baseOptions.scales?.y },
  },
  plugins: {
    ...baseOptions.plugins,
    tooltip: {
      ...baseOptions.plugins?.tooltip,
      callbacks: {
        label: (ctx: { parsed: { x: number } }) => formatCurrency(ctx.parsed.x),
      },
    },
  },
  onClick: (_e: unknown, elements: { index: number }[]) => {
    if (elements.length > 0) {
      const items = [...(store.byCategoryData?.items ?? [])].sort((a, b) => Number(b.revenue) - Number(a.revenue))
      const item = items[elements[0].index]
      if (item) openDrillDown('category', item.category_name, item.category_name)
    }
  },
}))

// Czy zakres > 45 dni (warunek renderowania line trend)
const showTrend = computed(() => {
  if (!props.dateFrom || !props.dateTo) return false
  const from = new Date(props.dateFrom)
  const to = new Date(props.dateTo)
  const diff = (to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24)
  return diff > 45
})

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
      sub: '',
      variant: 'accent',
      icon: 'banknote' as AppIconName,
      testId: 'kpi-period-revenue',
    },
    {
      value: s.contracts_in_period,
      label: 'Umów w okresie',
      sub: 'aktywnych umów',
      icon: 'file' as AppIconName,
      testId: 'kpi-period-contracts',
    },
    {
      value: s.total_rented,
      label: 'Wynajętych teraz',
      sub: `z ${s.total_machines} maszyn`,
      variant: 'success',
      icon: 'tractor' as AppIconName,
      testId: 'kpi-period-rented',
    },
    {
      value: `${s.utilization_pct}%`,
      label: 'Wykorzystanie',
      sub: 'floty teraz',
      variant: utilVariant,
      icon: 'chart' as AppIconName,
      testId: 'kpi-period-util',
    },
  ]
})

function onMachineRowClick(row: AnalyticsRow): void {
  const id = Number(row.machine_id)
  if (!Number.isFinite(id)) return
  // RAO-P2-065 #7: przekaż internal_number, by tytuł drawera zawierał nr wewnętrzny.
  const internalNumber = row.internal_number ? String(row.internal_number) : null
  openDrillDown('machine', id, String(row.name), internalNumber)
}

function onLocationRowClick(row: AnalyticsRow): void {
  // RAO-P1-013: drill-down po mieście (PNA usunięte z tabeli głównej)
  const city = String(row.city ?? '')
  if (city) openDrillDown('location', `city:${city}`, city)
}

function onServiceClick(row: AnalyticsRow) {
  // RAO-P1-014: drilldown do szczegółów usługi (które umowy, kiedy, kwota)
  const serviceId = Number(row.service_id)
  const serviceName = String(row.service_name ?? '')
  if (!Number.isFinite(serviceId) || !serviceName) return
  openDrillDown('service', serviceId, serviceName)
}

function onCategoryClick(row: AnalyticsRow) {
  // RAO-P1-014: drilldown do szczegółów kategorii (jakie maszyny, umowy, przychód)
  const categoryName = String(row.category_name ?? '')
  if (!categoryName) return
  openDrillDown('category', categoryName, categoryName)
}

// ── Fetch wszystkich 5 endpointów (parallel) ─────────────────────────────────
// RAO-P2-049: error state z mozliwoscia retry
const loadError = ref('')

async function loadAll(): Promise<void> {
  store.loading = true
  loadError.value = ''
  try {
    // RAO-P0-001/BUG-1: fetchSummary z pełnymi filtrami (contractorId/city/articleType)
    // RAO-P1-BUG-2: fetchPositions z articleType z filtra (nie hardcoded 'all')
    // RAO-P1-BUG-3: fetchByCategory z articleType + contractorId + city
    // RAO-P1-BUG-5: fetchAdditionalFees/fetchLocations z city
    await Promise.all([
      store.fetchSummary(props.dateFrom, props.dateTo, props.filters),
      store.fetchTopMachines(props.dateFrom, props.dateTo, props.filters, 10),
      store.fetchAdditionalFees(props.dateFrom, props.dateTo, props.filters),
      store.fetchLocations(props.dateFrom, props.dateTo, props.filters),
      store.fetchPositions(props.filters.articleType || 'all', props.dateFrom, props.dateTo, props.filters),
      store.fetchByCategory('main', props.dateFrom, props.dateTo, [], props.filters.articleType || 'all', props.filters),
      store.fetchByPeriod('month', props.dateFrom, props.dateTo, [], props.filters.articleType || 'all'),
    ])
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Nie udalo sie pobrac statystyk'
  } finally {
    store.loading = false
  }
}

onMounted(loadAll)
watch(
  () => [props.dateFrom, props.dateTo, props.filters.contractorId, props.filters.city, props.filters.internalNumber, props.filters.articleType],
  loadAll,
)
</script>

<template>
  <div class="period-rental-tab" data-testid="period-rental-tab">
    <StateMessage v-if="store.loading && !store.summary" type="loading" message="Ladowanie statystyk..." />

    <StateMessage v-else-if="loadError" type="error" :message="loadError" @action="loadAll" />

    <template v-else-if="store.summary">
      <!-- KPI -->
      <KpiRow :cards="kpiCards" />

      <!-- Wykres: Line trend przychodu miesięcznego (tylko gdy zakres > 45 dni) -->
      <ChartCard
        v-if="showTrend"
        title="Trend przychodu miesięcznego"
        icon="📈"
        :loading="store.loading"
        :empty="!(store.byPeriodData?.items?.length)"
        empty-message="Brak danych o trendzie w wybranym okresie"
        test-id="period-trend-chart"
        :height="280"
      >
        <Line :data="trendChartData" :options="trendChartOptions" />
      </ChartCard>

      <!-- Wykres: Bar przychód per kategoria główna -->
      <ChartCard
        title="Przychód per kategoria"
        icon="🗂️"
        :loading="store.loading"
        :empty="!(store.byCategoryData?.items?.length)"
        empty-message="Brak kategorii w wybranym okresie"
        test-id="period-category-chart"
        :height="Math.max(200, (store.byCategoryData?.items?.length ?? 0) * 32)"
      >
        <Bar :data="categoryBarData" :options="categoryBarOptions" />
      </ChartCard>

      <!-- Top maszyny -->
      <div class="pr-section">
        <div class="pr-section-title">
          <AppIcon name="trophy" :size="16" class="pr-section-icon" />
          Top maszyny po przychodzie ({{ topMachinesRows.length }})
        </div>
        <AnalyticsTable
          :columns="topMachinesColumns"
          :rows="sortedTopMachinesRows"
          :sort-key="String(topMachinesSort.sortKey.value)"
          :sort-dir="topMachinesSort.sortDir.value"
          row-key="machine_id"
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
        <div class="pr-section-title">
          <AppIcon name="banknote" :size="16" class="pr-section-icon" />
          Pozycje dodatkowe (usługi)
        </div>
        <AnalyticsTable
          :columns="feesColumns"
          :rows="feesRows"
          :clickable="true"
          sort-key="total_revenue"
          sort-dir="desc"
          row-key="service_name"
          :loading="store.loading"
          @row-click="onServiceClick"
        >
          <template #cell-total_revenue="{ value }">{{ formatCurrency(value as number) }}</template>
          <template #empty>Brak dodatkowych opłat w wybranym okresie</template>
        </AnalyticsTable>
      </div>

      <!-- Lokalizacje -->
      <div class="pr-section">
        <div class="pr-section-title">
          <AppIcon name="map-pin" :size="16" class="pr-section-icon" />
          Lokalizacje wynajmu
        </div>
        <AnalyticsTable
          :columns="locationsColumns"
          :rows="locationsRows"
          sort-key="total_revenue"
          sort-dir="desc"
          row-key="city"
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
        <div class="pr-section-title">
          <AppIcon name="file" :size="16" class="pr-section-icon" />
          Pozycje umów
        </div>
        <AnalyticsTable
          :columns="positionsColumns"
          :rows="sortedPositionsRows"
          :sort-key="String(positionsSort.sortKey.value)"
          :sort-dir="positionsSort.sortDir.value"
          row-key="item_id"
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

/* revenue-breakdown usunięte — szacunkowe wartości tylko w archiwum */

.pr-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.pr-section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
.pr-section-icon {
  color: var(--color-primary);
  flex: 0 0 auto;
}
</style>
