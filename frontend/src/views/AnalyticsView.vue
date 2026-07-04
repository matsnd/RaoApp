<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAnalyticsStore, type DrillDownKind } from '@/stores/analytics'
import { useContractorStore } from '@/stores/contractors'
import { useArticleStore } from '@/stores/articles'
import AnalyticsTabs, { type AnalyticsTab } from '@/components/analytics/AnalyticsTabs.vue'
import AnalyticsFilters, {
  type AnalyticsFiltersValue,
} from '@/components/analytics/AnalyticsFilters.vue'
import DrillDownDrawer from '@/components/analytics/DrillDownDrawer.vue'
import LiveFleetTab from '@/components/analytics/tabs/LiveFleetTab.vue'
import PeriodRentalTab from '@/components/analytics/tabs/PeriodRentalTab.vue'
import LocationsTab from '@/components/analytics/tabs/LocationsTab.vue'
import ExplorerTab from '@/components/analytics/tabs/ExplorerTab.vue'
import GlossaryTip from '@/components/GlossaryTip.vue'
import { formatCurrency, formatDate } from '@/utils/format'

const store = useAnalyticsStore()
const contractorsStore = useContractorStore()
const articleStore = useArticleStore()
const route = useRoute()

const tabs: AnalyticsTab[] = [
  { key: 'live', label: 'Flota teraz', icon: '🚜' },
  { key: 'period', label: 'Wynajem w okresie', icon: '📅' },
  { key: 'locations', label: 'Lokalizacje', icon: '📍' },
  { key: 'explorer', label: 'Eksplorator', icon: '🔍' },
]

const activeTab = ref<'live' | 'period' | 'locations' | 'explorer'>('period')

const today = computed(() =>
  new Date().toLocaleDateString('pl-PL', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }),
)

// ── Współdzielone filtry ─────────────────────────────────────────────────────
function presetRange(preset: string): { from: string; to: string } {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  const to = now.toISOString().slice(0, 10)
  let from = ''
  if (preset === 'today') from = to
  else if (preset === 'week') from = new Date(y, m, now.getDate() - 6).toISOString().slice(0, 10)
  else if (preset === 'month') from = new Date(y, m, 1).toISOString().slice(0, 10)
  else if (preset === 'quarter') from = new Date(y, Math.floor(m / 3) * 3, 1).toISOString().slice(0, 10)
  else if (preset === 'year') from = new Date(y, 0, 1).toISOString().slice(0, 10)
  else if (preset === 'all') from = ''
  return { from, to }
}

const initialRange = presetRange('month')

const filters = ref<AnalyticsFiltersValue>({
  dateFrom: initialRange.from,
  dateTo: initialRange.to,
  preset: 'month',
  articleType: 'all',
  contractorId: null,
  city: '',
})

const contractorOptions = computed(() =>
  (contractorsStore.list ?? []).map((c: { id: number; name: string }) => ({
    id: c.id,
    name: c.name,
  })),
)

function onFiltersUpdate(v: AnalyticsFiltersValue): void {
  // Jeśli zmieniono preset (nie custom) — przelicz zakres dat
  if (v.preset !== 'custom' && v.preset !== filters.value.preset) {
    const { from, to } = presetRange(v.preset)
    filters.value = { ...v, dateFrom: from, dateTo: to }
  } else {
    filters.value = v
  }
}

function onTabChange(key: string): void {
  activeTab.value = key as typeof activeTab.value
}

// ── Drill-down (udostępniony tabom przez provide) ────────────────────────────
function openDrillDown(kind: DrillDownKind, id: number | string, name: string): void {
  store.openDrillDown(kind, id, name, filters.value.dateFrom, filters.value.dateTo)
}
provide('analytics:openDrillDown', openDrillDown)

function onDrawerClose(): void {
  store.closeDrillDown()
}

// ── Drawer: treść zależna od typu ────────────────────────────────────────────
const drawerOpen = computed(() => store.drillDown.open)
const drawerTitle = computed(() => store.drillDown.title)
const drawerSubtitle = computed(() => store.drillDown.subtitle)

// ── Watcher: zmiana filtrów → reload aktywnych danych (ale NIE live) ─────────
watch(
  () => ({ ...filters.value }),
  (n, old) => {
    if (n.dateFrom === old?.dateFrom && n.dateTo === old?.dateTo &&
        n.contractorId === old?.contractorId && n.city === old?.city &&
        n.articleType === old?.articleType) return
    // PeriodRentalTab / ExplorerTab same reagują na props (watch w komponencie).
    // Tu tylko ewentualny dodatkowy reload — puste (delegowane do tabów).
  },
  { deep: true },
)

onMounted(async () => {
  // Załaduj kontrahentów do filtra (datalist)
  if (!contractorsStore.list?.length) {
    try {
      await contractorsStore.fetchList({ per_page: 500 })
    } catch {
      // ignore — filtr opcjonalny
    }
  }
  // RAO-P2-070 Faza 2: drilldown z DashboardView /articles → ?article=<id>
  // Otwórz historię wynajmów maszyny w drawerze
  const articleId = route.query.article
  if (articleId) {
    const id = Number(articleId)
    if (!Number.isNaN(id)) {
      activeTab.value = 'period'
      let articleName = `Maszyna #${id}`
      try {
        await articleStore.fetchOne(id)
        const fetched = articleStore.current as { name?: string } | null
        if (fetched?.name) articleName = fetched.name
      } catch {
        // ignore — użyjemy placeholder nazwy
      }
      openDrillDown('machine', id, articleName, filters.value.dateFrom, filters.value.dateTo)
    }
  }
})
</script>

<template>
  <div class="analytics-view" data-testid="analytics-view">
    <!-- HEADER -->
    <div class="av-header">
      <h1>Statystyki</h1>
      <span class="av-date">{{ today }}</span>
    </div>

    <!-- TABS -->
    <AnalyticsTabs :tabs="tabs" :active="activeTab" @change="onTabChange" />

    <!-- FILTRY (ukryte na zakładce 'live' — live = "teraz") -->
    <AnalyticsFilters
      v-if="activeTab !== 'live'"
      :model-value="filters"
      :contractors="contractorOptions"
      @update:model-value="onFiltersUpdate"
    />

    <!-- AKTYWNA TABA -->
    <div class="av-tab-content">
      <LiveFleetTab v-if="activeTab === 'live'" />
      <PeriodRentalTab
        v-else-if="activeTab === 'period'"
        :date-from="filters.dateFrom"
        :date-to="filters.dateTo"
        :filters="{
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
          contractorId: filters.contractorId,
          city: filters.city,
          articleType: filters.articleType,
        }"
      />
      <LocationsTab
        v-else-if="activeTab === 'locations'"
        :date-from="filters.dateFrom"
        :date-to="filters.dateTo"
      />
      <ExplorerTab
        v-else-if="activeTab === 'explorer'"
        :date-from="filters.dateFrom"
        :date-to="filters.dateTo"
      />
    </div>

    <!-- DRILL-DOWN DRAWER (współdzielony) -->
    <DrillDownDrawer
      :open="drawerOpen"
      :title="drawerTitle"
      :subtitle="drawerSubtitle"
      :loading="store.drillLoading"
      :error="store.drillError ?? undefined"
      @close="onDrawerClose"
    >
      <!-- MACHINE: historia wynajmów -->
      <div v-if="store.drillDown.kind === 'machine' && store.machineDetails" class="drill-machine">
        <div class="drill-metrics">
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(store.machineDetails.metrics.total_revenue) }}</span>
            <span class="dm-label">Przychód</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ store.machineDetails.metrics.total_days }} dni</span>
            <span class="dm-label">Wynajmu</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ store.machineDetails.metrics.rental_count }}</span>
            <span class="dm-label">Umów</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(store.machineDetails.metrics.avg_daily_revenue) }}</span>
            <span class="dm-label">Średnio/dzień</span>
          </div>
        </div>
        <table class="drill-table" role="table" aria-label="Historia wynajmów maszyny" data-testid="drill-machine-rentals">
          <thead>
            <tr role="row">
              <th role="columnheader">Umowa</th>
              <th role="columnheader">Kontrahent</th>
              <th role="columnheader">Od</th>
              <th role="columnheader">Do</th>
              <th role="columnheader">Dni</th>
              <th role="columnheader">Kwota</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in store.machineDetails.rentals" :key="r.contract_id" role="row">
              <td role="cell">{{ r.contract_number }}</td>
              <td role="cell">{{ r.contractor_name || '—' }}</td>
              <td role="cell">{{ formatDate(r.date_from) }}</td>
              <td role="cell">{{ formatDate(r.date_to) }}</td>
              <td role="cell">{{ r.days }}</td>
              <td role="cell" class="td-strong">{{ formatCurrency(r.revenue) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- LOCATION: umowy w lokalizacji -->
      <div v-else-if="store.drillDown.kind === 'location' && store.locationDetails" class="drill-location">
        <div class="drill-metrics">
          <div class="drill-metric">
            <span class="dm-value">{{ store.locationDetails.metrics.contracts_count }}</span>
            <span class="dm-label">Umów</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ store.locationDetails.metrics.unique_contractors }}</span>
            <span class="dm-label">Kontrahentów</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(store.locationDetails.metrics.total_revenue) }}</span>
            <span class="dm-label">Przychód</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(store.locationDetails.metrics.avg_revenue_per_contract) }}</span>
            <span class="dm-label">Średnio/umowę</span>
          </div>
          <div v-if="store.locationDetails.metrics.pna_count" class="drill-metric">
            <span class="dm-value">{{ store.locationDetails.metrics.pna_count }}</span>
            <span class="dm-label">Kodów PNA<GlossaryTip term="PNA" definition="Pocztowy Numer Adresowy — kod pocztowy" description="Kod pocztowy nadawany przez Pocztę Polską. W RAO służy do auto-uzupełniania miasta, gminy, powiatu i województwa." placement="bottom" :size="12" /></span>
          </div>
        </div>

        <!-- PNA breakdown (tylko dla drill po mieście — RAO-P2-069) -->
        <div v-if="store.locationDetails.pna_breakdown?.length" class="drill-subsection">
          <div class="drill-subtitle">📮 Rozbicie na kody PNA<GlossaryTip term="PNA" definition="Pocztowy Numer Adresowy — kod pocztowy" description="Kod pocztowy nadawany przez Pocztę Polską. W RAO służy do auto-uzupełniania miasta, gminy, powiatu i województwa." placement="bottom" :size="12" /></div>
          <table class="drill-table" role="table" aria-label="Rozbicie na kody PNA">
            <thead>
              <tr role="row"><th role="columnheader">PNA</th><th role="columnheader">Wynajmów</th><th role="columnheader">Przychód</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in store.locationDetails.pna_breakdown" :key="p.postal_code" role="row">
                <td role="cell">{{ p.postal_code }}</td>
                <td role="cell">{{ p.rentals_count }}×</td>
                <td role="cell" class="td-strong">{{ formatCurrency(p.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="store.locationDetails.top_machines.length" class="drill-subsection">
          <div class="drill-subtitle">🚜 Top maszyny</div>
          <table class="drill-table" role="table" aria-label="Top maszyny w lokalizacji">
            <thead>
              <tr role="row"><th role="columnheader">Maszyna</th><th role="columnheader">Razy</th><th role="columnheader">Przychód</th></tr>
            </thead>
            <tbody>
              <tr v-for="m in store.locationDetails.top_machines" :key="m.name" role="row">
                <td role="cell">{{ m.name }}</td>
                <td role="cell">{{ m.rental_count }}×</td>
                <td role="cell" class="td-strong">{{ formatCurrency(m.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="store.locationDetails.top_contractors.length" class="drill-subsection">
          <div class="drill-subtitle">🏆 Top kontrahenci</div>
          <table class="drill-table" role="table" aria-label="Top kontrahenci w lokalizacji">
            <thead>
              <tr role="row"><th role="columnheader">Kontrahent</th><th role="columnheader">Umów</th><th role="columnheader">Przychód</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in store.locationDetails.top_contractors" :key="c.contractor_name" role="row">
                <td role="cell">{{ c.contractor_name }}</td>
                <td role="cell">{{ c.contract_count }}</td>
                <td role="cell" class="td-strong">{{ formatCurrency(c.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pusty stan gdy brak danych -->
      <div
        v-else-if="!store.drillLoading && !store.drillError"
        class="drill-no-data"
      >
        Brak szczegółowych danych.
      </div>
    </DrillDownDrawer>
  </div>
</template>

<style scoped>
.analytics-view {
  padding: var(--spacing-xl) var(--spacing-2xl);
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  font-family: var(--font-family);
}

.av-header {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-md);
}
.av-header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-heading);
  margin: 0;
}
.av-date {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.av-tab-content {
  display: flex;
  flex-direction: column;
}

/* Drill-down treść */
.drill-machine,
.drill-location {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.drill-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--spacing-md);
}
.drill-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--spacing-md);
  background: var(--color-bg-light);
  border-radius: var(--border-radius-sm);
}
.dm-value {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
}
.dm-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.drill-subsection {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.drill-subtitle {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}

.drill-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.drill-table thead th {
  text-align: left;
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text-muted);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  border-bottom: 1px solid var(--color-border);
}
.drill-table tbody td {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-body);
}
.drill-table tbody tr:last-child td {
  border-bottom: none;
}
.drill-table .td-strong {
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  text-align: right;
}

.drill-no-data {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
</style>
