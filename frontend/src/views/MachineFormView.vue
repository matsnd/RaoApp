<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack" title="Wstecz" aria-label="Wstecz">← Wstecz</button>
      <span class="toolbar-info">{{ isEdit ? `Edycja maszyny: ${form.name}` : 'Nowa maszyna' }}</span>
      <button v-if="isEdit" class="toolbar-btn" title="Duplikuj" aria-label="Duplikuj maszynę" @click="handleDuplicate">⎘</button>
      <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="saving">
        {{ saving ? '...' : 'Zapisz' }}
      </button>
    </div>

    <div class="content-area">
      <div v-if="loading" class="empty-state">Ładowanie...</div>
      <div v-else class="page-card" style="max-width:800px;">
        <div v-if="errorMsg" style="color:var(--color-danger);padding:8px;background:#FED7D7;border-radius:6px;margin-bottom:12px;font-size:13px;" role="alert">{{ errorMsg }}</div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-name">Nazwa maszyny *</label>
            <input id="machine-name" v-model="form.name" type="text" class="form-control" :class="{ error: fieldErrors.name }" :aria-invalid="!!fieldErrors.name" aria-describedby="machine-name-error" placeholder="Np. Koparka gąsienicowa" required />
            <span v-if="fieldErrors.name" class="field-error" id="machine-name-error" role="alert">{{ fieldErrors.name }}</span>
          </div>
          <div class="form-group">
            <label class="checkbox-group">
              <input type="checkbox" v-model="form.is_external" />
              <span>Maszyna zewnętrzna (nie wliczana do floty własnej)</span>
            </label>
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-internal">Nr wewnętrzny</label>
            <input id="machine-internal" v-model="form.internal_number" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label" for="machine-reg">Nr rejestracyjny</label>
            <input id="machine-reg" v-model="form.registration_no" type="text" class="form-control" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-serial">Nr seryjny</label>
            <input id="machine-serial" v-model="form.serial_no" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label" for="machine-replacement">Wartość odtworzeniowa (zł)</label>
            <input id="machine-replacement" v-model="form.replacement_value" type="number" step="0.01" class="form-control" :class="{ error: fieldErrors.replacement_value }" :aria-invalid="!!fieldErrors.replacement_value" aria-describedby="machine-replacement-error" />
            <span v-if="fieldErrors.replacement_value" class="field-error" id="machine-replacement-error" role="alert">{{ fieldErrors.replacement_value }}</span>
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-brand">Marka</label>
            <input id="machine-brand" v-model="form.brand" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label" for="machine-model">Model</label>
            <input id="machine-model" v-model="form.model" type="text" class="form-control" />
          </div>
        </div>

        <div class="section-title" style="font-size:var(--font-size-sm);margin-top:var(--spacing-4);margin-bottom:var(--spacing-3);padding-bottom:var(--spacing-2);">Dane techniczne</div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-reach">Zasięg (m)</label>
            <input id="machine-reach" v-model.number="form.reach_m" type="number" class="form-control" min="0" step="0.1" placeholder="np. 21.5" />
          </div>
          <div class="form-group">
            <label class="form-label" for="machine-capacity">Udźwig (t)</label>
            <input id="machine-capacity" v-model.number="form.capacity_t" type="number" class="form-control" min="0" step="0.1" placeholder="np. 5.0" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-power-type">Typ zasilania</label>
            <select id="machine-power-type" v-model="form.power_type" class="form-control" data-testid="machine-power-type">
              <option value="diesel">Diesel</option>
              <option value="electric">Elektryk</option>
              <option value="other">Inny</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" for="machine-accessories">Dodatkowe wyposażenie</label>
            <textarea id="machine-accessories" v-model="form.accessories" class="form-control" rows="2" placeholder="np. Kosz osobowy, wciągarka..."></textarea>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="machine-technical-attrs">Atrybuty techniczne</label>
          <textarea id="machine-technical-attrs" v-model="form.technical_attributes" class="form-control" rows="3" placeholder="Dodatkowe parametry techniczne (dowolny tekst)"></textarea>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-cat-main">Kategoria</label>
            <div style="display:flex;flex-direction:column;gap:4px;">
              <select id="machine-cat-main" v-model="catSelectedMain" class="form-control" @change="catSelectedSub1 = null; catSelectedSub2 = null">
                <option :value="null">— brak kategorii —</option>
                <option v-for="c in catMainOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
              <select v-if="catSub1Options.length" v-model="catSelectedSub1" class="form-control" aria-label="Podkategoria poziom 1" @change="catSelectedSub2 = null">
                <option :value="null">— (poziom główny) —</option>
                <option v-for="c in catSub1Options" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
              <select v-if="catSub2Options.length" v-model="catSelectedSub2" class="form-control" aria-label="Podkategoria poziom 2">
                <option :value="null">— (poziom podrzędny) —</option>
                <option v-for="c in catSub2Options" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label" for="machine-owner-display">Właściciel (dostawca)</label>
            <div style="display:flex;gap:8px;">
              <input id="machine-owner-display" :value="ownerName" type="text" class="form-control" disabled placeholder="— własny —" style="flex:1;" />
              <button type="button" class="btn btn-secondary btn-sm" @click="showOwnerPicker = true">Wybierz</button>
              <button v-if="form.owner_id" type="button" class="btn btn-secondary btn-sm" @click="clearOwner" aria-label="Wyczyść właściciela">✕</button>
            </div>
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="machine-rental-days">Min. dni najmu</label>
            <input id="machine-rental-days" v-model.number="form.rental_days" type="number" class="form-control" :class="{ error: fieldErrors.rental_days }" :aria-invalid="!!fieldErrors.rental_days" aria-describedby="machine-rental-days-error" min="1" />
            <span v-if="fieldErrors.rental_days" class="field-error" id="machine-rental-days-error" role="alert">{{ fieldErrors.rental_days }}</span>
          </div>
          <div class="form-group">
            <label class="form-label" for="machine-branch">Filia</label>
            <select id="machine-branch" v-model="form.branch_id" class="form-control">
              <option :value="null">— główna —</option>
              <option v-for="br in settingsStore.branches" :key="br.id" :value="br.id">{{ br.name }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="machine-description">Opis</label>
          <textarea id="machine-description" v-model="form.description" class="form-control" rows="3"></textarea>
        </div>

        <div class="form-group">
          <label class="form-label" for="machine-notes">Uwagi</label>
          <textarea id="machine-notes" v-model="form.notes" class="form-control" rows="2"></textarea>
        </div>
      </div>
    </div>

    <!-- Owner picker modal -->
    <Transition name="modal">
      <div v-if="showOwnerPicker" class="modal-overlay" @click.self="showOwnerPicker = false">
        <div class="modal-box" style="min-width:580px;" role="dialog" aria-modal="true" aria-labelledby="owner-picker-title">
          <div class="modal-title" id="owner-picker-title">Wybierz właściciela (dostawcę)</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon" aria-hidden="true">⌕</span>
            <input v-model="pickerSearch" type="text" class="form-control" aria-label="Szukaj właściciela" placeholder="Szukaj..." @input="searchOwners" />
          </div>
          <div style="max-height:320px;overflow:auto;">
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>NIP</th><th>Miasto</th></tr></thead>
              <tbody>
                <tr v-for="c in pickerList" :key="c.id" @click="selectOwner(c)" style="cursor:pointer;">
                  <td>{{ c.name }}</td><td>{{ c.nip || '—' }}</td><td>{{ c.city || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showOwnerPicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useMachineStore } from '@/stores/machines'
import { useSettingsStore } from '@/stores/settings'
import { useToastStore } from '@/stores/toast'
import { extractErrorMessage } from '@/utils/validation'

import api from '@/composables/useApi'

const props = defineProps({ id: String })
const router = useRouter()
const store = useMachineStore()
const settingsStore = useSettingsStore()
const toastStore = useToastStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const fieldErrors = ref<Record<string, string>>({})
const ownerName = ref('')

const form = ref({
  name: '',
  internal_number: '',
  registration_no: '',
  serial_no: '',
  brand: '',
  model: '',
  replacement_value: null as number | null,
  category_id: null as number | null,
  owner_id: null as number | null,
  branch_id: null as number | null,
  description: '',
  notes: '',
  rental_days: null as number | null,
  reach_m: null as number | null,
  capacity_t: null as number | null,
  accessories: '',
  technical_attributes: '',
  is_external: false,
  power_type: 'other',
})

const showOwnerPicker = ref(false)
const pickerSearch = ref('')
const pickerList = ref<any[]>([])

// --- Cascade category pickers ---
const catSelectedMain = ref<number | null>(null)
const catSelectedSub1 = ref<number | null>(null)
const catSelectedSub2 = ref<number | null>(null)

const catMainOptions = computed(() => settingsStore.categoriesTree)
const catSub1Options = computed(() => {
  if (!catSelectedMain.value) return []
  return catMainOptions.value.find(c => c.id === catSelectedMain.value)?.children || []
})
const catSub2Options = computed(() => {
  if (!catSelectedSub1.value) return []
  return catSub1Options.value.find(c => c.id === catSelectedSub1.value)?.children || []
})

watch([catSelectedMain, catSelectedSub1, catSelectedSub2], () => {
  form.value.category_id = catSelectedSub2.value ?? catSelectedSub1.value ?? catSelectedMain.value
})

function findCatPath(tree: any[], id: number, path: any[] = []): any[] | null {
  for (const node of tree) {
    const newPath = [...path, node]
    if (node.id === id) return newPath
    if (node.children?.length) {
      const found = findCatPath(node.children, id, newPath)
      if (found) return found
    }
  }
  return null
}

function setCategoryFromId(categoryId: number | null) {
  if (!categoryId || !settingsStore.categoriesTree.length) {
    catSelectedMain.value = null
    catSelectedSub1.value = null
    catSelectedSub2.value = null
    return
  }
  const path = findCatPath(settingsStore.categoriesTree, categoryId)
  if (!path) return
  catSelectedMain.value = path[0]?.id || null
  catSelectedSub1.value = path[1]?.id || null
  catSelectedSub2.value = path[2]?.id || null
}

onMounted(async () => {
  await Promise.all([settingsStore.fetchCategoriesTree(), settingsStore.fetchBranches(), settingsStore.fetchRateTypes()])

  const { data } = await api.get('/contractors', { params: { supplier: true, per_page: 50 } })
  pickerList.value = data.items

  if (isEdit.value) {
    loading.value = true
    try {
      const data = await store.fetchOne(Number(props.id))
      Object.assign(form.value, data)
      if (data.owner_name) ownerName.value = data.owner_name
      setCategoryFromId(data.category_id)
    } finally {
      loading.value = false
    }
  }
})

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/machines')
  }
}

function validateForm() {
  fieldErrors.value = {}
  const errors: Record<string, string> = {}
  if (!form.value.name || !form.value.name.trim()) {
    errors.name = 'Podaj nazwę maszyny'
  }
  if (form.value.replacement_value !== null && form.value.replacement_value !== '' && form.value.replacement_value !== undefined) {
    const v = Number(form.value.replacement_value)
    if (Number.isNaN(v) || v < 0) {
      errors.replacement_value = 'Wartość odtworzeniowa musi być liczbą nieujemną'
    }
  }
  if (form.value.rental_days !== null && form.value.rental_days !== '' && form.value.rental_days !== undefined) {
    const d = Number(form.value.rental_days)
    if (Number.isNaN(d) || d < 1) {
      errors.rental_days = 'Min. dni najmu musi być liczbą >= 1'
    }
  }
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function handleSave() {
  if (!validateForm()) return
  if (!form.value.name) { errorMsg.value = 'Podaj nazwę maszyny'; return }
  saving.value = true
  errorMsg.value = ''
  try {
    const payload: Record<string, any> = { ...form.value }
    if (!payload.replacement_value) payload.replacement_value = null
    if (!payload.rental_days) payload.rental_days = null
    if (!payload.reach_m) payload.reach_m = null
    if (!payload.capacity_t) payload.capacity_t = null
    if (!payload.accessories) payload.accessories = null
    if (!payload.technical_attributes) payload.technical_attributes = null

    if (isEdit.value && props.id) {
      await store.update(Number(props.id), payload)
    } else {
      const result = await store.create(payload)
      router.push(`/machines/${result.id}/edit`)
      return
    }
  } catch (e: any) {
    errorMsg.value = extractErrorMessage(e, 'Błąd zapisu maszyny')
  } finally {
    saving.value = false
  }
}

async function handleDuplicate() {
  if (!isEdit.value) return
  try {
    const result = await store.duplicate(Number(props.id))
    router.push(`/machines/${result.id}/edit`)
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd duplikacji')
  }
}

let ownerTimer: any = null
async function searchOwners() {
  if (ownerTimer) clearTimeout(ownerTimer)
  ownerTimer = setTimeout(async () => {
    const { data } = await api.get('/contractors', { params: { search: pickerSearch.value, per_page: 50 } })
    pickerList.value = data.items
  }, 300)
}

onUnmounted(() => {
  if (ownerTimer) clearTimeout(ownerTimer)
})

function selectOwner(c: any) {
  form.value.owner_id = c.id
  ownerName.value = c.name
  showOwnerPicker.value = false
}

function clearOwner() {
  form.value.owner_id = null
  ownerName.value = ''
}
</script>

<style scoped>
.field-error {
  display: block;
  color: var(--color-error);
  font-size: 12px;
  margin-top: 4px;
  font-weight: 500;
}
.form-control.error {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}
</style>
