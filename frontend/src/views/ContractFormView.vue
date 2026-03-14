<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack">←</button>
      <span class="toolbar-info">{{ isEdit ? (contractStore.current?.number ? `Umowa: ${contractStore.current.number}` : 'Ładowanie...') : 'Nowa umowa' }}</span>
      <button v-if="isEdit" class="toolbar-btn" title="Drukuj PDF" @click="generateReport('contract')">⎙</button>
      <button v-if="isEdit" class="toolbar-btn" title="Protokół ZO" @click="generateReport('protocol_zo')">📄</button>
      <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="saving">
        {{ saving ? '...' : 'Zapisz' }}
      </button>
    </div>

    <div class="content-area" style="padding:var(--spacing-md);">
      <div v-if="loading" class="empty-state">Ładowanie...</div>
      <div v-else>
        <!-- Top section: contract data -->
        <div class="page-card" style="margin-bottom:var(--spacing-md);">
          <div v-if="errorMsg" style="color:var(--color-danger);padding:8px;background:#FED7D7;border-radius:6px;margin-bottom:12px;font-size:13px;">{{ errorMsg }}</div>
          <div class="form-row-4" style="align-items:start;">
            <div class="form-group">
              <label class="form-label">Typ umowy</label>
              <select v-model="form.contract_type" class="form-control" :disabled="isEdit">
                <option value="S">Umowa najmu (S)</option>
                <option value="U">Umowa usługi (U)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Numer umowy</label>
              <input :value="contractStore.current?.number || '(auto)'" type="text" class="form-control" disabled />
            </div>
            <div class="form-group">
              <label class="form-label">Data od</label>
              <input v-model="form.date_from" type="date" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Data do</label>
              <input v-model="form.date_to" type="date" class="form-control" />
            </div>
          </div>

          <div class="form-row-2" style="align-items:start;">
            <div class="form-group">
              <label class="form-label">Kontrahent *</label>
              <div style="display:flex;gap:8px;">
                <input :value="contractorName" type="text" class="form-control" disabled placeholder="Wybierz kontrahenta..." style="flex:1;" />
                <button type="button" class="btn btn-secondary btn-sm" @click="showContractorPicker = true">Wybierz</button>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Adres dostawy</label>
              <input v-model="form.delivery_address" type="text" class="form-control" />
            </div>
          </div>

          <div class="form-row-4">
            <div class="form-group">
              <label class="form-label">Handlowiec</label>
              <select v-model="form.salesperson_id" class="form-control">
                <option :value="null">— brak —</option>
                <option v-for="sp in settingsStore.salespeople" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Wartość (zł)</label>
              <input v-model="form.total_value" type="number" step="0.01" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Przedpłata (zł)</label>
              <input v-model="form.prepayment_amount" type="number" step="0.01" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Faktura (zł)</label>
              <input v-model="form.invoice_amount" type="number" step="0.01" class="form-control" />
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Osoba kontaktowa 1</label>
              <div style="display:flex;gap:8px;">
                <input v-model="form.contact_person1" type="text" class="form-control" placeholder="Imię i nazwisko" />
                <input v-model="form.contact_phone1" type="text" class="form-control" placeholder="Telefon" style="width:140px;" />
                <label class="checkbox-group" style="white-space:nowrap;"><input type="checkbox" v-model="form.show_person1" /> Drukuj</label>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Osoba kontaktowa 2</label>
              <div style="display:flex;gap:8px;">
                <input v-model="form.contact_person2" type="text" class="form-control" placeholder="Imię i nazwisko" />
                <input v-model="form.contact_phone2" type="text" class="form-control" placeholder="Telefon" style="width:140px;" />
                <label class="checkbox-group" style="white-space:nowrap;"><input type="checkbox" v-model="form.show_person2" /> Drukuj</label>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Uwagi</label>
            <textarea v-model="form.notes" class="form-control" rows="2"></textarea>
          </div>
        </div>

        <!-- Positions section -->
        <div v-if="isEdit" class="page-card" style="margin-bottom:var(--spacing-md);">
          <div style="display:flex;align-items:center;margin-bottom:12px;">
            <span class="section-title" style="margin:0;border:none;">Pozycje umowy</span>
            <button class="btn btn-primary btn-sm" style="margin-left:auto;" @click="addPosition">+ Dodaj pozycję</button>
          </div>
          <table class="data-grid">
            <thead>
              <tr>
                <th>#</th>
                <th>Artykuł</th>
                <th>Typ</th>
                <th>Dni</th>
                <th>Ilość</th>
                <th>Cena jedn.</th>
                <th>Dostawca</th>
                <th style="width:80px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!contractStore.positions.length">
                <td colspan="8" class="empty-state">Brak pozycji</td>
              </tr>
              <tr
                v-for="(pos, idx) in contractStore.positions"
                :key="pos.id"
                :class="{ selected: selectedPosId === pos.id }"
                @click="selectedPosId = pos.id"
                @dblclick="editPosition(pos)"
              >
                <td>{{ idx + 1 }}</td>
                <td>{{ pos.article_name }}</td>
                <td>{{ pos.rental_type || '—' }}</td>
                <td>{{ pos.rental_days || '—' }}</td>
                <td>{{ pos.quantity || 1 }}</td>
                <td>{{ pos.unit_price ? Number(pos.unit_price).toFixed(2) + ' zł' : '—' }}</td>
                <td>{{ pos.supplier_name || '—' }}</td>
                <td>
                  <button class="btn-icon" title="Usuń" @click.stop="deletePosition(pos)">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Service fees section -->
        <div v-if="isEdit" class="page-card">
          <div style="display:flex;align-items:center;margin-bottom:12px;">
            <span class="section-title" style="margin:0;border:none;">Usługi dodatkowe</span>
          </div>
          <table class="data-grid">
            <thead>
              <tr><th>#</th><th>Nazwa</th><th>Kwota od</th><th>Kwota do</th><th>Jednostka</th><th>Aktywna</th></tr>
            </thead>
            <tbody>
              <tr v-if="!contractStore.serviceFees.length">
                <td colspan="6" class="empty-state">Brak usług dodatkowych</td>
              </tr>
              <tr v-for="(fee, idx) in contractStore.serviceFees" :key="fee.id">
                <td>{{ idx + 1 }}</td>
                <td>{{ fee.name }}</td>
                <td>{{ fee.amount_from ? Number(fee.amount_from).toFixed(2) + ' zł' : '—' }}</td>
                <td>{{ fee.amount_to ? Number(fee.amount_to).toFixed(2) + ' zł' : '—' }}</td>
                <td>{{ fee.unit || '—' }}</td>
                <td><span :class="['badge', fee.is_active ? 'badge-success' : 'badge-muted']">{{ fee.is_active ? 'Tak' : 'Nie' }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Contractor picker modal -->
    <Transition name="modal">
      <div v-if="showContractorPicker" class="modal-overlay" @click.self="showContractorPicker = false">
        <div class="modal-box" style="min-width:600px;">
          <div class="modal-title">Wybierz kontrahenta</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon">⌕</span>
            <input v-model="pickerSearch" type="text" class="form-control" placeholder="Szukaj..." @input="searchContractors" />
          </div>
          <div style="max-height:320px;overflow:auto;">
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>NIP</th><th>Miasto</th></tr></thead>
              <tbody>
                <tr v-for="c in pickerList" :key="c.id" @click="selectContractor(c)" style="cursor:pointer;">
                  <td>{{ c.name }}</td><td>{{ c.nip || '—' }}</td><td>{{ c.city || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showContractorPicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Position form modal -->
    <Transition name="modal">
      <div v-if="showPosModal" class="modal-overlay" @click.self="showPosModal = false">
        <div class="modal-box" style="min-width:560px;">
          <div class="modal-title">{{ editingPos ? 'Edycja pozycji' : 'Nowa pozycja' }}</div>
          <div class="form-group">
            <label class="form-label">Artykuł *</label>
            <div style="display:flex;gap:8px;">
              <input :value="selectedArticleName" type="text" class="form-control" disabled placeholder="Wybierz artykuł..." style="flex:1;" />
              <button type="button" class="btn btn-secondary btn-sm" @click="showArticlePicker = true">Wybierz</button>
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Typ najmu</label>
              <input v-model="posForm.rental_type" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Dni najmu</label>
              <input v-model.number="posForm.rental_days" type="number" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Ilość</label>
              <input v-model.number="posForm.quantity" type="number" class="form-control" min="1" />
            </div>
            <div class="form-group">
              <label class="form-label">Cena jednostkowa (zł)</label>
              <input v-model="posForm.unit_price" type="number" step="0.01" class="form-control" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Opis</label>
            <textarea v-model="posForm.description" class="form-control" rows="2"></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showPosModal = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="savePosition" :disabled="savingPos">{{ savingPos ? '...' : 'Zapisz' }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Article picker modal -->
    <Transition name="modal">
      <div v-if="showArticlePicker" class="modal-overlay" @click.self="showArticlePicker = false">
        <div class="modal-box" style="min-width:600px;">
          <div class="modal-title">Wybierz artykuł</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon">⌕</span>
            <input v-model="articlePickerSearch" type="text" class="form-control" placeholder="Szukaj..." @input="searchArticles" />
          </div>
          <div style="max-height:320px;overflow:auto;">
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>Nr rej.</th><th>Marka</th><th>Typ</th></tr></thead>
              <tbody>
                <tr v-for="a in articlePickerList" :key="a.id" @click="selectArticle(a)" style="cursor:pointer;">
                  <td>{{ a.name }}</td><td>{{ a.registration_no || '—' }}</td><td>{{ a.brand || '—' }}</td>
                  <td><span :class="['badge', a.is_service ? 'badge-warning' : 'badge-info']">{{ a.is_service ? 'Usługa' : 'Sprzęt' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showArticlePicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useContractStore } from '@/stores/contracts'
import { useContractorStore } from '@/stores/contractors'
import { useArticleStore } from '@/stores/articles'
import { useSettingsStore } from '@/stores/settings'
import api from '@/composables/useApi'

const props = defineProps({ id: String })
const router = useRouter()
const route = useRoute()
const contractStore = useContractStore()
const contractorStore = useContractorStore()
const articleStore = useArticleStore()
const settingsStore = useSettingsStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const selectedPosId = ref(null)

const form = ref({
  contractor_id: null, branch_id: null, salesperson_id: null,
  contract_type: 'S', delivery_address: '', date_from: '', date_to: '',
  total_value: 0, prepayment_amount: 0, prepayment_document: '',
  invoice_amount: 0, invoice_document: '', notes: '',
  contact_person1: '', contact_phone1: '', show_person1: true,
  contact_person2: '', contact_phone2: '', show_person2: true,
  email: '', phone: '', contractor_name: '', working_days_per_week: 6, report_without_data: false,
})

const contractorName = ref('')
const showContractorPicker = ref(false)
const pickerSearch = ref('')
const pickerList = ref([])

const showPosModal = ref(false)
const editingPos = ref(null)
const savingPos = ref(false)
const posForm = ref({ article_id: null, rental_type: '', description: '', rental_days: null, quantity: 1, unit_price: null, rate_type_id: null, billing_frequency: null, billing_unit: null, supplier_id: null, delivery_date: null })
const selectedArticleName = ref('')
const showArticlePicker = ref(false)
const articlePickerSearch = ref('')
const articlePickerList = ref([])

onMounted(async () => {
  await settingsStore.fetchSalespeople()

  const [ctRes, artRes] = await Promise.allSettled([
    api.get('/contractors', { params: { per_page: 30 } }),
    api.get('/articles', { params: { per_page: 50 } }),
  ])
  if (ctRes.status === 'fulfilled') pickerList.value = ctRes.value.data.items
  if (artRes.status === 'fulfilled') articlePickerList.value = artRes.value.data.items

  const contractorIdFromQuery = route.query.contractor_id
  if (contractorIdFromQuery) {
    const ct = await contractorStore.fetchOne(Number(contractorIdFromQuery))
    form.value.contractor_id = ct.id
    contractorName.value = ct.name
    form.value.contractor_name = ct.name
  }

  if (isEdit.value) {
    loading.value = true
    try {
      const data = await contractStore.fetchOne(Number(props.id))
      Object.assign(form.value, data)
      if (data.contractor_id) {
        try { const ct = await contractorStore.fetchOne(data.contractor_id); contractorName.value = ct.name } catch {}
      }
      await contractStore.fetchPositions(Number(props.id))
      await contractStore.fetchServiceFees(Number(props.id))
    } finally {
      loading.value = false
    }
  }
})

function goBack() { router.push('/dashboard/contracts') }

async function handleSave() {
  if (!form.value.contractor_id) { errorMsg.value = 'Wybierz kontrahenta'; return }
  saving.value = true
  errorMsg.value = ''
  try {
    if (isEdit.value) {
      await contractStore.update(Number(props.id), form.value)
    } else {
      const result = await contractStore.create(form.value)
      router.push(`/contracts/${result.id}/edit`)
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Błąd zapisu'
  } finally {
    saving.value = false
  }
}

async function generateReport(type) {
  if (!isEdit.value) return
  try {
    await contractStore.generateReport(Number(props.id), type)
  } catch (e) {
    alert('Błąd generowania raportu')
  }
}

let pickerTimer = null
async function searchContractors() {
  clearTimeout(pickerTimer)
  pickerTimer = setTimeout(async () => {
    const { data } = await api.get('/contractors', { params: { search: pickerSearch.value, per_page: 30 } })
    pickerList.value = data.items
  }, 300)
}

function selectContractor(c) {
  form.value.contractor_id = c.id
  form.value.contractor_name = c.name
  contractorName.value = c.name
  showContractorPicker.value = false
}

function addPosition() {
  editingPos.value = null
  Object.assign(posForm.value, { article_id: null, rental_type: '', description: '', rental_days: null, quantity: 1, unit_price: null, rate_type_id: null, billing_frequency: null, billing_unit: null, supplier_id: null, delivery_date: null })
  selectedArticleName.value = ''
  showPosModal.value = true
}

function editPosition(pos) {
  editingPos.value = pos
  Object.assign(posForm.value, pos)
  selectedArticleName.value = pos.article_name || ''
  showPosModal.value = true
}

async function savePosition() {
  if (!posForm.value.article_id) { alert('Wybierz artykuł'); return }
  savingPos.value = true
  try {
    if (editingPos.value) {
      await contractStore.updatePosition(Number(props.id), editingPos.value.id, posForm.value)
    } else {
      await contractStore.createPosition(Number(props.id), posForm.value)
    }
    await contractStore.fetchPositions(Number(props.id))
    showPosModal.value = false
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd zapisu pozycji')
  } finally {
    savingPos.value = false
  }
}

async function deletePosition(pos) {
  if (!confirm('Usunąć tę pozycję?')) return
  try {
    await contractStore.deletePosition(Number(props.id), pos.id)
    await contractStore.fetchPositions(Number(props.id))
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd')
  }
}

let artTimer = null
async function searchArticles() {
  clearTimeout(artTimer)
  artTimer = setTimeout(async () => {
    const { data } = await api.get('/articles', { params: { search: articlePickerSearch.value, per_page: 50 } })
    articlePickerList.value = data.items
  }, 300)
}

function selectArticle(a) {
  posForm.value.article_id = a.id
  selectedArticleName.value = a.name
  showArticlePicker.value = false
}

</script>
