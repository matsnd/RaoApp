<template>
  <div style="display:flex;flex-direction:column;height:100%;overflow:hidden;">
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
      <!-- CONTRACTS -->
      <template v-if="section === 'contracts'">
        <div class="grid-container">
          <div class="grid-header">
            <div class="search-input-wrap" style="flex:1;max-width:380px;">
              <span class="search-icon">⌕</span>
              <input v-model="search" type="text" class="form-control" placeholder="Szukaj wg numeru, kontrahenta..." />
            </div>
            <select v-model="contractTypeFilter" class="form-control" style="width:160px;" aria-label="Filtr typu umowy">
              <option value="">Wszystkie typy</option>
              <option value="S">Umowy najmu (S)</option>
              <option value="U">Umowy usługi (U)</option>
            </select>
            <GlossaryTip term="S/U" definition="S = umowa najmu, U = umowa usługi" description="S — klient płaci za dni/miesiące użytkowania maszyny. U — klient płaci za wykonaną usługę (godz. pracy + operator)." placement="bottom" :size="12" />
            <!-- RAO-P2-022: filtr statusu rozliczenia -->
            <select v-model="settledFilter" class="form-control" style="width:160px;">
              <option value="false">Aktywne</option>
              <option value="true">Rozliczone</option>
              <option value="">Wszystkie</option>
            </select>
            <input v-model="dateFrom" type="date" class="form-control" style="width:140px;" placeholder="Data od" />
            <input v-model="dateTo" type="date" class="form-control" style="width:140px;" placeholder="Data do" />
            <!-- RAO-P2-070 Faza 4: filtr Handlowiec -->
            <select v-model="salespersonFilter" class="form-control" style="width:180px;">
              <option value="">Wszyscy handlowcy</option>
              <option v-for="sp in salespeopleList" :key="sp.id" :value="sp.name">{{ sp.name }}</option>
            </select>
            <!-- RAO-P2-070 Faza 4: filtr Miasto -->
            <input v-model="cityFilter" type="text" class="form-control" style="width:160px;" placeholder="Miasto..." />
          </div>
          <div class="grid-scroll">
            <table class="data-grid" role="table" aria-label="Lista umów">
              <thead>
                <tr role="row">
                  <th class="th-sortable" role="columnheader" @click="toggleSort('number')" aria-sort="other">Numer <span class="sort-indicator" aria-hidden="true">{{ sortIndicator('number') }}</span></th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('contractor_name')" aria-sort="other">Kontrahent <span class="sort-indicator" aria-hidden="true">{{ sortIndicator('contractor_name') }}</span></th>
                  <th role="columnheader">Adres dostawy</th>
                  <th role="columnheader">Typ</th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('date_from')" aria-sort="other">Data od <span class="sort-indicator" aria-hidden="true">{{ sortIndicator('date_from') }}</span></th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('date_to')" aria-sort="other">Data do <span class="sort-indicator" aria-hidden="true">{{ sortIndicator('date_to') }}</span></th>
                  <!-- RAO-P1-021/P2-033: Wartość usunięte (martwe pole) -->
                  <th class="th-sortable" role="columnheader" @click="toggleSort('salesperson_name')" aria-sort="other">Handlowiec <span class="sort-indicator" aria-hidden="true">{{ sortIndicator('salesperson_name') }}</span></th>
                  <th role="columnheader">Status</th>
                  <th role="columnheader">Wydruk</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="contractStore.loading" role="row">
                  <td colspan="10" role="cell"><SkeletonRow :cols="6" label="Ładowanie umów" /></td>
                </tr>
                <tr v-else-if="loadError" role="row">
                  <td colspan="10" role="cell"><StateMessage type="error" compact :message="loadError" @action="loadData" /></td>
                </tr>
                <tr v-else-if="!contractStore.list.length" role="row">
                  <td colspan="10" role="cell">
                    <StateMessage type="empty" compact message="Brak umow" action-label="+ Nowa umowa" @action="router.push({ name: 'ContractNew' })" />
                  </td>
                </tr>
                <tr v-else-if="!sortedFilteredContracts.length" role="row">
                  <td colspan="10" role="cell"><StateMessage type="empty" compact message="Brak umow spelniajacych filtry" /></td>
                </tr>
                <tr
                  v-for="c in sortedFilteredContracts"
                  :key="c.id"
                  role="row"
                  tabindex="0"
                  :aria-label="`Umowa ${c.number}, kontrahent ${c.contractor_name}`"
                  :class="['contract-row', { selected: selectedId === c.id }, c.is_settled ? 'row-settled' : expiryClass(c)]"
                  @click="selectedId = c.id"
                  @dblclick="editContract(c.id)"
                  @contextmenu.prevent="openContextMenu($event, c)"
                  @keydown.enter.prevent="editContract(c.id)"
                >
                  <td role="cell">{{ c.number }}</td>
                  <td role="cell">
                    <!-- RAO-P2-070 Faza 2: drilldown do edycji kontrahenta -->
                    <a class="drilldown-link" role="button" tabindex="0" :aria-label="`Edytuj kontrahenta: ${c.contractor_name}`" :title="`Edytuj kontrahenta: ${c.contractor_name}`" @click.stop="goToContractor(c.contractor_id)" @keydown.enter.stop.prevent="goToContractor(c.contractor_id)">{{ c.contractor_name }}</a>
                  </td>
                  <td role="cell" class="cell-address">{{ c.delivery_address || '—' }}</td>
                  <td role="cell"><span :class="['badge', c.contract_type === 'S' ? 'badge-info' : 'badge-warning']">{{ c.type_label }}</span></td>
                  <td role="cell">{{ formatDate(c.date_from) }}</td>
                  <td role="cell">
                    <span :title="expiryTitle(c)">{{ formatDate(c.date_to) }}</span>
                    <span v-if="!c.is_settled && daysLeft(c) !== null && daysLeft(c) >= 0 && daysLeft(c) <= 14" class="expiry-chip" :class="expiryClass(c)" :aria-label="expiryTitle(c)">
                      {{ daysLeft(c) + 'd' }}
                    </span>
                  </td>
                  <!-- RAO-P1-021/P2-033: Wartość usunięte -->
                  <td role="cell">{{ c.salesperson_name || '—' }}</td>
                  <!-- RAO-P2-022: kolumna statusu -->
                  <td role="cell">
                    <span v-if="c.is_settled" class="badge badge-settled">Rozliczona</span>
                    <span v-else-if="daysLeft(c) !== null && daysLeft(c) < 0" class="badge badge-overdue">Zamknięta</span>
                    <span v-else class="badge badge-active">Aktywna</span>
                  </td>
                  <td role="cell">
                    <span :class="['badge', c.is_print_current ? 'badge-success' : 'badge-muted']">
                      {{ c.is_print_current ? 'Aktualny' : (c.print_date ? 'Nieaktualny' : 'Brak') }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="grid-footer">
            <span>Łącznie: {{ contractStore.total }} umów{{ sortedFilteredContracts.length !== contractStore.list.length ? ' (' + sortedFilteredContracts.length + ' po filtrach)' : '' }}</span>
            <div class="pagination">
              <button class="page-btn" :disabled="page <= 1" aria-label="Poprzednia strona umów" @click="page--">‹</button>
              <span style="padding:0 8px;font-size:12px;" aria-current="page">{{ page }} / {{ totalPages }}</span>
              <button class="page-btn" :disabled="page >= totalPages" aria-label="Następna strona umów" @click="page++">›</button>
            </div>
          </div>
        </div>
      </template>

      <!-- OVERDUE CONTRACTS -->
      <template v-else-if="section === 'overdue'">
        <div class="grid-container">
          <div class="grid-header">
            <h2 class="section-title-overdue">🔴 Przeterminowane umowy</h2>
            <span class="section-subtitle">Umowy z datą zakończenia w przeszłości — nierozliczone</span>
          </div>
          <div class="grid-scroll">
            <table class="data-grid" role="table" aria-label="Przeterminowane umowy">
              <thead>
                <tr role="row">
                  <th role="columnheader">Numer</th>
                  <th role="columnheader">Kontrahent</th>
                  <th role="columnheader">Adres dostawy</th>
                  <th role="columnheader">Typ</th>
                  <th role="columnheader">Data od</th>
                  <th role="columnheader">Data do</th>
                  <th role="columnheader">Dni po terminie</th>
                  <!-- RAO-P1-021/P2-033: Wartość usunięte -->
                  <th role="columnheader">Handlowiec</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="contractStore.overdueLoading" role="row">
                  <td colspan="9" role="cell"><SkeletonRow :cols="6" label="Ładowanie przeterminowanych umów" /></td>
                </tr>
                <tr v-else-if="loadError" role="row">
                  <td colspan="9" role="cell"><StateMessage type="error" compact :message="loadError" @action="loadData" /></td>
                </tr>
                <tr v-else-if="!contractStore.overdueList.length" role="row">
                  <td colspan="9" role="cell"><StateMessage type="empty" compact message="Brak przeterminowanych umow" /></td>
                </tr>
                <tr
                  v-for="c in contractStore.overdueList"
                  :key="c.id"
                  role="row"
                  tabindex="0"
                  :aria-label="`Przeterminowana umowa ${c.number}, ${daysOverdue(c)} dni po terminie`"
                  :class="['contract-row', 'row-overdue']"
                  @click="selectedId = c.id"
                  @dblclick="editContract(c.id)"
                  @contextmenu.prevent="openContextMenu($event, c)"
                  @keydown.enter.prevent="editContract(c.id)"
                >
                  <td role="cell" class="cell-strong">{{ c.number }}</td>
                  <td role="cell">{{ c.contractor_name }}</td>
                  <td role="cell" class="cell-address">{{ c.delivery_address || '—' }}</td>
                  <td role="cell"><span :class="['badge', c.contract_type === 'S' ? 'badge-info' : 'badge-warning']">{{ c.type_label }}</span></td>
                  <td role="cell">{{ formatDate(c.date_from) }}</td>
                  <td role="cell">{{ formatDate(c.date_to) }}</td>
                  <td role="cell" class="cell-overdue-days">{{ daysOverdue(c) }} dni</td>
                  <!-- RAO-P1-021/P2-033: Wartość usunięte -->
                  <td role="cell">{{ c.salesperson_name || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="grid-footer">
            <span>Łącznie: {{ contractStore.overdueTotal }} przeterminowanych umów</span>
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
            <table class="data-grid" role="table" aria-label="Lista kontrahentów">
              <thead>
                <tr role="row">
                  <th class="th-sortable" role="columnheader" @click="toggleSort('name')">Nazwa <span class="sort-indicator">{{ sortIndicator('name') }}</span></th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('nip')">NIP <span class="sort-indicator">{{ sortIndicator('nip') }}</span></th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('city')">Miasto <span class="sort-indicator">{{ sortIndicator('city') }}</span></th>
                  <th role="columnheader">Telefon</th>
                  <th role="columnheader">Email</th>
                  <th role="columnheader">Aktywna umowa</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="contractorStore.loading" role="row">
                  <td colspan="6" role="cell"><SkeletonRow :cols="6" label="Ładowanie kontrahentów" /></td>
                </tr>
                <tr v-else-if="loadError" role="row">
                  <td colspan="6" role="cell"><StateMessage type="error" compact :message="loadError" @action="loadData" /></td>
                </tr>
                <tr v-else-if="!contractorStore.list.length" role="row">
                  <td colspan="6" role="cell">
                    <StateMessage type="empty" compact message="Brak kontrahentow" action-label="+ Nowy kontrahent" @action="router.push({ name: 'ContractorNew' })" />
                  </td>
                </tr>
                <tr
                  v-for="c in sortedContractors"
                  :key="c.id"
                  role="row"
                  :class="{ selected: selectedId === c.id }"
                  @click="selectedId = c.id"
                  @dblclick="editContractor(c.id)"
                >
                  <td role="cell">{{ c.name }}</td>
                  <td role="cell">{{ c.nip || '—' }}</td>
                  <td role="cell">{{ c.city || '—' }}</td>
                  <td role="cell">{{ c.phone1 || '—' }}</td>
                  <td role="cell">{{ c.email || '—' }}</td>
                  <td role="cell">
                    <!-- RAO-P2-070 Faza 2: drilldown do listy umow filtrowanej po numerze -->
                    <a v-if="c.active_contract_number" class="drilldown-link" :title="`Pokaż umowę: ${c.active_contract_number}`" @click.stop="goToContractByNumber(c.active_contract_number)">{{ c.active_contract_number }}</a>
                    <span v-else>—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="grid-footer">
            <span>Łącznie: {{ contractorStore.total }} kontrahentów</span>
            <div class="pagination">
              <button class="page-btn" :disabled="page <= 1" aria-label="Poprzednia strona kontrahentów" @click="page--">‹</button>
              <span style="padding:0 8px;font-size:12px;" aria-current="page">{{ page }} / {{ totalPages }}</span>
              <button class="page-btn" :disabled="page >= totalPages" aria-label="Następna strona kontrahentów" @click="page++">›</button>
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
            <table class="data-grid" role="table" aria-label="Lista maszyn">
              <thead>
                <tr role="row">
                  <th class="th-sortable" role="columnheader" @click="toggleSort('name')">Nazwa <span class="sort-indicator">{{ sortIndicator('name') }}</span></th>
                  <th role="columnheader">Typ</th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('internal_number')">Nr wew. <span class="sort-indicator">{{ sortIndicator('internal_number') }}</span></th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('registration_no')">Nr rej. <span class="sort-indicator">{{ sortIndicator('registration_no') }}</span></th>
                  <th class="th-sortable" role="columnheader" @click="toggleSort('brand')">Marka <span class="sort-indicator">{{ sortIndicator('brand') }}</span></th>
                  <th role="columnheader">Kategoria</th>
                  <th role="columnheader">Aktywna umowa</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="articleStore.loading" role="row">
                  <td colspan="7" role="cell"><SkeletonRow :cols="7" label="Ładowanie maszyn" /></td>
                </tr>
                <tr v-else-if="loadError" role="row">
                  <td colspan="7" role="cell"><StateMessage type="error" compact :message="loadError" @action="loadData" /></td>
                </tr>
                <tr v-else-if="!articleStore.list.length" role="row">
                  <td colspan="7" role="cell">
                    <StateMessage
                      type="empty"
                      compact
                      message="Brak maszyn"
                      action-label="+ Nowa maszyna"
                      @action="router.push({ name: 'ArticleNew' })"
                    />
                  </td>
                </tr>
                <tr
                  v-for="a in sortedArticles"
                  :key="a.id"
                  role="row"
                  :class="['article-row', { selected: selectedId === a.id }]"
                  @click="selectedId = a.id"
                  @dblclick="editArticle(a.id)"
                >
                  <td role="cell">
                    <!-- RAO-P2-070 Faza 2: drilldown do historii wynajmów w Analytics -->
                    <a class="drilldown-link" :title="`Historia wynajmów: ${a.name}`" @click.stop="goToArticleAnalytics(a.id)">{{ a.name }}</a>
                  </td>
                  <td role="cell"><span :class="['badge', a.is_service ? 'badge-warning' : 'badge-info']">{{ a.is_service ? 'Usługa' : 'Sprzęt' }}</span></td>
                  <td role="cell">{{ a.internal_number || '—' }}</td>
                  <td role="cell">{{ a.registration_no || '—' }}</td>
                  <td role="cell">{{ a.brand || '—' }}</td>
                  <td role="cell">{{ a.category_name || '—' }}</td>
                  <td role="cell">{{ a.active_contract_number || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="grid-footer">
            <span>Łącznie: {{ articleStore.total }} maszyn</span>
            <div class="pagination">
              <button class="page-btn" :disabled="page <= 1" aria-label="Poprzednia strona artykułów" @click="page--">‹</button>
              <span style="padding:0 8px;font-size:12px;" aria-current="page">{{ page }} / {{ totalPages }}</span>
              <button class="page-btn" :disabled="page >= totalPages" aria-label="Następna strona artykułów" @click="page++">›</button>
            </div>
          </div>
        </div>
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
      role="menu"
      aria-label="Menu akcji umowy"
      :style="{ top: ctxMenu.y + 'px', left: ctxMenu.x + 'px' }"
      @mouseleave="ctxMenu.visible = false"
    >
      <div class="ctx-menu-header">{{ ctxMenu.contract?.number }}</div>
      <button class="ctx-menu-item" role="menuitem" @click="ctxPrint('contract')">📄 Umowa</button>
      <button class="ctx-menu-item" role="menuitem" @click="ctxPrint('protocol_zo')">📋 Protokół ZO</button>
      <button class="ctx-menu-item" role="menuitem" @click="ctxPrint('protocol_zo_nodata')">📋 Protokół ZO (bez danych)</button>
      <div class="ctx-menu-sep"></div>
      <button class="ctx-menu-item" role="menuitem" @click="editContract(ctxMenu.contract?.id); ctxMenu.visible=false">✏️ Edytuj umowę</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppToolbar from '@/components/layout/AppToolbar.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import StateMessage from '@/components/StateMessage.vue'
import SkeletonRow from '@/components/SkeletonRow.vue'
import GlossaryTip from '@/components/GlossaryTip.vue'
import { useContractStore } from '@/stores/contracts'
import { useContractorStore } from '@/stores/contractors'
import { useArticleStore } from '@/stores/articles'
import { useSettingsStore } from '@/stores/settings'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatCurrency } from '@/utils/format'
const props = defineProps({ section: String })
const router = useRouter()
const route = useRoute()

const contractStore = useContractStore()
const contractorStore = useContractorStore()
const articleStore = useArticleStore()
const settingsStore = useSettingsStore()
const toastStore = useToastStore()

const search = ref('')
const contractTypeFilter = ref('')
const settledFilter = ref('')   // RAO-P2-022: domyślnie wszystkie umowy (zmienione z 'false' na '' ze względu na pustą listę)
const dateFrom = ref('')
const dateTo = ref('')
// RAO-P2-070 Faza 4: filtry handlowiec + miasto (client-side na załadowanej stronie)
const salespersonFilter = ref('')
const cityFilter = ref('')
const selectedId = ref(null)
const page = ref(1)
const perPage = 50
const showConfirm = ref(false)
// RAO-P2-070 Faza 3: sortowanie po kolumnach (client-side na załadowanej stronie)
const sortKey = ref('date_from')   // domyślnie po dacie
const sortDir = ref('desc')        // najnowsze pierwsze
// RAO-P2-070 Faza 4: lista handlowców dla dropdownu
const salespeopleList = computed(() => settingsStore.salespeople || [])
// RAO-P2-049: error state dla widokow listowych (retry przez loadData)
const loadError = ref('')

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

// RAO-P1-043: named handler dla removeEventListener (inline arrow nie działa z removeEventListener)
function handleCtxKeydown(e) { if (e.key === 'Escape') closeCtxMenu() }

const totalPages = computed(() => {
  const total = section.value === 'contracts' ? contractStore.total
    : section.value === 'overdue' ? contractStore.overdueTotal
    : section.value === 'contractors' ? contractorStore.total
    : articleStore.total
  return Math.ceil(total / perPage) || 1
})

const section = computed(() => props.section || 'contracts')

const toolbarInfo = computed(() => {
  if (section.value === 'contracts') return `Umowy (${contractStore.total} rekordów)`
  if (section.value === 'overdue') return `Przeterminowane umowy (${contractStore.overdueTotal} rekordów)`
  if (section.value === 'contractors') return `Kontrahenci (${contractorStore.total} rekordów)`
  if (section.value === 'articles') {
    return `Artykuły (${articleStore.total} rekordów)`
  }
  return ''
})

async function loadData() {
  selectedId.value = null
  loadError.value = ''
  const params = { page: page.value, per_page: perPage }
  if (search.value) params.search = search.value
  try {
    if (section.value === 'contracts') {
      if (contractTypeFilter.value) params.contract_type = contractTypeFilter.value
      if (settledFilter.value !== '') params.is_settled = settledFilter.value  // RAO-P2-022
      if (dateFrom.value) params.date_from = dateFrom.value
      if (dateTo.value) params.date_to = dateTo.value
      await contractStore.fetchList(params)
    } else if (section.value === 'overdue') {
      await contractStore.fetchOverdueList(params)
    } else if (section.value === 'contractors') {
      await contractorStore.fetchList(params)
    } else if (section.value === 'articles') {
      await articleStore.fetchList(params)
    }
  } catch (e) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Nie udalo sie pobrac danych'
  }
}

onMounted(() => {
  // RAO-P2-070 Faza 4: załaduj handlowców dla dropdownu (tylko dla sekcji contracts)
  if (section.value === 'contracts' && !settingsStore.salespeople.length) {
    settingsStore.fetchSalespeople().catch(() => { /* toast błędu niepotrzebny — dropdown pozostanie pusty */ })
  }
  // RAO-P2-070 Faza 2: obsługa ?search= z drilldownu (kontrahent → aktywna umowa)
  if (section.value === 'contracts' && route.query.search) {
    search.value = String(route.query.search)
  }
  loadData()
  document.addEventListener('click', closeCtxMenu)
  document.addEventListener('keydown', handleCtxKeydown)
})

// RAO-P1-043: cleanup event listenerów i timerów — zapobiega memory leakom
onUnmounted(() => {
  document.removeEventListener('click', closeCtxMenu)
  document.removeEventListener('keydown', handleCtxKeydown)
  if (searchTimer) clearTimeout(searchTimer)
})

watch([section, page], loadData)

let searchTimer = null
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadData() }, 400)
})
watch(contractTypeFilter, () => { page.value = 1; loadData() })
watch(settledFilter, () => { page.value = 1; loadData() })  // RAO-P2-022
watch(dateFrom, () => { page.value = 1; loadData() })
watch(dateTo, () => { page.value = 1; loadData() })

function handleAdd() {
  if (section.value === 'contracts') router.push({ name: 'ContractNew' })
  else if (section.value === 'contractors') router.push({ name: 'ContractorNew' })
  else if (section.value === 'articles') router.push({ name: 'ArticleNew' })
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

// RAO-P2-070 Faza 2: drilldowny cross-view
function goToContractor(contractorId) {
  if (contractorId) router.push(`/contractors/${contractorId}/edit`)
}
// Kontrahent → aktywna umowa: backend zwraca tylko numer (nie id), więc filtrujemy listę umów po numerze
function goToContractByNumber(contractNumber) {
  if (!contractNumber) return
  router.push({ path: '/dashboard/contracts', query: { search: contractNumber } })
}
// Artykuł → historia wynajmów w Analytics
function goToArticleAnalytics(articleId) {
  router.push({ path: '/analytics', query: { article: String(articleId) } })
}

// RAO-P2-070 Faza 3: sortowanie po kolumnach
function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = key === 'date_from' || key === 'date_to' ? 'desc' : 'asc'
  }
}
function sortIndicator(key) {
  if (sortKey.value !== key) return ''
  return sortDir.value === 'asc' ? '▲' : '▼'
}
// Uniwersalny komparator — obsługuje string, number, date (ISO string)
function compareValues(a, b) {
  const av = a ?? ''
  const bv = b ?? ''
  // Daty (ISO string z '-' na początku)
  if (typeof av === 'string' && typeof bv === 'string' && /^\d{4}-\d{2}-\d{2}/.test(av) && /^\d{4}-\d{2}-\d{2}/.test(bv)) {
    return av < bv ? -1 : av > bv ? 1 : 0
  }
  // Liczby
  if (typeof av === 'number' && typeof bv === 'number') return av - bv
  // Stringi (case-insensitive)
  const as = String(av).toLowerCase()
  const bs = String(bv).toLowerCase()
  return as < bs ? -1 : as > bs ? 1 : 0
}
function sortList(list) {
  if (!sortKey.value) return list
  const sorted = [...list].sort((a, b) => compareValues(a[sortKey.value], b[sortKey.value]))
  return sortDir.value === 'desc' ? sorted.reverse() : sorted
}

// RAO-P2-070 Faza 3+4: posortowane + przefiltrowane listy (client-side na załadowanej stronie)
const sortedFilteredContracts = computed(() => {
  let list = contractStore.list
  if (salespersonFilter.value) {
    list = list.filter(c => c.salesperson_name === salespersonFilter.value)
  }
  if (cityFilter.value) {
    const q = cityFilter.value.toLowerCase().trim()
    if (q) list = list.filter(c => (c.city || '').toLowerCase().includes(q))
  }
  return sortList(list)
})
const sortedContractors = computed(() => sortList(contractorStore.list))
const sortedArticles = computed(() => sortList(articleStore.list))

async function confirmDelete() {
  showConfirm.value = false
  if (!selectedId.value) return
  try {
    if (section.value === 'contracts') await contractStore.remove(selectedId.value)
    else if (section.value === 'contractors') await contractorStore.remove(selectedId.value)
    else if (section.value === 'articles') await articleStore.remove(selectedId.value)
    selectedId.value = null
    toastStore.success('Element usunięty')
    await loadData()
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd usuwania')
  }
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
  if (d < 0) return `Zamknięta od ${Math.abs(d)} dni`
  if (d === 0) return 'Kończy się dziś!'
  if (d <= 14) return `Kończy się za ${d} dni`
  return ''
}

function daysOverdue(c) {
  if (!c.date_to) return 0
  const today = new Date(); today.setHours(0,0,0,0)
  const dt = new Date(c.date_to); dt.setHours(0,0,0,0)
  return Math.round((today - dt) / 86400000)
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
  font-size: 13px;
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
/* RAO-P2-022: rozliczone — wyciszone szare tło */
.contract-row.row-settled td { background: #f8fafb; color: #5A6B7E; }
.contract-row.row-settled:hover td { background: #f0f4f8; }
.badge-settled { background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
.badge-active  { background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }
.badge-overdue { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

.expiry-chip {
  display: inline-block;
  margin-left: 5px;
  padding: 1px 5px;
  border-radius: 10px;
  font-size: 12px;
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
  font-size: 13px;
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
  font-size: 13px;
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
  color: #5A6B7E;
  cursor: default;
}

/* RAO-P2-070 Faza 3: sortowalne nagłówki kolumn */
.th-sortable {
  cursor: pointer;
  user-select: none;
  transition: color var(--transition-fast, 120ms);
}
.th-sortable:hover {
  color: var(--color-primary);
}
.sort-indicator {
  display: inline-block;
  margin-left: 4px;
  font-size: 12px;
  color: var(--color-primary);
  min-width: 10px;
}

/* RAO-P2-070 Faza 2: linki drilldown cross-view */
.drilldown-link {
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: none;
  border-bottom: 1px dashed var(--color-primary);
  transition: color var(--transition-fast, 120ms), border-color var(--transition-fast, 120ms);
}
.drilldown-link:hover {
  color: var(--color-primary-light, #2A3F6F);
  border-bottom-style: solid;
}
</style>
