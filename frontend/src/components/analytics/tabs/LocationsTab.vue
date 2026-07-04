<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useAnalyticsStore, type LocationRankingItem } from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import { useSort } from '@/composables/useSort'

interface Props {
  dateFrom: string
  dateTo: string
}
const props = defineProps<Props>()

const store = useAnalyticsStore()

const openDrillDown = inject<
  (kind: 'machine' | 'location', id: number | string, name: string) => void
>('analytics:openDrillDown', () => {})

// ── Toggle grupowania: miasto (1 wiersz per miasto) / PNA (rozbicie) ─────────
const groupBy = ref<'city' | 'pna'>('city')

// ── Wyszukiwarka miast (client-side) ─────────────────────────────────────────
const search = ref('')

const filteredLocations = computed<LocationRankingItem[]>(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return store.locationsRanking
  return store.locationsRanking.filter(
    (l) =>
      l.city.toLowerCase().includes(q) ||
      (l.postal_code ?? '').toLowerCase().includes(q) ||
      (l.gmina ?? '').toLowerCase().includes(q) ||
      (l.powiat ?? '').toLowerCase().includes(q) ||
      (l.wojewodztwo ?? '').toLowerCase().includes(q),
  )
})

// ── KPI ──────────────────────────────────────────────────────────────────────
const kpiCards = computed<KpiCard[]>(() => {
  const locs = store.locationsRanking
  if (!locs.length) return []
  const totalRentals = locs.reduce((s, l) => s + l.rentals_count, 0)
  const totalRevenue = locs.reduce((s, l) => s + l.total_revenue, 0)
  const top = locs[0]
  return [
    {
      value: locs.length,
      label: 'Lokalizacji',
      sub: 'z wynajmami w okresie',
      icon: '📍',
      testId: 'kpi-loc-count',
    },
    {
      value: totalRentals,
      label: 'Wynajmów',
      sub: 'we wszystkich miastach',
      icon: '📄',
      testId: 'kpi-loc-rentals',
    },
    {
      value: formatCurrency(totalRevenue),
      label: 'Przychód',
      sub: 'łącznie w okresie',
      variant: 'accent',
      icon: '💰',
      testId: 'kpi-loc-revenue',
    },
    {
      value: top.city,
      label: 'Top miasto',
      sub: formatCurrency(top.total_revenue),
      variant: 'success',
      icon: '🏆',
      testId: 'kpi-loc-top',
    },
  ]
})

// ── Wykres słupkowy (top 10, toggle metryki) ─────────────────────────────────
type ChartMetric = 'revenue' | 'rentals'
const chartMetric = ref<ChartMetric>('revenue')

const chartData = computed(() => {
  const locs = [...store.locationsRanking]
  locs.sort((a, b) =>
    chartMetric.value === 'revenue'
      ? b.total_revenue - a.total_revenue
      : b.rentals_count - a.rentals_count,
  )
  const top = locs.slice(0, 10)
  const max = Math.max(
    ...top.map((l) => (chartMetric.value === 'revenue' ? l.total_revenue : l.rentals_count)),
    1,
  )
  return top.map((l) => {
    const val = chartMetric.value === 'revenue' ? l.total_revenue : l.rentals_count
    return {
      key: (l.postal_code ?? '') + l.city,
      city: l.city,
      postal_code: l.postal_code,
      value: val,
      valueLabel:
        chartMetric.value === 'revenue' ? formatCurrency(val) : `${val} wynajm.`,
      pct: Math.round((val / max) * 100),
    }
  })
})

function onChartBarClick(bar: { city: string; postal_code: string | null }): void {
  if (groupBy.value === 'pna') {
    if (!bar.postal_code) return
    openDrillDown('location', bar.postal_code, `${bar.city} ${bar.postal_code}`.trim())
  } else {
    if (!bar.city) return
    openDrillDown('location', `city:${bar.city}`, bar.city)
  }
}

// ── Tabela rankingu ──────────────────────────────────────────────────────────
const rankingSort = useSort<AnalyticsRow>('total_revenue', 'desc')

// Kolumna PNA tylko w trybie 'pna' (rozbicie miasta na kody pocztowe)
const rankingColumns = computed<AnalyticsColumn[]>(() => {
  const cols: AnalyticsColumn[] = [
    { key: 'rank', label: '#', align: 'right', width: '48px' },
    { key: 'city', label: 'Miasto', sortable: true },
  ]
  if (groupBy.value === 'pna') {
    cols.push({ key: 'postal_code', label: 'PNA' })
  }
  cols.push(
    { key: 'gmina', label: 'Gmina', sortable: true },
    { key: 'powiat', label: 'Powiat', sortable: true },
    { key: 'wojewodztwo', label: 'Województwo', sortable: true },
    { key: 'rentals_count', label: 'Wynajmów', align: 'right', sortable: true },
    { key: 'total_revenue', label: 'Przychód', align: 'right', sortable: true },
  )
  return cols
})

const rankingRows = computed<AnalyticsRow[]>(() =>
  filteredLocations.value.map((l) => ({
    rank: l.rank,
    city: l.city,
    postal_code: l.postal_code ?? '',
    gmina: l.gmina ?? '',
    powiat: l.powiat ?? '',
    wojewodztwo: l.wojewodztwo ?? '',
    rentals_count: l.rentals_count,
    total_revenue: l.total_revenue,
  })),
)

const sortedRankingRows = computed(() => rankingSort.sortedRows(rankingRows.value))

function onRowClick(row: AnalyticsRow): void {
  if (groupBy.value === 'pna') {
    // Drill-down po PNA
    const pna = String(row.postal_code ?? '')
    if (!pna) return
    openDrillDown('location', pna, `${row.city} ${pna}`.trim())
  } else {
    // Drill-down po mieście (sumuje wszystkie PNA w mieście)
    const city = String(row.city ?? '')
    if (!city) return
    openDrillDown('location', `city:${city}`, city)
  }
}

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

// ── Fetch ────────────────────────────────────────────────────────────────────
async function load(): Promise<void> {
  await store.fetchLocationsRanking(props.dateFrom, props.dateTo, 100, groupBy.value)
}

onMounted(load)
watch(() => [props.dateFrom, props.dateTo], load)
watch(groupBy, load)
</script>

<template>
  <div class="locations-tab" data-testid="locations-tab">
    <div v-if="store.loadingLocations && !store.locationsRanking.length" class="loc-loading">
      Ładowanie lokalizacji…
    </div>

    <template v-else-if="store.locationsRanking.length">
      <!-- KPI -->
      <KpiRow :cards="kpiCards" />

      <!-- WYKRES: top 10 miast -->
      <div class="loc-section">
        <div class="loc-section-head">
          <span class="loc-section-title">📊 Top miasta</span>
          <div class="loc-chart-toggle" role="group" aria-label="Metryka wykresu">
            <button
              :class="['loc-toggle-btn', { active: chartMetric === 'revenue' }]"
              data-testid="loc-chart-revenue"
              @click="chartMetric = 'revenue'"
            >Przychód</button>
            <button
              :class="['loc-toggle-btn', { active: chartMetric === 'rentals' }]"
              data-testid="loc-chart-rentals"
              @click="chartMetric = 'rentals'"
            >Wynajmy</button>
          </div>
        </div>
        <div class="loc-chart" data-testid="loc-chart">
          <div
            v-for="bar in chartData"
            :key="bar.key"
            :class="['loc-bar-row', { clickable: groupBy === 'pna' ? !!bar.postal_code : !!bar.city }]"
            @click="onChartBarClick(bar)"
          >
            <span class="loc-bar-city" :title="bar.city">
              {{ bar.city }}
              <span v-if="bar.postal_code" class="loc-bar-pna">{{ bar.postal_code }}</span>
            </span>
            <div class="loc-bar-track">
              <div class="loc-bar-fill" :style="{ width: bar.pct + '%' }"></div>
            </div>
            <span class="loc-bar-value">{{ bar.valueLabel }}</span>
          </div>
        </div>
      </div>

      <!-- WYSZUKIWARKA + RANKING -->
      <div class="loc-section">
        <div class="loc-section-head">
          <span class="loc-section-title">📍 Ranking {{ groupBy === 'city' ? 'miast' : 'PNA' }} ({{ filteredLocations.length }})</span>
          <div class="loc-group-toggle" role="group" aria-label="Grupowanie">
            <button
              :class="['loc-toggle-btn', { active: groupBy === 'city' }]"
              data-testid="loc-group-city"
              @click="groupBy = 'city'"
            >Miasto</button>
            <button
              :class="['loc-toggle-btn', { active: groupBy === 'pna' }]"
              data-testid="loc-group-pna"
              @click="groupBy = 'pna'"
            >PNA</button>
          </div>
          <input
            v-model="search"
            type="text"
            class="loc-search"
            placeholder="Szukaj: miasto, PNA, gmina, powiat…"
            data-testid="loc-search"
          />
        </div>
        <AnalyticsTable
          :columns="rankingColumns"
          :rows="sortedRankingRows"
          :sort-key="String(rankingSort.sortKey.value)"
          :sort-dir="rankingSort.sortDir.value"
          row-key="rank"
          clickable
          data-testid="loc-ranking-table"
          @sort="rankingSort.toggleSort"
          @row-click="onRowClick"
        >
          <template #cell-total_revenue="{ value }">
            <span class="loc-td-strong">{{ formatCurrency(value as number) }}</span>
          </template>
          <template #empty>Brak miast pasujących do wyszukiwania</template>
        </AnalyticsTable>
      </div>
    </template>

    <div v-else class="loc-empty" data-testid="loc-empty">
      Brak danych o lokalizacjach w wybranym okresie.
      <span class="loc-empty-hint">Lokalizacje wykrywane są z adresu dostawy umowy (kod pocztowy).</span>
    </div>
  </div>
</template>

<style scoped>
.loc-loading {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.loc-section {
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}
.loc-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}
.loc-section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-heading);
}
/* Toggle metryki wykresu */
.loc-chart-toggle,
.loc-group-toggle {
  display: flex;
  gap: var(--spacing-xs);
}
.loc-toggle-btn {
  padding: 4px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-pill, 24px);
  background: var(--color-bg-card);
  color: var(--color-text-body);
  font-family: var(--font-family);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.loc-toggle-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.loc-toggle-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-on-primary, #fff);
}
.loc-toggle-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
/* Wykres słupkowy poziomy */
.loc-chart {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.loc-bar-row {
  display: grid;
  grid-template-columns: 220px 1fr 130px;
  align-items: center;
  gap: var(--spacing-md);
}
.loc-bar-row.clickable {
  cursor: pointer;
}
.loc-bar-row.clickable:hover .loc-bar-fill {
  background: var(--color-accent, #2563eb);
}
.loc-bar-row.clickable:hover .loc-bar-city {
  color: var(--color-primary);
}
.loc-bar-city {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-heading);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.15s ease;
}
.loc-bar-pna {
  font-weight: 400;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  margin-left: 4px;
}
.loc-bar-track {
  height: 14px;
  background: var(--color-bg-hover, #f1f3f7);
  border-radius: 7px;
  overflow: hidden;
}
.loc-bar-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 7px;
  transition: width 0.4s ease, background 0.15s ease;
  min-width: 2px;
}
.loc-bar-value {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-body);
  text-align: right;
  white-space: nowrap;
}
.loc-td-strong {
  font-weight: 600;
}
/* Wyszukiwarka */
.loc-search {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  width: 300px;
  max-width: 100%;
}
.loc-search:focus {
  outline: none;
  border-color: var(--color-primary);
}
/* Empty state */
.loc-empty {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.loc-empty-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  opacity: 0.8;
}
@media (max-width: 900px) {
  .loc-bar-row {
    grid-template-columns: 140px 1fr 110px;
  }
}
</style>
