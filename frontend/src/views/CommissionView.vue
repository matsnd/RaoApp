<template>
  <div class="commission-view page-container">
    <div class="page-header">
      <h1 class="page-title">Prowizje handlowców</h1>
      <div class="header-filters">
        <label for="commission-date-from">Od:
          <input id="commission-date-from" type="date" v-model="dateFrom" @change="load" />
        </label>
        <label for="commission-date-to">Do:
          <input id="commission-date-to" type="date" v-model="dateTo" @change="load" />
        </label>
        <button class="btn btn-primary" @click="load">Odśwież</button>
        <button class="btn btn-print print-hide" @click="printPage" aria-label="Drukuj zestawienie prowizji">🖨 Drukuj</button>
      </div>
    </div>

    <div v-if="loading" class="state-loading" role="status" aria-live="polite">Ładowanie…</div>
    <div v-else-if="error" class="state-error" role="alert">{{ error }}</div>
    <template v-else>
      <div class="summary-cards">
        <div class="page-card kpi-card">
          <div class="card-label">Łączny przychód</div>
          <div class="card-value">{{ formatCurrency(report.grand_total_revenue) }}</div>
        </div>
        <div class="page-card kpi-card">
          <div class="card-label">Łączna prowizja</div>
          <div class="card-value highlight">{{ formatCurrency(report.grand_total_commission) }}</div>
        </div>
        <div class="page-card kpi-card">
          <div class="card-label">Okres</div>
          <div class="card-value small">{{ report.date_from }} — {{ report.date_to }}</div>
        </div>
      </div>

      <div class="page-card section-block">
        <h2>Zestawienie per handlowiec</h2>
        <table class="data-grid" v-if="report.items.length">
          <thead>
            <tr>
              <th>Handlowiec</th>
              <th class="num">Umów</th>
              <th class="num">Stawka prowizji</th>
              <th class="num">Przychód</th>
              <th class="num">Prowizja</th>
              <th class="num actions-col">Szczegóły</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in report.items" :key="item.salesperson_id">
              <td>{{ item.salesperson_name }}</td>
              <td class="num">{{ item.contracts_count }}</td>
              <td class="num">{{ item.commission_rate ?? '—' }} %</td>
              <td class="num">{{ formatCurrency(item.total_revenue) }}</td>
              <td class="num commission">{{ formatCurrency(item.commission_amount) }}</td>
              <td class="num actions-col">
                <button
                  type="button"
                  class="btn btn-link drill-btn"
                  :data-testid="`commission-drill-open-${item.salesperson_id}`"
                  :aria-label="`Pokaż umowy handlowca ${item.salesperson_name}`"
                  @click="openDrill(item)"
                >Umowy →</button>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="3"><strong>RAZEM</strong></td>
              <td class="num"><strong>{{ formatCurrency(report.grand_total_revenue) }}</strong></td>
              <td class="num commission"><strong>{{ formatCurrency(report.grand_total_commission) }}</strong></td>
              <td class="num actions-col"></td>
            </tr>
          </tfoot>
        </table>
        <p v-else class="empty-msg">Brak danych dla wybranego okresu.</p>
      </div>

      <div class="note">
        <strong>Jak ustawić stawkę prowizji?</strong>
        Przejdź do <em>Ustawienia → Handlowcy</em> i edytuj pole „Prowizja (%)" dla każdego handlowca.
      </div>
    </template>

    <!-- P1-123 Faza 2: drill-down umów handlowca -->
    <DrillDownDrawer
      :open="drillOpen"
      :title="drillTitle"
      :subtitle="drillSubtitle"
      :loading="drillLoading"
      :error="drillError ?? undefined"
      @close="closeDrill"
    >
      <div v-if="drillData" class="drill-contracts" data-testid="commission-drill-body">
        <!-- KPI kontrastowe z tabelą nadrzędną: przychód, koszt firmy, zarobek, prowizja -->
        <div class="drill-metrics">
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(drillData.total_revenue) }}</span>
            <span class="dm-label">Przychód</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(drillData.total_company_cost) }}</span>
            <span class="dm-label">Koszt firmy</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value">{{ formatCurrency(drillData.total_earnings) }}</span>
            <span class="dm-label">Zarobek firmy</span>
          </div>
          <div class="drill-metric">
            <span class="dm-value highlight">{{ formatCurrency(drillData.total_commission) }}</span>
            <span class="dm-label">Prowizja</span>
          </div>
        </div>

        <table class="drill-table" data-testid="commission-drill-table" v-if="drillData.items.length">
          <thead>
            <tr>
              <th>Umowa</th>
              <th>Kontrahent</th>
              <th>Okres</th>
              <th class="num">Przychód</th>
              <th class="num">Koszt firmy</th>
              <th class="num">Zarobek</th>
              <th class="num">Stawka</th>
              <th class="num">Prowizja</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in drillData.items" :key="row.contract_id">
              <td class="td-strong">{{ row.number }}</td>
              <td>{{ row.contractor_name ?? '—' }}</td>
              <td class="muted">
                {{ formatDate(row.date_from) }} — {{ formatDate(row.date_to) }}
              </td>
              <td class="num">{{ formatCurrency(row.total_revenue) }}</td>
              <td class="num">{{ formatCurrency(row.total_company_cost) }}</td>
              <td class="num">
                {{ formatCurrency(row.earnings) }}
                <span
                  v-if="row.fallback_applied"
                  class="fallback-badge"
                  data-testid="commission-fallback-badge"
                  title="Brak kompletnego rozliczenia — prowizja liczona od przychodu z pozycji umowy"
                >szac.</span>
              </td>
              <td class="num">{{ row.commission_rate ?? '—' }} %</td>
              <td class="num commission">{{ formatCurrency(row.commission_amount) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="drill-total-row">
              <td colspan="3"><strong>RAZEM</strong></td>
              <td class="num"><strong>{{ formatCurrency(drillData.total_revenue) }}</strong></td>
              <td class="num"><strong>{{ formatCurrency(drillData.total_company_cost) }}</strong></td>
              <td class="num"><strong>{{ formatCurrency(drillData.total_earnings) }}</strong></td>
              <td></td>
              <td class="num commission"><strong>{{ formatCurrency(drillData.total_commission) }}</strong></td>
            </tr>
          </tfoot>
        </table>
        <p v-else class="empty-msg">Brak umów dla tego handlowca w wybranym okresie.</p>

        <div class="drill-legend">
          <span class="fallback-badge">szac.</span> — brak kompletnego rozliczenia
          (oba koszty <code>cost_client</code>/<code>cost_company</code>); prowizja liczona
          od przychodu z pozycji umowy jako fallback.
        </div>
      </div>
    </DrillDownDrawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/composables/useApi'
import { useFileDownload } from '@/composables/useFileDownload'
import { useToastStore } from '@/stores/toast'
import { formatCurrency, formatDate } from '@/utils/format'
import DrillDownDrawer from '@/components/analytics/DrillDownDrawer.vue'

const today = new Date()
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)

const dateFrom = ref(firstDay.toISOString().slice(0, 10))
const dateTo   = ref(today.toISOString().slice(0, 10))
const loading  = ref(false)
const error    = ref(null)
const report   = ref({ items: [], grand_total_revenue: 0, grand_total_commission: 0, date_from: '', date_to: '' })
const { saveToFolder } = useFileDownload()
const toastStore = useToastStore()

// P1-123 Faza 2: drill-down stan
const drillOpen    = ref(false)
const drillLoading = ref(false)
const drillError   = ref(null)
const drillData    = ref(null)
const drillContext = ref({ salesperson_id: null, salesperson_name: '' })

const drillTitle = computed(() =>
  drillContext.value.salesperson_name
    ? `Umowy — ${drillContext.value.salesperson_name}`
    : 'Umowy handlowca',
)
const drillSubtitle = computed(() => {
  const df = drillData.value?.date_from ?? dateFrom.value
  const dt = drillData.value?.date_to ?? dateTo.value
  return `${formatDate(df)} — ${formatDate(dt)}`
})

async function printPage() {
  try {
    const response = await api.get('/reports/summary/commissions', {
      params: { date_from: dateFrom.value, date_to: dateTo.value },
      responseType: 'blob',
    })
    const cd = response.headers['content-disposition'] || ''
    // Parsowanie nazwy pliku z Content-Disposition
    let filename = 'Prowizje.pdf'
    const rfc5987 = cd.match(/filename\*=UTF-8''([^;]+)/i)
    if (rfc5987) {
      try { filename = decodeURIComponent(rfc5987[1]) } catch { }
    } else {
      const classic = cd.match(/filename="?([^";\n]+)"?/i)
      if (classic) filename = classic[1].trim()
    }
    // RAO-TECH-003: zestawienia nie mają folderu per-oddział — fallback download
    await saveToFolder(response.data, cd, filename, 'zestawienia')
    toastStore.showToast(`${filename} pobrany`, 'success')
  } catch {
    toastStore.error('Błąd generowania PDF')
  }
}

async function load() {
  loading.value = true
  error.value   = null
  try {
    const { data } = await api.get('/stats/commissions', {
      params: { date_from: dateFrom.value, date_to: dateTo.value },
    })
    report.value = data
    // Jeśli drawer jest otwarty, odśwież jego dane dla tego samego zakresu
    if (drillOpen.value && drillContext.value.salesperson_id) {
      await loadDrill(drillContext.value.salesperson_id)
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Błąd pobierania danych'
  } finally {
    loading.value = false
  }
}

// P1-123 Faza 2: pobranie szczegółów umów dla handlowca
async function loadDrill(salespersonId) {
  drillLoading.value = true
  drillError.value   = null
  drillData.value    = null
  try {
    const { data } = await api.get(
      `/stats/commissions/${salespersonId}/contracts`,
      { params: { date_from: dateFrom.value, date_to: dateTo.value } },
    )
    drillData.value = data
  } catch (e) {
    drillError.value = e?.response?.data?.detail || 'Błąd pobierania umów handlowca'
  } finally {
    drillLoading.value = false
  }
}

function openDrill(item) {
  drillContext.value = {
    salesperson_id: item.salesperson_id,
    salesperson_name: item.salesperson_name,
  }
  drillOpen.value = true
  loadDrill(item.salesperson_id)
}

function closeDrill() {
  drillOpen.value = false
  // Zachowaj dane do następnego otwarcia tylko jeśli nie ma błędu;
  // czyścimy przy zamknięciu, by uniknąć wyświetlania starych umów innego handlowca
  drillData.value = null
  drillError.value = null
}

onMounted(load)
</script>

<style scoped>
/* RAO-P3-071 Faza 4: unifikacja design system — używa zmiennych CSS + klas globalnych */
.commission-view { padding: var(--spacing-xl); max-width: 960px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-xl); flex-wrap: wrap; gap: var(--spacing-md); }
.page-title { font-size: var(--font-size-2xl); font-weight: 700; color: var(--color-text-heading); margin: 0; }
.header-filters { display: flex; gap: var(--spacing-md); align-items: center; flex-wrap: wrap; }
.header-filters label { display: flex; align-items: center; gap: var(--spacing-xs); font-size: var(--font-size-sm); color: var(--color-text-body); }
.header-filters input { padding: var(--spacing-xs) var(--spacing-sm); border: 1px solid var(--color-border); border-radius: var(--border-radius-sm); font-size: var(--font-size-sm); }
.btn-print { background: var(--color-bg-light); color: var(--color-primary); border: 1px solid var(--color-border); }

.state-loading, .empty-msg { color: var(--color-text-muted); font-style: italic; margin: var(--spacing-lg) 0; }
.state-error { color: var(--color-danger); font-style: italic; margin: var(--spacing-lg) 0; }

.summary-cards { display: flex; gap: var(--spacing-lg); margin-bottom: var(--spacing-xl); flex-wrap: wrap; }
.kpi-card { padding: var(--spacing-lg) var(--spacing-xl); min-width: 160px; }
.card-label { font-size: var(--font-size-xs); color: var(--color-text-muted); text-transform: uppercase; letter-spacing: .04em; margin-bottom: var(--spacing-xs); }
.card-value { font-size: var(--font-size-2xl); font-weight: 700; color: var(--color-text-heading); }
.card-value.highlight { color: var(--color-success); }
.card-value.small { font-size: var(--font-size-lg); font-weight: 500; }

.section-block { padding: var(--spacing-lg) var(--spacing-xl); margin-bottom: var(--spacing-xl); }
.section-block h2 { font-size: var(--font-size-lg); font-weight: 600; color: var(--color-text-heading); margin: 0 0 var(--spacing-md); }

/* Nadpisanie .data-grid dla CommissionView (read-only, bez cursor:pointer) */
.data-grid tbody tr { cursor: default; }
.data-grid td.num, .data-grid th.num { text-align: right; }
.data-grid td.commission { color: var(--color-success); font-weight: 600; }
.total-row td { background: var(--color-bg-light); border-top: 2px solid var(--color-border); font-weight: 700; }

.note { background: var(--color-bg-light); border-left: 3px solid var(--color-primary); padding: var(--spacing-md) var(--spacing-lg); font-size: var(--font-size-sm); border-radius: var(--border-radius-sm); color: var(--color-text-body); }

/* P1-123 Faza 2: drill-down umów handlowca */
.actions-col { white-space: nowrap; }
.btn-link {
  background: transparent;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-sm);
  text-decoration: underline;
  border-radius: var(--border-radius-sm);
}
.btn-link:hover { background: var(--color-bg-light); }

.drill-contracts { display: flex; flex-direction: column; gap: var(--spacing-lg); }
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
.dm-value { font-size: var(--font-size-lg); font-weight: 700; color: var(--color-text-heading); }
.dm-value.highlight { color: var(--color-success); }
.dm-label { font-size: var(--font-size-xs); color: var(--color-text-muted); text-transform: uppercase; letter-spacing: .04em; }

.drill-table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.drill-table thead th {
  text-align: left;
  padding: var(--spacing-sm);
  border-bottom: 2px solid var(--color-border);
  color: var(--color-text-muted);
  font-weight: 600;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
}
.drill-table tbody td {
  padding: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-body);
}
.drill-table td.num, .drill-table th.num { text-align: right; }
.drill-table td.muted { color: var(--color-text-muted); }
.drill-table td.td-strong { font-weight: 600; color: var(--color-text-heading); }
.drill-table td.commission { color: var(--color-success); font-weight: 600; }
.drill-total-row td {
  background: var(--color-bg-light);
  border-top: 2px solid var(--color-border);
  font-weight: 700;
}

.fallback-badge {
  display: inline-block;
  margin-left: var(--spacing-xs);
  padding: 0 var(--spacing-xs);
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--color-warning, #b87b00);
  background: var(--color-warning-bg, rgba(184, 123, 0, 0.12));
  border-radius: var(--border-radius-sm);
  vertical-align: middle;
}

.drill-legend {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  line-height: 1.5;
}
.drill-legend code {
  background: var(--color-bg-light);
  padding: 0 var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-family-mono, monospace);
}
</style>
