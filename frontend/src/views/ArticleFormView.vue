<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack">←</button>
      <span class="toolbar-info">{{ isEdit ? `Edycja artykułu: ${form.name}` : 'Nowy artykuł' }}</span>
      <button v-if="isEdit" class="toolbar-btn" title="Duplikuj" @click="handleDuplicate">⎘</button>
      <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="saving">
        {{ saving ? '...' : 'Zapisz' }}
      </button>
    </div>

    <div class="content-area">
      <div v-if="loading" class="empty-state">Ładowanie...</div>
      <div v-else class="page-card" style="max-width:800px;">
        <div v-if="errorMsg" style="color:var(--color-danger);padding:8px;background:#FED7D7;border-radius:6px;margin-bottom:12px;font-size:13px;">{{ errorMsg }}</div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label">Nazwa artykułu *</label>
            <input v-model="form.name" type="text" class="form-control" placeholder="Np. Koparka gąsienicowa" required />
          </div>
          <div class="form-group">
            <label class="form-label">Typ artykułu</label>
            <select v-model="form.article_type" class="form-control">
              <option value="">— brak —</option>
              <option value="machine">Maszyna</option>
              <option value="vehicle">Pojazd</option>
              <option value="tool">Narzędzie</option>
              <option value="service">Usługa</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="checkbox-group">
            <input type="checkbox" v-model="form.is_service" />
            <span>Artykuł jest usługą (nie sprzętem)</span>
          </label>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label">Nr wewnętrzny</label>
            <input v-model="form.internal_number" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label">Nr rejestracyjny</label>
            <input v-model="form.registration_no" type="text" class="form-control" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label">Nr seryjny</label>
            <input v-model="form.serial_no" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label">Wartość odtworzeniowa (zł)</label>
            <input v-model="form.replacement_value" type="number" step="0.01" class="form-control" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label">Marka</label>
            <input v-model="form.brand" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label">Model</label>
            <input v-model="form.model" type="text" class="form-control" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label">Kategoria</label>
            <select v-model="form.category_id" class="form-control">
              <option :value="null">— brak —</option>
              <option v-for="cat in settingsStore.categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Właściciel (dostawca)</label>
            <div style="display:flex;gap:8px;">
              <input :value="ownerName" type="text" class="form-control" disabled placeholder="— własny —" style="flex:1;" />
              <button type="button" class="btn btn-secondary btn-sm" @click="showOwnerPicker = true">Wybierz</button>
              <button v-if="form.owner_id" type="button" class="btn btn-secondary btn-sm" @click="clearOwner">✕</button>
            </div>
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label">Min. dni najmu</label>
            <input v-model.number="form.rental_days" type="number" class="form-control" min="1" />
          </div>
          <div class="form-group">
            <label class="form-label">Filia</label>
            <select v-model="form.branch_id" class="form-control">
              <option :value="null">— główna —</option>
              <option v-for="br in settingsStore.branches" :key="br.id" :value="br.id">{{ br.name }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Opis</label>
          <textarea v-model="form.description" class="form-control" rows="3"></textarea>
        </div>

        <div class="form-group">
          <label class="form-label">Uwagi</label>
          <textarea v-model="form.notes" class="form-control" rows="2"></textarea>
        </div>
      </div>
    </div>

    <!-- Owner picker modal -->
    <Transition name="modal">
      <div v-if="showOwnerPicker" class="modal-overlay" @click.self="showOwnerPicker = false">
        <div class="modal-box" style="min-width:580px;">
          <div class="modal-title">Wybierz właściciela (dostawcę)</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon">⌕</span>
            <input v-model="pickerSearch" type="text" class="form-control" placeholder="Szukaj..." @input="searchOwners" />
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

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useArticleStore } from '@/stores/articles'
import { useSettingsStore } from '@/stores/settings'
import api from '@/composables/useApi'

const props = defineProps({ id: String })
const router = useRouter()
const store = useArticleStore()
const settingsStore = useSettingsStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const ownerName = ref('')

const form = ref({
  name: '', is_service: false, internal_number: '', registration_no: '',
  serial_no: '', brand: '', model: '', replacement_value: null,
  category_id: null, owner_id: null, branch_id: null,
  description: '', notes: '', rental_days: null, article_type: '',
})

const showOwnerPicker = ref(false)
const pickerSearch = ref('')
const pickerList = ref([])

onMounted(async () => {
  await settingsStore.fetchCategories()
  await settingsStore.fetchBranches()

  const { data } = await api.get('/contractors', { params: { supplier: true, per_page: 50 } })
  pickerList.value = data.items

  if (isEdit.value) {
    loading.value = true
    try {
      const data = await store.fetchOne(Number(props.id))
      Object.assign(form.value, data)
      if (data.owner_name) ownerName.value = data.owner_name
    } finally {
      loading.value = false
    }
  }
})

function goBack() { router.push('/dashboard/articles') }

async function handleSave() {
  if (!form.value.name) { errorMsg.value = 'Podaj nazwę artykułu'; return }
  saving.value = true
  errorMsg.value = ''
  try {
    const payload = { ...form.value }
    if (!payload.replacement_value) payload.replacement_value = null
    if (!payload.rental_days) payload.rental_days = null
    if (!payload.article_type) payload.article_type = null

    if (isEdit.value) {
      await store.update(Number(props.id), payload)
    } else {
      const result = await store.create(payload)
      router.push(`/articles/${result.id}/edit`)
      return
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Błąd zapisu'
  } finally {
    saving.value = false
  }
}

async function handleDuplicate() {
  if (!isEdit.value) return
  try {
    const result = await store.duplicate(Number(props.id))
    router.push(`/articles/${result.id}/edit`)
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd duplikacji')
  }
}

let ownerTimer = null
async function searchOwners() {
  clearTimeout(ownerTimer)
  ownerTimer = setTimeout(async () => {
    const { data } = await api.get('/contractors', { params: { search: pickerSearch.value, per_page: 50 } })
    pickerList.value = data.items
  }, 300)
}

function selectOwner(c) {
  form.value.owner_id = c.id
  ownerName.value = c.name
  showOwnerPicker.value = false
}

function clearOwner() {
  form.value.owner_id = null
  ownerName.value = ''
}
</script>
