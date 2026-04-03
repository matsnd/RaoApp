<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <AppToolbar
      :info-text="toolbarInfo"
      :show-view-button="section === 'contracts'"
      :show-help-button="section === 'contracts'"
      @add="handleAdd"
      @remove="handleRemove"
      @view="handleView"
      @help="handleHelp"
    />
    <div class="content-area" style="padding:var(--spacing-md);">
      <!-- PRINT ALERTS PANEL -->
      <div v-if="section === 'contracts' && (unprintedContracts.length || staleContracts.length)" class="print-alerts-panel">
        <div v-if="unprintedContracts.length" class="print-alert-group">
          <div class="print-alert-title">⚠️ Niewydrukowane ({{ unprintedContracts.length }})</div>
          <div class="print-alert-list">
            <span
              v-for="c in unprintedContracts.slice(0, 8)"
              :key="c.id"
              class="print-alert-chip unprinted"
              :title="(c.contractor_name || '') + '\n' + formatDate(c.date_from) + ' – ' + formatDate(c.date_to)"
              @click="editContract(c.id)"
            >{{ c.number }}</span>
            <span v-if="unprintedContracts.length > 8" class="print-alert-chip more">+{{ unprintedContracts.length - 8 }} więcej</span>
          </div>
        </div>
        <div v-if="staleContracts.length" class="print-alert-group">
          <div class="print-alert-title">🔄 Nieaktualny wydruk ({{ staleContracts.length }})</div>
          <div class="print-alert-list">
            <span
              v-for="c in staleContracts.slice(0, 8)"
              :key="c.id"
              class="print-alert-chip stale"
              :title="(c.contractor_name || '') + '\nWydruk: ' + c.print_date + '\nZmiana: ' + c.updated_at"
              @click="editContract(c.id)"
            >{{ c.number }}</span>
            <span v-if="staleContracts.length > 8" class="print-alert-chip more">+{{ staleContracts.length - 8 }} więcej</span>
          </div>
        </div>
      </div>

      <!-- CONTRACTS -->
      <template v-if="section === 'contracts'">
        <div class="grid-container">
          <div class="grid-header">
            <div class="search-input-wrap" style="flex:1;max-width:380px;">
              <span class="search-icon">⌕</span>
              <input v-model="search" type="text" class="form-control" placeholder="Szukaj wg numeru, kontrahenta..." />
            </div>
            <select v-model="contractTypeFilter" class="form-control" style="width:160px;">
              <option value="">Wszystkie typy</option>
              <option value="S">Umowy najmu</option>
              <option value="U">Umowy usługi</option>
            </select>
          </div>
          <div class="grid-scroll">
            <table class="data-grid">
              <thead>
                <tr>
                  <th>Numer</th>
                  <th>Kontrahent</th>
                  <th>Typ</th>
                  <th>Data od</th>
                  <th>Data do</th>
                  <th>Wartość</th>
                  <th>Handlowiec</th>
                  <th>Wydruk</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="contractStore.loading">
                  <td colspan="8" class="empty-state">Ładowanie...</td>
                </tr>
                <tr v-else-if="!contractStore.list.length">
                  <td colspan="8" class="empty-state">Brak umów</td>
                </tr>
                <tr
                  v-for="c in contractStore.list"
                  :key="c.id"
                  :class="['contract-row', { selected: selectedId === c.id }, expiryClass(c)]"
                  @click="selectedId = c.id"
                  @dblclick="editContract(c.id)"
                  @contextmenu.prevent="openContextMenu($event, c)"
                >
                  <td>{{ c.number }}</td>
                  <td>{{ c.contractor_name }}</td>
                  <td><span :class="['badge', c.contract_type === 'S' ? 'badge-info' : 'badge-warning']">{{ c.type_label }}</span></td>
                  <td>{{ formatDate(c.date_from) }}</td>
                  <td>
                    <span :title="expiryTitle(c)">{{ formatDate(c.date_to) }}</span>
                    <span v-if="daysLeft(c) !== null && daysLeft(c) >= 0 && daysLeft(c) <= 14" class="expiry-chip" :class="expiryClass(c)">
                      {{ daysLeft(c) + 'd' }}
                    </span>
                  </td>
                  <td style="font-weight:600;">{{ formatMoney(c.total_value) }}</td>
                  <td>{{ c.salesperson_name || '—' }}</td>
                  <td>
                    <span :class="['badge', c.is_print_current ? 'badge-success' : 'badge-muted']">
                      {{ c.is_print_current ? 'Aktualny' : (c.print_date ? 'Nieaktualny' : 'Brak') }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="grid-footer">
            <span>Łącznie: {{ contractStore.total }} umów</span>
            <div class="pagination">
              <button class="page-btn" :disabled="page <= 1" @click="page--">‹</button>
              <span style="padding:0 8px;font-size:12px;">{{ page }} / {{ totalPages }}</span>
              <button class="page-btn" :disabled="page >= totalPages" @click="page++">›</button>
            </div>
          </div>
        </div>
      </template>

      <!-- CONTRACTORS -->
      <template v-else-if="section === 'contractors'">
        <div class="grid-container">
          <div class="grid-header">
            <div class="search-input-wrap" style="flex:1;max-width:380px;">
              <span class="search-icon">⌕</span>
              <input v-model="search" type="text" class="form-control" placeholder="Szukaj wg nazwy, NIP..." />
            </div>
          </div>
          <div class="grid-scroll">
            <table class="data-grid">
              <thead>
                <tr>
                  <th>Nazwa</th>
                  <th>NIP</th>
                  <th>Miasto</th>
                  <th>Telefon</th>
                  <th>Email</th>
                  <th>Aktywna umowa</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="contractorStore.loading">
                  <td colspan="6" class="empty-state">Ładowanie...</td>
                </tr>
                <tr v-else-if="!contractorStore.list.length">
                  <td colspan="6" class="empty-state">Brak kontrahentów</td>
                </tr>
                <tr
                  v-for="c in contractorStore.list"
                  :key="c.id"
                  :class="{ selected: selectedId === c.id }"
                  @click="selectedId = c.id"
                  @dblclick="editContractor(c.id)"
                >
                  <td>{{ c.name }}</td>
                  <td>{{ c.nip || '—' }}</td>
                  <td>{{ c.city || '—' }}</td>
                  <td>{{ c.phone1 || '—' }}</td>
                  <td>{{ c.email || '—' }}</td>
                  <td>{{ c.active_contract_number || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="grid-footer">
            <span>Łącznie: {{ contractorStore.total }} kontrahentów</span>
            <div class="pagination">
              <button class="page-btn" :disabled="page <= 1" @click="page--">‹</button>
              <span style="padding:0 8px;font-size:12px;">{{ page }} / {{ totalPages }}</span>
              <button class="page-btn" :disabled="page >= totalPages" @click="page++">›</button>
            </div>
          </div>
        </div>
      </template>

      <!-- ARTICLES -->
      <template v-else-if="section === 'articles'">
        <div class="grid-container">
          <div class="grid-header">
            <div class="search-input-wrap" style="flex:1;max-width:380px;">
              <span class="search-icon">⌕</span>
              <input v-model="search" type="text" class="form-control" placeholder="Szukaj wg nazwy, numeru..." />
            </div>
          </div>
          <div class="grid-scroll">
            <table class="data-grid">
              <thead>
                <tr>
                  <th>Nazwa</th>
                  <th>Typ</th>
                  <th>Nr wew.</th>
                  <th>Nr rej.</th>
                  <th>Marka</th>
                  <th>Kategoria</th>
                  <th>Aktywna umowa</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="articleStore.loading">
                  <td colspan="7" class="empty-state">Ładowanie...</td>
                </tr>
                <tr v-else-if="!articleStore.list.length">
                  <td colspan="7" class="empty-state">Brak artykułów</td>
                </tr>
                <tr
                  v-for="a in articleStore.list"
                  :key="a.id"
                  :class="{ selected: selectedId === a.id }"
                  @click="selectedId = a.id"
                  @dblclick="editArticle(a.id)"
                >
                  <td>{{ a.name }}</td>
                  <td><span :class="['badge', a.is_service ? 'badge-warning' : 'badge-info']">{{ a.is_service ? 'Usługa' : 'Sprzęt' }}</span></td>
                  <td>{{ a.internal_number || '—' }}</td>
                  <td>{{ a.registration_no || '—' }}</td>
                  <td>{{ a.brand || '—' }}</td>
                  <td>{{ a.category_name || '—' }}</td>
                  <td>{{ a.active_contract_number || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="grid-footer">
            <span>Łącznie: {{ articleStore.total }} artykułów</span>
            <div class="pagination">
              <button class="page-btn" :disabled="page <= 1" @click="page--">‹</button>
              <span style="padding:0 8px;font-size:12px;">{{ page }} / {{ totalPages }}</span>
              <button class="page-btn" :disabled="page >= totalPages" @click="page++">›</button>
            </div>
          </div>
        </div>
      </template>

      <!-- REPORTS -->
      <template v-else-if="section === 'reports'">
        <ReportsSection />
      </template>
    </div>

    <ConfirmDialog
      :visible="showConfirm"
      title="Usuń element"
      message="Czy na pewno chcesz usunąć ten element? Tej operacji nie można cofnąć."
      @confirm="confirmDelete"
      @cancel="showConfirm = false"
    />

    <!-- CONTEXT MENU -->
    <div
      v-if="ctxMenu.visible"
      class="ctx-menu"
      :style="{ top: ctxMenu.y + 'px', left: ctxMenu.x + 'px' }"
      @mouseleave="ctxMenu.visible = false"
    >
      <div class="ctx-menu-header">{{ ctxMenu.contract?.number }}</div>
      <button class="ctx-menu-item" @click="ctxPrint('contract')">📄 Umowa</button>
      <button class="ctx-menu-item" @click="ctxPrint('protocol_zo')">📋 Protokół ZO</button>
      <button class="ctx-menu-item" @click="ctxPrint('protocol_zo_nodata')">📋 Protokół ZO (bez danych)</button>
      <div class="ctx-menu-sep"></div>
      <button class="ctx-menu-item" @click="editContract(ctxMenu.contract?.id); ctxMenu.visible=false">✏️ Edytuj umowę</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppToolbar from '@/components/layout/AppToolbar.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import ReportsSection from '@/components/reports/ReportsSection.vue'
import { useContractStore } from '@/stores/contracts'
import { useContractorStore } from '@/stores/contractors'
import { useArticleStore } from '@/stores/articles'
import api from '@/composables/useApi'

const props = defineProps({ section: String })
const router = useRouter()

const contractStore = useContractStore()
const contractorStore = useContractorStore()
const articleStore = useArticleStore()

const search = ref('')
const contractTypeFilter = ref('')
const selectedId = ref(null)
const page = ref(1)
const perPage = 50
const showConfirm = ref(false)

const unprintedContracts = ref([])
const staleContracts = ref([])

async function loadPrintAlerts() {
  try {
    const [r1, r2] = await Promise.all([
      api.get('/stats/unprinted-contracts'),
      api.get('/stats/stale-print-contracts'),
    ])
    unprintedContracts.value = r1.data
    staleContracts.value = r2.data
  } catch { /* silent */ }
}

const ctxMenu = ref({ visible: false, x: 0, y: 0, contract: null })

function openContextMenu(event, contract) {
  selectedId.value = contract.id
  const vw = window.innerWidth
  const vh = window.innerHeight
  let x = event.clientX
  let y = event.clientY
  if (x + 200 > vw) x = vw - 210
  if (y + 160 > vh) y = vh - 170
  ctxMenu.value = { visible: true, x, y, contract }
}

function ctxPrint(type) {
  if (ctxMenu.value.contract) {
    contractStore.generateReport(ctxMenu.value.contract.id, type)
  }
  ctxMenu.value.visible = false
}

function closeCtxMenu() { ctxMenu.value.visible = false }

const totalPages = computed(() => {
  const total = section.value === 'contracts' ? contractStore.total
    : section.value === 'contractors' ? contractorStore.total
    : articleStore.total
  return Math.ceil(total / perPage) || 1
})

const section = computed(() => props.section || 'contracts')

const toolbarInfo = computed(() => {
  if (section.value === 'contracts') return `Umowy (${contractStore.total} rekordów)`
  if (section.value === 'contractors') return `Kontrahenci (${contractorStore.total} rekordów)`
  if (section.value === 'articles') return `Artykuły (${articleStore.total} rekordów)`
  return ''
})

async function loadData() {
  selectedId.value = null
  const params = { page: page.value, per_page: perPage }
  if (search.value) params.search = search.value
  if (section.value === 'contracts') {
    if (contractTypeFilter.value) params.contract_type = contractTypeFilter.value
    await contractStore.fetchList(params)
  } else if (section.value === 'contractors') {
    await contractorStore.fetchList(params)
  } else if (section.value === 'articles') {
    await articleStore.fetchList(params)
  }
}

onMounted(() => {
  loadData()
  loadPrintAlerts()
  document.addEventListener('click', closeCtxMenu)
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeCtxMenu() })
})

watch([section, page], loadData)

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadData() }, 400)
})
watch(contractTypeFilter, () => { page.value = 1; loadData() })

function handleAdd() {
  if (section.value === 'contracts') router.push('/contracts/new')
  else if (section.value === 'contractors') router.push('/contractors/new')
  else if (section.value === 'articles') router.push('/articles/new')
}

function handleRemove() {
  if (selectedId.value) showConfirm.value = true
}

function handleView() {
  if (selectedId.value && section.value === 'contracts') {
    contractStore.generateReport(selectedId.value, 'contract')
  }
}

function handleHelp() {
  if (selectedId.value && section.value === 'contracts') {
    router.push(`/contracts/${selectedId.value}/edit`)
  }
}

function editContract(id) { router.push(`/contracts/${id}/edit`) }
function editContractor(id) { router.push(`/contractors/${id}/edit`) }
function editArticle(id) { router.push(`/articles/${id}/edit`) }

async function confirmDelete() {
  showConfirm.value = false
  if (!selectedId.value) return
  try {
    if (section.value === 'contracts') await contractStore.remove(selectedId.value)
    else if (section.value === 'contractors') await contractorStore.remove(selectedId.value)
    else if (section.value === 'articles') await articleStore.remove(selectedId.value)
    selectedId.value = null
    await loadData()
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd usuwania')
  }
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pl-PL')
}

function formatMoney(v) {
  if (!v && v !== 0) return '—'
  return Number(v).toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł'
}

function daysLeft(c) {
  if (!c.date_to) return null
  const today = new Date(); today.setHours(0,0,0,0)
  const dt = new Date(c.date_to); dt.setHours(0,0,0,0)
  return Math.round((dt - today) / 86400000)
}

function expiryClass(c) {
  const d = daysLeft(c)
  if (d === null) return ''
  if (d < 0) return 'row-overdue'
  if (d <= 7) return 'row-expiring-soon'
  if (d <= 14) return 'row-expiring'
  return ''
}

function expiryTitle(c) {
  const d = daysLeft(c)
  if (d === null) return ''
  if (d < 0) return `Przeterminowana o ${Math.abs(d)} dni`
  if (d === 0) return 'Kończy się dziś!'
  if (d <= 14) return `Kończy się za ${d} dni`
  return ''
}
</script>

<style scoped>
.ctx-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  min-width: 200px;
  padding: 4px 0;
  user-select: none;
}
.ctx-menu-header {
  padding: 6px 14px 5px;
  font-size: 11px;
  font-weight: 700;
  color: #0F234E;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border-bottom: 1px solid #E2E8F0;
  margin-bottom: 3px;
}
.ctx-menu-item {
  display: block;
  width: 100%;
  padding: 8px 14px;
  background: transparent;
  border: none;
  text-align: left;
  font-size: 13px;
  color: #4A5568;
  cursor: pointer;
  font-family: inherit;
  transition: background 120ms;
}
.ctx-menu-item:hover {
  background: #F0F4FF;
  color: #0F234E;
}
.ctx-menu-sep {
  height: 1px;
  background: #E2E8F0;
  margin: 3px 0;
}

.contract-row.row-overdue td { background: #fff5f5; }
.contract-row.row-overdue:hover td { background: #ffe8e8; }
.contract-row.row-expiring-soon td { background: #fff9e6; }
.contract-row.row-expiring-soon:hover td { background: #fff3cc; }
.contract-row.row-expiring td { background: #fffcf0; }
.contract-row.row-expiring:hover td { background: #fff7d6; }

.expiry-chip {
  display: inline-block;
  margin-left: 5px;
  padding: 1px 5px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
  vertical-align: middle;
}
.expiry-chip.row-overdue { background: #ffd5d5; color: #b91c1c; }
.expiry-chip.row-expiring-soon { background: #fde68a; color: #92400e; }
.expiry-chip.row-expiring { background: #fef3c7; color: #78350f; }

.print-alerts-panel {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.print-alert-group {
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 8px 12px;
  flex: 1;
  min-width: 0;
}
.print-alert-title {
  font-size: 11px;
  font-weight: 700;
  color: #4A5568;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.print-alert-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.print-alert-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}
.print-alert-chip.unprinted {
  background: #FEF3C7;
  color: #92400E;
  border: 1px solid #FDE68A;
}
.print-alert-chip.unprinted:hover { background: #FDE68A; }
.print-alert-chip.stale {
  background: #FFF5F5;
  color: #C53030;
  border: 1px solid #FED7D7;
}
.print-alert-chip.stale:hover { background: #FED7D7; }
.print-alert-chip.more {
  background: #EDF2F7;
  color: #718096;
  cursor: default;
}
</style>
