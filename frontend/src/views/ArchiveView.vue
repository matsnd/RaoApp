<template>
  <div class="archive-view">
    <!-- Banner ostrzegawczy -->
    <div class="archive-banner">
      <span class="banner-icon">⚠️</span>
      <div class="banner-text">
        <strong>Archiwum — dane historyczne (szacunkowe).</strong>
        Wartości pochodzą z cenników sprzed migracji, nie z systemu rozliczeń.
      </div>
    </div>

    <!-- Zakładki -->
    <div class="archive-tabs">
      <button
        v-for="tab in visibleTabs"
        :key="tab.id"
        :class="['archive-tab', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Zawartość zakładki -->
    <div class="archive-content">
      <!-- UMOWY -->
      <div v-if="activeTab === 'contracts'" class="tab-pane">
        <div class="grid-container">
          <div class="grid-header">
            <div class="search-input-wrap" style="flex:1;max-width:380px;">
              <span class="search-icon">⌕</span>
              <input
                v-model="contractFilters.search"
                type="text"
                class="form-control"
                placeholder="Szukaj wg numeru, kontrahenta..."
                @keydown.enter="applyContractFilters"
              />
            </div>
            <select v-model="contractFilters.contract_type" class="form-control" style="width:160px;" @change="applyContractFilters">
              <option :value="null">Wszystkie typy</option>
              <option value="S">Umowy najmu (S)</option>
              <option value="U">Umowy usługi (U)</option>
            </select>
            <input v-model="contractFilters.date_from" type="date" class="form-control" style="width:140px;" placeholder="Data od" @change="applyContractFilters" />
            <input v-model="contractFilters.date_to" type="date" class="form-control" style="width:140px;" placeholder="Data do" @change="applyContractFilters" />
            <button class="btn btn-primary btn-sm" @click="applyContractFilters">Filtruj</button>
            <button class="btn-icon" title="Wyczyść filtry" @click="clearContractFilters">↺</button>
          </div>

          <div class="grid-scroll">
            <table class="data-grid">
              <thead>
                <tr>
                  <th>Numer</th>
                  <th>Typ</th>
                  <th>Kontrahent</th>
                  <th>Data od</th>
                  <th>Data do</th>
                  <th>Pozycji</th>
                  <th>Wartość szac.</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="archiveStore.contractsLoading">
                  <td colspan="8" class="empty-state">Ładowanie...</td>
                </tr>
                <tr v-else-if="archiveStore.contractsError">
                  <td colspan="8" class="empty-state error">Błąd: {{ archiveStore.contractsError }}</td>
                </tr>
                <tr v-else-if="!archiveStore.contracts.length">
                  <td colspan="8" class="empty-state">Brak umów archiwum</td>
                </tr>
                <tr
                  v-for="c in archiveStore.contracts"
                  :key="c.id"
                  class="contract-row"
                  :class="{ selected: selectedContractId === c.id }"
                  @click="toggleContractDetails(c.id)"
                >
                  <td style="font-weight:600;">{{ c.number }}</td>
                  <td>
                    <span :class="['badge', c.contract_type === 'S' ? 'badge-info' : 'badge-warning']">{{ c.type_label }}</span>
                  </td>
                  <td>{{ c.contractor_name || '—' }}</td>
                  <td>{{ formatDate(c.date_from) }}</td>
                  <td>{{ formatDate(c.date_to) }}</td>
                  <td>{{ c.position_count ?? '—' }}</td>
                  <td>
                    <span class="est-value">{{ formatMoney(c.invoice_amount) }}</span>
                    <span class="est-suffix">[szac.]</span>
                  </td>
                  <td>
                    <span :class="['badge', c.is_settled ? 'badge-success' : 'badge-muted']">
                      {{ c.is_settled ? 'Rozliczona' : 'Nierozliczona' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Szczegóły umowy (rozwinięte) -->
            <div v-if="selectedContractId" class="contract-details">
              <div v-if="archiveStore.currentContractLoading" class="empty-state">Ładowanie szczegółów...</div>
              <div v-else-if="archiveStore.currentContract" class="details-body">
                <div class="details-header">
                  <h3>Szczegóły umowy {{ archiveStore.currentContract.number }}</h3>
                  <button class="btn-icon" title="Zamknij" @click="selectedContractId = null">✕</button>
                </div>

                <div class="details-grid">
                  <div><strong>Kontrahent:</strong> {{ archiveStore.currentContract.contractor_name || '—' }}</div>
                  <div><strong>Adres dostawy:</strong> {{ archiveStore.currentContract.delivery_address || '—' }}</div>
                  <div><strong>Okres:</strong> {{ formatDate(archiveStore.currentContract.date_from) }} – {{ formatDate(archiveStore.currentContract.date_to) }}</div>
                  <div><strong>Osoba kontaktowa:</strong> {{ archiveStore.currentContract.contact_person1 || '—' }} {{ archiveStore.currentContract.contact_phone1 || '' }}</div>
                  <div><strong>Zaliczka:</strong> {{ formatMoney(archiveStore.currentContract.prepayment_amount) }}</div>
                  <div><strong>Faktura:</strong> <span class="est-value">{{ formatMoney(archiveStore.currentContract.invoice_amount) }}</span> <span class="est-suffix">[szac.]</span></div>
                </div>

                <h4>Pozycje ({{ archiveStore.currentContract.positions.length }})</h4>
                <table class="data-grid details-table">
                  <thead>
                    <tr>
                      <th>Maszyna</th>
                      <th>Typ wynajmu</th>
                      <th>Dni</th>
                      <th>Ilość</th>
                      <th>Cena/jm.</th>
                      <th>Warunki</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in archiveStore.currentContract.positions" :key="p.id">
                      <td>{{ p.article_name || '—' }}</td>
                      <td>{{ p.rental_type || '—' }}</td>
                      <td>{{ p.rental_days ?? '—' }}</td>
                      <td>{{ p.quantity ?? '—' }}</td>
                      <td>{{ formatMoney(p.unit_price) }}</td>
                      <td>{{ p.conditions.length }}</td>
                    </tr>
                  </tbody>
                </table>

                <h4 v-if="archiveStore.currentContract.service_fees.length">Opłaty dodatkowe ({{ archiveStore.currentContract.service_fees.length }})</h4>
                <table v-if="archiveStore.currentContract.service_fees.length" class="data-grid details-table">
                  <thead>
                    <tr><th>Nazwa</th><th>Od</th><th>Do</th><th>Jm.</th><th>Aktywna</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="f in archiveStore.currentContract.service_fees" :key="f.id">
                      <td>{{ f.name }}</td>
                      <td>{{ formatMoney(f.amount_from) }}</td>
                      <td>{{ formatMoney(f.amount_to) }}</td>
                      <td>{{ f.unit || '—' }}</td>
                      <td>
                        <span :class="['badge', f.is_active ? 'badge-success' : 'badge-muted']">{{ f.is_active ? 'Tak' : 'Nie' }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>

                <h4 v-if="archiveStore.currentContract.settlements.length">Rozliczenia ({{ archiveStore.currentContract.settlements.length }})</h4>
                <table v-if="archiveStore.currentContract.settlements.length" class="data-grid details-table">
                  <thead>
                    <tr><th>Koszt klienta</th><th>Koszt firma</th><th>Notatki</th><th>Data</th><th>Źródło</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="s in archiveStore.currentContract.settlements" :key="s.id">
                      <td>{{ formatMoney(s.cost_client) }}</td>
                      <td>{{ formatMoney(s.cost_company) }}</td>
                      <td>{{ s.notes || '—' }}</td>
                      <td>{{ formatDate(s.settled_at) }}</td>
                      <td>{{ s.source || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="grid-footer">
            <span>Łącznie: {{ archiveStore.contractsTotal }} umów</span>
            <div class="pagination">
              <select v-model.number="contractsPerPageLocal" class="form-control" style="width:80px;" @change="changeContractsPerPage">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
              </select>
              <button class="page-btn" :disabled="archiveStore.contractsPage <= 1" @click="prevContractsPage">‹</button>
              <span style="padding:0 8px;font-size:12px;">{{ archiveStore.contractsPage }} / {{ contractsTotalPages }}</span>
              <button class="page-btn" :disabled="archiveStore.contractsPage >= contractsTotalPages" @click="nextContractsPage">›</button>
            </div>
          </div>
        </div>
      </div>

      <!-- MASZYNY -->
      <div v-else-if="activeTab === 'articles'" class="tab-pane">
        <div class="grid-container">
          <div class="grid-header">
            <div class="search-input-wrap" style="flex:1;max-width:380px;">
              <span class="search-icon">⌕</span>
              <input
                v-model="articleFilters.search"
                type="text"
                class="form-control"
                placeholder="Szukaj wg nazwy, numeru wewnętrznego..."
                @keydown.enter="applyArticleFilters"
              />
            </div>
            <select v-model="articleFilters.category_id" class="form-control" style="width:200px;" @change="applyArticleFilters">
              <option :value="null">Wszystkie kategorie</option>
              <option v-for="cat in archiveStore.categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
            <button class="btn btn-primary btn-sm" @click="applyArticleFilters">Filtruj</button>
            <button class="btn-icon" title="Wyczyść filtry" @click="clearArticleFilters">↺</button>
          </div>

          <div class="grid-scroll">
            <table class="data-grid">
              <thead>
                <tr>
                  <th>Nr wewn.</th>
                  <th>Nazwa</th>
                  <th>Marka/Model</th>
                  <th>Kategoria</th>
                  <th>Wypożyczeń</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="archiveStore.articlesLoading">
                  <td colspan="5" class="empty-state">Ładowanie...</td>
                </tr>
                <tr v-else-if="archiveStore.articlesError">
                  <td colspan="5" class="empty-state error">Błąd: {{ archiveStore.articlesError }}</td>
                </tr>
                <tr v-else-if="!archiveStore.articles.length">
                  <td colspan="5" class="empty-state">Brak maszyn archiwum</td>
                </tr>
                <tr v-for="a in archiveStore.articles" :key="a.id">
                  <td>{{ a.internal_number || '—' }}</td>
                  <td style="font-weight:600;">{{ a.name }}</td>
                  <td>{{ [a.brand, a.model].filter(Boolean).join(' ') || '—' }}</td>
                  <td>
                    <!-- Admin: dropdown edytowalny -->
                    <select
                      v-if="authStore.isAdmin"
                      :value="a.category_id"
                      class="form-control form-control-xs"
                      style="width:200px;"
                      @change="onArticleCategoryChange(a.id, $event)"
                    >
                      <option :value="null">— brak kategorii —</option>
                      <option v-for="cat in archiveStore.categories" :key="cat.id" :value="cat.id">
                        {{ cat.name }}
                      </option>
                    </select>
                    <!-- User: tekst read-only -->
                    <span v-else>{{ categoryName(a.category_id) }}</span>
                  </td>
                  <td>{{ a.contracts_count ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="grid-footer">
            <span>Łącznie: {{ archiveStore.articlesTotal }} maszyn</span>
            <div class="pagination">
              <button class="page-btn" :disabled="archiveStore.articlesPage <= 1" @click="prevArticlesPage">‹</button>
              <span style="padding:0 8px;font-size:12px;">{{ archiveStore.articlesPage }} / {{ articlesTotalPages }}</span>
              <button class="page-btn" :disabled="archiveStore.articlesPage >= articlesTotalPages" @click="nextArticlesPage">›</button>
            </div>
          </div>
        </div>
      </div>

      <!-- STATYSTYKI -->
      <div v-else-if="activeTab === 'stats'" class="tab-pane">
        <div class="stats-filters">
          <label>
            Data od:
            <input v-model="statsDateFrom" type="date" class="form-control" style="width:140px;" />
          </label>
          <label>
            Data do:
            <input v-model="statsDateTo" type="date" class="form-control" style="width:140px;" />
          </label>
          <button class="btn btn-primary btn-sm" @click="loadStats">Odśwież</button>
        </div>

        <div v-if="archiveStore.statsLoading" class="empty-state">Ładowanie statystyk...</div>
        <div v-else-if="archiveStore.statsError" class="empty-state error">Błąd: {{ archiveStore.statsError }}</div>

        <template v-else>
          <!-- Podsumowanie -->
          <div class="stats-card">
            <div class="stats-card-header">📊 Podsumowanie</div>
            <div class="stats-card-body">
              <div class="stat-item">
                <span class="stat-label">Umów</span>
                <span class="stat-value">{{ archiveStore.statsSummary?.contracts_count ?? 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Pozycji</span>
                <span class="stat-value">{{ archiveStore.statsSummary?.positions_count ?? 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Przychód</span>
                <span class="stat-value">
                  {{ formatMoney(archiveStore.statsSummary?.revenue_estimate) }}
                  <span class="est-suffix">[szac.]</span>
                </span>
              </div>
            </div>
          </div>

          <!-- Top maszyny -->
          <div class="stats-card">
            <div class="stats-card-header">🏆 Top maszyny</div>
            <div class="stats-card-body no-pad">
              <table class="data-grid">
                <thead>
                  <tr><th>Nazwa</th><th>Nr wewn.</th><th>Wypożyczeń</th><th>Dni</th><th>Przychód</th></tr>
                </thead>
                <tbody>
                  <tr v-if="!archiveStore.topMachines.length">
                    <td colspan="5" class="empty-state">Brak danych</td>
                  </tr>
                  <tr v-for="m in archiveStore.topMachines" :key="m.article_id">
                    <td>{{ m.article_name }}</td>
                    <td>{{ m.internal_number || '—' }}</td>
                    <td>{{ m.contracts_count }}</td>
                    <td>{{ m.rented_days }}</td>
                    <td>
                      <span class="est-value">{{ formatMoney(m.revenue_estimate) }}</span>
                      <span class="est-suffix">[szac.]</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Kategorie -->
          <div class="stats-card">
            <div class="stats-card-header">📁 Kategorie</div>
            <div class="stats-card-body no-pad">
              <table class="data-grid">
                <thead>
                  <tr><th>Kategoria</th><th>Umów</th><th>Pozycji</th><th>Przychód</th></tr>
                </thead>
                <tbody>
                  <tr v-if="!archiveStore.byCategory.length">
                    <td colspan="4" class="empty-state">Brak danych</td>
                  </tr>
                  <tr v-for="c in archiveStore.byCategory" :key="c.category_id ?? c.category_name">
                    <td>{{ c.category_name }}</td>
                    <td>{{ c.contracts_count }}</td>
                    <td>{{ c.positions_count }}</td>
                    <td>
                      <span class="est-value">{{ formatMoney(c.revenue_estimate) }}</span>
                      <span class="est-suffix">[szac.]</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ROI maszyny -->
          <div class="stats-card">
            <div class="stats-card-header">📈 ROI maszyny</div>
            <div class="stats-card-body">
              <div class="roi-form">
                <label>
                  ID maszyny:
                  <input v-model.number="roiArticleId" type="number" class="form-control" style="width:120px;" placeholder="article_id" />
                </label>
                <button class="btn btn-primary btn-sm" :disabled="!roiArticleId" @click="loadRoi">Oblicz ROI</button>
              </div>

              <div v-if="archiveStore.machineRoi" class="roi-result">
                <div class="stat-item">
                  <span class="stat-label">Maszyna</span>
                  <span class="stat-value">{{ archiveStore.machineRoi.name }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Wartość zakupu</span>
                  <span class="stat-value">{{ formatMoney(archiveStore.machineRoi.replacement_value) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Przychód</span>
                  <span class="stat-value">
                    {{ formatMoney(archiveStore.machineRoi.revenue_estimate) }}
                    <span class="est-suffix">[szac.]</span>
                  </span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">ROI</span>
                  <span class="stat-value roi-value">
                    {{ archiveStore.machineRoi.roi_pct != null ? archiveStore.machineRoi.roi_pct.toFixed(2) + ' %' : '—' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- KATEGORIE (admin: edycja, user: read-only) -->
      <div v-else-if="activeTab === 'categories'" class="tab-pane">
        <div class="grid-container">
          <div v-if="authStore.isAdmin" class="grid-header">
            <input v-model="newCat.name" type="text" class="form-control" placeholder="Nazwa nowej kategorii" style="max-width:240px;" />
            <input v-model="newCat.code" type="text" class="form-control" placeholder="Kod (opcj.)" style="max-width:120px;" />
            <select v-model="newCat.parent_id" class="form-control" style="width:200px;">
              <option :value="null">— kategoria główna —</option>
              <option v-for="cat in flatCategoriesForSelect" :key="cat.id" :value="cat.id">
                {{ '— '.repeat(cat._depth) }}{{ cat.name }}
              </option>
            </select>
            <button class="btn btn-primary btn-sm" @click="addCategory">+ Dodaj kategorię</button>
          </div>
          <div v-else class="grid-header">
            <span class="est-suffix" style="font-size:13px;">Kategorie historyczne (szacunkowe) — read-only</span>
          </div>

          <div class="grid-scroll">
            <table class="data-grid">
              <thead>
                <tr><th>Nazwa</th><th>Kod</th><th>Poziom</th><th v-if="authStore.isAdmin" style="width:120px;"></th></tr>
              </thead>
              <tbody>
                <tr v-if="archiveStore.categoriesLoading">
                  <td :colspan="authStore.isAdmin ? 4 : 3" class="empty-state">Ładowanie...</td>
                </tr>
                <tr v-else-if="!flatCategoryTree.length">
                  <td :colspan="authStore.isAdmin ? 4 : 3" class="empty-state">Brak kategorii archiwum</td>
                </tr>
                <template v-for="cat in flatCategoryTree" :key="cat.id">
                  <tr v-if="editingCatId === cat.id && authStore.isAdmin" class="row-editing">
                    <td :style="{ paddingLeft: (cat._depth * 20 + 8) + 'px' }">
                      <input v-model="editingCatData.name" class="form-control form-control-xs" @keydown.enter="saveEditCat" @keydown.esc="editingCatId = null" />
                    </td>
                    <td><input v-model="editingCatData.code" class="form-control form-control-xs" @keydown.enter="saveEditCat" @keydown.esc="editingCatId = null" /></td>
                    <td style="color:var(--color-text-muted);font-size:11px;">{{ cat.level }}</td>
                    <td>
                      <button class="btn-icon" style="color:var(--color-success);" @click="saveEditCat" title="Zapisz">✓</button>
                      <button class="btn-icon" @click="editingCatId = null" title="Anuluj">✕</button>
                    </td>
                  </tr>
                  <tr v-else>
                    <td :style="{ paddingLeft: (cat._depth * 20 + 8) + 'px' }">
                      <span :style="cat._depth > 0 ? 'color:var(--color-text-muted)' : 'font-weight:600'">
                        {{ cat._depth > 0 ? '└ ' : '' }}{{ cat.name }}
                      </span>
                    </td>
                    <td>{{ cat.code || '—' }}</td>
                    <td style="color:var(--color-text-muted);font-size:11px;">{{ cat.level }}</td>
                    <td v-if="authStore.isAdmin">
                      <button class="btn-icon" @click="startEditCat(cat)" title="Edytuj">✎</button>
                      <button
                        class="btn-icon"
                        :disabled="cat.children && cat.children.length > 0"
                        :title="cat.children && cat.children.length > 0 ? 'Ma podkategorie' : 'Usuń'"
                        @click="deleteCat(cat.id)"
                      >✕</button>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useArchiveStore } from '@/stores/archive'
import { useAuthStore } from '@/stores/auth'
import type {
  ArchiveCategoryPayload,
  ArchiveCategoryTreeNode,
} from '@/stores/archive'

const archiveStore = useArchiveStore()
const authStore = useAuthStore()

// ── Zakładki ─────────────────────────────────────────────────────────────────
type TabId = 'contracts' | 'articles' | 'stats' | 'categories'
const allTabs: { id: TabId; label: string; adminOnly?: boolean }[] = [
  { id: 'contracts', label: 'Umowy' },
  { id: 'articles', label: 'Maszyny' },
  { id: 'stats', label: 'Statystyki' },
  { id: 'categories', label: 'Kategorie' },
]
const visibleTabs = computed(() =>
  allTabs.filter((t) => !t.adminOnly || authStore.isAdmin),
)
const activeTab = ref<TabId>('contracts')

// ── Filtry umów ──────────────────────────────────────────────────────────────
const contractFilters = ref<{
  search: string
  contract_type: 'S' | 'U' | null
  date_from: string | null
  date_to: string | null
}>({
  search: '',
  contract_type: null,
  date_from: null,
  date_to: null,
})
const contractsPerPageLocal = ref(50)
const selectedContractId = ref<number | null>(null)

const contractsTotalPages = computed(() =>
  Math.max(1, Math.ceil(archiveStore.contractsTotal / archiveStore.contractsPerPage)),
)

async function applyContractFilters() {
  archiveStore.contractsPage = 1
  await archiveStore.fetchContracts({
    search: contractFilters.value.search || undefined,
    contract_type: contractFilters.value.contract_type ?? undefined,
    date_from: contractFilters.value.date_from,
    date_to: contractFilters.value.date_to,
    page: 1,
    per_page: contractsPerPageLocal.value,
  })
}

function clearContractFilters() {
  contractFilters.value = { search: '', contract_type: null, date_from: null, date_to: null }
  void applyContractFilters()
}

async function changeContractsPerPage() {
  await applyContractFilters()
}

async function prevContractsPage() {
  if (archiveStore.contractsPage <= 1) return
  await archiveStore.fetchContracts({
    ...contractFilters.value,
    page: archiveStore.contractsPage - 1,
    per_page: contractsPerPageLocal.value,
  })
}

async function nextContractsPage() {
  if (archiveStore.contractsPage >= contractsTotalPages.value) return
  await archiveStore.fetchContracts({
    ...contractFilters.value,
    page: archiveStore.contractsPage + 1,
    per_page: contractsPerPageLocal.value,
  })
}

async function toggleContractDetails(id: number) {
  if (selectedContractId.value === id) {
    selectedContractId.value = null
    archiveStore.currentContract = null
    return
  }
  selectedContractId.value = id
  try {
    await archiveStore.fetchContract(id)
  } catch {
    selectedContractId.value = null
  }
}

// ── Filtry artykułów ─────────────────────────────────────────────────────────
const articleFilters = ref<{ search: string; category_id: number | null }>({
  search: '',
  category_id: null,
})

const articlesTotalPages = computed(() =>
  Math.max(1, Math.ceil(archiveStore.articlesTotal / archiveStore.articlesPerPage)),
)

async function applyArticleFilters() {
  archiveStore.articlesPage = 1
  await archiveStore.fetchArticles({
    search: articleFilters.value.search || undefined,
    category_id: articleFilters.value.category_id ?? undefined,
    page: 1,
  })
}

function clearArticleFilters() {
  articleFilters.value = { search: '', category_id: null }
  void applyArticleFilters()
}

async function prevArticlesPage() {
  if (archiveStore.articlesPage <= 1) return
  await archiveStore.fetchArticles({
    ...articleFilters.value,
    page: archiveStore.articlesPage - 1,
  })
}

async function nextArticlesPage() {
  if (archiveStore.articlesPage >= articlesTotalPages.value) return
  await archiveStore.fetchArticles({
    ...articleFilters.value,
    page: archiveStore.articlesPage + 1,
  })
}

async function onArticleCategoryChange(articleId: number, event: Event) {
  const target = event.target as HTMLSelectElement
  const categoryId = target.value ? Number(target.value) : null
  try {
    await archiveStore.updateArticleCategory(articleId, categoryId)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err?.response?.data?.detail ?? 'Błąd zmiany kategorii')
    // Odśwież listę aby przywrócić poprawny stan
    void applyArticleFilters()
  }
}

function categoryName(categoryId: number | null): string {
  if (categoryId == null) return '—'
  const cat = archiveStore.categories.find((c) => c.id === categoryId)
  return cat?.name ?? '—'
}

// ── Statystyki ───────────────────────────────────────────────────────────────
const statsDateFrom = ref<string | null>(null)
const statsDateTo = ref<string | null>(null)
const roiArticleId = ref<number | null>(null)

async function loadStats() {
  try {
    await archiveStore.fetchAllStats(statsDateFrom.value, statsDateTo.value)
  } catch {
    // error już w store.statsError
  }
}

async function loadRoi() {
  if (!roiArticleId.value) return
  try {
    await archiveStore.fetchMachineRoi(roiArticleId.value, statsDateFrom.value, statsDateTo.value)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err?.response?.data?.detail ?? 'Błąd pobierania ROI')
  }
}

// ── Kategorie (admin) ────────────────────────────────────────────────────────
const newCat = ref<{ name: string; code: string; parent_id: number | null }>({
  name: '',
  code: '',
  parent_id: null,
})
const editingCatId = ref<number | null>(null)
const editingCatData = ref<{ name: string; code: string }>({ name: '', code: '' })

const flatCategoryTree = computed<Array<ArchiveCategoryTreeNode & { _depth: number }>>(() => {
  const result: Array<ArchiveCategoryTreeNode & { _depth: number }> = []
  function flatten(nodes: ArchiveCategoryTreeNode[], depth: number) {
    for (const node of nodes) {
      result.push({ ...node, _depth: depth })
      if (node.children && node.children.length) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(archiveStore.categoriesTree, 0)
  return result
})

const flatCategoriesForSelect = computed(() =>
  flatCategoryTree.value.filter((c) => c.level !== 'sub3'),
)

function levelFor(parent: ArchiveCategoryTreeNode & { _depth: number } | null): 'main' | 'sub1' | 'sub2' | 'sub3' {
  if (!parent) return 'main'
  const map: Record<string, 'main' | 'sub1' | 'sub2' | 'sub3'> = {
    main: 'sub1',
    sub1: 'sub2',
    sub2: 'sub3',
    sub3: 'sub3',
  }
  return map[parent.level] ?? 'sub1'
}

async function addCategory() {
  if (!newCat.value.name.trim()) return
  const parent = newCat.value.parent_id
    ? flatCategoryTree.value.find((c) => c.id === newCat.value.parent_id) ?? null
    : null
  const payload: ArchiveCategoryPayload = {
    name: newCat.value.name.trim(),
    code: newCat.value.code || null,
    parent_id: newCat.value.parent_id,
    level: levelFor(parent),
  }
  try {
    await archiveStore.createCategory(payload)
    newCat.value = { name: '', code: '', parent_id: null }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err?.response?.data?.detail ?? 'Błąd dodawania kategorii')
  }
}

function startEditCat(cat: ArchiveCategoryTreeNode & { _depth: number }) {
  editingCatId.value = cat.id
  editingCatData.value = { name: cat.name, code: cat.code ?? '' }
}

async function saveEditCat() {
  if (!editingCatId.value || !editingCatData.value.name.trim()) return
  const cat = flatCategoryTree.value.find((c) => c.id === editingCatId.value)
  if (!cat) return
  const payload: ArchiveCategoryPayload = {
    name: editingCatData.value.name.trim(),
    code: editingCatData.value.code || null,
    parent_id: cat.parent_id,
    level: (cat.level as 'main' | 'sub1' | 'sub2' | 'sub3'),
  }
  try {
    await archiveStore.updateCategory(editingCatId.value, payload)
    editingCatId.value = null
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err?.response?.data?.detail ?? 'Błąd zapisu kategorii')
  }
}

async function deleteCat(id: number) {
  if (!confirm('Usunąć tę kategorię? Operacja nieodwracalna.')) return
  try {
    await archiveStore.deleteCategory(id)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    alert(err?.response?.data?.detail ?? 'Błąd usuwania kategorii')
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(d: string | null | undefined): string {
  if (!d) return '—'
  try {
    return new Date(d).toLocaleDateString('pl-PL')
  } catch {
    return String(d)
  }
}

function formatMoney(v: string | number | null | undefined): string {
  if (v == null || v === '') return '—'
  const num = typeof v === 'string' ? parseFloat(v) : v
  if (isNaN(num)) return '—'
  return num.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł'
}

// ── Ładowanie danych przy zmianie zakładki ───────────────────────────────────
async function loadTabData(tab: TabId) {
  try {
    if (tab === 'contracts' && !archiveStore.contracts.length) {
      await archiveStore.fetchContracts({ page: 1, per_page: contractsPerPageLocal.value })
    } else if (tab === 'articles') {
      if (!archiveStore.articles.length) {
        await archiveStore.fetchArticles({ page: 1 })
      }
      if (!archiveStore.categories.length) {
        await archiveStore.fetchCategories()
      }
    } else if (tab === 'stats') {
      if (!archiveStore.statsSummary) {
        await loadStats()
      }
    } else if (tab === 'categories') {
      if (!archiveStore.categoriesTree.length) {
        await archiveStore.fetchCategoriesTree()
      }
    }
  } catch {
    // błędy są w store
  }
}

watch(activeTab, (tab) => {
  void loadTabData(tab)
})

onMounted(() => {
  void loadTabData('contracts')
})
</script>

<style scoped>
.archive-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--color-bg-light);
  font-family: var(--font-family);
}

/* ── Banner ─────────────────────────────────────────────────────────────────── */
.archive-banner {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-5);
  background: var(--color-bg-light);
  border-left: 4px solid var(--color-warning);
  border-bottom: 1px solid rgba(245, 158, 11, 0.3);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
}
.banner-icon {
  font-size: var(--font-size-md);
  color: var(--color-warning);
}
.banner-text strong {
  color: var(--color-text-heading);
}

/* ── Tabs ───────────────────────────────────────────────────────────────────── */
.archive-tabs {
  display: flex;
  gap: 2px;
  padding: 0 var(--spacing-5);
  background: var(--color-bg-white);
  border-bottom: 1px solid var(--color-border);
}
.archive-tab {
  padding: var(--spacing-3) var(--spacing-5);
  border: none;
  background: transparent;
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.archive-tab:hover {
  color: var(--color-primary);
}
.archive-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

/* ── Content ────────────────────────────────────────────────────────────────── */
.archive-content {
  flex: 1;
  overflow: auto;
  padding: var(--spacing-5);
}
.tab-pane {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

/* ── Szacunkowe wartości (kreska — przekreślone) ───────────────────────────── */
.est-value {
  color: var(--color-text-muted);
  font-weight: var(--font-weight-medium);
  text-decoration: line-through;
  text-decoration-color: var(--color-warning);
  text-decoration-thickness: 2px;
}
.est-suffix {
  color: var(--color-warning);
  font-size: var(--font-size-xs);
  margin-left: 4px;
  font-weight: var(--font-weight-semibold);
}

/* ── Contract details ───────────────────────────────────────────────────────── */
.contract-details {
  margin-top: var(--spacing-4);
  background: var(--color-bg-white);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-5);
}
.details-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-4);
}
.details-header h3 {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--color-primary);
}
.details-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-5);
  font-size: var(--font-size-sm);
}
.details-grid strong {
  color: var(--color-text-heading);
}
.details-table {
  margin-top: var(--spacing-2);
  margin-bottom: var(--spacing-5);
}
h4 {
  font-size: var(--font-size-base);
  color: var(--color-primary);
  margin: var(--spacing-4) 0 var(--spacing-2);
}

/* ── Stats ──────────────────────────────────────────────────────────────────── */
.stats-filters {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-bg-white);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  font-size: var(--font-size-sm);
}
.stats-filters label {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--color-text-body);
}

.stats-card {
  background: var(--color-bg-white);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.stats-card-header {
  padding: var(--spacing-3) var(--spacing-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  border-bottom: 1px solid var(--color-border);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.stats-card-body {
  padding: var(--spacing-4);
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-5);
}
.stats-card-body.no-pad {
  padding: 0;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 140px;
}
.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.stat-value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
}
.roi-value {
  color: var(--color-warning);
}

.roi-form {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}
.roi-result {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-5);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border);
}

/* ── Error state ────────────────────────────────────────────────────────────── */
.empty-state.error {
  color: var(--color-error);
}

/* ── Form control xs (inline edit) ──────────────────────────────────────────── */
.form-control-xs {
  padding: 4px 8px;
  font-size: var(--font-size-xs);
}
</style>
