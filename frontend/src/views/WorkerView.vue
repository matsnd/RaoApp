<template>
  <div class="worker-view">
    <div class="worker-header">
      <h1>Pulpit operacyjny</h1>
      <span class="worker-date">{{ today }}</span>
    </div>

    <div class="worker-grid">

      <!-- KOŃCZĄCE SIĘ UMOWY — full width -->
      <section class="worker-card expiring full-width">
        <div class="card-header">
          <span class="card-icon">⏰</span>
          <h2>Kończące się umowy</h2>
          <span class="badge-count" v-if="expiring.length">{{ expiring.length }}</span>
          <div class="days-filter">
            <button v-for="d in [7, 14, 30]" :key="d" :class="{ active: expiringDays === d }" @click="setExpiringDays(d)">
              {{ d }}d
            </button>
          </div>
        </div>
        <div class="card-body">
          <div v-if="loadingExpiring" class="skeleton-list">
            <div class="skel-row" v-for="i in 3" :key="i"></div>
          </div>
          <div v-else-if="!expiring.length" class="empty">
            <span class="empty-ok">✓</span> Brak kończących się umów w ciągu {{ expiringDays }} dni
          </div>
          <div v-else class="exp-grid">
            <div
              v-for="c in expiring"
              :key="c.id"
              class="exp-card"
              :class="urgencyClass(c.days_left)"
              @click="$router.push(`/contracts/${c.id}/edit`)"
            >
              <div class="exp-bar"></div>
              <div class="exp-content">
                <div class="exp-top">
                  <span class="exp-number">{{ c.number }}</span>
                  <span class="exp-days-badge" :class="urgencyClass(c.days_left)">
                    {{ c.days_left === 0 ? 'Dziś!' : c.days_left + ' dni' }}
                  </span>
                </div>
                <div class="exp-contractor">{{ c.contractor_name }}</div>
                <div class="exp-details">
                  <span v-if="c.delivery_address" class="exp-addr">📍 {{ c.delivery_address }}</span>
                  <span class="exp-date">do {{ formatDate(c.date_to) }}</span>
                  <span v-if="c.salesperson_name" class="exp-salesperson">· {{ c.salesperson_name }}</span>
                </div>
                <div class="exp-contact" v-if="c.contact_person1 || c.contact_phone1">
                  <span v-if="c.contact_person1" class="contact-name">{{ c.contact_person1 }}</span>
                  <a v-if="c.contact_phone1" :href="`tel:${c.contact_phone1}`" class="contact-phone" @click.stop>📞 {{ c.contact_phone1 }}</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- DOSTAWY -->
      <section class="worker-card deliveries">
        <div class="card-header">
          <span class="card-icon">🚚</span>
          <h2>Dostawy</h2>
          <span class="badge-count badge-blue" v-if="deliveries.length">{{ deliveries.length }}</span>
          <div class="days-filter print-hide">
            <button v-for="d in [1, 2, 3, 7]" :key="d" :class="{ active: deliveryLookahead === d }" @click="setDeliveryLookahead(d)">
              {{ d === 1 ? 'Dziś' : d === 2 ? 'Jutro' : d + 'd' }}
            </button>
          </div>
        </div>
        <div class="card-body no-pad">
          <div v-if="loadingDeliveries" class="skeleton-list padded">
            <div class="skel-row" v-for="i in 3" :key="i"></div>
          </div>
          <div v-else-if="!deliveries.length" class="empty">
            <span class="empty-ok">✓</span> Brak dostaw w wybranym okresie
          </div>
          <div v-else class="delivery-list">
            <div v-for="d in deliveries" :key="d.contract_id + '-' + d.article_name" class="delivery-row">
              <div class="del-chip" :class="isToday(d.delivery_date) ? 'chip-today' : 'chip-future'">
                {{ isToday(d.delivery_date) ? 'Dziś' : isTomorrow(d.delivery_date) ? 'Jutro' : formatDate(d.delivery_date) }}
              </div>
              <div class="del-body">
                <div class="del-top">
                  <router-link :to="`/contracts/${d.contract_id}/edit`" class="del-number">{{ d.contract_number }}</router-link>
                  <span class="del-machine">{{ d.article_name || '—' }}</span>
                </div>
                <div class="del-contractor">{{ d.contractor_name }}</div>
                <div class="del-details">
                  <span v-if="d.delivery_address" class="del-addr">📍 {{ d.delivery_address }}</span>
                </div>
                <div class="del-contact" v-if="d.contact_person1 || d.contact_phone1">
                  <span v-if="d.contact_person1" class="contact-name">{{ d.contact_person1 }}</span>
                  <a v-if="d.contact_phone1" :href="`tel:${d.contact_phone1}`" class="contact-phone">📞 {{ d.contact_phone1 }}</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- NIEWYDRUKOWANE -->
      <section class="worker-card unprinted">
        <div class="card-header">
          <span class="card-icon">🖨️</span>
          <h2>Niewydrukowane umowy</h2>
          <span class="badge-count badge-red" v-if="unprinted.length">{{ unprinted.length }}</span>
        </div>
        <div class="card-body no-pad">
          <div v-if="loadingUnprinted" class="skeleton-list padded">
            <div class="skel-row" v-for="i in 2" :key="i"></div>
          </div>
          <div v-else-if="!unprinted.length" class="empty">
            <span class="empty-ok">✓</span> Wszystkie umowy wydrukowane
          </div>
          <div v-else class="unprinted-list">
            <div v-for="c in unprinted" :key="c.id" class="unp-row">
              <div class="unp-info" @click="$router.push(`/contracts/${c.id}/edit`)">
                <span class="unp-number">{{ c.number }}</span>
                <span class="unp-contractor">{{ c.contractor_name }}</span>
                <span class="unp-dates">{{ formatDate(c.date_from) }} – {{ formatDate(c.date_to) }}</span>
              </div>
              <button class="print-btn" @click="printContract(c.id)" title="Drukuj PDF">⎙ Drukuj</button>
            </div>
          </div>
        </div>
      </section>

      <!-- NIEAKTUALNY WYDRUK -->
      <section class="worker-card stale-print">
        <div class="card-header">
          <span class="card-icon">🔄</span>
          <h2>Nieaktualny wydruk</h2>
          <span class="badge-count badge-orange" v-if="stale.length">{{ stale.length }}</span>
        </div>
        <div class="card-body no-pad">
          <div v-if="loadingStale" class="skeleton-list padded">
            <div class="skel-row" v-for="i in 2" :key="i"></div>
          </div>
          <div v-else-if="!stale.length" class="empty">
            <span class="empty-ok">✓</span> Wszystkie wydruki aktualne
          </div>
          <div v-else class="unprinted-list">
            <div v-for="c in stale" :key="c.id" class="unp-row">
              <div class="unp-info" @click="$router.push(`/contracts/${c.id}/edit`)">
                <span class="unp-number">{{ c.number }}</span>
                <span class="unp-contractor">{{ c.contractor_name }}</span>
                <span class="unp-dates stale-meta" :title="'Wydruk: ' + c.print_date">⚠️ Zmiana: {{ c.updated_at }}</span>
              </div>
              <button class="print-btn" @click="printContract(c.id)" title="Dodrukuj PDF">⎙ Dodrukuj</button>
            </div>
          </div>
        </div>
      </section>

      <!-- PRZETERMINOWANE UMOWY -->
      <section class="worker-card overdue">
        <div class="card-header">
          <span class="card-icon">⚠️</span>
          <h2>Przeterminowane umowy</h2>
          <span class="badge-count badge-red" v-if="overdue.length">{{ overdue.length }}</span>
        </div>
        <div class="card-body no-pad">
          <div v-if="loadingOverdue" class="skeleton-list padded">
            <div class="skel-row" v-for="i in 2" :key="i"></div>
          </div>
          <div v-else-if="!overdue.length" class="empty">
            <span class="empty-ok">✓</span> Brak przeterminowanych umów
          </div>
          <div v-else class="unprinted-list">
            <div v-for="c in overdue" :key="c.id" class="unp-row">
              <div class="unp-info" @click="$router.push(`/contracts/${c.id}/edit`)">
                <span class="unp-number">{{ c.number }}</span>
                <span class="unp-contractor">{{ c.contractor_name }}</span>
                <span class="unp-dates overdue-meta">⚠️ {{ c.days_overdue }} dni po terminie (do {{ formatDate(c.date_to) }})</span>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/composables/useApi'
import { useContractStore } from '@/stores/contracts'
import { formatDate } from '@/utils/format'
import { useToastStore } from '@/stores/toast'

const contractStore = useContractStore()
const toastStore = useToastStore()

const today = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('pl-PL', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
})

const expiring = ref([])
const deliveries = ref([])
const unprinted = ref([])
const stale = ref([])
const overdue = ref([])

const loadingExpiring = ref(false)
const loadingDeliveries = ref(false)
const loadingUnprinted = ref(false)
const loadingStale = ref(false)
const loadingOverdue = ref(false)

const expiringDays = ref(14)
const deliveryLookahead = ref(2)

const todayStr = new Date().toISOString().slice(0, 10)
const tomorrowStr = new Date(Date.now() + 86400000).toISOString().slice(0, 10)

function isToday(d) { return d && String(d).slice(0, 10) === todayStr }
function isTomorrow(d) { return d && String(d).slice(0, 10) === tomorrowStr }

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

async function loadStale() {
  loadingStale.value = true
  try {
    const res = await api.get('/stats/stale-print-contracts')
    stale.value = res.data
  } finally {
    loadingStale.value = false
  }
}

async function loadOverdue() {
  loadingOverdue.value = true
  try {
    const res = await api.get('/stats/overdue-contracts')
    overdue.value = res.data
  } finally {
    loadingOverdue.value = false
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
    toastStore.error('Błąd generowania raportu')
  }
}

onMounted(() => {
  loadExpiring()
  loadDeliveries()
  loadUnprinted()
  loadStale()
  loadOverdue()
})
</script>

<style scoped>
.worker-view {
  padding: 20px 24px;
  width: 100%;
  margin: 0 auto;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
  background: var(--color-bg-light);
}

.worker-header {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-bottom: 20px;
}
.worker-header h1 {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0;
}
.worker-date {
  font-size: 13px;
  color: #5A6B7E;
  text-transform: capitalize;
}

/* ── GRID ── */
.worker-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.full-width {
  grid-column: 1 / -1;
}

/* ── CARD ── */
.worker-card {
  background: #fff;
  border-radius: var(--border-radius);
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #EDF2F7;
}
.card-icon { font-size: 16px; }
.card-header h2 {
  font-size: 13px;
  font-weight: 700;
  margin: 0;
  flex: 1;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: .04em;
}
.badge-count {
  background: #F59E0B;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  min-width: 20px;
  text-align: center;
}
.badge-blue   { background: #3B82F6; }
.badge-red    { background: #EF4444; }
.badge-orange { background: #F59E0B; }

.days-filter {
  display: flex;
  gap: 4px;
}
.days-filter button {
  padding: 3px 9px;
  font-size: 13px;
  border: 1px solid #CBD5E0;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  color: #4A5568;
  font-family: inherit;
  transition: all 120ms;
}
.days-filter button:hover { background: #EDF2F7; }
.days-filter button.active { background: var(--color-primary); color: var(--color-text-on-primary); border-color: var(--color-primary); }

.card-body { padding: 12px 16px; }
.card-body.no-pad { padding: 0; }

/* ── LOADING SKELETON ── */
.skeleton-list { padding: 12px 16px; display: flex; flex-direction: column; gap: 8px; }
.skeleton-list.padded { padding: 12px 16px; }
.skel-row {
  height: 52px;
  background: #EDF2F7;
  border-radius: 6px;
  animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

/* ── EMPTY ── */
.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  color: #A0AEC0;
  padding: 20px;
}
.empty-ok { color: #10B981; font-size: 16px; }

/* ── EXPIRING GRID ── */
.exp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
}
.exp-card {
  display: flex;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 150ms, border-color 150ms;
}
.exp-card:hover { box-shadow: 0 3px 10px rgba(0,0,0,.1); border-color: #C7D2F0; }
.exp-bar { width: 4px; flex-shrink: 0; }
.exp-card.urgent .exp-bar   { background: #EF4444; }
.exp-card.warning .exp-bar  { background: #F59E0B; }
.exp-card:not(.urgent):not(.warning) .exp-bar { background: #FCD34D; }

.exp-content { padding: 10px 12px; flex: 1; min-width: 0; }
.exp-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}
.exp-number { font-size: 13px; font-weight: 700; color: #0F234E; }
.exp-days-badge {
  font-size: 13px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: var(--border-radius);
  white-space: nowrap;
}
.exp-days-badge.urgent  { background: #FEE2E2; color: #991B1B; }
.exp-days-badge.warning { background: #FEF3C7; color: #92400E; }
.exp-days-badge:not(.urgent):not(.warning) { background: #FFF8DC; color: #78350F; }

.exp-contractor { font-size: 13px; font-weight: 600; color: #2D3748; margin-bottom: 4px; }
.exp-details {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 13px;
  color: #5A6B7E;
  margin-bottom: 4px;
}
.exp-addr { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.exp-contact { display: flex; flex-wrap: wrap; gap: 10px; font-size: 13px; }
.contact-name { color: #4A5568; }
.contact-phone {
  color: #3B82F6;
  text-decoration: none;
  font-weight: 600;
}
.contact-phone:hover { text-decoration: underline; }

/* ── DELIVERIES ── */
.delivery-list { }
.delivery-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 11px 16px;
  border-bottom: 1px solid #F0F4F8;
}
.delivery-row:last-child { border-bottom: none; }
.del-chip {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: .04em;
  white-space: nowrap;
}
.chip-today   { background: #DBEAFE; color: #1E40AF; }
.chip-future  { background: #E0E7FF; color: #3730A3; }
.del-body { flex: 1; min-width: 0; }
.del-top { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
.del-number {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  text-decoration: none;
}
.del-number:hover { text-decoration: underline; }
.del-machine {
  font-size: 12px;
  font-weight: 600;
  color: #2D3748;
}
.del-contractor { font-size: 13px; color: #5A6B7E; margin-bottom: 2px; }
.del-details { font-size: 13px; color: #5A6B7E; margin-bottom: 2px; }
.del-addr { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-contact { font-size: 13px; display: flex; gap: 10px; }

/* ── UNPRINTED ── */
.unprinted-list { }
.unp-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid #F0F4F8;
}
.unp-row:last-child { border-bottom: none; }
.unp-info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}
.unp-number {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  display: block;
  margin-bottom: 2px;
}
.unp-contractor {
  font-size: 12px;
  color: #2D3748;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}
.unp-dates {
  font-size: 13px;
  color: #A0AEC0;
  display: block;
}
.print-btn {
  flex-shrink: 0;
  background: #F0F4FF;
  border: 1px solid #C7D2F0;
  border-radius: 5px;
  padding: 5px 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  font-family: inherit;
  white-space: nowrap;
  transition: background 120ms;
}
.print-btn:hover { background: #DDE6FF; }
.stale-meta { color: #C05621; }
.overdue-meta { color: #DC2626; font-weight: 600; }

@media (max-width: 900px) {
  .worker-grid { grid-template-columns: 1fr; }
  .full-width { grid-column: 1; }
  .exp-grid { grid-template-columns: 1fr; }
}
</style>
