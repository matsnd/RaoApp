<template>
  <div class="reports-dashboard">
    <!-- DATE PILLS -->
    <div class="date-pills">
      <button
        v-for="p in presets"
        :key="p.key"
        :class="['pill', { active: activePreset === p.key }]"
        @click="selectPreset(p.key)"
      >{{ p.label }}</button>
      <div class="pill-custom" v-if="activePreset === 'custom'">
        <input type="date" v-model="customFrom" class="pill-date" />
        <span>—</span>
        <input type="date" v-model="customTo" class="pill-date" />
        <button class="pill pill-go" @click="loadAll()">Filtruj</button>
      </div>
      <button :class="['pill', { active: activePreset === 'custom' }]" @click="activePreset = 'custom'">📅 Własny</button>
      <button class="btn-print print-hide" @click="printPage">🖨 Drukuj</button>
    </div>

    <!-- LOADING -->
    <div v-if="statsStore.loading" class="reports-loading">
      <div class="spinner"></div>
      <span>Ładowanie statystyk...</span>
    </div>

    <template v-else>
      <!-- KPI CARDS -->
      <div class="kpi-row" v-if="statsStore.summary">
        <div class="kpi-card">
          <div class="kpi-value kpi-accent">{{ statsStore.summary.total_rented }}</div>
          <div class="kpi-label">Wynajętych teraz</div>
          <div class="kpi-sub">z {{ statsStore.summary.total_machines }} maszyn</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value" :class="utilClass">{{ statsStore.summary.utilization_pct }}%</div>
          <div class="kpi-label">Wykorzystanie floty</div>
          <div class="kpi-sub">aktywne maszyny u klientów</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ formatMoney(statsStore.summary.period_revenue) }}</div>
          <div class="kpi-label">Przychód w okresie</div>
          <div class="kpi-sub">{{ statsStore.summary.contracts_in_period }} umów</div>
        </div>
        <div class="kpi-card kpi-highlight" v-if="statsStore.summary.top_machine_name">
          <div class="kpi-value kpi-small">{{ statsStore.summary.top_machine_name }}</div>
          <div class="kpi-label">Top maszyna</div>
          <div class="kpi-sub">{{ formatMoney(statsStore.summary.top_machine_revenue) }}</div>
        </div>
        <div class="kpi-card" v-else>
          <div class="kpi-value kpi-muted">—</div>
          <div class="kpi-label">Top maszyna</div>
          <div class="kpi-sub">brak danych</div>
        </div>
      </div>

      <!-- CHARTS ROW -->
      <div class="charts-row">
        <div class="chart-panel chart-wide">
          <div class="chart-title">🏗️ TOP 10 Maszyn wg przychodu</div>
          <div class="chart-wrap" style="height:280px;">
            <canvas ref="barCanvas"></canvas>
          </div>
          <div v-if="!statsStore.topMachines.length" class="chart-empty">Brak danych w wybranym okresie</div>
        </div>
        <div class="chart-panel chart-narrow">
          <div class="chart-title">📊 Wykorzystanie floty</div>
          <div class="chart-wrap" style="height:240px;">
            <canvas ref="donutCanvas"></canvas>
          </div>
        </div>
      </div>

      <!-- BOTTOM TABLES -->
      <div class="tables-row">
        <div class="table-panel">
          <div class="table-title">💰 Usługi dodatkowe</div>
          <table class="stats-table" v-if="statsStore.additionalFees?.breakdown?.length">
            <thead>
              <tr>
                <th>Usługa</th>
                <th style="text-align:right;">Przychód</th>
                <th style="text-align:right;">Umów</th>
                <th style="width:120px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in statsStore.additionalFees.breakdown" :key="s.article_id">
                <td>{{ s.service_name }}</td>
                <td style="text-align:right;font-weight:600;">{{ formatMoney(s.total_revenue) }}</td>
                <td style="text-align:right;">{{ s.times_billed }}</td>
                <td>
                  <div class="bar-bg">
                    <div class="bar-fill" :style="{ width: feeBarWidth(s.total_revenue) + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td style="font-weight:700;">Razem</td>
                <td style="text-align:right;font-weight:700;">{{ formatMoney(statsStore.additionalFees.total_services_revenue) }}</td>
                <td></td>
                <td></td>
              </tr>
            </tfoot>
          </table>
          <div v-else class="chart-empty">Brak usług w wybranym okresie</div>
        </div>

        <div class="table-panel">
          <div class="table-title">📍 Lokalizacje — ranking</div>
          <table class="stats-table" v-if="statsStore.locations.length">
            <thead>
              <tr>
                <th>#</th>
                <th>Miasto</th>
                <th style="text-align:right;">Umów</th>
                <th style="text-align:right;">Przychód</th>
                <th style="width:100px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(loc, i) in statsStore.locations" :key="loc.city">
                <td style="color:#718096;">{{ i + 1 }}</td>
                <td style="font-weight:600;">{{ loc.city }}</td>
                <td style="text-align:right;">{{ loc.rentals_count }}</td>
                <td style="text-align:right;">{{ formatMoney(loc.total_revenue) }}</td>
                <td>
                  <div class="bar-bg">
                    <div class="bar-fill bar-fill-blue" :style="{ width: locBarWidth(loc.rentals_count) + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="chart-empty">Brak danych lokalizacji</div>
        </div>
      </div>

      <!-- CURRENTLY RENTED LIST -->
      <div class="table-panel full-width" v-if="statsStore.currentlyRented?.items?.length">
        <div class="table-title">🟢 Maszyny aktualnie wynajęte ({{ statsStore.currentlyRented.total_rented }})</div>
        <div class="rented-scroll">
          <table class="stats-table">
            <thead>
              <tr>
                <th>Maszyna</th>
                <th>Nr wewnętrzny</th>
                <th>Umowa</th>
                <th>Kontrahent</th>
                <th>Planowany zwrot</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in statsStore.currentlyRented.items" :key="item.article_id + item.contract_number">
                <td>{{ item.name }}</td>
                <td>{{ item.internal_number || '—' }}</td>
                <td style="font-weight:600;">{{ item.contract_number }}</td>
                <td>{{ item.contractor_name || '—' }}</td>
                <td>{{ item.return_date ? new Date(item.return_date).toLocaleDateString('pl-PL') : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useStatsStore } from '@/stores/stats'

Chart.register(...registerables)

const statsStore = useStatsStore()

const barCanvas = ref(null)
const donutCanvas = ref(null)
let barChart = null
let donutChart = null

const presets = [
  { key: 'month', label: 'Ten miesiąc' },
  { key: 'quarter', label: 'Ten kwartał' },
  { key: 'year', label: 'Ten rok' },
  { key: 'all', label: 'Wszystko' },
]

const activePreset = ref('year')
const customFrom = ref('')
const customTo = ref('')

function getDateRange(preset) {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  if (preset === 'month') return [new Date(y, m, 1), now]
  if (preset === 'quarter') {
    const qStart = Math.floor(m / 3) * 3
    return [new Date(y, qStart, 1), now]
  }
  if (preset === 'year') return [new Date(y, 0, 1), now]
  if (preset === 'all') return [new Date(2000, 0, 1), new Date(2099, 11, 31)]
  return [null, null]
}

function fmt(d) {
  if (!d) return null
  return d.toISOString().slice(0, 10)
}

async function loadAll() {
  let df, dt
  if (activePreset.value === 'custom') {
    df = customFrom.value || null
    dt = customTo.value || null
  } else {
    const [from, to] = getDateRange(activePreset.value)
    df = fmt(from)
    dt = fmt(to)
  }
  await statsStore.fetchAll(df, dt)
  await nextTick()
  renderCharts()
}

function selectPreset(key) {
  activePreset.value = key
  if (key !== 'custom') loadAll()
}

function printPage() { window.print() }

const utilClass = computed(() => {
  if (!statsStore.summary) return ''
  const v = statsStore.summary.utilization_pct
  if (v >= 70) return 'kpi-success'
  if (v >= 40) return 'kpi-warning'
  return 'kpi-danger'
})

const maxFeeRevenue = computed(() => {
  if (!statsStore.additionalFees?.breakdown?.length) return 1
  return Math.max(...statsStore.additionalFees.breakdown.map(s => Number(s.total_revenue)))
})

const maxLocCount = computed(() => {
  if (!statsStore.locations.length) return 1
  return Math.max(...statsStore.locations.map(l => l.rentals_count))
})

function feeBarWidth(val) {
  return Math.round(Number(val) / maxFeeRevenue.value * 100)
}

function locBarWidth(val) {
  return Math.round(val / maxLocCount.value * 100)
}

function formatMoney(v) {
  if (!v && v !== 0) return '—'
  return Number(v).toLocaleString('pl-PL', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' zł'
}

function renderCharts() {
  renderBarChart()
  renderDonutChart()
}

function renderBarChart() {
  if (barChart) barChart.destroy()
  if (!barCanvas.value || !statsStore.topMachines.length) return

  const labels = statsStore.topMachines.map(m => {
    const num = m.internal_number ? `[${m.internal_number}] ` : ''
    const name = m.name.length > 25 ? m.name.slice(0, 25) + '...' : m.name
    return num + name
  })
  const data = statsStore.topMachines.map(m => Number(m.revenue))

  barChart = new Chart(barCanvas.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Przychód (zł)',
        data,
        backgroundColor: 'rgba(15, 35, 78, 0.75)',
        hoverBackgroundColor: 'rgba(15, 35, 78, 0.95)',
        borderRadius: 4,
        barThickness: 22,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const m = statsStore.topMachines[ctx.dataIndex]
              return `${formatMoney(m.revenue)} · ${m.rented_days} dni · ${m.contracts_count} umów`
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            callback: (v) => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v,
            font: { size: 11 },
          },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        y: {
          ticks: { font: { size: 11 } },
          grid: { display: false },
        },
      },
    },
  })
}

function renderDonutChart() {
  if (donutChart) donutChart.destroy()
  if (!donutCanvas.value || !statsStore.currentlyRented) return

  const rented = statsStore.currentlyRented.total_rented
  const free = statsStore.currentlyRented.total_machines - rented

  donutChart = new Chart(donutCanvas.value.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Wynajęte', 'Dostępne'],
      datasets: [{
        data: [rented, Math.max(free, 0)],
        backgroundColor: ['#0F234E', '#E2E8F0'],
        hoverBackgroundColor: ['#1A3266', '#CBD5E0'],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 12 }, padding: 16 },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.raw} maszyn`,
          },
        },
      },
    },
    plugins: [{
      id: 'centerText',
      afterDraw(chart) {
        const { ctx, chartArea } = chart
        const cx = (chartArea.left + chartArea.right) / 2
        const cy = (chartArea.top + chartArea.bottom) / 2
        ctx.save()
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.font = 'bold 28px Inter, sans-serif'
        ctx.fillStyle = '#0F234E'
        ctx.fillText(rented, cx, cy - 8)
        ctx.font = '11px Inter, sans-serif'
        ctx.fillStyle = '#718096'
        ctx.fillText('wynajętych', cx, cy + 14)
        ctx.restore()
      },
    }],
  })
}

onMounted(() => loadAll())

onBeforeUnmount(() => {
  if (barChart) barChart.destroy()
  if (donutChart) donutChart.destroy()
})
</script>

<style scoped>
.reports-dashboard { padding: 0; }

.date-pills {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.pill {
  padding: 7px 16px;
  border-radius: 99px;
  border: 1px solid #E2E8F0;
  background: #fff;
  color: #4A5568;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms;
  font-family: inherit;
}
.pill:hover { border-color: #0F234E; color: #0F234E; }
.pill.active { background: #0F234E; color: #fff; border-color: #0F234E; }
.pill-custom { display: flex; align-items: center; gap: 6px; }
.pill-date {
  padding: 5px 10px;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  font-size: 12px;
  font-family: inherit;
}
.pill-go { padding: 6px 14px; font-size: 12px; }

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.kpi-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 18px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  text-align: center;
  transition: box-shadow 250ms;
}
.kpi-card:hover { box-shadow: 0 6px 20px rgba(15,35,78,0.1); }
.kpi-value {
  font-size: 32px;
  font-weight: 800;
  color: #0F234E;
  line-height: 1.1;
}
.kpi-value.kpi-small { font-size: 16px; font-weight: 700; }
.kpi-value.kpi-muted { color: #CBD5E0; }
.kpi-accent { color: #0F234E; }
.kpi-success { color: #38A169; }
.kpi-warning { color: #D69E2E; }
.kpi-danger { color: #E53E3E; }
.kpi-label {
  font-size: 12px;
  font-weight: 600;
  color: #718096;
  margin-top: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.kpi-sub {
  font-size: 11px;
  color: #A0AEC0;
  margin-top: 2px;
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.chart-panel {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  position: relative;
}
.chart-wrap {
  position: relative;
  width: 100%;
}
.chart-title {
  font-size: 14px;
  font-weight: 700;
  color: #0F234E;
  margin-bottom: 12px;
}
.chart-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #A0AEC0;
  font-size: 13px;
}

.tables-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.table-panel {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.table-panel.full-width { grid-column: 1 / -1; }
.table-title {
  font-size: 14px;
  font-weight: 700;
  color: #0F234E;
  margin-bottom: 10px;
}
.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.stats-table th {
  text-align: left;
  padding: 6px 8px;
  font-size: 11px;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  border-bottom: 2px solid #E2E8F0;
}
.stats-table td {
  padding: 7px 8px;
  border-bottom: 1px solid #F0F0F0;
  color: #4A5568;
}
.stats-table tfoot td {
  border-top: 2px solid #E2E8F0;
  border-bottom: none;
  padding-top: 10px;
}
.stats-table tbody tr:hover { background: #F7FAFC; }

.bar-bg {
  height: 6px;
  background: #EDF2F7;
  border-radius: 3px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: #0F234E;
  border-radius: 3px;
  transition: width 600ms ease;
}
.bar-fill-blue {
  background: #3182CE;
}

.rented-scroll {
  max-height: 300px;
  overflow: auto;
}

.reports-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 0;
  color: #718096;
  font-size: 14px;
}
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #E2E8F0;
  border-top-color: #0F234E;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.kpi-highlight {
  background: linear-gradient(135deg, #0F234E 0%, #1A3266 100%);
}
.kpi-highlight .kpi-value { color: #fff; }
.kpi-highlight .kpi-label { color: rgba(255,255,255,0.7); }
.kpi-highlight .kpi-sub { color: rgba(255,255,255,0.5); }

@media (max-width: 1100px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
  .tables-row { grid-template-columns: 1fr; }
}
</style>
