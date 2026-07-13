<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  useAnalyticsStore,
  type AnalyticsFiltersPayload,
  type CategoryStatItem,
} from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import ChartCard from '@/components/analytics/ChartCard.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
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
const { colors, baseOptions } = useChartTheme()

const openDrillDown = inject<
  (kind: 'machine' | 'location' | 'service' | 'category', id: number | string, name: string, internalNumber?: string | null) => void
>('analytics:openDrillDown', () => {})

// ── Stan drill-down hierarchicznego ───────────────────────────────────────────
type Level = 'main' | 'sub1' | 'sub2'
const currentLevel = ref<Level>('main')
const breadcrumb = ref<{ level: Level; name: string }[]>([])
const categoryMainFilter = ref<string[]>([])
const categorySub1Filter = ref<string | null>(null)

// ── Toggle metryki ────────────────────────────────────────────────────────────
type Metric = 'revenue' | 'rented_days' | 'contracts_count'
const metric = ref<Metric>('revenue')

const metricConfig: Record<Metric, { label: string; color: string; format: (v: number) => string }> = {
  revenue: { label: 'Przychód', color: colors.primary, format: (v) => formatCurrency(v) },
  rented_days: { label: 'Dni', color: colors.success, format: (v) => `${v} dni` },
  contracts_count: { label: 'Umów', color: colors.warning, format: (v) => `${v} umów` },
}

// ── Stan ładowania ────────────────────────────────────────────────────────────
const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<CategoryStatItem[]>([])

// ── Kolumny tabeli ────────────────────────────────────────────────────────────
const columns: AnalyticsColumn[] = [
  { key: 'category_name', label: 'Kategoria', sortable: true, clickable: true },
  { key: 'articles_count', label: 'Maszyn', align: 'right', sortable: true },
  { key: 'rented_days', label: 'Dni', align: 'right', sortable: true },
  { key: 'contracts_count', label: 'Umów', align: 'right', sortable: true },
  { key: 'revenue', label: 'Przychód', align: 'right', sortable: true },
]

const sort = useSort<AnalyticsRow>('revenue', 'desc')

// ── Computed: wiersze tabeli ──────────────────────────────────────────────────
const rows = computed<AnalyticsRow[]>(() =>
  data.value.map((c: CategoryStatItem) => ({
    category_name: c.category_name,
    articles_count: c.articles_count,
    rented_days: c.rented_days,
    contracts_count: c.contracts_count,
    revenue: Number(c.revenue),
  })),
)
const sortedRows = computed(() => sort.sortedRows(rows.value))

// ── Computed: dane wykresu ────────────────────────────────────────────────────
const chartData = computed(() => {
  const items = [...data.value].sort((a, b) => {
    const va = Number(metric.value === 'revenue' ? a.revenue : a[metric.value])
    const vb = Number(metric.value === 'revenue' ? b.revenue : b[metric.value])
    return vb - va
  }).slice(0, 15)

  return {
    labels: items.map((i) => i.category_name),
    datasets: [
      {
        label: metricConfig[metric.value].label,
        data: items.map((i) => Number(metric.value === 'revenue' ? i.revenue : i[metric.value])),
        backgroundColor: metricConfig[metric.value].color,
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  ...baseOptions,
  indexAxis: 'y' as const,
  scales: {
    x: {
      ...baseOptions.scales?.x,
      ticks: {
        ...baseOptions.scales?.x?.ticks,
        callback: function (this: unknown, value: number | string) {
          if (metric.value === 'revenue') {
            const n = Number(value)
            return n >= 1000 ? `${(n / 1000).toFixed(0)}k` : n
          }
          return value
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
        label: (ctx: { parsed: { x: number } }) => {
          const v = ctx.parsed.x
          return metricConfig[metric.value].format(v)
        },
      },
    },
  },
  onClick: (_e: unknown, elements: { index: number }[]) => {
    if (elements.length > 0) {
      const item = data.value[elements[0].index]
      if (item) onDrillDown(item.category_name)
    }
  },
}))

// ── KPI ───────────────────────────────────────────────────────────────────────
const kpiCards = computed<KpiCard[]>(() => {
  if (!data.value.length) return []
  const totalRevenue = data.value.reduce((s, c) => s + Number(c.revenue), 0)
  const totalDays = data.value.reduce((s, c) => s + c.rented_days, 0)
  const totalContracts = data.value.reduce((s, c) => s + c.contracts_count, 0)
  const top = [...data.value].sort((a, b) => Number(b.revenue) - Number(a.revenue))[0]
  const avg = totalRevenue / data.value.length
  return [
    {
      value: data.value.length,
      label: 'Kategorii',
      sub: currentLevel.value === 'main' ? 'głównych' : 'podkategorii',
      icon: '🗂️' as never,
      testId: 'kpi-categories-count',
    },
    {
      value: formatCurrency(totalRevenue),
      label: 'Przychód łączny',
      sub: 'z wszystkich kategorii',
      variant: 'accent',
      icon: '💰' as never,
      testId: 'kpi-categories-revenue',
    },
    {
      value: top?.category_name ?? '—',
      label: 'Top kategoria',
      sub: formatCurrency(Number(top?.revenue ?? 0)),
      variant: 'success',
      icon: '🏆' as never,
      testId: 'kpi-categories-top',
    },
    {
      value: formatCurrency(avg),
      label: 'Średni przychód',
      sub: 'per kategoria',
      icon: '📊' as never,
      testId: 'kpi-categories-avg',
    },
  ]
})

// ── Drill-down hierarchiczny ──────────────────────────────────────────────────
function onDrillDown(categoryName: string) {
  if (currentLevel.value === 'main') {
    // main → sub1
    currentLevel.value = 'sub1'
    categoryMainFilter.value = [categoryName]
    breadcrumb.value = [{ level: 'main', name: categoryName }]
  } else if (currentLevel.value === 'sub1') {
    // sub1 → sub2
    currentLevel.value = 'sub2'
    categorySub1Filter.value = categoryName
    breadcrumb.value = [
      ...breadcrumb.value,
      { level: 'sub1', name: categoryName },
    ]
  } else {
    // sub2 — koniec hierarchii, otwórz drill-down drawer
    openDrillDown('category', categoryName, categoryName)
    return
  }
  load()
}

function onBreadcrumbClick(idx: number) {
  if (idx < 0) {
    // "Wszystkie" → reset do main
    currentLevel.value = 'main'
    categoryMainFilter.value = []
    categorySub1Filter.value = null
    breadcrumb.value = []
  } else {
    const target = breadcrumb.value[idx]
    if (target.level === 'main') {
      currentLevel.value = 'sub1'
      categoryMainFilter.value = [target.name]
      categorySub1Filter.value = null
      breadcrumb.value = breadcrumb.value.slice(0, idx + 1)
    }
  }
  load()
}

function onRowClick(row: AnalyticsRow) {
  const name = String(row.category_name ?? '')
  if (name) onDrillDown(name)
}

// ── Ładowanie danych ──────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  error.value = null
  try {
    const resp = await store.fetchByCategory(
      currentLevel.value,
      props.dateFrom,
      props.dateTo,
      categoryMainFilter.value,
      props.filters.articleType || 'all',
      props.filters,
    )
    data.value = resp.items ?? []
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Błąd ładowania danych'
    data.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch(
  () => [props.dateFrom, props.dateTo, props.filters?.contractorId, props.filters?.city, props.filters?.articleType],
  load,
)
</script>

<template>
  <div class="categories-tab" data-testid="categories-tab">
    <StateMessage v-if="loading && !data.length" type="loading" message="Ładowanie statystyk kategorii..." />

    <StateMessage v-else-if="error" type="error" :message="error" @action="load" />

    <template v-else>
      <!-- P1-121: Breadcrumb zawsze widoczny gdy jesteśmy w drill-down, niezależnie od data.length -->
      <div v-if="breadcrumb.length" class="ct-breadcrumb" data-testid="categories-breadcrumb">
        <button class="ct-crumb" @click="onBreadcrumbClick(-1)">Wszystkie</button>
        <template v-for="(b, idx) in breadcrumb" :key="idx">
          <span class="ct-sep">›</span>
          <button class="ct-crumb" @click="onBreadcrumbClick(idx)">{{ b.name }}</button>
        </template>
      </div>

      <template v-if="data.length">
        <!-- KPI -->
        <KpiRow :cards="kpiCards" />

        <!-- Wykres -->
        <ChartCard
          title="Ranking kategorii"
          icon="📊"
          :loading="loading"
          :empty="!data.length"
          empty-message="Brak kategorii w wybranym okresie"
          test-id="categories-chart"
          :height="Math.max(250, data.length * 32)"
        >
          <template #actions>
            <div class="ct-metric-toggle">
              <button
                v-for="m in (['revenue', 'rented_days', 'contracts_count'] as Metric[])"
                :key="m"
                :class="['ct-metric-btn', { active: metric === m }]"
                @click="metric = m"
              >
                {{ metricConfig[m].label }}
              </button>
            </div>
          </template>
          <Bar :data="chartData" :options="chartOptions" />
        </ChartCard>

        <!-- Tabela -->
        <div class="ct-section">
          <div class="ct-section-title">Szczegóły ({{ data.length }})</div>
          <AnalyticsTable
            :columns="columns"
            :rows="sortedRows"
            :sort-key="String(sort.sortKey.value)"
            :sort-dir="sort.sortDir.value"
            row-key="category_name"
            :clickable="true"
            :loading="loading"
            data-testid="categories-table"
            @sort="sort.toggleSort"
            @row-click="onRowClick"
          >
            <template #cell-revenue="{ value }">{{ formatCurrency(value as number) }}</template>
            <template #empty>Brak kategorii w wybranym okresie</template>
          </AnalyticsTable>
        </div>
      </template>

      <div v-else class="ct-empty">
        {{ breadcrumb.length ? `Brak podkategorii dla „${breadcrumb[breadcrumb.length - 1].name}"` : 'Brak danych o kategoriach w wybranym okresie' }}
      </div>
    </template>
  </div>
</template>

<style scoped>
.categories-tab {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  font-family: var(--font-family);
}

.ct-empty {
  padding: var(--spacing-2xl) var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
}

.ct-breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}
.ct-crumb {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  padding: 2px 6px;
  border-radius: var(--border-radius-sm);
}
.ct-crumb:hover {
  background: var(--color-bg-light);
}
.ct-sep {
  color: var(--color-text-muted);
}

.ct-metric-toggle {
  display: flex;
  gap: var(--spacing-xs);
}
.ct-metric-btn {
  padding: 4px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-card);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-family: var(--font-family);
  cursor: pointer;
  transition: all 0.15s;
}
.ct-metric-btn.active {
  background: var(--color-primary);
  color: #FFFFFF;
  border-color: var(--color-primary);
}

.ct-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.ct-section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
</style>
