<template>
  <div class="home-view">
    <!-- HEADER -->
    <div class="home-header">
      <div class="home-greeting">
        <h1 class="greeting-title">{{ greetingText }}</h1>
        <span class="greeting-date">{{ todayLabel }}</span>
      </div>
      <div class="quick-actions">
        <button class="qa-btn qa-primary" @click="$router.push('/contracts/new')">
          <span class="qa-icon">+</span> Nowa umowa
        </button>
        <button class="qa-btn qa-secondary" @click="$router.push('/contractors/new')">
          <span class="qa-icon">+</span> Nowy kontrahent
        </button>
        <button class="qa-btn qa-ghost" @click="$router.push('/dashboard/contracts')">
          Wszystkie umowy →
        </button>
      </div>
    </div>

    <!-- KPI STRIP -->
    <div class="kpi-strip">
      <div class="kpi-card" :class="kpiFleetClass">
        <div class="kpi-icon">🔧</div>
        <div class="kpi-body">
          <div class="kpi-value" v-if="!loading.fleet">
            {{ fleet.total_rented }}<span class="kpi-denom">/{{ fleet.total_machines }}</span>
          </div>
          <div class="kpi-value skeleton" v-else>&nbsp;</div>
          <div class="kpi-label">Maszyny w terenie</div>
          <div class="kpi-sub" v-if="!loading.fleet">{{ fleet.utilization_pct }}% wykorzystania</div>
        </div>
      </div>

      <div class="kpi-card" :class="expiring.length >= 3 ? 'kpi-danger' : expiring.length >= 1 ? 'kpi-warn' : 'kpi-ok'">
        <div class="kpi-icon">⏰</div>
        <div class="kpi-body">
          <div class="kpi-value" v-if="!loading.expiring">{{ expiring.length }}</div>
          <div class="kpi-value skeleton" v-else>&nbsp;</div>
          <div class="kpi-label">Kończy się w 14 dni</div>
          <div class="kpi-sub" v-if="!loading.expiring && expiring.length">
            Najwcześniej za {{ minDaysLeft }}d
          </div>
          <div class="kpi-sub" v-else-if="!loading.expiring">Brak pilnych</div>
        </div>
      </div>

      <div class="kpi-card" :class="deliveries.length ? 'kpi-info' : 'kpi-ok'">
        <div class="kpi-icon">📦</div>
        <div class="kpi-body">
          <div class="kpi-value" v-if="!loading.deliveries">{{ deliveries.length }}</div>
          <div class="kpi-value skeleton" v-else>&nbsp;</div>
          <div class="kpi-label">Dostawy dziś/jutro</div>
          <div class="kpi-sub" v-if="!loading.deliveries && deliveries.length">{{ todayDeliveriesCount }} dziś</div>
          <div class="kpi-sub" v-else-if="!loading.deliveries">Brak dostaw</div>
        </div>
      </div>

      <div class="kpi-card" :class="unprinted.length >= 5 ? 'kpi-danger' : unprinted.length >= 1 ? 'kpi-warn' : 'kpi-ok'">
        <div class="kpi-icon">🖨</div>
        <div class="kpi-body">
          <div class="kpi-value" v-if="!loading.unprinted">{{ unprinted.length }}</div>
          <div class="kpi-value skeleton" v-else>&nbsp;</div>
          <div class="kpi-label">Niewydrukowane</div>
          <div class="kpi-sub" v-if="!loading.unprinted && unprinted.length">Oczekują na wydruk</div>
          <div class="kpi-sub" v-else-if="!loading.unprinted">Wszystko OK</div>
        </div>
      </div>

      <div class="kpi-card" :class="stale.length >= 3 ? 'kpi-danger' : stale.length >= 1 ? 'kpi-warn' : 'kpi-ok'">
        <div class="kpi-icon">🔄</div>
        <div class="kpi-body">
          <div class="kpi-value" v-if="!loading.stale">{{ stale.length }}</div>
          <div class="kpi-value skeleton" v-else>&nbsp;</div>
          <div class="kpi-label">Nieaktualny wydruk</div>
          <div class="kpi-sub" v-if="!loading.stale && stale.length">Wymaga dodruku</div>
          <div class="kpi-sub" v-else-if="!loading.stale">Wszystko OK</div>
        </div>
      </div>
    </div>

    <!-- QUICK NAV STRIP -->
    <div class="quick-nav-strip">
      <div class="nav-grid-full">
        <button class="nav-tile" @click="$router.push('/dashboard/contracts')">
          <span class="nav-tile-icon">📄</span>
          <span>Umowy</span>
        </button>
        <button class="nav-tile" @click="$router.push('/dashboard/contractors')">
          <span class="nav-tile-icon">👤</span>
          <span>Kontrahenci</span>
        </button>
        <button class="nav-tile" @click="$router.push('/dashboard/articles')">
          <span class="nav-tile-icon">🔧</span>
          <span>Artykuły</span>
        </button>
        <button class="nav-tile" @click="$router.push('/worker')">
          <span class="nav-tile-icon">🖥</span>
          <span>Pulpit</span>
        </button>
        <button class="nav-tile" @click="$router.push('/dashboard/reports')">
          <span class="nav-tile-icon">📊</span>
          <span>Raporty</span>
        </button>
        <button class="nav-tile" @click="$router.push('/commissions')">
          <span class="nav-tile-icon">💰</span>
          <span>Prowizje</span>
        </button>
      </div>
    </div>

    <!-- MAIN CONTENT GRID -->
    <div class="home-grid">
      <!-- LEFT COLUMN -->
      <div class="home-left">
        <!-- LEFT: Expiring contracts -->
        <div class="home-panel panel-expiring">
          <div class="panel-header">
            <span class="panel-icon">⏰</span>
            <h2>Kończące się umowy</h2>
            <span class="panel-badge" v-if="expiring.length">{{ expiring.length }}</span>
          </div>

          <div v-if="loading.expiring" class="panel-loading">
            <div class="skel-row" v-for="i in 4" :key="i"></div>
          </div>

          <div v-else-if="!expiring.length" class="panel-empty">
            <span class="empty-icon">📋</span>
            <p>Brak umów kończących się w ciągu 14 dni</p>
          </div>

          <div v-else class="expiring-list">
            <div
              v-for="c in expiring"
              :key="c.id"
              class="exp-row"
              :class="urgencyClass(c.days_left)"
              @click="$router.push(`/contracts/${c.id}/edit`)"
            >
              <div class="exp-urgency-bar"></div>
              <div class="exp-body">
                <div class="exp-top">
                  <span class="exp-number">{{ c.number }}</span>
                  <span class="exp-days" :class="urgencyClass(c.days_left)">
                    {{ c.days_left === 0 ? 'Dziś!' : `${c.days_left}d` }}
                  </span>
                </div>
                <div class="exp-contractor">{{ c.contractor_name }}</div>
                <div class="exp-meta">
                  <span v-if="c.delivery_address" class="exp-addr">📍 {{ c.delivery_address }}</span>
                  <span class="exp-date">do {{ fmtDate(c.date_to) }}</span>
                </div>
                <div class="exp-contact" v-if="c.contact_person1 || c.contact_phone1">
                  <span v-if="c.contact_person1">{{ c.contact_person1 }}</span>
                  <a v-if="c.contact_phone1" :href="`tel:${c.contact_phone1}`" class="phone-link" @click.stop>
                    📞 {{ c.contact_phone1 }}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Overdue contracts -->
        <div class="home-panel panel-overdue">
          <div class="panel-header">
            <span class="panel-icon">🔴</span>
            <h2>Przeterminowane umowy</h2>
            <span class="panel-badge panel-badge-red" v-if="overdue.length">{{ overdue.length }}</span>
          </div>

          <div v-if="loading.overdue" class="panel-loading">
            <div class="skel-row" v-for="i in 4" :key="i"></div>
          </div>

          <div v-else-if="!overdue.length" class="panel-empty">
            <span class="empty-icon">✅</span>
            <p>Brak przeterminowanych umów</p>
          </div>

          <div v-else class="expiring-list">
            <div
              v-for="c in overdue"
              :key="c.id"
              class="exp-row overdue-row"
              @click="$router.push(`/contracts/${c.id}/edit`)"
            >
              <div class="exp-urgency-bar overdue-bar"></div>
              <div class="exp-body">
                <div class="exp-top">
                  <span class="exp-number">{{ c.number }}</span>
                  <span class="exp-days overdue-days">
                    {{ daysOverdue(c) }} dni
                  </span>
                </div>
                <div class="exp-contractor">{{ c.contractor_name }}</div>
                <div class="exp-meta">
                  <span v-if="c.delivery_address" class="exp-addr">📍 {{ c.delivery_address }}</span>
                  <span class="exp-date">zakończono {{ fmtDate(c.date_to) }}</span>
                </div>
                <div class="exp-contact" v-if="c.contact_person1 || c.contact_phone1">
                  <span v-if="c.contact_person1">{{ c.contact_person1 }}</span>
                  <a v-if="c.contact_phone1" :href="`tel:${c.contact_phone1}`" class="phone-link" @click.stop>
                    📞 {{ c.contact_phone1 }}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="home-right">

        <!-- Deliveries -->
        <div class="home-panel panel-deliveries">
          <div class="panel-header">
            <span class="panel-icon">📦</span>
            <h2>Dostawy</h2>
            <span class="panel-badge panel-badge-blue" v-if="deliveries.length">{{ deliveries.length }}</span>
          </div>

          <div v-if="loading.deliveries" class="panel-loading">
            <div class="skel-row" v-for="i in 2" :key="i"></div>
          </div>

          <div v-else-if="!deliveries.length" class="panel-empty panel-empty-sm">
            <span class="empty-icon">🚚</span>
            <p>Brak dostaw na dziś i jutro</p>
          </div>

          <div v-else class="delivery-list">
            <div v-for="d in deliveries" :key="`${d.contract_id}-${d.article_name}`" class="delivery-row">
              <div class="del-date-chip" :class="isToday(d.delivery_date) ? 'chip-today' : 'chip-tomorrow'">
                {{ isToday(d.delivery_date) ? 'Dziś' : 'Jutro' }}
              </div>
              <div class="del-body">
                <div class="del-article">{{ d.article_name }}</div>
                <div class="del-meta">
                  <span class="del-contractor">{{ d.contractor_name }}</span>
                  <span v-if="d.delivery_address" class="del-addr"> · {{ d.delivery_address }}</span>
                </div>
                <div class="del-contact" v-if="d.contact_phone1">
                  <a :href="`tel:${d.contact_phone1}`" class="phone-link">📞 {{ d.contact_phone1 }}</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Unprinted -->
        <div class="home-panel panel-unprinted">
          <div class="panel-header">
            <span class="panel-icon">🖨</span>
            <h2>Niewydrukowane umowy</h2>
            <span class="panel-badge panel-badge-red" v-if="unprinted.length">{{ unprinted.length }}</span>
          </div>

          <div v-if="loading.unprinted" class="panel-loading">
            <div class="skel-row" v-for="i in 2" :key="i"></div>
          </div>

          <div v-else-if="!unprinted.length" class="panel-empty panel-empty-sm">
            <span class="empty-icon">✅</span>
            <p>Wszystkie umowy wydrukowane</p>
          </div>

          <div v-else class="unprinted-list">
            <div
              v-for="c in unprinted.slice(0, 6)"
              :key="c.id"
              class="unprinted-row"
              @click="$router.push(`/contracts/${c.id}/edit`)"
            >
              <div class="unp-number">{{ c.number }}</div>
              <div class="unp-contractor">{{ c.contractor_name }}</div>
              <div class="unp-date">od {{ c.created_at }}</div>
            </div>
            <div v-if="unprinted.length > 6" class="unp-more">
              + {{ unprinted.length - 6 }} więcej →
            </div>
          </div>
        </div>

        <!-- Stale print -->
        <div class="home-panel panel-stale">
          <div class="panel-header">
            <span class="panel-icon">🔄</span>
            <h2>Nieaktualny wydruk</h2>
            <span class="panel-badge panel-badge-orange" v-if="stale.length">{{ stale.length }}</span>
          </div>

          <div v-if="loading.stale" class="panel-loading">
            <div class="skel-row" v-for="i in 2" :key="i"></div>
          </div>

          <div v-else-if="!stale.length" class="panel-empty panel-empty-sm">
            <span class="empty-icon">✓</span>
            <p>Wszystkie wydruki aktualne</p>
          </div>

          <div v-else class="unprinted-list">
            <div
              v-for="c in stale.slice(0, 6)"
              :key="c.id"
              class="unprinted-row stale-row"
              @click="$router.push(`/contracts/${c.id}/edit`)"
            >
              <div class="unp-number">{{ c.number }}</div>
              <div class="unp-contractor">{{ c.contractor_name }}</div>
              <div class="unp-date" :title="'Zmiana: ' + c.updated_at">{{ c.updated_at }}</div>
            </div>
            <div v-if="stale.length > 6" class="unp-more">
              + {{ stale.length - 6 }} więcej →
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/composables/useApi'

const loading = ref({ fleet: true, expiring: true, deliveries: true, unprinted: true, stale: true, overdue: true })
const fleet = ref({ total_rented: 0, total_machines: 0, utilization_pct: 0, period_revenue: 0, contracts_in_period: 0 })
const expiring = ref([])
const deliveries = ref([])
const unprinted = ref([])
const stale = ref([])
const overdue = ref([])

const today = new Date()
today.setHours(0, 0, 0, 0)

const todayLabel = computed(() => {
  return new Date().toLocaleDateString('pl-PL', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
})

const greetingText = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Dzień dobry!'
  if (h < 18) return 'Witaj!'
  return 'Dobry wieczór!'
})

const kpiFleetClass = computed(() => {
  const p = fleet.value.utilization_pct
  if (p >= 70) return 'kpi-ok'
  if (p >= 40) return 'kpi-warn'
  return 'kpi-info'
})

const minDaysLeft = computed(() => {
  if (!expiring.value.length) return null
  return Math.min(...expiring.value.map(c => c.days_left))
})

const todayStr = new Date().toISOString().slice(0, 10)
const tomorrowStr = new Date(Date.now() + 86400000).toISOString().slice(0, 10)

const todayDeliveriesCount = computed(() =>
  deliveries.value.filter(d => d.delivery_date === todayStr || (d.delivery_date && d.delivery_date.slice(0, 10) === todayStr)).length
)

function isToday(d) {
  if (!d) return false
  return String(d).slice(0, 10) === todayStr
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function urgencyClass(days) {
  if (days === null || days === undefined) return ''
  if (days <= 3) return 'urgent-critical'
  if (days <= 7) return 'urgent-high'
  return 'urgent-medium'
}

function daysOverdue(c) {
  if (!c.date_to) return 0
  const today = new Date(); today.setHours(0,0,0,0)
  const dt = new Date(c.date_to); dt.setHours(0,0,0,0)
  return Math.round((today - dt) / 86400000)
}

async function loadAll() {
  const df = new Date()
  df.setDate(1)
  const dfStr = df.toISOString().slice(0, 10)
  const dtStr = new Date().toISOString().slice(0, 10)

  const [fleetRes, expiringRes, deliveriesRes, unprintedRes, staleRes, overdueRes] = await Promise.allSettled([
    api.get('/stats/fleet-summary', { params: { date_from: dfStr, date_to: dtStr } }),
    api.get('/stats/expiring-contracts', { params: { days: 14 } }),
    api.get('/stats/deliveries-today', { params: { lookahead: 2 } }),
    api.get('/stats/unprinted-contracts'),
    api.get('/stats/stale-print-contracts'),
    api.get('/contracts/overdue', { params: { page: 1, per_page: 20 } }),
  ])

  if (fleetRes.status === 'fulfilled') fleet.value = fleetRes.value.data
  loading.value.fleet = false

  if (expiringRes.status === 'fulfilled') expiring.value = expiringRes.value.data
  loading.value.expiring = false

  if (deliveriesRes.status === 'fulfilled') deliveries.value = deliveriesRes.value.data
  loading.value.deliveries = false

  if (unprintedRes.status === 'fulfilled') unprinted.value = unprintedRes.value.data
  loading.value.unprinted = false

  if (staleRes.status === 'fulfilled') stale.value = staleRes.value.data
  loading.value.stale = false

  if (overdueRes.status === 'fulfilled') overdue.value = overdueRes.value.data.items
  loading.value.overdue = false
}

onMounted(loadAll)
</script>

<style scoped>
.home-view {
  padding: 24px 28px;
  height: 100%;
  overflow-y: auto;
  background: #F4F6FB;
  box-sizing: border-box;
}

/* ── HEADER ── */
.home-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.greeting-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-heading);
  margin: 0 0 2px;
}
.greeting-date {
  font-size: 13px;
  color: var(--color-text-muted);
  text-transform: capitalize;
}
.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.qa-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 16px;
  border-radius: var(--border-radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 150ms;
}
.qa-primary { background: var(--color-primary); color: var(--color-text-on-primary); }
.qa-primary:hover { background: var(--color-primary-dark); }
.qa-secondary { background: #E8EEFF; color: var(--color-primary); border: 1px solid #C7D2F0; }
.qa-secondary:hover { background: #D6E0FF; }
.qa-ghost { background: transparent; color: var(--color-text-muted); border: 1px solid var(--color-border); }
.qa-ghost:hover { background: var(--color-bg-light); color: var(--color-text-heading); }
.qa-icon { font-weight: 800; font-size: 15px; line-height: 1; }

/* ── KPI STRIP ── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.kpi-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: var(--shadow-card);
  border-left: 4px solid transparent;
  transition: box-shadow 150ms;
}
.kpi-card:hover { box-shadow: var(--shadow-card-hover); }
.kpi-ok { border-left-color: var(--color-success); }
.kpi-warn { border-left-color: var(--color-warning); }
.kpi-danger { border-left-color: var(--color-error); }
.kpi-info { border-left-color: var(--color-info); }
.kpi-icon { font-size: 26px; flex-shrink: 0; }
.kpi-body { min-width: 0; }
.kpi-value {
  font-size: 26px;
  font-weight: 800;
  color: var(--color-text-heading);
  line-height: 1.1;
}
.kpi-value.skeleton {
  background: var(--color-border);
  border-radius: 4px;
  width: 60px;
  height: 28px;
  animation: pulse 1.4s ease-in-out infinite;
}
.kpi-denom { font-size: 16px; font-weight: 500; color: var(--color-text-muted); }
.kpi-label { font-size: 11px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: .04em; margin-top: 2px; }
.kpi-sub { font-size: 12px; color: var(--color-text-body); margin-top: 3px; }

/* ── QUICK NAV STRIP ── */
.quick-nav-strip {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  padding: 12px 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-card);
}
.nav-grid-full {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

/* ── MAIN GRID ── */
.home-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  align-items: start;
}
.home-left {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.home-right {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── PANELS ── */
.home-panel {
  background: var(--color-bg-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px 12px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-card);
  color: var(--color-text-heading);
}
.panel-icon { font-size: 16px; }
.panel-header h2 {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-heading);
  margin: 0;
  flex: 1;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.panel-badge {
  background: var(--color-warning);
  color: var(--color-text-on-primary);
  font-size: 11px;
  font-weight: 700;
  border-radius: 20px;
  padding: 2px 8px;
  min-width: 20px;
  text-align: center;
}
.panel-badge-blue { background: var(--color-info); }
.panel-badge-red { background: var(--color-error); }
.panel-badge-orange { background: var(--color-warning); }

/* ── LOADING ── */
.panel-loading { padding: 12px 16px; display: flex; flex-direction: column; gap: 8px; }
.skel-row {
  height: 48px;
  background: var(--color-border);
  border-radius: var(--border-radius-sm);
  animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .5; }
}

/* ── EMPTY ── */
.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 16px;
  color: var(--color-text-muted);
  gap: 8px;
}
.panel-empty-sm { padding: 18px 16px; flex-direction: row; gap: 8px; }
.empty-icon { font-size: 20px; color: var(--color-success); }
.panel-empty p { font-size: 13px; margin: 0; }

/* ── EXPIRING LIST ── */
.expiring-list { max-height: 520px; overflow-y: auto; }
.exp-row {
  display: flex;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border);
  transition: background 120ms;
}
.exp-row:hover { background: var(--color-bg-light); }
.exp-urgency-bar { width: 4px; flex-shrink: 0; }
.exp-row.urgent-critical .exp-urgency-bar { background: var(--color-error); }
.exp-row.urgent-high .exp-urgency-bar { background: var(--color-warning); }
.exp-row.urgent-medium .exp-urgency-bar { background: #FCD34D; }
.exp-body { padding: 10px 14px; flex: 1; min-width: 0; }
.exp-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
.exp-number { font-size: 13px; font-weight: 700; color: var(--color-text-heading); }
.exp-days {
  font-size: 12px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 10px;
}
.exp-days.urgent-critical { background: #FEE2E2; color: #991B1B; }
.exp-days.urgent-high { background: #FEF3C7; color: #92400E; }
.exp-days.urgent-medium { background: #FFF8DC; color: #78350F; }
.exp-contractor { font-size: 13px; color: var(--color-text-body); margin-bottom: 3px; }
.exp-meta { display: flex; gap: 10px; font-size: 11px; color: var(--color-text-muted); margin-bottom: 2px; flex-wrap: wrap; }
.exp-addr { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 280px; }
.exp-contact { display: flex; gap: 12px; font-size: 11px; color: var(--color-text-body); }
.phone-link { color: var(--color-info); text-decoration: none; }
.phone-link:hover { text-decoration: underline; }

/* ── OVERDUE ── */
.overdue-row:hover { background: #FEF2F2; }
.overdue-bar { background: #EF4444; }
.overdue-days {
  background: #FEE2E2;
  color: #991B1B;
}

/* ── DELIVERIES ── */
.delivery-list { padding: 4px 0; }
.delivery-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
}
.del-date-chip {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--border-radius-sm);
  flex-shrink: 0;
  margin-top: 1px;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.chip-today { background: #DBEAFE; color: #1E40AF; }
.chip-tomorrow { background: #E0E7FF; color: #3730A3; }
.del-body { flex: 1; min-width: 0; }
.del-article { font-size: 13px; font-weight: 600; color: var(--color-text-heading); }
.del-meta { font-size: 11px; color: var(--color-text-muted); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-contact { font-size: 11px; margin-top: 2px; }

/* ── UNPRINTED ── */
.unprinted-list { padding: 4px 0; }
.unprinted-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 120ms;
}
.unprinted-row:hover { background: #FFF9F0; }
.unp-number { font-size: 12px; font-weight: 700; color: var(--color-text-heading); min-width: 80px; }
.unp-contractor { font-size: 12px; color: var(--color-text-body); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.unp-date { font-size: 11px; color: var(--color-text-muted); flex-shrink: 0; }
.unp-more {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--color-info);
  cursor: pointer;
  text-align: center;
}
.stale-row:hover { background: #FFF5F5; }

/* ── QUICK NAV ── */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px;
}
.nav-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 12px 8px;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-body);
  transition: all 150ms;
}
.nav-tile:hover { background: #E8EEFF; border-color: #C7D2F0; color: var(--color-primary); transform: translateY(-1px); }
.nav-tile-icon { font-size: 20px; }

/* ── RESPONSIVE ── */
@media (max-width: 1400px) {
  .kpi-strip { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 1100px) {
  .kpi-strip { grid-template-columns: repeat(2, 1fr); }
  .home-grid { grid-template-columns: 1fr; }
}
@media (max-width: 700px) {
  .kpi-strip { grid-template-columns: 1fr 1fr; }
  .home-header { flex-direction: column; align-items: flex-start; }
}
</style>
