<template>
  <div class="rate-presets-section">
    <div class="section-title">
      <span>Cenniki rozliczenia</span>
      <button type="button" class="btn btn-secondary btn-sm" @click="openNewPresetForm">+ Nowy cennik</button>
    </div>
    <p class="section-hint">
      Predefiniowane zestawy warunków rozliczenia dla tej maszyny. Po zastosowaniu w umowie
      warunki są kopiowane (snapshot) — edycja cenniku nie wpływa na istniejące umowy.
    </p>

    <div v-if="settingsStore.ratePresetsLoading" class="empty-state">Ładowanie cenników…</div>
    <div v-else-if="!settingsStore.ratePresets.length" class="empty-state">
      Brak cenników — utwórz pierwszy cennik powyżej.
    </div>

    <div v-for="preset in settingsStore.ratePresets" :key="preset.id" class="preset-card">
      <div class="preset-header">
        <div style="display:flex;align-items:center;gap:8px;">
          <span v-if="editingPresetId !== preset.id" style="font-weight:600;font-size:14px;">{{ preset.name }}</span>
          <input
            v-else
            v-model="editingPresetName"
            class="form-control form-control-xs"
            style="width:260px;"
            @keydown.enter="savePresetName(preset)"
            @keydown.esc="editingPresetId = null"
          />
          <span v-if="preset.is_default" class="badge badge-muted" style="font-size:10px;">Domyślny</span>
          <span style="font-size:11px;color:#5A6B7E;">({{ preset.items.length }} pozycji)</span>
        </div>
        <div style="display:flex;gap:4px;">
          <button
            v-if="editingPresetId !== preset.id"
            class="btn-icon"
            aria-label="Zmień nazwę"
            title="Zmień nazwę"
            @click="startEditPreset(preset)"
          >✎</button>
          <button
            v-else
            class="btn-icon"
            style="color:#22543D;"
            aria-label="Zapisz"
            title="Zapisz"
            @click="savePresetName(preset)"
          >✓</button>
          <button
            v-if="!preset.is_default"
            class="btn-icon"
            aria-label="Ustaw jako domyślny"
            title="Ustaw jako domyślny"
            @click="setDefault(preset.id)"
          >★</button>
          <button
            class="btn-icon"
            :class="{ active: expandedPresetId === preset.id }"
            aria-label="Pokaż/ukryj pozycje"
            title="Pokaż/ukryj pozycje"
            @click="toggleExpand(preset.id)"
          >{{ expandedPresetId === preset.id ? '▲' : '▼' }}</button>
          <button
            class="btn-icon"
            aria-label="Usuń cennik"
            title="Usuń cennik"
            @click="deletePreset(preset.id)"
          >✕</button>
        </div>
      </div>

      <!-- Expanded items -->
      <div v-if="expandedPresetId === preset.id" class="preset-items">
        <table class="data-grid" style="margin-top:8px;">
          <thead>
            <tr>
              <th style="width:18%;">Typ stawki</th>
              <th style="width:10%;">Stawka 1 (zł)</th>
              <th style="width:10%;">Stawka 2 (zł)</th>
              <th style="width:10%;">Jednostka</th>
              <th style="width:8%;">Okresy</th>
              <th style="width:8%;">Minimum</th>
              <th>Opis</th>
              <th style="width:64px;"></th>
            </tr>
          </thead>
          <tbody v-if="preset.items && preset.items.length > 0">
            <tr v-for="item in preset.items" :key="item.id">
              <template v-if="editingItemId === item.id">
                <td>
                  <select v-model="editingItemData.rate_type_id" class="form-control form-control-xs">
                    <option :value="null">— brak —</option>
                    <option v-for="rt in rateTypes" :key="rt.id" :value="rt.id">{{ rt.name }}</option>
                  </select>
                </td>
                <td><input v-model="editingItemData.rate1" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveItem(preset.id)" @keydown.esc="editingItemId = null" /></td>
                <td><input v-model="editingItemData.rate2" type="number" step="0.01" class="form-control form-control-xs" @keydown.enter="saveItem(preset.id)" @keydown.esc="editingItemId = null" /></td>
                <td>
                  <select v-model="editingItemData.billing_label" class="form-control form-control-xs">
                    <option value="">— brak —</option>
                    <option value="doba">doba</option>
                    <option value="tydzień">tydzień</option>
                    <option value="2 tygodnie">2 tygodnie</option>
                    <option value="miesiąc">miesiąc</option>
                    <option value="godzina">godzina</option>
                    <option value="jednorazowo">jednorazowo</option>
                  </select>
                </td>
                <td><input v-model.number="editingItemData.period_count" type="number" class="form-control form-control-xs" @keydown.enter="saveItem(preset.id)" @keydown.esc="editingItemId = null" /></td>
                <td><input v-model.number="editingItemData.minimum" type="number" class="form-control form-control-xs" @keydown.enter="saveItem(preset.id)" @keydown.esc="editingItemId = null" /></td>
                <td><input v-model="editingItemData.description" class="form-control form-control-xs" @keydown.enter="saveItem(preset.id)" @keydown.esc="editingItemId = null" /></td>
                <td>
                  <button class="btn-icon" style="color:#22543D;" aria-label="Zapisz" title="Zapisz" @click="saveItem(preset.id)">✓</button>
                  <button class="btn-icon" aria-label="Anuluj" title="Anuluj" @click="editingItemId = null">✕</button>
                </td>
              </template>
              <template v-else>
                <td @click="startEditItem(item)" style="cursor:pointer;">{{ rateTypeName(item.rate_type_id) }}</td>
                <td @click="startEditItem(item)" style="cursor:pointer;font-weight:600;">{{ item.rate1 ? formatCurrency(item.rate1) : '—' }}</td>
                <td @click="startEditItem(item)" style="cursor:pointer;">{{ item.rate2 ? formatCurrency(item.rate2) : '—' }}</td>
                <td @click="startEditItem(item)" style="cursor:pointer;">{{ item.billing_label || '—' }}</td>
                <td @click="startEditItem(item)" style="cursor:pointer;">{{ item.period_count || '—' }}</td>
                <td @click="startEditItem(item)" style="cursor:pointer;">{{ item.minimum || '—' }}</td>
                <td @click="startEditItem(item)" style="cursor:pointer;font-size:11px;">{{ item.description || '—' }}</td>
                <td>
                  <button class="btn-icon" aria-label="Edytuj" title="Edytuj" @click.stop="startEditItem(item)">✎</button>
                  <button class="btn-icon" aria-label="Usuń" title="Usuń" @click.stop="deleteItem(item.id)">✕</button>
                </td>
              </template>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="8" style="text-align:center;padding:20px;color:#5A6B7E;">
                Brak warunków w tym cenniku
              </td>
            </tr>
          </tbody>
          <!-- Nowy wiersz -->
          <tbody>
            <tr v-if="addingToPresetId === preset.id" style="background:#f0fff4;">
              <td>
                <select v-model="newItem.rate_type_id" class="form-control form-control-xs">
                  <option :value="null">— brak —</option>
                  <option v-for="rt in rateTypes" :key="rt.id" :value="rt.id">{{ rt.name }}</option>
                </select>
              </td>
              <td><input v-model="newItem.rate1" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" @keydown.enter="saveNewItem(preset.id)" @keydown.esc="addingToPresetId = null" /></td>
              <td><input v-model="newItem.rate2" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" @keydown.enter="saveNewItem(preset.id)" @keydown.esc="addingToPresetId = null" /></td>
              <td>
                <select v-model="newItem.billing_label" class="form-control form-control-xs">
                  <option value="">— brak —</option>
                  <option value="doba">doba</option>
                  <option value="tydzień">tydzień</option>
                  <option value="2 tygodnie">2 tygodnie</option>
                  <option value="miesiąc">miesiąc</option>
                  <option value="godzina">godzina</option>
                  <option value="jednorazowo">jednorazowo</option>
                </select>
              </td>
              <td><input v-model.number="newItem.period_count" type="number" class="form-control form-control-xs" placeholder="np. 5" @keydown.enter="saveNewItem(preset.id)" @keydown.esc="addingToPresetId = null" /></td>
              <td><input v-model.number="newItem.minimum" type="number" class="form-control form-control-xs" placeholder="np. 1" @keydown.enter="saveNewItem(preset.id)" @keydown.esc="addingToPresetId = null" /></td>
              <td><input v-model="newItem.description" class="form-control form-control-xs" @keydown.enter="saveNewItem(preset.id)" @keydown.esc="addingToPresetId = null" /></td>
              <td>
                <button class="btn-icon" style="color:#22543D;" aria-label="Dodaj (Enter)" title="Dodaj (Enter)" @click="saveNewItem(preset.id)">✓</button>
                <button class="btn-icon" aria-label="Anuluj" title="Anuluj" @click="addingToPresetId = null">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
        <button class="btn btn-secondary btn-sm" style="margin-top:8px;" @click="startAddItem(preset.id)">+ Dodaj warunek</button>
      </div>
    </div>

    <!-- Modal: nowy cennik z warunkami -->
    <Transition name="modal">
      <div v-if="showNewPresetModal" class="modal-overlay" @click.self="closeNewPresetForm">
        <div class="modal-box" style="min-width:640px;" role="dialog" aria-modal="true" aria-labelledby="new-preset-title">
          <div class="modal-title" id="new-preset-title">Nowy cennik rozliczenia</div>
          <p style="font-size:13px;color:var(--color-text-muted);margin:4px 0 12px;">
            <strong>{{ articleName }}</strong> — utwórz zestaw warunków rozliczenia do wielokrotnego użytku.
          </p>
          <div v-if="presetError" style="color:var(--color-danger);padding:8px;background:#FED7D7;border-radius:6px;margin-bottom:12px;font-size:13px;" role="alert">
            {{ presetError }}
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Nazwa cennika *</label>
              <input v-model="newPreset.name" type="text" class="form-control" placeholder="np. Standard, Promo Q1…" />
            </div>
            <div class="form-group">
              <label class="form-label">Opis (opcjonalnie)</label>
              <input v-model="newPreset.description" type="text" class="form-control" placeholder="Krótki opis" />
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-group">
              <input type="checkbox" v-model="newPreset.is_default" />
              <span>Ustaw jako domyślny cennik tej maszyny</span>
            </label>
          </div>

          <div class="section-title" style="font-size:13px;margin-top:16px;margin-bottom:8px;">Warunki rozliczenia</div>
          <table class="data-grid" style="font-size:12px;">
            <thead>
              <tr>
                <th style="width:18%;">Typ stawki</th>
                <th style="width:10%;">Stawka 1</th>
                <th style="width:10%;">Stawka 2</th>
                <th style="width:12%;">Jednostka</th>
                <th style="width:8%;">Okresy</th>
                <th style="width:8%;">Min.</th>
                <th>Opis</th>
                <th style="width:40px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in newPreset.items" :key="idx">
                <td>
                  <select v-model="item.rate_type_id" class="form-control form-control-xs">
                    <option :value="null">— brak —</option>
                    <option v-for="rt in rateTypes" :key="rt.id" :value="rt.id">{{ rt.name }}</option>
                  </select>
                </td>
                <td><input v-model="item.rate1" type="number" step="0.01" class="form-control form-control-xs" /></td>
                <td><input v-model="item.rate2" type="number" step="0.01" class="form-control form-control-xs" /></td>
                <td>
                  <select v-model="item.billing_label" class="form-control form-control-xs">
                    <option value="">—</option>
                    <option value="doba">doba</option>
                    <option value="tydzień">tydzień</option>
                    <option value="2 tygodnie">2 tygodnie</option>
                    <option value="miesiąc">miesiąc</option>
                    <option value="godzina">godzina</option>
                    <option value="jednorazowo">jednorazowo</option>
                  </select>
                </td>
                <td><input v-model.number="item.period_count" type="number" class="form-control form-control-xs" /></td>
                <td><input v-model.number="item.minimum" type="number" class="form-control form-control-xs" /></td>
                <td><input v-model="item.description" class="form-control form-control-xs" /></td>
                <td>
                  <button class="btn-icon" aria-label="Usuń wiersz" title="Usuń wiersz" @click="newPreset.items.splice(idx, 1)">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
          <button class="btn btn-secondary btn-sm" style="margin-top:8px;" @click="addNewPresetItemRow">+ Dodaj warunek</button>

          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="closeNewPresetForm">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="saveNewPreset" :disabled="presetSaving">
              {{ presetSaving ? '...' : 'Zapisz cennik' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/format'

const props = defineProps({
  articleId: { type: Number, required: true },
  articleName: { type: String, default: '' },
})

const emit = defineEmits(['presets-changed'])

const settingsStore = useSettingsStore()
const toastStore = useToastStore()
const rateTypes = computed(() => settingsStore.rateTypes || [])

const expandedPresetId = ref(null)
const editingPresetId = ref(null)
const editingPresetName = ref('')
const editingItemId = ref(null)
const editingItemData = ref({})
const addingToPresetId = ref(null)
const newItem = ref(emptyItem())

const showNewPresetModal = ref(false)
const presetSaving = ref(false)
const presetError = ref('')
const newPreset = ref({ name: '', description: '', is_default: false, items: [] })

function emptyItem() {
  return {
    rate_type_id: null, rate1: null, rate2: null,
    billing_label: '', period_count: null, minimum: null, description: '',
  }
}

function rateTypeName(id) {
  if (!id) return '—'
  return rateTypes.value.find(rt => rt.id === id)?.name || '—'
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
  try {
    await settingsStore.updateRatePreset(preset.id, { name: editingPresetName.value })
    editingPresetId.value = null
    toastStore.success('Nazwa cennika zapisana')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd zapisu')
  }
}

async function setDefault(presetId) {
  try {
    await settingsStore.setDefaultRatePreset(presetId)
    toastStore.success('Ustawiono jako domyślny')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd')
  }
}

async function deletePreset(presetId) {
  if (!confirm('Usunąć ten cennik i wszystkie jego warunki?')) return
  try {
    await settingsStore.deleteRatePreset(presetId)
    if (expandedPresetId.value === presetId) expandedPresetId.value = null
    toastStore.success('Cennik usunięty')
    emit('presets-changed')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd usuwania')
  }
}

function startEditItem(item) {
  editingItemId.value = item.id
  editingItemData.value = {
    rate_type_id: item.rate_type_id,
    rate1: item.rate1,
    rate2: item.rate2,
    billing_label: item.billing_label || '',
    period_count: item.period_count,
    minimum: item.minimum,
    description: item.description || '',
  }
}

async function saveItem(presetId) {
  try {
    const payload = { ...editingItemData.value }
    if (!payload.billing_label) payload.billing_label = null
    if (!payload.rate2) payload.rate2 = null
    if (!payload.description) payload.description = null
    await settingsStore.updateRatePresetItem(editingItemId.value, payload)
    editingItemId.value = null
    toastStore.success('Warunek zapisany')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd zapisu')
  }
}

async function deleteItem(itemId) {
  if (!confirm('Usunąć ten warunek z cennika?')) return
  try {
    await settingsStore.deleteRatePresetItem(itemId)
    toastStore.success('Warunek usunięty')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd usuwania')
  }
}

function startAddItem(presetId) {
  addingToPresetId.value = presetId
  newItem.value = emptyItem()
}

async function saveNewItem(presetId) {
  try {
    const payload = { ...newItem.value }
    if (!payload.billing_label) payload.billing_label = null
    if (!payload.rate2) payload.rate2 = null
    if (!payload.description) payload.description = null
    await settingsStore.addRatePresetItem(presetId, payload)
    addingToPresetId.value = null
    toastStore.success('Warunek dodany')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd dodawania')
  }
}

// --- Nowy cennik z warunkami (modal) ---
function openNewPresetForm() {
  newPreset.value = { name: '', description: '', is_default: false, items: [] }
  presetError.value = ''
  showNewPresetModal.value = true
}

function closeNewPresetForm() {
  showNewPresetModal.value = false
  presetError.value = ''
}

function addNewPresetItemRow() {
  newPreset.value.items.push(emptyItem())
}

async function saveNewPreset() {
  if (!newPreset.value.name?.trim()) {
    presetError.value = 'Podaj nazwę cennika'
    return
  }
  presetSaving.value = true
  presetError.value = ''
  try {
    // Normalizuj items przed wysłaniem
    const items = newPreset.value.items.map(it => ({
      rate_type_id: it.rate_type_id || null,
      rate1: it.rate1 === '' || it.rate1 === null ? null : it.rate1,
      rate2: it.rate2 === '' || it.rate2 === null ? null : it.rate2,
      billing_label: it.billing_label || null,
      period_count: it.period_count || null,
      minimum: it.minimum || null,
      description: it.description || null,
    }))
    await settingsStore.createRatePreset(props.articleId, {
      name: newPreset.value.name,
      description: newPreset.value.description || null,
      is_default: newPreset.value.is_default,
      items,
    })
    toastStore.success('Cennik utworzony')
    closeNewPresetForm()
    emit('presets-changed')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    presetError.value = err?.response?.data?.detail || 'Błąd zapisu cennika'
  } finally {
    presetSaving.value = false
  }
}
</script>

<style scoped>
.rate-presets-section {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border, #e2e8f0);
}
.section-title {
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-2);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: -4px 0 12px;
  line-height: 1.5;
}
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
}
.preset-items {
  padding: 8px 14px 14px;
  background: #fff;
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
.empty-state {
  font-size: 13px;
  text-align: left;
  padding: 12px;
  color: var(--color-text-muted);
}
</style>
