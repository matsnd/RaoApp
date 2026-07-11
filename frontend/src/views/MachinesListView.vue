<template>
  <div style="display:flex;flex-direction:column;height:100%;overflow:hidden;">
    <AppToolbar
      info-text="Maszyny"
      @add="handleAdd"
      @remove="handleRemove"
    />
    <div class="content-area" style="padding:var(--spacing-md);">
      <div class="grid-container">
        <div class="grid-header">
          <div class="search-input-wrap" style="flex:1;max-width:380px;">
            <span class="search-icon">⌕</span>
            <input v-model="search" type="text" class="form-control" placeholder="Szukaj wg nazwy, numeru..." aria-label="Szukaj maszyn" />
          </div>
          <select v-model="categoryFilter" class="form-control" style="width:200px;" aria-label="Filtr kategorii">
            <option value="">Wszystkie kategorie</option>
            <option v-for="c in categoryOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <label class="toggle-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;font-size:13px;color:var(--color-text-body);">
            <input v-model="archivalFilter" type="checkbox" true-value="archival" false-value="active" style="accent-color:var(--color-primary);width:16px;height:16px;" />
            Archiwalne
          </label>
        </div>
        <div class="grid-scroll">
          <table class="data-grid" role="table" aria-label="Lista maszyn">
            <thead>
              <tr role="row">
                <th class="th-sortable" role="columnheader" @click="toggleSort('name')">Nazwa <span class="sort-indicator">{{ sortIndicator('name') }}</span></th>
                <th class="th-sortable" role="columnheader" @click="toggleSort('internal_number')">Nr wew. <span class="sort-indicator">{{ sortIndicator('internal_number') }}</span></th>
                <th class="th-sortable" role="columnheader" @click="toggleSort('registration_no')">Nr rej. <span class="sort-indicator">{{ sortIndicator('registration_no') }}</span></th>
                <th class="th-sortable" role="columnheader" @click="toggleSort('brand')">Marka <span class="sort-indicator">{{ sortIndicator('brand') }}</span></th>
                <th role="columnheader">Kategoria</th>
                <th role="columnheader">Zasilanie</th>
                <th role="columnheader">Aktywna umowa</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="store.loading" role="row">
                <td colspan="7" role="cell"><SkeletonRow :cols="7" label="Ładowanie maszyn" /></td>
              </tr>
              <tr v-else-if="loadError" role="row">
                <td colspan="7" role="cell"><StateMessage type="error" compact :message="loadError" @action="loadData" /></td>
              </tr>
              <tr v-else-if="!store.list.length" role="row">
                <td colspan="7" role="cell">
                  <StateMessage
                    v-if="archivalFilter === 'active'"
                    type="empty" compact message="Brak maszyn"
                    action-label="+ Nowa maszyna"
                    @action="router.push({ name: 'MachineNew' })"
                  />
                  <StateMessage v-else type="empty" compact message="Brak maszyn archiwalnych" />
                </td>
              </tr>
              <tr v-else-if="!sortedMachines.length" role="row">
                <td colspan="7" role="cell"><StateMessage type="empty" compact message="Brak maszyn spełniających filtry" /></td>
              </tr>
              <tr
                v-for="m in sortedMachines"
                :key="m.id"
                role="row"
                tabindex="0"
                :aria-label="`Maszyna ${m.name}`"
                :class="['article-row', { selected: selectedId === m.id, 'row-archival': m.is_archival }]"
                @click="selectedId = m.id"
                @dblclick="editMachine(m.id)"
                @keydown.enter.prevent="editMachine(m.id)"
              >
                <td role="cell">{{ m.name }}</td>
                <td role="cell">{{ m.internal_number || '—' }}</td>
                <td role="cell">{{ m.registration_no || '—' }}</td>
                <td role="cell">{{ m.brand || '—' }}</td>
                <td role="cell">{{ m.category_name || '—' }}</td>
                <td role="cell">{{ powerTypeLabel(m.power_type) }}</td>
                <td role="cell">{{ m.active_contract_number || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="grid-footer">
          <span>Łącznie: {{ store.total }} maszyn{{ sortedMachines.length !== store.list.length ? ' (' + sortedMachines.length + ' po filtrach)' : '' }}</span>
          <div class="pagination">
            <button class="page-btn" :disabled="page <= 1" aria-label="Poprzednia strona" @click="page--">‹</button>
            <span style="padding:0 8px;font-size:12px;" aria-current="page">{{ page }} / {{ totalPages }}</span>
            <button class="page-btn" :disabled="page >= totalPages" aria-label="Następna strona" @click="page++">›</button>
          </div>
        </div>
      </div>
    </div>

    <ConfirmDialog
      :visible="showConfirm"
      title="Usuń maszynę"
      message="Czy na pewno chcesz usunąć tę maszynę? Tej operacji nie można cofnąć."
      @confirm="confirmDelete"
      @cancel="showConfirm = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppToolbar from '@/components/layout/AppToolbar.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import StateMessage from '@/components/StateMessage.vue'
import SkeletonRow from '@/components/SkeletonRow.vue'
import { useMachineStore } from '@/stores/machines'
import { useSettingsStore } from '@/stores/settings'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const store = useMachineStore()
const settingsStore = useSettingsStore()
const toastStore = useToastStore()

const search = ref('')
const categoryFilter = ref<number | string>('')
const archivalFilter = ref('active')
const selectedId = ref<number | null>(null)
const page = ref(1)
const perPage = 50
const showConfirm = ref(false)
const loadError = ref('')
const sortKey = ref('name')
const sortDir = ref('asc')

const categoryOptions = computed(() => settingsStore.categoriesTree || [])

const totalPages = computed(() => Math.ceil(store.total / perPage) || 1)

async function loadData() {
  selectedId.value = null
  loadError.value = ''
  const params: Record<string, any> = { page: page.value, per_page: perPage }
  if (search.value) params.search = search.value
  if (archivalFilter.value === 'archival') params.archival_status = 'archival'
  try {
    await store.fetchList(params)
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Nie udało się pobrać maszyn'
  }
}

onMounted(async () => {
  if (!settingsStore.categoriesTree.length) {
    try { await settingsStore.fetchCategoriesTree() } catch {}
  }
  loadData()
})

let searchTimer: any = null
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadData() }, 400)
})
watch(archivalFilter, () => { page.value = 1; loadData() })
watch(page, loadData)

onUnmounted(() => { if (searchTimer) clearTimeout(searchTimer) })

function handleAdd() { router.push({ name: 'MachineNew' }) }
function handleRemove() { if (selectedId.value) showConfirm.value = true }

async function confirmDelete() {
  showConfirm.value = false
  if (!selectedId.value) return
  try {
    await store.remove(selectedId.value)
    toastStore.success('Maszyna usunięta')
    await loadData()
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd usuwania')
  }
}

function editMachine(id: number) { router.push(`/machines/${id}/edit`) }

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}
function sortIndicator(key: string) {
  if (sortKey.value !== key) return ''
  return sortDir.value === 'asc' ? '▲' : '▼'
}
function compareValues(a: any, b: any) {
  const av = a ?? ''
  const bv = b ?? ''
  if (typeof av === 'number' && typeof bv === 'number') return av - bv
  const as = String(av).toLowerCase()
  const bs = String(bv).toLowerCase()
  return as < bs ? -1 : as > bs ? 1 : 0
}
const sortedMachines = computed(() => {
  let list = store.list
  if (categoryFilter.value) {
    list = list.filter((m: any) => m.category_id === categoryFilter.value)
  }
  if (!sortKey.value) return list
  const sorted = [...list].sort((a, b) => compareValues(a[sortKey.value], b[sortKey.value]))
  return sortDir.value === 'desc' ? sorted.reverse() : sorted
})

function powerTypeLabel(pt: string) {
  if (pt === 'diesel') return 'Diesel'
  if (pt === 'electric') return 'Elektryk'
  if (pt === 'other') return 'Inny'
  return '—'
}
</script>
