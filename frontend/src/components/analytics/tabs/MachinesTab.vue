<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  useAnalyticsStore,
  type AnalyticsFiltersPayload,
  type PositionStatItem,
} from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import ChartCard from '@/components/analytics/ChartCard.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import ExportCsvButton, { type CsvColumn } from '@/components/analytics/ExportCsvButton.vue'
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

const search = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<PositionStatItem[]>([])
const totalRevenue = ref<number>(0)

const sort = useSort<AnalyticsRow>('revenue', 'desc')

const columns: AnalyticsColumn[] = [
  { key: 'rank', label: '#', align: 'right', width: '48px' },
  { key: 'article_name', label: 'Maszyna', sortable: true },
  { key: 'internal_number', label: 'Nr wewnętrzny', sortable: true },
  { key: 'category_main', label: 'Kategoria', sortable: true },
  { key: 'revenue', label: 'Przychód', align: 'right', sortable: true },
  { key: 'rented_days', label: 'Dni', align: 'right', sortable: true },
  { key: 'contracts_count', label: 'Umów', align: 'right', sortable: true },
  { key: 'times_billed', label: 'Razy', align: 'right', sortable: true },
]

const filteredData = computed<PositionStatItem[]>(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return data.value
  return data.value.filter(
    (item) =>
      item.article_name?.toLowerCase().includes(q) ||
      item.internal_number?.toLowerCase().includes(q) ||
      item.category_main?.toLowerCase().includes(q),
  )
})

const rows = computed<AnalyticsRow[]>(() =>
  filteredData.value.map((item, idx) => ({
    rank: idx + 1,
    article_name: item.article_name,
    internal_number: item.internal_number ?? '—',
    category_main: item.category_main ?? '—',
    revenue: Number(item.revenue),
    rented_days: item.rented_days,
    contracts_count: item.contracts_count,
    times_billed: item.times_billed,
    machine_id: item.machine_id ?? item.article_id,
  })),
)

const sortedRows = computed(() => sort.sortedRows(rows.value))

const kpiCards = computed<KpiCard[]>(() => {
  if (!data.value.length) return []
  const totalDays = data.value.reduce((s, item) => s + item.rented_days, 0)
  const totalContracts = data.value.reduce((s, item) => s + item.contracts_count, 0)
  const top = [...data.value].sort((a, b) => Number(b.revenue) - Number(a.revenue))[0]
  return [
    {
      value: data.value.length,
      label: 'Maszyn',
      sub: 'z wynajmami w okresie',
      icon: '🏗️' as never,
      testId: 'kpi-machines-count',
    },
    {
      value: formatCurrency(totalRevenue.value),
      label: 'Przychód',
      sub: 'łącznie z maszyn',
      variant: 'accent',
      icon: '💰' as never,
      testId: 'kpi-machines-revenue',
    },
    {
      value: totalDays,
      label: 'Dni wynajmu',
      sub: 'łącznie',
      icon: '📅' as never,
      testId: 'kpi-machines-days',
    },
    {
      value: top?.article_name ?? '—',
      label: 'Top maszyna',
      sub: formatCurrency(Number(top?.revenue ?? 0)),
      variant: 'success',
      icon: '🏆' as never,
      testId: 'kpi-machines-top',
    },
  ]
})

const csvColumns: CsvColumn[] = [
  { key: 'rank', label: '#' },
  { key: 'article_name', label: 'Maszyna' },
  { key: 'internal_number', label: 'Nr wewnętrzny' },
  { key: 'category_main', label: 'Kategoria' },
  { key: 'revenue', label: 'Przychód', format: (v) => formatCurrency(Number(v)) },
  { key: 'rented_days', label: 'Dni' },
  { key: 'contracts_count', label: 'Umów' },
  { key: 'times_billed', label: 'Razy' },
]

// ── Chart: Top 10 maszyn po przychodzie ───────────────────────────────────────
const { colors, baseOptions } = useChartTheme()

const top10ChartData = computed(() => {
  const top10 = [...data.value]
    .sort((a, b) => Number(b.revenue) - Number(a.revenue))
    .slice(0, 10)
  return {
    labels: top10.map((m) => m.article_name?.length > 20 ? m.article_name.slice(0, 18) + '…' : m.article_name),
    datasets: [
      {
        label: 'Przychód',
        data: top10.map((m) => Number(m.revenue)),
        backgroundColor: top10.map((_, i) => i === 0 ? colors.success : colors.primary),
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  }
})

const top10ChartOptions = computed(() => ({
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
        label: (ctx: { dataIndex: number }) => {
          const item = [...data.value].sort((a, b) => Number(b.revenue) - Number(a.revenue))[ctx.dataIndex]
          const rev = formatCurrency(Number(item?.revenue ?? 0))
          const num = item?.internal_number ? ` (${item.internal_number})` : ''
          return `${rev}${num}`
        },
      },
    },
  },
  onClick: (_e: unknown, elements: { index: number }[]) => {
    if (elements.length > 0) {
      const item = [...data.value].sort((a, b) => Number(b.revenue) - Number(a.revenue))[elements[0].index]
      if (item) {
        const machineId = item.machine_id ?? item.article_id
        if (machineId) openDrillDown('machine', machineId as number, String(item.article_name), item.internal_number ?? null)
      }
    }
  },
}))

function onRowClick(row: AnalyticsRow): void {
  const machineId = row.machine_id as number
  if (!machineId) return
  openDrillDown('machine', machineId, String(row.article_name), row.internal_number as string | null)
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const resp = await store.fetchPositions('machines', props.dateFrom, props.dateTo, props.filters, undefined, 'desc')
    data.value = resp.items || []
    totalRevenue.value = Number(resp.total_machines_revenue || 0)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    error.value = err.response?.data?.detail || 'Błąd pobierania danych'
    data.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => [props.dateFrom, props.dateTo, props.filters?.contractorId, props.filters?.city, props.filters?.articleType], load)
</script>

<template>
  <div class="machines-tab" data-testid="machines-tab">
    <div v-if="loading && !data.length" class="mt-loading">
      Ładowanie maszyn…
    </div>

    <template v-else-if="data.length">
      <KpiRow :cards="kpiCards" />

      <ChartCard
        title="Top 10 maszyn po przychodzie"
        icon="📊"
        :loading="loading"
        :empty="!data.length"
        empty-message="Brak maszyn w wybranym okresie"
        test-id="machines-chart"
        :height="320"
      >
        <Bar :data="top10ChartData" :options="top10ChartOptions" />
      </ChartCard>

      <div class="mt-section">
        <div class="mt-section-head">
          <span class="mt-section-title">🏗️ Maszyny ({{ filteredData.length }})</span>
          <div class="mt-actions">
            <input
              v-model="search"
              type="text"
              class="mt-search"
              placeholder="Szukaj: nazwa, nr wewnętrzny, kategoria…"
              data-testid="machines-search"
            />
            <ExportCsvButton
              :columns="csvColumns"
              :rows="sortedRows"
              filename="maszyny.csv"
            />
          </div>
        </div>
        <AnalyticsTable
          :columns="columns"
          :rows="sortedRows"
          :sort-key="String(sort.sortKey.value)"
          :sort-dir="sort.sortDir.value"
          row-key="machine_id"
          clickable
          data-testid="machines-table"
          @sort="sort.toggleSort"
          @row-click="onRowClick"
        >
          <template #cell-revenue="{ value }">
            <span class="mt-td-strong">{{ formatCurrency(Number(value)) }}</span>
          </template>
          <template #empty>Brak maszyn pasujących do wyszukiwania</template>
        </AnalyticsTable>
      </div>
    </template>

    <div v-else-if="error" class="mt-error">
      <StateMessage type="error" :message="error" />
    </div>

    <div v-else class="mt-empty" data-testid="machines-empty">
      Brak danych o maszynach w wybranym okresie.
    </div>
  </div>
</template>

<style scoped>
.machines-tab {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}
.mt-loading {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.mt-section {
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-lg);
}
.mt-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}
.mt-section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-heading);
}
.mt-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.mt-search {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  width: 300px;
  max-width: 100%;
}
.mt-search:focus {
  outline: none;
  border-color: var(--color-primary);
}
.mt-td-strong {
  font-weight: 600;
  color: var(--color-primary);
}
.mt-empty {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.mt-error {
  padding: var(--spacing-lg) 0;
}
</style>
