<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import {
  useAnalyticsStore,
  type AnalyticsFiltersPayload,
  type PositionStatItem,
} from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import ExportCsvButton, { type CsvColumn } from '@/components/analytics/ExportCsvButton.vue'
import StateMessage from '@/components/StateMessage.vue'
import { useSort } from '@/composables/useSort'
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
  { key: 'article_name', label: 'Usługa dodatkowa', sortable: true },
  { key: 'category_main', label: 'Kategoria', sortable: true },
  { key: 'revenue', label: 'Przychód', align: 'right', sortable: true },
  { key: 'contracts_count', label: 'Umów', align: 'right', sortable: true },
  { key: 'times_billed', label: 'Razy', align: 'right', sortable: true },
]

const filteredData = computed<PositionStatItem[]>(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return data.value
  return data.value.filter(
    (item) =>
      item.article_name?.toLowerCase().includes(q) ||
      item.category_main?.toLowerCase().includes(q),
  )
})

const rows = computed<AnalyticsRow[]>(() =>
  filteredData.value.map((item, idx) => ({
    rank: idx + 1,
    article_name: item.article_name,
    category_main: item.category_main ?? '—',
    revenue: Number(item.revenue),
    rented_days: item.rented_days,
    contracts_count: item.contracts_count,
    times_billed: item.times_billed,
    article_id: item.article_id,
  })),
)

const sortedRows = computed(() => sort.sortedRows(rows.value))

const kpiCards = computed<KpiCard[]>(() => {
  if (!data.value.length) return []
  const totalBilled = data.value.reduce((s, item) => s + item.times_billed, 0)
  const totalContracts = data.value.reduce((s, item) => s + item.contracts_count, 0)
  const top = [...data.value].sort((a, b) => Number(b.revenue) - Number(a.revenue))[0]
  return [
    {
      value: data.value.length,
      label: 'Usług dodatkowych',
      sub: 'w umowach najmu (S)',
      icon: '📦' as never,
      testId: 'kpi-svc-s-count',
    },
    {
      value: formatCurrency(totalRevenue.value),
      label: 'Przychód',
      sub: 'z usług dodatkowych',
      variant: 'accent',
      icon: '💰' as never,
      testId: 'kpi-svc-s-revenue',
    },
    {
      value: totalBilled,
      label: 'Razy zafakturowane',
      sub: 'łącznie',
      icon: '📄' as never,
      testId: 'kpi-svc-s-billed',
    },
    {
      value: top?.article_name ?? '—',
      label: 'Top usługa',
      sub: formatCurrency(Number(top?.revenue ?? 0)),
      variant: 'success',
      icon: '🏆' as never,
      testId: 'kpi-svc-s-top',
    },
  ]
})

const csvColumns: CsvColumn[] = [
  { key: 'rank', label: '#' },
  { key: 'article_name', label: 'Usługa dodatkowa' },
  { key: 'category_main', label: 'Kategoria' },
  { key: 'revenue', label: 'Przychód', format: (v) => formatCurrency(Number(v)) },
  { key: 'contracts_count', label: 'Umów' },
  { key: 'times_billed', label: 'Razy' },
]

function onRowClick(row: AnalyticsRow): void {
  const articleId = row.article_id as number
  if (!articleId) return
  openDrillDown('service', articleId, String(row.article_name))
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const resp = await store.fetchPositions('services', props.dateFrom, props.dateTo, props.filters, undefined, 'desc', 'S')
    data.value = resp.items || []
    totalRevenue.value = data.value.reduce((s, item) => s + Number(item.revenue), 0)
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
  <div class="svc-tab" data-testid="services-additional-tab">
    <div v-if="loading && !data.length" class="svc-loading">
      Ładowanie usług dodatkowych…
    </div>

    <template v-else-if="data.length">
      <KpiRow :cards="kpiCards" />

      <div class="svc-section">
        <div class="svc-section-head">
          <span class="svc-section-title">📦 Usługi dodatkowe w umowach najmu ({{ filteredData.length }})</span>
          <div class="svc-actions">
            <input
              v-model="search"
              type="text"
              class="svc-search"
              placeholder="Szukaj: nazwa, kategoria…"
              data-testid="svc-s-search"
            />
            <ExportCsvButton
              :columns="csvColumns"
              :rows="sortedRows"
              filename="uslugi_dodatkowe.csv"
            />
          </div>
        </div>
        <AnalyticsTable
          :columns="columns"
          :rows="sortedRows"
          :sort-key="String(sort.sortKey.value)"
          :sort-dir="sort.sortDir.value"
          row-key="article_id"
          clickable
          data-testid="svc-s-table"
          @sort="sort.toggleSort"
          @row-click="onRowClick"
        >
          <template #cell-revenue="{ value }">
            <span class="svc-td-strong">{{ formatCurrency(Number(value)) }}</span>
          </template>
          <template #empty>Brak usług pasujących do wyszukiwania</template>
        </AnalyticsTable>
      </div>
    </template>

    <div v-else-if="error" class="svc-error">
      <StateMessage type="error" :message="error" />
    </div>

    <div v-else class="svc-empty" data-testid="svc-s-empty">
      Brak danych o usługach dodatkowych w wybranym okresie.
    </div>
  </div>
</template>

<style scoped>
.svc-tab {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}
.svc-loading {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.svc-section {
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-lg);
}
.svc-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}
.svc-section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-heading);
}
.svc-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.svc-search {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  width: 300px;
  max-width: 100%;
}
.svc-search:focus {
  outline: none;
  border-color: var(--color-primary);
}
.svc-td-strong {
  font-weight: 600;
  color: var(--color-primary);
}
.svc-empty {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.svc-error {
  padding: var(--spacing-lg) 0;
}
</style>
