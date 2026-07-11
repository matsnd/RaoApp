<template>
  <div style="display:flex;flex-direction:column;height:100%;overflow:hidden;">
    <AppToolbar
      info-text="Usługi"
      @add="handleAdd"
      @remove="handleRemove"
    />
    <div class="content-area" style="padding:var(--spacing-md);">
      <div class="grid-container">
        <div class="grid-header">
          <div class="search-input-wrap" style="flex:1;max-width:380px;">
            <span class="search-icon">⌕</span>
            <input v-model="search" type="text" class="form-control" placeholder="Szukaj wg nazwy, numeru..." aria-label="Szukaj usług" />
          </div>
        </div>
        <div class="grid-scroll">
          <table class="data-grid" role="table" aria-label="Lista usług">
            <thead>
              <tr role="row">
                <th class="th-sortable" role="columnheader" @click="toggleSort('name')">Nazwa <span class="sort-indicator">{{ sortIndicator('name') }}</span></th>
                <th class="th-sortable" role="columnheader" @click="toggleSort('internal_number')">Nr wew. <span class="sort-indicator">{{ sortIndicator('internal_number') }}</span></th>
                <th role="columnheader">Kategoria</th>
                <th role="columnheader">Aktywna umowa</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="store.loading" role="row">
                <td colspan="4" role="cell"><SkeletonRow :cols="4" label="Ładowanie usług" /></td>
              </tr>
              <tr v-else-if="loadError" role="row">
                <td colspan="4" role="cell"><StateMessage type="error" compact :message="loadError" @action="loadData" /></td>
              </tr>
              <tr v-else-if="!store.list.length" role="row">
                <td colspan="4" role="cell">
                  <StateMessage type="empty" compact message="Brak usług"
                    action-label="+ Nowa usługa"
                    @action="router.push({ name: 'ServiceNew' })"
                  />
                </td>
              </tr>
              <tr v-else-if="!sortedServices.length" role="row">
                <td colspan="4" role="cell"><StateMessage type="empty" compact message="Brak usług spełniających filtry" /></td>
              </tr>
              <tr
                v-for="s in sortedServices"
                :key="s.id"
                role="row"
                tabindex="0"
                :aria-label="`Usługa ${s.name}`"
                :class="['article-row', { selected: selectedId === s.id }]"
                @click="selectedId = s.id"
                @dblclick="editService(s.id)"
                @keydown.enter.prevent="editService(s.id)"
              >
                <td role="cell">{{ s.name }}</td>
                <td role="cell">{{ s.internal_number || '—' }}</td>
                <td role="cell">{{ s.category_name || '—' }}</td>
                <td role="cell">{{ s.active_contract_number || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="grid-footer">
          <span>Łącznie: {{ store.total }} usług{{ sortedServices.length !== store.list.length ? ' (' + sortedServices.length + ' po filtrach)' : '' }}</span>
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
      title="Usuń usługę"
      message="Czy na pewno chcesz usunąć tę usługę? Tej operacji nie można cofnąć."
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
import { useServiceStore } from '@/stores/services'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const store = useServiceStore()
const toastStore = useToastStore()

const search = ref('')
const selectedId = ref<number | null>(null)
const page = ref(1)
const perPage = 50
const showConfirm = ref(false)
const loadError = ref('')
const sortKey = ref('name')
const sortDir = ref('asc')

const totalPages = computed(() => Math.ceil(store.total / perPage) || 1)

async function loadData() {
  selectedId.value = null
  loadError.value = ''
  const params: Record<string, any> = { page: page.value, per_page: perPage }
  if (search.value) params.search = search.value
  try {
    await store.fetchList(params)
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || e?.message || 'Nie udało się pobrać usług'
  }
}

onMounted(() => { loadData() })

let searchTimer: any = null
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadData() }, 400)
})
watch(page, loadData)

onUnmounted(() => { if (searchTimer) clearTimeout(searchTimer) })

function handleAdd() { router.push({ name: 'ServiceNew' }) }
function handleRemove() { if (selectedId.value) showConfirm.value = true }

async function confirmDelete() {
  showConfirm.value = false
  if (!selectedId.value) return
  try {
    await store.remove(selectedId.value)
    toastStore.success('Usługa usunięta')
    await loadData()
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd usuwania')
  }
}

function editService(id: number) { router.push(`/services/${id}/edit`) }

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
const sortedServices = computed(() => {
  const list = store.list
  if (!sortKey.value) return list
  const sorted = [...list].sort((a, b) => compareValues(a[sortKey.value], b[sortKey.value]))
  return sortDir.value === 'desc' ? sorted.reverse() : sorted
})
</script>
