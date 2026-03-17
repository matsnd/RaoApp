<template>
  <div class="commission-view">
    <div class="page-header">
      <h1>Prowizje handlowców</h1>
      <div class="header-filters">
        <label>Od:
          <input type="date" v-model="dateFrom" @change="load" />
        </label>
        <label>Do:
          <input type="date" v-model="dateTo" @change="load" />
        </label>
        <button class="btn-primary" @click="load">Odśwież</button>
        <button class="btn-print print-hide" @click="printPage">🖨 Drukuj</button>
      </div>
    </div>

    <div v-if="loading" class="loading-msg">Ładowanie…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else>
      <div class="summary-cards">
        <div class="card">
          <div class="card-label">Łączny przychód</div>
          <div class="card-value">{{ fmt(report.grand_total_revenue) }} zł</div>
        </div>
        <div class="card">
          <div class="card-label">Łączna prowizja</div>
          <div class="card-value highlight">{{ fmt(report.grand_total_commission) }} zł</div>
        </div>
        <div class="card">
          <div class="card-label">Okres</div>
          <div class="card-value small">{{ report.date_from }} — {{ report.date_to }}</div>
        </div>
      </div>

      <div class="section-block">
        <h2>Zestawienie per handlowiec</h2>
        <table class="data-table" v-if="report.items.length">
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
              <td class="num">{{ fmt(item.total_revenue) }} zł</td>
              <td class="num commission">{{ fmt(item.commission_amount) }} zł</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="3"><strong>RAZEM</strong></td>
              <td class="num"><strong>{{ fmt(report.grand_total_revenue) }} zł</strong></td>
              <td class="num commission"><strong>{{ fmt(report.grand_total_commission) }} zł</strong></td>
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
import api from '@/api/axios'

const today = new Date()
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)

const dateFrom = ref(firstDay.toISOString().slice(0, 10))
const dateTo   = ref(today.toISOString().slice(0, 10))
const loading  = ref(false)
const error    = ref(null)
const report   = ref({ items: [], grand_total_revenue: 0, grand_total_commission: 0, date_from: '', date_to: '' })

function printPage() { window.print() }

function fmt(val) {
  const n = parseFloat(val) || 0
  return n.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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
.commission-view { padding: 1.5rem; max-width: 960px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: .75rem; }
.page-header h1 { font-size: 1.4rem; font-weight: 700; color: #1D2B53; margin: 0; }
.header-filters { display: flex; gap: .75rem; align-items: center; flex-wrap: wrap; }
.header-filters label { display: flex; align-items: center; gap: .4rem; font-size: .85rem; color: #444; }
.header-filters input { padding: .3rem .5rem; border: 1px solid #ccc; border-radius: 4px; font-size: .85rem; }
.btn-primary { padding: .4rem .9rem; background: #1D2B53; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-size: .85rem; }
.btn-primary:hover { background: #2a3f7e; }
.btn-print { padding: .35rem .85rem; background: #f0f4ff; color: #1D2B53; border: 1px solid #c0cce8; border-radius: 5px; cursor: pointer; font-size: .82rem; font-weight: 600; }
.btn-print:hover { background: #dde6ff; }

.loading-msg, .error-msg, .empty-msg { color: #888; font-style: italic; margin: 1rem 0; }
.error-msg { color: #c00; }

.summary-cards { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.card { background: #fff; border: 1px solid #e0e4ef; border-radius: 8px; padding: 1rem 1.5rem; min-width: 160px; }
.card-label { font-size: .75rem; color: #888; text-transform: uppercase; letter-spacing: .04em; margin-bottom: .3rem; }
.card-value { font-size: 1.4rem; font-weight: 700; color: #1D2B53; }
.card-value.highlight { color: #27ae60; }
.card-value.small { font-size: 1rem; font-weight: 500; }

.section-block { background: #fff; border: 1px solid #e0e4ef; border-radius: 8px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; }
.section-block h2 { font-size: 1rem; font-weight: 600; color: #1D2B53; margin: 0 0 .75rem; }

.data-table { width: 100%; border-collapse: collapse; font-size: .88rem; }
.data-table th, .data-table td { padding: .55rem .75rem; border-bottom: 1px solid #f0f0f0; text-align: left; }
.data-table th { background: #f7f8fc; font-weight: 600; color: #555; font-size: .8rem; text-transform: uppercase; }
.data-table tbody tr:hover { background: #f9faff; }
.data-table td.num, .data-table th.num { text-align: right; }
.data-table td.commission { color: #27ae60; font-weight: 600; }
.total-row td { background: #f0f4f8; border-top: 2px solid #d0d8e8; }

.note { background: #f0f4ff; border-left: 3px solid #1D2B53; padding: .75rem 1rem; font-size: .85rem; border-radius: 4px; color: #444; }
</style>
