<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <span class="toolbar-info">Ustawienia</span>
    </div>
    <div class="content-area">
      <div style="display:grid;grid-template-columns:200px 1fr;gap:var(--spacing-md);height:100%;">
        <!-- Settings nav -->
        <div class="panel">
          <div class="panel-header">Sekcje</div>
          <div class="panel-body" style="padding:0;">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              :class="['sidebar-btn', { active: activeTab === tab.id }]"
              style="font-size:13px;padding:10px 16px;"
              @click="activeTab = tab.id"
            >{{ tab.label }}</button>
          </div>
        </div>

        <!-- Settings content -->
        <div class="panel">
          <div class="panel-header">{{ currentTabLabel }}</div>
          <div class="panel-body">

            <!-- Company tab -->
            <div v-if="activeTab === 'company'">
              <div v-if="settingsStore.loading" class="empty-state">Ładowanie...</div>
              <div v-else>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Nazwa firmy</label>
                    <input v-model="companyForm.name" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Nazwa skrócona</label>
                    <input v-model="companyForm.name_short" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">NIP</label>
                    <input v-model="companyForm.nip" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">REGON</label>
                    <input v-model="companyForm.regon" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Kod pocztowy</label>
                    <input v-model="companyForm.postal_code" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Miasto</label>
                    <input v-model="companyForm.city" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">Ulica</label>
                  <input v-model="companyForm.street" type="text" class="form-control" />
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Bank</label>
                    <input v-model="companyForm.bank_name" type="text" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Numer konta</label>
                    <input v-model="companyForm.bank_account" type="text" class="form-control" />
                  </div>
                </div>
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Numeracja od</label>
                    <input v-model.number="companyForm.numbering_start" type="number" class="form-control" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Krok inkrement</label>
                    <input v-model="companyForm.increment_step" type="number" step="0.01" class="form-control" />
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">Nagłówek wydruku</label>
                  <textarea v-model="companyForm.header_text" class="form-control" rows="3"></textarea>
                </div>
                <div style="margin-top:16px;">
                  <button class="btn btn-primary" @click="saveCompany" :disabled="savingCompany">
                    {{ savingCompany ? '...' : 'Zapisz dane firmy' }}
                  </button>
                  <span v-if="companySaved" style="color:var(--color-success);margin-left:12px;font-size:13px;">✓ Zapisano</span>
                </div>
              </div>
            </div>

            <!-- Salespeople tab -->
            <div v-if="activeTab === 'salespeople'">
              <div style="display:flex;gap:8px;margin-bottom:16px;">
                <input v-model="newSp.name" type="text" class="form-control" placeholder="Imię i nazwisko" style="max-width:240px;" />
                <input v-model="newSp.phone" type="text" class="form-control" placeholder="Telefon" style="max-width:160px;" />
                <button class="btn btn-primary btn-sm" @click="addSalesperson">+ Dodaj</button>
              </div>
              <table class="data-grid">
                <thead><tr><th>Nazwa</th><th>Telefon</th><th>Aktywny</th><th></th></tr></thead>
                <tbody>
                  <tr v-for="sp in settingsStore.salespeople" :key="sp.id">
                    <td>{{ sp.name }}</td>
                    <td>{{ sp.phone || '—' }}</td>
                    <td><span :class="['badge', sp.is_active ? 'badge-success' : 'badge-muted']">{{ sp.is_active ? 'Tak' : 'Nie' }}</span></td>
                    <td><button class="btn-icon" @click="toggleSp(sp.id)" title="Przełącz">⇄</button></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Categories tab -->
            <div v-if="activeTab === 'categories'">
              <div style="display:flex;gap:8px;margin-bottom:16px;">
                <input v-model="newCat.name" type="text" class="form-control" placeholder="Nazwa kategorii" style="max-width:240px;" />
                <input v-model="newCat.code" type="text" class="form-control" placeholder="Kod" style="max-width:120px;" />
                <button class="btn btn-primary btn-sm" @click="addCategory">+ Dodaj</button>
              </div>
              <table class="data-grid">
                <thead><tr><th>Nazwa</th><th>Kod</th><th>Opis</th></tr></thead>
                <tbody>
                  <tr v-for="cat in settingsStore.categories" :key="cat.id">
                    <td>{{ cat.name }}</td>
                    <td>{{ cat.code || '—' }}</td>
                    <td>{{ cat.description || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Rate types tab -->
            <div v-if="activeTab === 'rate-types'">
              <div style="display:flex;gap:8px;margin-bottom:16px;">
                <input v-model="newRt.name" type="text" class="form-control" placeholder="Nazwa typu stawki" style="max-width:300px;" />
                <button class="btn btn-primary btn-sm" @click="addRateType">+ Dodaj</button>
              </div>
              <table class="data-grid">
                <thead><tr><th>Nazwa</th><th>Opis</th><th>Zależna</th></tr></thead>
                <tbody>
                  <tr v-for="rt in settingsStore.rateTypes" :key="rt.id">
                    <td>{{ rt.name }}</td>
                    <td>{{ rt.description || '—' }}</td>
                    <td>{{ rt.is_dependent ? 'Tak' : 'Nie' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Fee templates tab -->
            <div v-if="activeTab === 'fee-templates'">
              <div style="display:flex;gap:8px;align-items:flex-end;margin-bottom:16px;flex-wrap:wrap;">
                <div class="form-group" style="margin:0;">
                  <label class="form-label">Typ umowy</label>
                  <select v-model="newFee.contract_type" class="form-control" style="width:160px;">
                    <option value="S">Najem (S)</option>
                    <option value="U">Usługa (U)</option>
                  </select>
                </div>
                <div class="form-group" style="margin:0;flex:1;">
                  <label class="form-label">Nazwa</label>
                  <input v-model="newFee.name" type="text" class="form-control" placeholder="Nazwa usługi" />
                </div>
                <div class="form-group" style="margin:0;width:120px;">
                  <label class="form-label">Kwota od</label>
                  <input v-model="newFee.amount_from" type="number" step="0.01" class="form-control" />
                </div>
                <div class="form-group" style="margin:0;width:120px;">
                  <label class="form-label">Kwota do</label>
                  <input v-model="newFee.amount_to" type="number" step="0.01" class="form-control" />
                </div>
                <button class="btn btn-primary btn-sm" @click="addFeeTemplate" style="margin-bottom:0;">+ Dodaj</button>
              </div>
              <table class="data-grid">
                <thead><tr><th>Typ</th><th>#</th><th>Nazwa</th><th>Kwota od</th><th>Kwota do</th><th>Jedn.</th><th>Aktywna</th></tr></thead>
                <tbody>
                  <tr v-for="f in settingsStore.feeTemplates" :key="f.id">
                    <td><span :class="['badge', f.contract_type === 'S' ? 'badge-info' : 'badge-warning']">{{ f.contract_type }}</span></td>
                    <td>{{ f.sort_order }}</td>
                    <td>{{ f.name }}</td>
                    <td>{{ f.amount_from ? Number(f.amount_from).toFixed(2) + ' zł' : '—' }}</td>
                    <td>{{ f.amount_to ? Number(f.amount_to).toFixed(2) + ' zł' : '—' }}</td>
                    <td>{{ f.unit || '—' }}</td>
                    <td><span :class="['badge', f.is_active ? 'badge-success' : 'badge-muted']">{{ f.is_active ? 'Tak' : 'Nie' }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import api from '@/composables/useApi'

const settingsStore = useSettingsStore()

const activeTab = ref('company')
const tabs = [
  { id: 'company', label: 'Dane firmy' },
  { id: 'salespeople', label: 'Handlowcy' },
  { id: 'categories', label: 'Kategorie' },
  { id: 'rate-types', label: 'Typy stawek' },
  { id: 'fee-templates', label: 'Szablony usług' },
]

const currentTabLabel = computed(() => tabs.find(t => t.id === activeTab.value)?.label || '')

const companyForm = ref({ name: '', name_short: '', nip: '', regon: '', postal_code: '', city: '', street: '', bank_name: '', bank_account: '', numbering_start: 1, increment_step: 50, header_text: '' })
const savingCompany = ref(false)
const companySaved = ref(false)

const newSp = ref({ name: '', phone: '' })
const newCat = ref({ name: '', code: '', description: '' })
const newRt = ref({ name: '', description: '', is_dependent: false })
const newFee = ref({ contract_type: 'S', name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true })

onMounted(async () => {
  await settingsStore.fetchAll()
  const company = await settingsStore.fetchCompany()
  if (company) Object.assign(companyForm.value, company)
})

async function saveCompany() {
  savingCompany.value = true
  try {
    await settingsStore.updateCompany(companyForm.value)
    companySaved.value = true
    setTimeout(() => { companySaved.value = false }, 3000)
  } finally {
    savingCompany.value = false
  }
}

async function addSalesperson() {
  if (!newSp.value.name) return
  await api.post('/settings/salespeople', newSp.value)
  await settingsStore.fetchSalespeople()
  newSp.value = { name: '', phone: '' }
}

async function toggleSp(id) {
  await api.patch(`/settings/salespeople/${id}/toggle`)
  await settingsStore.fetchSalespeople()
}

async function addCategory() {
  if (!newCat.value.name) return
  await api.post('/settings/categories', newCat.value)
  await settingsStore.fetchCategories()
  newCat.value = { name: '', code: '', description: '' }
}

async function addRateType() {
  if (!newRt.value.name) return
  await api.post('/settings/rate-types', newRt.value)
  await settingsStore.fetchRateTypes()
  newRt.value = { name: '', description: '', is_dependent: false }
}

async function addFeeTemplate() {
  if (!newFee.value.name) return
  await api.post('/settings/service-fee-templates', newFee.value)
  await settingsStore.fetchFeeTemplates()
  newFee.value = { contract_type: 'S', name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true }
}
</script>
