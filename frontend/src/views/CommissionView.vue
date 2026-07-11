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
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in report.items" :key="item.salesperson_id">
              <td>{{ item.salesperson_name }}</td>
              <td class="num">{{ item.contracts_count }}</td>
              <td class="num">{{ item.commission_rate ?? '—' }} %</td>
              <td class="num">{{ formatCurrency(item.total_revenue) }}</td>
              <td class="num commission">{{ formatCurrency(item.commission_amount) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="3"><strong>RAZEM</strong></td>
              <td class="num"><strong>{{ formatCurrency(report.grand_total_revenue) }}</strong></td>
              <td class="num commission"><strong>{{ formatCurrency(report.grand_total_commission) }}</strong></td>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/composables/useApi'
import { useFileDownload } from '@/composables/useFileDownload'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/format'

const today = new Date()
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)

const dateFrom = ref(firstDay.toISOString().slice(0, 10))
const dateTo   = ref(today.toISOString().slice(0, 10))
const loading  = ref(false)
const error    = ref(null)
const report   = ref({ items: [], grand_total_revenue: 0, grand_total_commission: 0, date_from: '', date_to: '' })
const { saveToFolder } = useFileDownload()
const toastStore = useToastStore()

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
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Błąd pobierania danych'
  } finally {
    loading.value = false
  }
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
</style>
