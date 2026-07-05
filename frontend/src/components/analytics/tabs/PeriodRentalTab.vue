<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
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
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import AppIcon, { type AppIconName } from '@/components/shared/AppIcon.vue'
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
  (kind: 'machine' | 'location', id: number | string, name: string, internalNumber?: string | null) => void
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
      // RAO-P2-065 #11: backend zwraca "razem (rzecz.+szac.)" gdy oba źródła > 0.
      sub: s.revenue_source_label ?? '',
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
  const id = Number(row.article_id)
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
  // Używamy alert jako tymczasowe rozwiązanie (TODO: drilldown modal)
  const serviceName = row.service_name as string
  const revenue = row.total_revenue as number
  alert(`Szczegóły usługi: ${serviceName}\nPrzychód: ${revenue.toLocaleString('pl-PL')} zł\n\nTODO: Implement drilldown modal z listą umów`)
}

function onCategoryClick(row: AnalyticsRow) {
  // RAO-P1-014: drilldown do szczegółów kategorii (jakie maszyny, umowy, przychód)
  // Używamy alert jako tymczasowe rozwiązanie (TODO: drilldown modal)
  const categoryName = row.category_name as string
  const revenue = row.revenue as number
  alert(`Szczegóły kategorii: ${categoryName}\nPrzychód: ${revenue.toLocaleString('pl-PL')} zł\n\nTODO: Implement drilldown modal z listą maszyn/umów`)
}

// ── Fetch wszystkich 5 endpointów (parallel) ─────────────────────────────────
// RAO-P2-049: error state z mozliwoscia retry
const loadError = ref('')

async function loadAll(): Promise<void> {
  store.loading = true
  loadError.value = ''
  try {
    await Promise.all([
      store.fetchSummary(props.dateFrom, props.dateTo, props.filters.internalNumber),
      store.fetchTopMachines(props.dateFrom, props.dateTo, props.filters, 10),
      store.fetchAdditionalFees(props.dateFrom, props.dateTo, props.filters.contractorId),
      store.fetchLocations(props.dateFrom, props.dateTo, props.filters),
      store.fetchPositions('all', props.dateFrom, props.dateTo, props.filters),
      // RAO-P2-065 #6: agregat przychodu per kategoria (level=main).
      store.fetchByCategory('main', props.dateFrom, props.dateTo, [], 'all'),
    ])
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Nie udalo sie pobrac statystyk'
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
    <StateMessage v-if="store.loading && !store.summary" type="loading" message="Ladowanie statystyk..." />

    <StateMessage v-else-if="loadError" type="error" :message="loadError" @action="loadAll" />

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
        <div class="pr-section-title">
          <AppIcon name="trophy" :size="16" class="pr-section-icon" />
          Top maszyny po przychodzie ({{ topMachinesRows.length }})
        </div>
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

      <!-- RAO-P2-065 #6: Kategorie — agregat przychodu per kategoria główna -->
      <div class="pr-section">
        <div class="pr-section-title">
          <AppIcon name="layers" :size="16" class="pr-section-icon" />
          Kategorie ({{ categoriesRows.length }})
        </div>
        <AnalyticsTable
          :columns="categoriesColumns"
          :rows="sortedCategoriesRows"
          :sort-key="String(categoriesSort.sortKey.value)"
          :sort-dir="categoriesSort.sortDir.value"
          row-key="category_name"
          :clickable="true"
          :loading="store.loading"
          data-testid="categories-table"
          @sort="categoriesSort.toggleSort"
          @row-click="onCategoryClick"
        >
          <template #cell-revenue="{ value }">{{ formatCurrency(value as number) }}</template>
          <template #empty>Brak kategorii w wybranym okresie</template>
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
