<script setup lang="ts">
import { computed, onMounted, inject } from 'vue'
import { Doughnut, Bar } from 'vue-chartjs'
import { useAnalyticsStore, type CurrentlyRentedItem } from '@/stores/analytics'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import ChartCard from '@/components/analytics/ChartCard.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import { type AppIconName } from '@/components/shared/AppIcon.vue'
import { useSort } from '@/composables/useSort'
import { useChartTheme } from '@/composables/useChartTheme'
import { formatDate } from '@/utils/format'

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
    machine_id: it.machine_id ?? it.article_id,
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
      icon: 'check-circle' as AppIconName,
      testId: 'kpi-live-available',
    },
    {
      value: cr.total_rented,
      label: 'Wynajęte teraz',
      sub: 'maszyn u klientów',
      variant: 'accent',
      icon: 'tractor' as AppIconName,
      testId: 'kpi-live-rented',
    },
    {
      value: `${cr.utilization_pct}%`,
      label: 'Wykorzystanie floty',
      sub: '% maszyn u klientów teraz',
      variant: utilVariant,
      icon: 'chart' as AppIconName,
      testId: 'kpi-live-util',
    },
  ]
})

const utilPct = computed(() => store.currentlyRented?.utilization_pct ?? 0)

// ── Chart 1: Doughnut wykorzystania floty ─────────────────────────────────────
const { colors, baseOptions } = useChartTheme()

const fleetDoughnutData = computed(() => {
  const cr = store.currentlyRented
  if (!cr) return { labels: [], datasets: [] }
  const available = cr.total_machines - cr.total_rented
  return {
    labels: ['Wynajęte', 'Dostępne'],
    datasets: [
      {
        data: [cr.total_rented, available],
        backgroundColor: [colors.primary, colors.bgLight],
        borderWidth: 2,
        borderColor: '#FFFFFF',
      },
    ],
  }
})

const fleetDoughnutOptions = computed(() => ({
  ...baseOptions,
  scales: undefined,
  cutout: '65%',
  plugins: {
    ...baseOptions.plugins,
    legend: {
      display: true,
      position: 'bottom' as const,
      labels: {
        color: colors.textMuted,
        font: { family: colors.fontFamily, size: 12 },
        padding: 12,
        boxWidth: 16,
      },
    },
    tooltip: {
      ...baseOptions.plugins?.tooltip,
      callbacks: {
        label: (ctx: { parsed: number; label: string }) => {
          const total = store.currentlyRented?.total_machines ?? 0
          const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(0) : '0'
          return `${ctx.label}: ${ctx.parsed} (${pct}%)`
        },
      },
    },
  },
}))

// ── Chart 2: Bar — wynajęte maszyny per kategoria ─────────────────────────────
const categoryBarData = computed(() => {
  const items = store.currentlyRented?.items ?? []
  // Agregacja client-side po category_main
  const byCat: Record<string, number> = {}
  for (const it of items) {
    const cat = it.category_main || 'Inne'
    byCat[cat] = (byCat[cat] || 0) + 1
  }
  const sorted = Object.entries(byCat).sort((a, b) => b[1] - a[1]).slice(0, 5)
  return {
    labels: sorted.map(([k]) => k),
    datasets: [
      {
        label: 'Wynajęte',
        data: sorted.map(([, v]) => v),
        backgroundColor: colors.info,
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
      ticks: { ...baseOptions.scales?.x?.ticks, precision: 0 },
    },
    y: { ...baseOptions.scales?.y },
  },
  plugins: {
    ...baseOptions.plugins,
    tooltip: {
      ...baseOptions.plugins?.tooltip,
      callbacks: {
        label: (ctx: { parsed: { x: number } }) => `${ctx.parsed.x} maszyn`,
      },
    },
  },
}))

function onRowClick(row: AnalyticsRow): void {
  const machineId = Number(row.machine_id)
  if (!Number.isFinite(machineId)) return
  openDrillDown('machine', machineId, String(row.name))
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

      <!-- Wykresy: doughnut + bar w grid 2-kol -->
      <div class="lf-charts-grid">
        <ChartCard
          title="Wykorzystanie floty"
          icon="🚜"
          :loading="store.loadingLive"
          :empty="!store.currentlyRented"
          empty-message="Brak danych o flocie"
          test-id="live-doughnut"
          :height="260"
        >
          <div class="lf-doughnut-wrap">
            <Doughnut :data="fleetDoughnutData" :options="fleetDoughnutOptions" />
            <div class="lf-doughnut-center">
              <span class="lf-doughnut-pct">{{ utilPct }}%</span>
              <span class="lf-doughnut-label">wykorzystanie</span>
            </div>
          </div>
        </ChartCard>

        <ChartCard
          title="Wynajęte per kategoria"
          icon="📊"
          :loading="store.loadingLive"
          :empty="!(store.currentlyRented?.items?.length)"
          empty-message="Brak wynajętych maszyn"
          test-id="live-category-bar"
          :height="260"
        >
          <Bar :data="categoryBarData" :options="categoryBarOptions" />
        </ChartCard>
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
          row-key="machine_id"
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

.lf-charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-lg);
}
@media (min-width: 1024px) {
  .lf-charts-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.lf-doughnut-wrap {
  position: relative;
  width: 100%;
  height: 100%;
}
.lf-doughnut-center {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}
.lf-doughnut-pct {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
  display: block;
}
.lf-doughnut-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-lg);
}
.lf-section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
</style>
