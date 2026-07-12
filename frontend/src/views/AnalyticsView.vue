<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from 'vue'
import { useAnalyticsStore, type DrillDownKind, type AnalyticsFiltersPayload } from '@/stores/analytics'
import { useContractorStore } from '@/stores/contractors'
import AnalyticsTabs, { type AnalyticsTab } from '@/components/analytics/AnalyticsTabs.vue'
import AnalyticsFilters, {
  type AnalyticsFiltersValue,
} from '@/components/analytics/AnalyticsFilters.vue'
import DrillDownDrawer from '@/components/analytics/DrillDownDrawer.vue'
import LiveFleetTab from '@/components/analytics/tabs/LiveFleetTab.vue'
import PeriodRentalTab from '@/components/analytics/tabs/PeriodRentalTab.vue'
import LocationsTab from '@/components/analytics/tabs/LocationsTab.vue'
import MachinesTab from '@/components/analytics/tabs/MachinesTab.vue'
import ServicesAdditionalTab from '@/components/analytics/tabs/ServicesAdditionalTab.vue'
import ServicesRegularTab from '@/components/analytics/tabs/ServicesRegularTab.vue'

const store = useAnalyticsStore()
const contractorsStore = useContractorStore()

const tabs: AnalyticsTab[] = [
  { key: 'live', label: 'Flota teraz', icon: '🚜' },
  { key: 'machines', label: 'Maszyny', icon: '🏗️' },
  { key: 'services-u', label: 'Usługi zwykłe', icon: '�' },
  { key: 'services-s', label: 'Usługi dodatkowe', icon: '�' },
  { key: 'locations', label: 'Lokalizacje', icon: '�' },
  { key: 'period', label: 'Rankingi wynajmu', icon: '�' },
]

const activeTab = ref<'live' | 'machines' | 'services-s' | 'services-u' | 'period' | 'locations'>('live')

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
  articleType: 'all',  // RAO Faza 4b: filter nadal obsługuje maszyny+usługi (backend stats)
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
// RAO-P2-065 #7: internalNumber opcjonalny — dodawany do subtitle drawera
// RAO-P1-014: rozszerzone o 'service' | 'category' (drilldown modal z listą umów/maszyn)
function openDrillDown(
  kind: DrillDownKind,
  id: number | string,
  name: string,
  internalNumber?: string | null,
): void {
  const filtersPayload: AnalyticsFiltersPayload = {
    dateFrom: filters.value.dateFrom,
    dateTo: filters.value.dateTo,
    contractorId: filters.value.contractorId,
    city: filters.value.city,
    articleType: filters.value.articleType,
  }
  store.openDrillDown(kind, id, name, filters.value.dateFrom, filters.value.dateTo, filtersPayload)
}
provide('analytics:openDrillDown', openDrillDown)

function onDrawerClose(): void {
  store.closeDrillDown()
}

// ── Drawer: treść zależna od typu ────────────────────────────────────────────
const drawerOpen = computed(() => store.drillDown.open)
const drawerTitle = computed(() => store.drillDown.title)
const drawerSubtitle = computed(() => store.drillDown.subtitle)

function formatCurrency(v: number | string | null | undefined): string {
  if (v === null || v === undefined || v === '') return '0 zł'
  const n = typeof v === 'string' ? parseFloat(v) : v
  if (Number.isNaN(n)) return '0 zł'
  return n.toLocaleString('pl-PL', {
    style: 'currency',
    currency: 'PLN',
    minimumFractionDigits: 2,
  })
}

function formatDate(d: string | null | undefined): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pl-PL')
}

// RAO-P2-065 #1: klasa koloru ROI — usunięte (ROI panel removed)

// ── Watcher: zmiana filtrów → reload aktywnych danych (ale NIE live) ─────────
watch(
  () => ({ ...filters.value }),
  (n, old) => {
    if (n.dateFrom === old?.dateFrom && n.dateTo === old?.dateTo &&
        n.contractorId === old?.contractorId && n.city === old?.city &&
        n.articleType === old?.articleType) return
    // PeriodRentalTab / LocationsTab reagują na props (watch w komponencie).
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

    <!-- FILTRY (ukryte na zakładce 'live') -->
    <AnalyticsFilters
      v-if="activeTab !== 'live'"
      :model-value="filters"
      :contractors="contractorOptions"
      :active-tab="activeTab"
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
        :filters="{
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
          contractorId: filters.contractorId,
          city: filters.city,
          articleType: filters.articleType,
        }"
      />
      <MachinesTab
        v-else-if="activeTab === 'machines'"
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
      <ServicesAdditionalTab
        v-else-if="activeTab === 'services-s'"
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
      <ServicesRegularTab
        v-else-if="activeTab === 'services-u'"
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

        <table class="drill-table" data-testid="drill-machine-rentals">
          <thead>
            <tr>
              <th>Umowa</th>
              <th>Kontrahent</th>
              <th>Od</th>
              <th>Do</th>
              <th>Dni</th>
              <th>Kwota</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in store.machineDetails.rentals" :key="r.contract_id">
              <td>{{ r.contract_number }}</td>
              <td>{{ r.contractor_name || '—' }}</td>
              <td>{{ formatDate(r.date_from) }}</td>
              <td>{{ formatDate(r.date_to) }}</td>
              <td>{{ r.days }}</td>
              <td class="td-strong">{{ formatCurrency(r.revenue) }}</td>
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
            <span class="dm-label">Kodów PNA</span>
          </div>
        </div>

        <!-- PNA breakdown (tylko dla drill po mieście — RAO-P2-069) -->
        <div v-if="store.locationDetails.pna_breakdown?.length" class="drill-subsection">
          <div class="drill-subtitle">📮 Rozbicie na kody PNA</div>
          <table class="drill-table">
            <thead>
              <tr><th>PNA</th><th>Wynajmów</th><th>Przychód</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in store.locationDetails.pna_breakdown" :key="p.postal_code">
                <td>{{ p.postal_code }}</td>
                <td>{{ p.rentals_count }}×</td>
                <td class="td-strong">{{ formatCurrency(p.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="store.locationDetails.top_machines.length" class="drill-subsection">
          <div class="drill-subtitle">🚜 Top maszyny</div>
          <table class="drill-table">
            <thead>
              <tr><th>Maszyna</th><th>Razy</th><th>Przychód</th></tr>
            </thead>
            <tbody>
              <tr v-for="m in store.locationDetails.top_machines" :key="m.name">
                <td>{{ m.name }}</td>
                <td>{{ m.rental_count }}×</td>
                <td class="td-strong">{{ formatCurrency(m.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="store.locationDetails.top_contractors.length" class="drill-subsection">
          <div class="drill-subtitle">🏆 Top kontrahenci</div>
          <table class="drill-table">
            <thead>
              <tr><th>Kontrahent</th><th>Umów</th><th>Przychód</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in store.locationDetails.top_contractors" :key="c.contractor_name">
                <td>{{ c.contractor_name }}</td>
                <td>{{ c.contract_count }}</td>
                <td class="td-strong">{{ formatCurrency(c.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- SERVICE: szczegóły usługi (top kontrahenci + lokalizacje) -->
      <div v-else-if="store.drillDown.kind === 'service' && store.serviceDetails" class="drill-machine">
        <div class="drill-metrics">
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(store.serviceDetails.metrics.total_revenue) }}</span>
            <span class="dm-label">Przychód</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ store.serviceDetails.metrics.times_billed }}</span>
            <span class="dm-label">Razy zafakturowane</span>
          </div>
        </div>

        <div v-if="store.serviceDetails.top_contractors?.length" class="drill-subsection">
          <span class="drill-subtitle">Top kontrahenci</span>
          <table class="drill-table">
            <thead>
              <tr>
                <th>Kontrahent</th>
                <th style="text-align:right;">Umów</th>
                <th style="text-align:right;">Przychód</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in store.serviceDetails.top_contractors" :key="c.contractor_name">
                <td>{{ c.contractor_name }}</td>
                <td style="text-align:right;">{{ c.contract_count }}</td>
                <td class="td-strong">{{ formatCurrency(c.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="store.serviceDetails.location_breakdown?.length" class="drill-subsection">
          <span class="drill-subtitle">Lokalizacje</span>
          <table class="drill-table">
            <thead>
              <tr>
                <th>Miasto</th>
                <th>PNA</th>
                <th style="text-align:right;">Umów</th>
                <th style="text-align:right;">Przychód</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in store.serviceDetails.location_breakdown" :key="`${l.city}-${l.postal_code}`">
                <td>{{ l.city }}</td>
                <td>{{ l.postal_code ?? '—' }}</td>
                <td style="text-align:right;">{{ l.contract_count }}</td>
                <td class="td-strong">{{ formatCurrency(l.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- CATEGORY: lista maszyn w kategorii -->
      <div v-else-if="store.drillDown.kind === 'category' && store.categoryDetails" class="drill-machine">
        <div class="drill-metrics">
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(store.categoryDetails.total_revenue) }}</span>
            <span class="dm-label">Przychód kategorii</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ store.categoryDetails.items.length }}</span>
            <span class="dm-label">Maszyn</span>
          </div>
        </div>

        <div v-if="store.categoryDetails.items.length" class="drill-subsection">
          <span class="drill-subtitle">Maszyny w kategorii</span>
          <table class="drill-table">
            <thead>
              <tr>
                <th>Maszyna</th>
                <th>Nr wewn.</th>
                <th style="text-align:right;">Dni</th>
                <th style="text-align:right;">Umów</th>
                <th style="text-align:right;">Przychód</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in store.categoryDetails.items" :key="m.machine_id ?? m.article_id">
                <td>{{ m.machine_name || m.article_name }}</td>
                <td>{{ m.internal_number ?? '—' }}</td>
                <td style="text-align:right;">{{ m.rented_days }}</td>
                <td style="text-align:right;">{{ m.contracts_count }}</td>
                <td class="td-strong">{{ formatCurrency(m.revenue) }}</td>
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
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  box-sizing: border-box;
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

/* RAO-P2-065 #1: sekcja ROI — usunięte */

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
