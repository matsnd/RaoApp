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
              <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
                <input v-model="newSp.name" type="text" class="form-control" placeholder="Imię i nazwisko" style="max-width:240px;" />
                <input v-model="newSp.phone" type="text" class="form-control" placeholder="Telefon" style="max-width:160px;" />
                <input v-model.number="newSp.commission_rate" type="number" min="0" max="100" step="0.5" class="form-control" placeholder="Prowizja %" style="max-width:110px;" />
                <button class="btn btn-primary btn-sm" @click="addSalesperson">+ Dodaj</button>
              </div>
              <table class="data-grid">
                <thead><tr><th>Nazwa</th><th>Telefon</th><th>Prowizja %</th><th>Aktywny</th><th style="width:100px;"></th></tr></thead>
                <tbody>
                  <tr v-for="sp in settingsStore.salespeople" :key="sp.id">
                    <td>{{ sp.name }}</td>
                    <td>{{ sp.phone || '—' }}</td>
                    <td>{{ sp.commission_rate != null ? sp.commission_rate + ' %' : '—' }}</td>
                    <td><span :class="['badge', sp.is_active ? 'badge-success' : 'badge-muted']">{{ sp.is_active ? 'Tak' : 'Nie' }}</span></td>
                    <td>
                      <button class="btn-icon" @click="toggleSp(sp.id)" title="Przełącz">⇄</button>
                      <button class="btn-icon" @click="deleteSp(sp.id)" title="Usuń">✕</button>
                    </td>
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
                <thead><tr><th>Nazwa</th><th>Kod</th><th>Opis</th><th style="width:80px;"></th></tr></thead>
                <tbody>
                  <template v-for="cat in settingsStore.categories" :key="cat.id">
                    <tr v-if="editingCatId === cat.id" class="row-editing">
                      <td><input v-model="editingCatData.name" class="form-control form-control-xs" @keydown.enter="saveEditCat" @keydown.esc="editingCatId = null" /></td>
                      <td><input v-model="editingCatData.code" class="form-control form-control-xs" @keydown.enter="saveEditCat" @keydown.esc="editingCatId = null" /></td>
                      <td><input v-model="editingCatData.description" class="form-control form-control-xs" @keydown.enter="saveEditCat" @keydown.esc="editingCatId = null" /></td>
                      <td>
                        <button class="btn-icon" style="color:#22543D;" @click="saveEditCat" title="Zapisz">✓</button>
                        <button class="btn-icon" @click="editingCatId = null" title="Anuluj">✕</button>
                      </td>
                    </tr>
                    <tr v-else>
                      <td>{{ cat.name }}</td>
                      <td>{{ cat.code || '—' }}</td>
                      <td>{{ cat.description || '—' }}</td>
                      <td>
                        <button class="btn-icon" @click="startEditCat(cat)" title="Edytuj">✎</button>
                        <button class="btn-icon" @click="deleteCat(cat.id)" title="Usuń">✕</button>
                      </td>
                    </tr>
                  </template>
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
                <thead><tr><th>Nazwa</th><th>Opis</th><th>Zależna</th><th style="width:80px;"></th></tr></thead>
                <tbody>
                  <template v-for="rt in settingsStore.rateTypes" :key="rt.id">
                    <tr v-if="editingRtId === rt.id" class="row-editing">
                      <td><input v-model="editingRtData.name" class="form-control form-control-xs" @keydown.enter="saveEditRt" @keydown.esc="editingRtId = null" /></td>
                      <td><input v-model="editingRtData.description" class="form-control form-control-xs" @keydown.enter="saveEditRt" @keydown.esc="editingRtId = null" /></td>
                      <td style="text-align:center;"><input type="checkbox" v-model="editingRtData.is_dependent" /></td>
                      <td>
                        <button class="btn-icon" style="color:#22543D;" @click="saveEditRt" title="Zapisz">✓</button>
                        <button class="btn-icon" @click="editingRtId = null" title="Anuluj">✕</button>
                      </td>
                    </tr>
                    <tr v-else>
                      <td>{{ rt.name }}</td>
                      <td>{{ rt.description || '—' }}</td>
                      <td>{{ rt.is_dependent ? 'Tak' : 'Nie' }}</td>
                      <td>
                        <button class="btn-icon" @click="startEditRt(rt)" title="Edytuj">✎</button>
                        <button class="btn-icon" @click="deleteRt(rt.id)" title="Usuń">✕</button>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>

            <!-- Fee preset groups tab -->
            <div v-if="activeTab === 'fee-presets'">
              <!-- new preset form -->
              <div style="display:flex;gap:8px;align-items:flex-end;margin-bottom:16px;flex-wrap:wrap;">
                <div class="form-group" style="margin:0;">
                  <label class="form-label">Typ umowy</label>
                  <select v-model="newPreset.contract_type" class="form-control" style="width:130px;">
                    <option value="S">Najem (S)</option>
                    <option value="U">Usługa (U)</option>
                  </select>
                </div>
                <div class="form-group" style="margin:0;flex:1;min-width:220px;">
                  <label class="form-label">Nazwa zestawu</label>
                  <input v-model="newPreset.name" type="text" class="form-control" placeholder="np. Standardowy, Premium…" @keydown.enter="addPreset" />
                </div>
                <div class="form-group" style="margin:0;flex:2;min-width:200px;">
                  <label class="form-label">Opis (opcjonalnie)</label>
                  <input v-model="newPreset.description" type="text" class="form-control" placeholder="Krótki opis zestawu" />
                </div>
                <button class="btn btn-primary btn-sm" @click="addPreset" style="margin-bottom:0;">+ Nowy zestaw</button>
              </div>

              <div v-if="!feePresets.length" class="empty-state">Brak zestawów — utwórz pierwszy zestaw powyżej.</div>

              <div v-for="preset in feePresets" :key="preset.id" class="preset-card">
                <div class="preset-header">
                  <div style="display:flex;align-items:center;gap:8px;">
                    <span :class="['badge', preset.contract_type === 'S' ? 'badge-info' : 'badge-warning']">{{ preset.contract_type }}</span>
                    <span v-if="editingPresetId !== preset.id" style="font-weight:600;font-size:14px;">{{ preset.name }}</span>
                    <input v-else v-model="editingPresetName" class="form-control form-control-xs" style="width:260px;" @keydown.enter="savePresetName(preset)" @keydown.esc="editingPresetId = null" />
                    <span v-if="preset.is_default" class="badge badge-muted" style="font-size:10px;">Domyślny</span>
                    <span style="font-size:11px;color:#718096;">({{ preset.templates.length }} pozycji)</span>
                  </div>
                  <div style="display:flex;gap:4px;">
                    <button v-if="editingPresetId !== preset.id" class="btn-icon" title="Zmień nazwę" @click="startEditPreset(preset)">✎</button>
                    <button v-else class="btn-icon" style="color:#22543D;" title="Zapisz" @click="savePresetName(preset)">✓</button>
                    <button class="btn-icon" :class="{ active: expandedPresetId === preset.id }" title="Pokaż/ukryj pozycje" @click="toggleExpand(preset.id)">{{ expandedPresetId === preset.id ? '▲' : '▼' }}</button>
                    <button class="btn-icon" title="Usuń zestaw" @click="deletePreset(preset.id)">✕</button>
                  </div>
                </div>

                <!-- Expanded items -->
                <div v-if="expandedPresetId === preset.id" class="preset-items">
                  <table class="data-grid" style="margin-top:8px;">
                    <thead>
                      <tr>
                        <th style="width:28%;">Nazwa</th>
                        <th style="width:10%;">Cena dom.</th>
                        <th style="width:10%;">Kwota od</th>
                        <th style="width:10%;">Kwota do</th>
                        <th style="width:8%;">J.m.</th>
                        <th>Opis</th>
                        <th style="width:60px;">Aktywna</th>
                        <th style="width:64px;"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <template v-for="tpl in preset.templates" :key="tpl.id">
                        <tr v-if="editingPresetItemId === tpl.id" style="background:#fffff0;">
                          <td>
                            <!-- RAO-P1-011: Article picker instead of text input -->
                            <select v-model="editingPresetItemData.article_id" class="form-control form-control-xs" @change="onArticleSelected('edit')" style="margin-bottom:4px;">
                              <option :value="null">-- Wybierz artykuł --</option>
                              <option v-for="art in articleStore.list" :key="art.id" :value="art.id">{{ art.name }}</option>
                            </select>
                            <input v-model="editingPresetItemData.name" class="form-control form-control-xs" placeholder="Nazwa (auto z artykułu)" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" />
                          </td>
                          <td><input v-model="editingPresetItemData.default_price" type="number" step="0.01" class="form-control form-control-xs" placeholder="Cena domyślna" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.amount_from" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.amount_to" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td><input v-model="editingPresetItemData.description" class="form-control form-control-xs" @keydown.enter="savePresetItem(preset.id)" @keydown.esc="editingPresetItemId = null" /></td>
                          <td style="text-align:center;"><input type="checkbox" v-model="editingPresetItemData.is_active" /></td>
                          <td>
                            <button class="btn-icon" style="color:#22543D;" title="Zapisz" @click="savePresetItem(preset.id)">✓</button>
                            <button class="btn-icon" title="Anuluj" @click="editingPresetItemId = null">✕</button>
                          </td>
                        </tr>
                        <tr v-else @click="startEditPresetItem(tpl)" style="cursor:pointer;" :class="{ 'row-inactive-tpl': !tpl.is_active }">
                          <td>{{ tpl.article_name || tpl.name }}</td>
                          <td>{{ tpl.default_price ? Number(tpl.default_price).toFixed(2) + ' zł' : '—' }}</td>
                          <td>{{ tpl.amount_from ? Number(tpl.amount_from).toFixed(2) + ' zł' : '—' }}</td>
                          <td>{{ tpl.amount_to ? Number(tpl.amount_to).toFixed(2) + ' zł' : '—' }}</td>
                          <td>{{ tpl.unit || '—' }}</td>
                          <td style="font-size:11px;">{{ tpl.description || '—' }}</td>
                          <td><span :class="['badge', tpl.is_active ? 'badge-success' : 'badge-muted']">{{ tpl.is_active ? 'Tak' : 'Nie' }}</span></td>
                          <td>
                            <button class="btn-icon" title="Edytuj" @click.stop="startEditPresetItem(tpl)">✎</button>
                            <button class="btn-icon" title="Usuń" @click.stop="deletePresetItem(preset.id, tpl.id)">✕</button>
                          </td>
                        </tr>
                      </template>
                      <!-- new item row -->
                      <tr v-if="addingToPresetId === preset.id" style="background:#f0fff4;">
                        <td>
                          <!-- RAO-P1-011: Article picker for new item -->
                          <select v-model="newPresetItem.article_id" class="form-control form-control-xs" @change="onArticleSelected('new')" style="margin-bottom:4px;">
                            <option :value="null">-- Wybierz artykuł --</option>
                            <option v-for="art in articleStore.list" :key="art.id" :value="art.id">{{ art.name }}</option>
                          </select>
                          <input v-model="newPresetItem.name" class="form-control form-control-xs" placeholder="Nazwa (auto z artykułu)" ref="newPresetItemNameRef" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" />
                        </td>
                        <td><input v-model="newPresetItem.default_price" type="number" step="0.01" class="form-control form-control-xs" placeholder="Cena domyślna" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.amount_from" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.amount_to" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.unit" class="form-control form-control-xs" placeholder="h, km…" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td><input v-model="newPresetItem.description" class="form-control form-control-xs" @keydown.enter="saveNewPresetItem(preset)" @keydown.esc="addingToPresetId = null" /></td>
                        <td style="text-align:center;"><input type="checkbox" v-model="newPresetItem.is_active" /></td>
                        <td>
                          <button class="btn-icon" style="color:#22543D;" title="Dodaj (Enter)" @click="saveNewPresetItem(preset)">✓</button>
                          <button class="btn-icon" title="Anuluj" @click="addingToPresetId = null">✕</button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <button class="btn btn-secondary btn-sm" style="margin-top:8px;" @click="startAddPresetItem(preset.id)">+ Dodaj pozycję</button>
                </div>
              </div>
            </div>


          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useArticleStore } from '@/stores/articles'
import api from '@/composables/useApi'

const settingsStore = useSettingsStore()
const articleStore = useArticleStore()

const activeTab = ref('company')
const tabs = [
  { id: 'company', label: 'Dane firmy' },
  { id: 'salespeople', label: 'Handlowcy' },
  { id: 'categories', label: 'Kategorie' },
  { id: 'rate-types', label: 'Typy stawek' },
  { id: 'fee-presets', label: 'Zestawy usług' },
]

const currentTabLabel = computed(() => tabs.find(t => t.id === activeTab.value)?.label || '')

const companyForm = ref({ name: '', name_short: '', nip: '', regon: '', postal_code: '', city: '', street: '', bank_name: '', bank_account: '', numbering_start: 1, increment_step: 50, header_text: '' })
const savingCompany = ref(false)
const companySaved = ref(false)

const newSp = ref({ name: '', phone: '', commission_rate: null })
const newCat = ref({ name: '', code: '', description: '' })
const newRt = ref({ name: '', description: '', is_dependent: false })

const feePresets = ref([])
const newPreset = ref({ contract_type: 'S', name: '', description: '' })
const expandedPresetId = ref(null)
const editingPresetId = ref(null)
const editingPresetName = ref('')
const editingPresetItemId = ref(null)
const editingPresetItemData = ref({})
const addingToPresetId = ref(null)
const newPresetItem = ref({ name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true, article_id: null, default_price: null })
const newPresetItemNameRef = ref(null)

onMounted(async () => {
  await settingsStore.fetchAll()
  const company = await settingsStore.fetchCompany()
  if (company) Object.assign(companyForm.value, company)
  await loadFeePresets()
  // RAO-P1-011: Load articles for picker
  await articleStore.fetchList({ is_service: true })
})

async function loadFeePresets() {
  const { data } = await api.get('/settings/fee-preset-groups')
  feePresets.value = data
}

async function addPreset() {
  if (!newPreset.value.name) return
  const payload = { ...newPreset.value }
  if (!payload.description) payload.description = null
  await api.post('/settings/fee-preset-groups', payload)
  await loadFeePresets()
  newPreset.value = { contract_type: newPreset.value.contract_type, name: '', description: '' }
}

async function deletePreset(id) {
  if (!confirm('Usunąć ten zestaw i wszystkie jego pozycje?')) return
  await api.delete(`/settings/fee-preset-groups/${id}`)
  if (expandedPresetId.value === id) expandedPresetId.value = null
  await loadFeePresets()
}

function toggleExpand(id) {
  expandedPresetId.value = expandedPresetId.value === id ? null : id
  addingToPresetId.value = null
}

function startEditPreset(preset) {
  editingPresetId.value = preset.id
  editingPresetName.value = preset.name
}

async function savePresetName(preset) {
  if (!editingPresetName.value) return
  await api.put(`/settings/fee-preset-groups/${preset.id}`, {
    name: editingPresetName.value,
    contract_type: preset.contract_type,
    description: preset.description,
    is_default: preset.is_default,
  })
  editingPresetId.value = null
  await loadFeePresets()
}

function startEditPresetItem(tpl) {
  editingPresetItemId.value = tpl.id
  editingPresetItemData.value = {
    name: tpl.name,
    article_id: tpl.article_id,
    default_price: tpl.default_price,
    amount_from: tpl.amount_from,
    amount_to: tpl.amount_to,
    unit: tpl.unit || '',
    description: tpl.description || '',
    is_active: tpl.is_active,
    contract_type: tpl.contract_type,
  }
}

function onArticleSelected(mode) {
  // RAO-P1-011: Auto-fill name from selected article
  const data = mode === 'edit' ? editingPresetItemData.value : newPresetItem.value
  if (data.article_id) {
    const article = articleStore.list.find(a => a.id === data.article_id)
    if (article) {
      data.name = article.name
      if (!data.default_price && article.price) {
        data.default_price = article.price
      }
    }
  }
}

async function savePresetItem(presetId) {
  if (!editingPresetItemData.value.name) return
  const payload = { ...editingPresetItemData.value }
  if (!payload.unit) payload.unit = null
  if (!payload.description) payload.description = null
  // RAO-P1-011: Send article_id and default_price
  if (!payload.article_id) payload.article_id = null
  if (!payload.default_price) payload.default_price = null
  await api.put(`/settings/fee-preset-groups/${presetId}/templates/${editingPresetItemId.value}`, payload)
  editingPresetItemId.value = null
  await loadFeePresets()
}

async function deletePresetItem(presetId, tplId) {
  if (!confirm('Usunąć tę pozycję z zestawu?')) return
  await api.delete(`/settings/fee-preset-groups/${presetId}/templates/${tplId}`)
  await loadFeePresets()
}

async function startAddPresetItem(presetId) {
  addingToPresetId.value = presetId
  newPresetItem.value = { name: '', amount_from: null, amount_to: null, unit: '', description: '', is_active: true }
  await import('vue').then(({ nextTick }) => nextTick(() => newPresetItemNameRef.value?.focus()))
}

// Watch for fuel items — auto-set 200 zł default
watch(() => newPresetItem.value.name, (newName) => {
  if (!newName) return
  const lower = newName.toLowerCase()
  if ((lower.includes('tankowanie') || lower.includes('paliwo') || lower.includes('fuel')) && 
      newPresetItem.value.amount_from === null && newPresetItem.value.amount_to === null) {
    newPresetItem.value.amount_from = 200
    newPresetItem.value.amount_to = 200
    newPresetItem.value.unit = 'szt'
  }
})

async function saveNewPresetItem(preset) {
  if (!newPresetItem.value.name) return
  const payload = {
    ...newPresetItem.value,
    contract_type: preset.contract_type,
    preset_id: preset.id,
  }
  if (!payload.unit) payload.unit = null
  if (!payload.description) payload.description = null
  // RAO-P1-011: Send article_id and default_price
  if (!payload.article_id) payload.article_id = null
  if (!payload.default_price) payload.default_price = null
  await api.post(`/settings/fee-preset-groups/${preset.id}/templates`, payload)
  addingToPresetId.value = null
  await loadFeePresets()
}

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
  newSp.value = { name: '', phone: '', commission_rate: null }
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


async function deleteSp(id) {
  if (!confirm('Usunąć tego handlowca?')) return
  await api.delete(`/settings/salespeople/${id}`)
  await settingsStore.fetchSalespeople()
}

async function deleteCat(id) {
  if (!confirm('Usunąć tę kategorię?')) return
  await settingsStore.deleteCategory(id)
}

async function deleteRt(id) {
  if (!confirm('Usunąć ten typ stawki?')) return
  await settingsStore.deleteRateType(id)
}

// Inline edit — categories
const editingCatId = ref(null)
const editingCatData = ref({ name: '', code: '', description: '' })
function startEditCat(cat) {
  editingCatId.value = cat.id
  editingCatData.value = { name: cat.name, code: cat.code || '', description: cat.description || '' }
}
async function saveEditCat() {
  if (!editingCatData.value.name) return
  await settingsStore.updateCategory(editingCatId.value, editingCatData.value)
  editingCatId.value = null
}

// Inline edit — rate types
const editingRtId = ref(null)
const editingRtData = ref({ name: '', description: '', is_dependent: false })
function startEditRt(rt) {
  editingRtId.value = rt.id
  editingRtData.value = { name: rt.name, description: rt.description || '', is_dependent: rt.is_dependent }
}
async function saveEditRt() {
  if (!editingRtData.value.name) return
  await settingsStore.updateRateType(editingRtId.value, editingRtData.value)
  editingRtId.value = null
}
</script>

<style scoped>
.sidebar-btn {
  color: var(--color-text);
}
.sidebar-btn:hover {
  background: var(--color-primary);
  color: #fff;
}
.sidebar-btn.active {
  background: var(--color-primary);
  color: #fff;
  border-left: 3px solid var(--color-primary-dark, #1a3a5c);
}
.form-control-xs {
  padding: 2px 6px;
  height: 28px;
  font-size: 12px;
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: #fff;
}
.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  opacity: 0.6;
  transition: opacity 150ms;
}
.btn-icon:hover { opacity: 1; }
.row-inactive-tpl td { opacity: 0.5; }

.preset-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
}
.preset-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f7f8ff;
  cursor: default;
}
.preset-items {
  padding: 8px 14px 14px;
  background: #fff;
}
</style>
