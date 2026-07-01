<template>
  <div class="stats-view">
    <!-- HEADER -->
    <div class="stats-header">
      <h1>Statystyki</h1>
      <span class="stats-date">{{ today }}</span>
    </div>

    <!-- TABS -->
    <div class="tabs-bar">
      <button
        :class="['tab', { 'tab-active': activeTab === 'fleet' }]"
        @click="switchTab('fleet')"
      >
        <span class="tab-dot" :class="activeTab === 'fleet' ? 'tab-dot-active' : ''"></span>
        Flota teraz
      </button>
      <button
        :class="['tab', { 'tab-active': activeTab === 'period' }]"
        @click="switchTab('period')"
      >📅 Wynajem w okresie</button>
    </div>

    <!-- ══════════════════ TAB: FLEETA TERAZ ══════════════════ -->
    <div v-show="activeTab === 'fleet'">
      <div class="section-header">
        <div class="section-title">📊 Stan aktualny floty</div>
        <div class="section-subtitle">Dane na dzień dzisiejszy — niezależne od filtrów datowych</div>
      </div>

      <div v-if="statsStore.loadingLive" class="loading-box">
        <div class="spinner"></div>
        <span>Ładowanie stanu floty...</span>
      </div>
      <template v-else-if="statsStore.currentlyRented">
        <!-- KPI ROW -->
        <div class="kpi-row">
          <div class="kpi-card">
            <div class="kpi-value kpi-success">{{ statsStore.currentlyRented.total_machines - statsStore.currentlyRented.total_rented }}</div>
            <div class="kpi-label">Dostępnych</div>
            <div class="kpi-sub">z {{ statsStore.currentlyRented.total_machines }} maszyn łącznie</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-value kpi-accent">{{ statsStore.currentlyRented.total_rented }}</div>
            <div class="kpi-label">Wynajętych teraz</div>
            <div class="kpi-sub">maszyn u klientów</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-value" :class="utilClass(statsStore.currentlyRented.utilization_pct)">
              {{ statsStore.currentlyRented.utilization_pct }}%
            </div>
            <div class="kpi-label">Wykorzystanie floty</div>
            <div class="kpi-sub">% maszyn u klientów teraz</div>
          </div>
        </div>

        <!-- UTILIZATION BAR -->
        <div class="util-bar-wrap">
          <div class="util-bar-label">Wykorzystanie: {{ statsStore.currentlyRented.utilization_pct }}%</div>
          <div class="util-bar-track">
            <div class="util-bar-fill" :style="{ width: statsStore.currentlyRented.utilization_pct + '%' }"></div>
          </div>
        </div>

        <!-- RENTED TABLE -->
        <div class="table-panel" v-if="statsStore.currentlyRented.items?.length">
          <div class="table-title">Maszyny aktualnie wynajęte ({{ statsStore.currentlyRented.items.length }})</div>
          <div class="table-scroll">
            <table class="stats-table" data-testid="stats-rented-table">
              <thead>
                <tr>
                  <th>Maszyna</th>
                  <th>Nr wewnętrzny</th>
                  <th>Kategoria</th>
                  <th>Umowa</th>
                  <th>Kontrahent</th>
                  <th>Planowany zwrot</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in statsStore.currentlyRented.items" :key="item.article_id + '-' + item.contract_number">
                  <td>{{ item.name }}</td>
                  <td>{{ item.internal_number || '—' }}</td>
                  <td>{{ item.category_main || '—' }}</td>
                  <td class="td-strong">{{ item.contract_number }}</td>
                  <td>{{ item.contractor_name || '—' }}</td>
                  <td>{{ item.return_date ? formatDate(item.return_date) : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="empty-state">
          <span class="empty-ok">✓</span> Brak aktywnych wynajmów — wszystkie maszyny dostępne
        </div>
      </template>
      <div v-else class="empty-state">
        <span class="empty-icon">📊</span> Brak danych o flocie
      </div>
    </div>

    <!-- ══════════════════ TAB: WYNAJEM W OKRESIE ══════════════════ -->
    <div v-show="activeTab === 'period'">
      <!-- DATE FILTERS -->
      <div class="filter-bar">
        <span class="filter-label">Okres:</span>
        <button
          v-for="p in presets"
          :key="p.key"
          :class="['pill', { active: activePreset === p.key }]"
          @click="selectPreset(p.key)"
        >{{ p.label }}</button>
        <button :class="['pill', { active: activePreset === 'custom' }]" @click="activePreset = 'custom'">📅 Własny</button>
        <div class="pill-custom" v-if="activePreset === 'custom'">
          <input type="date" v-model="customFrom" class="pill-date" />
          <span>—</span>
          <input type="date" v-model="customTo" class="pill-date" />
          <button class="pill pill-go" @click="applyPeriodFilter()">Filtruj</button>
        </div>
      </div>

      <!-- INTERNAL NUMBER FILTER -->
      <div class="filter-bar">
        <span class="filter-label">Nr wewnętrzny:</span>
        <input
          type="text"
          v-model="internalNumber"
          class="filter-input"
          placeholder="— wszystkie —"
          list="articles-datalist"
        />
        <datalist id="articles-datalist">
          <option v-for="a in articlesList" :key="a.id" :value="a.internal_number">{{ a.name }}</option>
        </datalist>
        <button class="pill" @click="internalNumber = ''" v-if="internalNumber">✕ Wyczyść</button>
      </div>

      <div v-if="statsStore.loading" class="loading-box">
        <div class="spinner"></div>
        <span>Ładowanie statystyk...</span>
      </div>
      <template v-else>
        <!-- KPI ROW -->
        <div class="kpi-row" v-if="statsStore.summary">
          <div class="kpi-card">
            <div class="kpi-value kpi-accent">{{ formatCurrency(statsStore.summary.period_revenue) }}</div>
            <div class="kpi-label">Przychód w okresie</div>
            <div class="kpi-sub" :class="revenueSourceClass">{{ statsStore.summary.revenue_source_label }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-value">{{ statsStore.summary.contracts_in_period }}</div>
            <div class="kpi-label">Umów w okresie</div>
            <div class="kpi-sub">aktywnych umów</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-value kpi-success">{{ statsStore.summary.total_rented }}</div>
            <div class="kpi-label">Wynajętych teraz</div>
            <div class="kpi-sub">z {{ statsStore.summary.total_machines }} maszyn</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-value" :class="utilClass(statsStore.summary.utilization_pct)">
              {{ statsStore.summary.utilization_pct }}%
            </div>
            <div class="kpi-label">Wykorzystanie</div>
            <div class="kpi-sub">floty teraz</div>
          </div>
        </div>

        <!-- REVENUE BREAKDOWN (actual vs estimate) -->
        <div class="revenue-breakdown" v-if="statsStore.summary && statsStore.summary.revenue_actual > 0">
          <div class="breakdown-item">
            <span class="breakdown-label">Rzeczywiste (z rozliczeń):</span>
            <span class="breakdown-value breakdown-actual">{{ formatCurrency(statsStore.summary.revenue_actual) }}</span>
          </div>
          <div class="breakdown-item" v-if="statsStore.summary.revenue_estimate > 0">
            <span class="breakdown-label">Szacunek (cennik):</span>
            <span class="breakdown-value breakdown-estimate">{{ formatCurrency(statsStore.summary.revenue_estimate) }}</span>
          </div>
        </div>

        <!-- TOP MACHINES TABLE -->
        <div class="table-panel" v-if="statsStore.topMachines?.length">
          <div class="table-title">🏆 Top maszyny po przychodzie ({{ statsStore.topMachines.length }})</div>
          <div class="table-scroll">
            <table class="stats-table" data-testid="stats-top-machines">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Maszyna</th>
                  <th>Nr wewnętrzny</th>
                  <th>Przychód</th>
                  <th>Dni wynajmu</th>
                  <th>Liczba umów</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(m, i) in statsStore.topMachines" :key="m.article_id">
                  <td class="td-rank">{{ i + 1 }}</td>
                  <td>{{ m.name }}</td>
                  <td>{{ m.internal_number || '—' }}</td>
                  <td class="td-strong">{{ formatCurrency(m.revenue) }}</td>
                  <td>{{ m.rented_days }}</td>
                  <td>{{ m.contracts_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="empty-state">
          <span class="empty-icon">📊</span> Brak danych o top maszynach w wybranym okresie
        </div>

        <!-- ADDITIONAL FEES -->
        <div class="table-panel" v-if="statsStore.additionalFees?.breakdown?.length">
          <div class="table-title">💰 Pozycje dodatkowe (usługi)</div>
          <div class="table-scroll">
            <table class="stats-table" data-testid="stats-additional-fees">
              <thead>
                <tr>
                  <th>Usługa</th>
                  <th>Przychód</th>
                  <th>Liczba rozliczeń</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="f in statsStore.additionalFees.breakdown" :key="f.article_id + '-' + f.service_name">
                  <td>{{ f.service_name }}</td>
                  <td class="td-strong">{{ formatCurrency(f.total_revenue) }}</td>
                  <td>{{ f.times_billed }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="tfoot-row">
                  <td>Razem</td>
                  <td class="td-strong">{{ formatCurrency(statsStore.additionalFees.total_services_revenue) }}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- LOCATIONS -->
        <div class="table-panel" v-if="statsStore.locations?.length">
          <div class="table-title">📍 Lokalizacje wynajmu</div>
          <div class="table-scroll">
            <table class="stats-table" data-testid="stats-locations">
              <thead>
                <tr>
                  <th>Miasto</th>
                  <th>Kod pocztowy</th>
                  <th>Gmina</th>
                  <th>Powiat</th>
                  <th>Województwo</th>
                  <th>Liczba wynajmów</th>
                  <th>Przychód</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="loc in statsStore.locations" :key="loc.city + '-' + (loc.postal_code || '')">
                  <td class="td-strong">{{ loc.city }}</td>
                  <td>{{ loc.postal_code || '—' }}</td>
                  <td>{{ loc.gmina || '—' }}</td>
                  <td>{{ loc.powiat || '—' }}</td>
                  <td>{{ loc.wojewodztwo || '—' }}</td>
                  <td>{{ loc.rentals_count }}</td>
                  <td class="td-strong">{{ formatCurrency(loc.total_revenue) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useStatsStore } from '@/stores/stats'
import { useArticleStore } from '@/stores/articles'

const statsStore = useStatsStore()
const articlesStore = useArticleStore()

const activeTab = ref<'fleet' | 'period'>('period')
const activePreset = ref('month')
const customFrom = ref('')
const customTo = ref('')
const internalNumber = ref('')

const today = computed(() => new Date().toLocaleDateString('pl-PL', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }))

const presets = [
  { key: 'month', label: 'Miesiąc' },
  { key: 'quarter', label: '3 miesiące' },
  { key: 'year', label: 'Rok' },
]

const articlesList = computed(() => articlesStore.list || [])

function switchTab(tab: 'fleet' | 'period') {
  activeTab.value = tab
  if (tab === 'fleet' && !statsStore.currentlyRented) {
    statsStore.fetchCurrentlyRented()
  }
}

function selectPreset(key: string) {
  activePreset.value = key
  const today = new Date()
  let from: string, to: string
  if (key === 'month') {
    from = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0, 10)
    to = today.toISOString().slice(0, 10)
  } else if (key === 'quarter') {
    from = new Date(today.getFullYear(), today.getMonth() - 2, 1).toISOString().slice(0, 10)
    to = today.toISOString().slice(0, 10)
  } else if (key === 'year') {
    from = new Date(today.getFullYear(), 0, 1).toISOString().slice(0, 10)
    to = today.toISOString().slice(0, 10)
  }
  if (from && to) loadPeriod(from, to)
}

function applyPeriodFilter() {
  if (customFrom.value && customTo.value) {
    loadPeriod(customFrom.value, customTo.value)
  }
}

async function loadPeriod(from: string, to: string) {
  const params = internalNumber.value ? { internal_number: internalNumber.value } : {}
  // stats store nie wspiera internal_number w fetchPeriod — wywołujemy bezpośrednio
  await statsStore.fetchSummary(from, to)
  await statsStore.fetchTopMachines(from, to)
  await statsStore.fetchAdditionalFees(from, to)
  await statsStore.fetchLocations(from, to)
}

function formatDate(d: string | Date): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pl-PL')
}

function formatCurrency(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === '') return '0 zł'
  const n = typeof v === 'string' ? parseFloat(v) : v
  if (isNaN(n)) return '0 zł'
  return n.toLocaleString('pl-PL', { style: 'currency', currency: 'PLN', minimumFractionDigits: 2 })
}

function utilClass(pct: number): string {
  if (pct >= 80) return 'kpi-success'
  if (pct >= 50) return 'kpi-accent'
  return 'kpi-warning'
}

const revenueSourceClass = computed(() => {
  const label = statsStore.summary?.revenue_source_label
  if (label === 'rzeczywiste') return 'source-actual'
  if (label === 'szacunek') return 'source-estimate'
  return 'source-empty'
})

watch(internalNumber, () => {
  if (activePreset.value !== 'custom') {
    selectPreset(activePreset.value)
  } else if (customFrom.value && customTo.value) {
    applyPeriodFilter()
  }
})

onMounted(async () => {
  // Domyślnie ładuj okres (miesiąc) + flota
  selectPreset('month')
  await statsStore.fetchCurrentlyRented()
  // Załaduj listę artykułów dla datalist (nr wewnętrzny)
  if (!articlesStore.list?.length) {
    try { await articlesStore.fetchList({ per_page: 200 }) } catch {}
  }
})
</script>

<style scoped>
.stats-view {
  padding: 24px 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-header {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-bottom: 20px;
}
.stats-header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-heading);
  margin: 0;
}
.stats-date {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* TABS */
.tabs-bar {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid var(--color-border);
  margin-bottom: 24px;
}
.tab {
  padding: 10px 20px;
  border: none;
  background: transparent;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  transition: all 0.15s;
  font-family: var(--font-family);
  display: flex;
  align-items: center;
  gap: 8px;
}
.tab:hover { color: var(--color-text-body); }
.tab-active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}
.tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border);
}
.tab-dot-active {
  background: var(--color-success);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

/* SECTION HEADER */
.section-header {
  margin-bottom: 16px;
}
.section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
.section-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* KPI CARDS */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}
.kpi-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  padding: 20px;
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s;
}
.kpi-card:hover {
  box-shadow: var(--shadow-card-hover);
}
.kpi-value {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-extrabold);
  color: var(--color-text-heading);
  line-height: 1.1;
  margin-bottom: 4px;
}
.kpi-success { color: var(--color-success); }
.kpi-accent { color: var(--color-accent-blue); }
.kpi-warning { color: var(--color-warning); }
.kpi-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-body);
}
.kpi-sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: 4px;
}
.source-actual { color: var(--color-success); font-weight: var(--font-weight-semibold); }
.source-estimate { color: var(--color-warning); font-weight: var(--font-weight-semibold); }
.source-empty { color: var(--color-text-muted); }

/* UTIL BAR */
.util-bar-wrap {
  margin-bottom: 24px;
}
.util-bar-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  margin-bottom: 6px;
  font-weight: var(--font-weight-medium);
}
.util-bar-track {
  height: 12px;
  background: var(--color-bg-light);
  border-radius: var(--border-radius-pill);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
.util-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-success), var(--color-accent-blue));
  border-radius: var(--border-radius-pill);
  transition: width 0.3s ease;
}

/* REVENUE BREAKDOWN */
.revenue-breakdown {
  display: flex;
  gap: 24px;
  padding: 12px 20px;
  background: var(--color-bg-light);
  border-radius: var(--border-radius-md);
  margin-bottom: 20px;
  border: 1px solid var(--color-border);
}
.breakdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.breakdown-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}
.breakdown-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
}
.breakdown-actual { color: var(--color-success); }
.breakdown-estimate { color: var(--color-warning); }

/* TABLE PANEL */
.table-panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  margin-bottom: 20px;
  overflow: hidden;
}
.table-title {
  padding: 14px 20px;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-light);
}
.table-scroll {
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}
.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.stats-table thead {
  position: sticky;
  top: 0;
  background: var(--color-bg-card);
  z-index: 1;
}
.stats-table th {
  padding: 10px 16px;
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-muted);
  border-bottom: 2px solid var(--color-border);
  white-space: nowrap;
}
.stats-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-body);
}
.stats-table tbody tr:hover {
  background: var(--color-bg-light);
}
.td-strong { font-weight: var(--font-weight-semibold); color: var(--color-text-heading); }
.td-rank {
  font-weight: var(--font-weight-bold);
  color: var(--color-accent-blue);
  text-align: center;
  width: 40px;
}
.tfoot-row {
  background: var(--color-bg-light);
  font-weight: var(--font-weight-bold);
}
.tfoot-row td {
  border-top: 2px solid var(--color-border);
  border-bottom: none;
}

/* FILTERS */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.filter-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-body);
  margin-right: 4px;
}
.pill {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  border-radius: var(--border-radius-pill);
  font-size: var(--font-size-sm);
  cursor: pointer;
  color: var(--color-text-body);
  font-family: var(--font-family);
  transition: all 0.15s;
}
.pill:hover {
  border-color: var(--color-border-hover);
}
.pill.active {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  border-color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}
.pill-go {
  background: var(--color-accent-blue);
  color: white;
  border-color: var(--color-accent-blue);
}
.pill-custom {
  display: flex;
  align-items: center;
  gap: 6px;
}
.pill-date {
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
}
.filter-input {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  width: 180px;
}

/* LOADING + EMPTY */
.loading-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
}
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 32px;
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
  background: var(--color-bg-light);
  border-radius: var(--border-radius-md);
  border: 1px dashed var(--color-border);
  justify-content: center;
}
.empty-ok {
  color: var(--color-success);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-lg);
}
.empty-icon {
  font-size: var(--font-size-lg);
}

/* RESPONSIVE */
@media (max-width: 768px) {
  .stats-view { padding: 16px; }
  .kpi-row { grid-template-columns: 1fr; }
  .revenue-breakdown { flex-direction: column; gap: 8px; }
  .tabs-bar { overflow-x: auto; }
}
</style>
