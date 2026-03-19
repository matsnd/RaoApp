<template>
  <div class="worker-view">
    <div class="worker-header">
      <h1>Pulpit operacyjny</h1>
      <span class="worker-date">{{ today }}</span>
    </div>

    <div class="worker-grid">

      <!-- KOŃCZĄCE SIĘ UMOWY -->
      <section class="worker-card expiring">
        <div class="card-header">
          <span class="card-icon">⏰</span>
          <h2>Kończące się umowy</h2>
          <div class="days-filter">
            <button v-for="d in [7, 14, 30]" :key="d" :class="{ active: expiringDays === d }" @click="setExpiringDays(d)">
              {{ d }}d
            </button>
          </div>
        </div>
        <div class="card-body">
          <div v-if="loadingExpiring" class="loading">Ładowanie…</div>
          <div v-else-if="!expiring.length" class="empty">Brak kończących się umów</div>
          <table v-else class="worker-table">
            <thead>
              <tr>
                <th>Nr umowy</th>
                <th>Kontrahent</th>
                <th>Koniec</th>
                <th>Dni</th>
                <th>Adres</th>
                <th>Kontakt</th>
                <th>Handlowiec</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in expiring" :key="c.id" :class="urgencyClass(c.days_left)">
                <td><router-link :to="`/contracts/${c.id}/edit`">{{ c.number }}</router-link></td>
                <td>{{ c.contractor_name }}</td>
                <td>{{ formatDate(c.date_to) }}</td>
                <td class="days-badge" :class="urgencyClass(c.days_left)">{{ c.days_left }}</td>
                <td>{{ c.delivery_address || '—' }}</td>
                <td>{{ c.contact_person1 || '—' }}{{ c.contact_phone1 ? ', ' + c.contact_phone1 : '' }}</td>
                <td>{{ c.salesperson_name || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>


      <!-- DOSTAWY -->
      <section class="worker-card deliveries">
        <div class="card-header">
          <span class="card-icon">🚚</span>
          <h2>Dostawy</h2>
          <div class="days-filter print-hide">
            <button v-for="d in [1, 2, 3, 7]" :key="d" :class="{ active: deliveryLookahead === d }" @click="setDeliveryLookahead(d)">
              {{ d === 1 ? 'Dziś' : d === 2 ? 'Jutro' : d + 'd' }}
            </button>
          </div>
        </div>
        <div class="card-body">
          <div v-if="loadingDeliveries" class="loading">Ładowanie…</div>
          <div v-else-if="!deliveries.length" class="empty">Brak dostaw w wybranym okresie</div>
          <table v-else class="worker-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Nr umowy</th>
                <th>Kontrahent</th>
                <th>Maszyna</th>
                <th>Adres dostawy</th>
                <th>Kontakt</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in deliveries" :key="d.contract_id + '-' + d.article_name">
                <td>{{ formatDate(d.delivery_date) }}</td>
                <td><router-link :to="`/contracts/${d.contract_id}/edit`">{{ d.contract_number }}</router-link></td>
                <td>{{ d.contractor_name }}</td>
                <td>{{ d.article_name || '—' }}</td>
                <td>{{ d.delivery_address || '—' }}</td>
                <td>{{ d.contact_person1 || '—' }}{{ d.contact_phone1 ? ', ' + d.contact_phone1 : '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- NIEWYDRUKOWANE -->
      <section class="worker-card unprinted">
        <div class="card-header">
          <span class="card-icon">🖨️</span>
          <h2>Niewydrukowane umowy</h2>
          <span class="badge-count print-hide" v-if="unprinted.length">{{ unprinted.length }}</span>
        </div>
        <div class="card-body">
          <div v-if="loadingUnprinted" class="loading">Ładowanie…</div>
          <div v-else-if="!unprinted.length" class="empty">Wszystkie aktywne umowy zostały wydrukowane</div>
          <table v-else class="worker-table">
            <thead>
              <tr>
                <th>Nr umowy</th>
                <th>Kontrahent</th>
                <th>Od</th>
                <th>Do</th>
                <th>Utworzona</th>
                <th>Akcja</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in unprinted" :key="c.id">
                <td><router-link :to="`/contracts/${c.id}/edit`">{{ c.number }}</router-link></td>
                <td>{{ c.contractor_name }}</td>
                <td>{{ formatDate(c.date_from) }}</td>
                <td>{{ formatDate(c.date_to) }}</td>
                <td>{{ c.created_at || '—' }}</td>
                <td>
                  <button class="print-btn" @click="printContract(c.id)" title="Drukuj PDF">⎙</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/composables/useApi'
import { useContractStore } from '@/stores/contracts'

const contractStore = useContractStore()

const today = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('pl-PL', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
})

const expiring = ref([])
const deliveries = ref([])
const unprinted = ref([])

const loadingExpiring = ref(false)
const loadingDeliveries = ref(false)
const loadingUnprinted = ref(false)

const expiringDays = ref(14)
const deliveryLookahead = ref(2)

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pl-PL')
}

function urgencyClass(daysLeft) {
  if (daysLeft <= 2) return 'urgent'
  if (daysLeft <= 5) return 'warning'
  return ''
}

async function loadExpiring() {
  loadingExpiring.value = true
  try {
    const res = await api.get('/stats/expiring-contracts', { params: { days: expiringDays.value } })
    expiring.value = res.data
  } finally {
    loadingExpiring.value = false
  }
}

async function loadDeliveries() {
  loadingDeliveries.value = true
  try {
    const res = await api.get('/stats/deliveries-today', { params: { lookahead: deliveryLookahead.value } })
    deliveries.value = res.data
  } finally {
    loadingDeliveries.value = false
  }
}

async function loadUnprinted() {
  loadingUnprinted.value = true
  try {
    const res = await api.get('/stats/unprinted-contracts')
    unprinted.value = res.data
  } finally {
    loadingUnprinted.value = false
  }
}

function setExpiringDays(d) {
  expiringDays.value = d
  loadExpiring()
}

function setDeliveryLookahead(d) {
  deliveryLookahead.value = d
  loadDeliveries()
}

async function printContract(id) {
  try {
    await contractStore.generateReport(id, 'contract')
  } catch {
    alert('Błąd generowania raportu')
  }
}

onMounted(() => {
  loadExpiring()
  loadDeliveries()
  loadUnprinted()
})
</script>

<style scoped>
.worker-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.worker-header {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-bottom: 24px;
}

.worker-header h1 {
  font-size: 22px;
  font-weight: 600;
  color: #1D2B53;
  margin: 0;
}

.worker-date {
  font-size: 13px;
  color: #888;
}

.btn-print {
  margin-left: auto;
  padding: .35rem .85rem;
  background: #f0f4ff;
  color: #1D2B53;
  border: 1px solid #c0cce8;
  border-radius: 5px;
  cursor: pointer;
  font-size: .82rem;
  font-weight: 600;
}
.btn-print:hover { background: #dde6ff; }

.worker-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.worker-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.card-icon {
  font-size: 16px;
}

.card-header h2 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  flex: 1;
  color: #1D2B53;
}

.badge-count {
  background: #E07800;
  color: #fff;
  font-size: 11px;
  font-weight: bold;
  padding: 2px 7px;
  border-radius: 10px;
}

.days-filter {
  display: flex;
  gap: 4px;
}

.days-filter button {
  padding: 2px 8px;
  font-size: 11px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  color: #555;
}

.days-filter button.active {
  background: #1D2B53;
  color: #fff;
  border-color: #1D2B53;
}

.card-body {
  padding: 12px 16px;
  overflow-x: auto;
}

.loading, .empty {
  font-size: 13px;
  color: #888;
  padding: 12px 0;
  text-align: center;
}

.worker-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.worker-table th {
  text-align: left;
  font-size: 11px;
  color: #888;
  font-weight: normal;
  padding: 4px 6px;
  border-bottom: 1px solid #e0e0e0;
  white-space: nowrap;
}

.worker-table td {
  padding: 5px 6px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}

.worker-table tr:last-child td {
  border-bottom: none;
}

.worker-table a {
  color: #1D2B53;
  font-weight: 600;
  text-decoration: none;
}

.worker-table a:hover {
  text-decoration: underline;
}

.worker-table tr.urgent td {
  background: #fff0f0;
}

.worker-table tr.warning td {
  background: #fffbe6;
}

.days-badge {
  font-weight: bold;
  text-align: center;
}

.days-badge.urgent { color: #c00; }
.days-badge.warning { color: #c07000; }

.overdue-days {
  font-weight: bold;
  color: #c00;
}

.print-btn {
  background: none;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 2px 8px;
  cursor: pointer;
  font-size: 14px;
}

.print-btn:hover {
  background: #f0f0f0;
}

@media (max-width: 1100px) {
  .worker-grid {
    grid-template-columns: 1fr;
  }
}
</style>
