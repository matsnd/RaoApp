<template>
  <div class="condition-panel">
    <!-- UX Help Section -->
    <div class="help-section">
      <button class="help-toggle" @click="showHelp = !showHelp">
        📖 Jak wpisać warunki rozliczenia?
        <span class="help-toggle-icon">{{ showHelp ? '▼' : '▶' }}</span>
      </button>
      <Transition name="help-slide">
        <div v-if="showHelp" class="help-content">
          <div class="help-example">
            <strong>Przykład — koparka z kaskadową stawką dobową (jak w starej aplikacji):</strong>
            <div class="help-example-item">
              <div>Warunek 1: <code>rate_type="dobowa"</code>, <code>rate1=540</code>, <code>period_count=3</code>, <code>billing_label="doba"</code></div>
              <div class="help-preview">→ preview: <strong>"1 - 3 dni - 540,00 / doba"</strong></div>
            </div>
            <div class="help-example-item">
              <div>Warunek 2: <code>rate_type="dobowa"</code>, <code>rate1=410</code>, <code>period_count=16</code>, <code>billing_label="doba"</code></div>
              <div class="help-preview">→ preview: <strong>"4 - 16 dni - 410,00 / doba"</strong></div>
            </div>
            <div class="help-example-item">
              <div>Warunek 3: <code>rate_type="dobowa"</code>, <code>rate2=350</code>, <code>billing_label="doba"</code> (bez <code>period_count</code>)</div>
              <div class="help-preview">→ preview: <strong>"powyżej 16 dni - 350,00 / doba"</strong></div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- RAO-P2-071: helper text + akcje nad gridem (inline editing, zero modali ustawień) -->
    <div class="cond-header">
      <div class="cond-header-left">
        <span class="cond-title">Warunki rozliczenia</span>
        <span class="cond-hint">Kliknij wiersz aby edytować • Enter = zapisz • Esc = anuluj</span>
      </div>
      <div style="display:flex;gap:6px;">
        <button class="btn btn-secondary btn-sm" @click="openPresetPicker" :disabled="!articleId" title="Zastosuj predefiniowany cennik">
          📋 Zastosuj cennik
        </button>
        <button class="btn btn-secondary btn-sm" @click="autoPrefillFromLast" :disabled="!articleId || autoPrefillLoading" title="Wypełnij z ostatniej umowy tej maszyny">
          {{ autoPrefillLoading ? '...' : '↻ Z ostatniej umowy' }}
        </button>
        <button class="btn btn-primary btn-sm" @click="addCondition" :disabled="showNewCondRow || editingCondId !== null" data-testid="add-condition">+ Dodaj warunek</button>
      </div>
    </div>

    <table class="data-grid" v-if="conditions.length || showNewCondRow">
      <thead>
        <tr>
          <th>Typ stawki</th>
          <th>Od</th>
          <th>Do</th>
          <th>Stawka 1 (zł)</th>
          <th>Stawka 2 (zł)</th>
          <th>Jednostka</th>
          <th>Minimum</th>
          <th style="width:80px;"></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(cond, idx) in conditions" :key="cond.id">
          <!-- EDIT MODE (inline) -->
          <tr v-if="editingCondId === cond.id" class="row-editing">
            <td>
              <select v-model="editingCondData.rate_type_id" class="form-control form-control-xs" data-testid="rate-type">
                <option :value="null">— brak —</option>
                <option v-for="rt in rateTypes" :key="rt.id" :value="rt.id">{{ rt.name }}</option>
              </select>
            </td>
            <td>
              <input v-model.number="editingCondData.period_from" type="number" min="1" class="form-control form-control-xs" placeholder="1" data-testid="period-from" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.period_to" type="number" min="1" class="form-control form-control-xs" placeholder="np. 3" data-testid="period-to" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.rate1" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="rate1" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.rate2" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="rate2" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model="editingCondData.billing_label" type="text" class="form-control form-control-xs" placeholder="doba" data-testid="billing-label" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.minimum" type="number" min="0" class="form-control form-control-xs" placeholder="0" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click.stop="saveInlineCond" :disabled="savingCond">✓</button>
              <button class="btn-icon" title="Anuluj (Esc)" @click.stop="cancelInlineCond" :disabled="savingCond">✕</button>
            </td>
          </tr>
          <!-- DISPLAY MODE -->
          <tr
            v-else
            :class="{ selected: selectedCondId === cond.id, 'row-error': cond._error }"
            style="cursor:pointer;"
            @click="selectedCondId = cond.id"
            @dblclick="startEditCond(cond)"
          >
            <td>{{ cond.rate_type_name || '—' }}</td>
            <td>{{ cond.period_from || '—' }}</td>
            <td>{{ cond.period_to || '—' }}</td>
            <td style="font-weight:600;">{{ cond.rate1 ? formatCurrency(cond.rate1) : '—' }}</td>
            <td>{{ cond.rate2 ? formatCurrency(cond.rate2) : '—' }}</td>
            <td>{{ cond.billing_label || '—' }}</td>
            <td>{{ cond.minimum || '—' }}</td>
            <td>
              <button class="btn-icon" aria-label="Edytuj" title="Edytuj" @click.stop="startEditCond(cond)" data-testid="edit-condition">✎</button>
              <button class="btn-icon" aria-label="Usuń" title="Usuń" @click.stop="removeCondition(cond)" data-testid="delete-condition">✕</button>
            </td>
          </tr>
        </template>
        <!-- NEW ROW (inline add) -->
        <tr v-if="showNewCondRow" class="row-editing">
          <td>
            <select ref="newCondRateTypeSelect" v-model="newCondData.rate_type_id" class="form-control form-control-xs" data-testid="new-rate-type">
              <option :value="null">— brak —</option>
              <option v-for="rt in rateTypes" :key="rt.id" :value="rt.id">{{ rt.name }}</option>
            </select>
          </td>
          <td>
            <input v-model.number="newCondData.period_from" type="number" min="1" class="form-control form-control-xs" placeholder="1" data-testid="new-period-from" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.period_to" type="number" min="1" class="form-control form-control-xs" placeholder="np. 3" data-testid="new-period-to" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.rate1" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="new-rate1" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.rate2" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="new-rate2" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model="newCondData.billing_label" type="text" class="form-control form-control-xs" placeholder="doba" data-testid="new-billing-label" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.minimum" type="number" min="0" class="form-control form-control-xs" placeholder="0" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click.stop="saveNewCondRow" :disabled="savingCond">✓</button>
            <button class="btn-icon" title="Anuluj (Esc)" @click.stop="cancelNewCondRow" :disabled="savingCond">✕</button>
          </td>
        </tr>
        <tr v-if="gapError" class="row-error">
          <td colspan="8" style="color:var(--color-error);font-size:11px;padding:4px;">
            ⚠️ {{ gapError }}
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="8" style="font-weight:700;text-align:right;padding-top:8px;">
            Wartość pozycji: {{ formatCurrency(calculatedValue) }}
          </td>
        </tr>
      </tfoot>
    </table>
    <!-- EMPTY STATE z CTA — tylko gdy nie dodajemy (RAO-P2-071) -->
    <div v-else class="empty-state" style="padding:16px;">
      Brak warunków — <button class="btn-link" @click="addCondition"><strong>dodaj warunek rozliczenia</strong></button>
    </div>

    <!-- Confirm modal — zastępuje confirm() (RAO-P2-071) -->
    <Transition name="modal">
      <div v-if="confirmState.show" class="modal-overlay" @click.self="cancelConfirm">
        <div class="modal-box" style="max-width:440px;" role="dialog" aria-modal="true">
          <div class="modal-title">{{ confirmState.title }}</div>
          <p style="margin:12px 0 20px;font-size:14px;line-height:1.5;color:var(--color-text-body);">{{ confirmState.message }}</p>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="cancelConfirm">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="acceptConfirm">{{ confirmState.confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- RAO-P1-001: Apply preset picker (jedyne dozwolone użycie modala) -->
    <Transition name="modal">
      <div v-if="showPresetPicker" class="modal-overlay" @click.self="showPresetPicker = false">
        <div class="modal-box" style="min-width:560px;" role="dialog" aria-modal="true" aria-labelledby="preset-picker-title">
          <div class="modal-title" id="preset-picker-title">Zastosuj cennik rozliczenia</div>
          <p style="font-size:13px;color:var(--color-text-muted);margin:4px 0 12px;">
            Warunki zostaną skopiowane (snapshot) do tej pozycji.
            <label class="checkbox-group" style="display:flex;align-items:center;gap:6px;margin-top:8px;">
              <input type="checkbox" v-model="applyReplace" />
              <span>Zastąp istniejące warunki (odznacz = dopisz do istniejących)</span>
            </label>
          </p>
          <div v-if="presetPickerLoading" class="empty-state">Ładowanie cenników…</div>
          <div v-else-if="!availablePresets.length" class="empty-state">
            Brak predefiniowanych cenników dla tej maszyny.
            Utwórz cennik w szczegółach maszyny (zakładka „Cenniki rozliczenia”).
          </div>
          <div v-else style="max-height:360px;overflow:auto;">
            <div
              v-for="preset in availablePresets"
              :key="preset.id"
              class="preset-pick-row"
              :class="{ selected: selectedPresetId === preset.id }"
              @click="selectedPresetId = preset.id"
              @dblclick="applySelectedPreset()"
            >
              <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-weight:600;">{{ preset.name }}</span>
                <span v-if="preset.is_default" class="badge badge-muted" style="font-size:10px;">Domyślny</span>
                <span style="font-size:11px;color:#5A6B7E;">({{ preset.items.length }} warunków)</span>
              </div>
              <div v-if="preset.description" style="font-size:11px;color:#5A6B7E;margin-top:2px;">{{ preset.description }}</div>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showPresetPicker = false">Anuluj</button>
            <button
              class="btn btn-primary btn-sm"
              @click="applySelectedPreset"
              :disabled="!selectedPresetId || applyingPreset"
            >
              {{ applyingPreset ? '...' : 'Zastosuj' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { useContractStore } from '@/stores/contracts'
import { useSettingsStore } from '@/stores/settings'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/format'
import api from '@/composables/useApi'

const props = defineProps({
  contractId: { type: Number, required: true },
  positionId: { type: Number, required: true },
  articleId: { type: Number, default: null },  // RAO-P1-001: do apply-preset + auto-prefill
})

const emit = defineEmits(['value-changed'])

const contractStore = useContractStore()
const settingsStore = useSettingsStore()
const toastStore = useToastStore()
const rateTypes = computed(() => settingsStore.rateTypes || [])

const conditions = ref([])
const showHelp = ref(false)
const selectedCondId = ref(null)
const savingCond = ref(false)

// RAO-P2-071: inline editing w gridzie (pattern z ContractFormView.vue — zero modali ustawień)
const editingCondId = ref<number | null>(null)
const editingCondData = ref(emptyCondData())
const showNewCondRow = ref(false)
const newCondData = ref(emptyCondData())
const newCondRateTypeSelect = ref<HTMLSelectElement | null>(null)

const gapError = ref('')  // RAO-P1-005: walidacja ciągłości

// RAO-P2-071: Confirm modal — zastępuje confirm() (pattern z ContractFormView.vue)
const confirmState = ref<{
  show: boolean
  title: string
  message: string
  confirmText: string
  onConfirm: (() => void) | null
}>({ show: false, title: '', message: '', confirmText: 'Potwierdź', onConfirm: null })

function requestConfirm(message: string, onConfirm: () => void, title = 'Potwierdzenie', confirmText = 'Potwierdź') {
  confirmState.value = { show: true, title, message, confirmText, onConfirm }
}
function acceptConfirm() {
  const fn = confirmState.value.onConfirm
  confirmState.value = { show: false, title: '', message: '', confirmText: 'Potwierdź', onConfirm: null }
  fn?.()
}
function cancelConfirm() {
  confirmState.value = { show: false, title: '', message: '', confirmText: 'Potwierdź', onConfirm: null }
}

function emptyCondData() {
  return {
    rate_type_id: null as number | null,
    description: '' as string,
    rate1: null as number | null,
    rate2: null as number | null,
    billing_label: '' as string,
    period_count: null as number | null,
    period_from: null as number | null,
    period_to: null as number | null,
    minimum: null as number | null,
  }
}

const calculatedValue = computed(() => {
  return conditions.value.reduce((sum, c) => {
    const days = c.period_to ? (c.period_to - (c.period_from || 1) + 1) : (c.period_count || 0)
    return sum + (Number(c.rate1) || 0) * days
  }, 0)
})

// RAO-P1-005: walidacja ciągłości warunków
function validateContinuity() {
  const sorted = [...conditions.value].sort((a, b) => (a.period_from || 0) - (b.period_from || 0))
  for (let i = 0; i < sorted.length - 1; i++) {
    const curr = sorted[i]
    const next = sorted[i + 1]
    if (curr.period_to && next.period_from && curr.period_to + 1 !== next.period_from) {
      gapError.value = `Luka: warunek ${curr.period_from}-${curr.period_to}, następny ${next.period_from}-${next.period_to || '∞'} (brak ${curr.period_to + 1})`
      return
    }
  }
  gapError.value = ''
}

watch(conditions, validateContinuity, { deep: true })

// RAO-P1-005: podgląd PDF live
function formatPreview(cond) {
  if (cond.period_from && cond.period_to) {
    return `${cond.period_from} - ${cond.period_to} dni - ${formatCurrency(cond.rate1)} / ${cond.billing_label || 'doba'}`
  }
  if (cond.period_from && !cond.period_to) {
    return `powyżej ${cond.period_from} dni - ${formatCurrency(cond.rate1)} / ${cond.billing_label || 'doba'}`
  }
  return `${formatCurrency(cond.rate1)} / ${cond.billing_label || 'doba'}`
}

watch(calculatedValue, (val) => emit('value-changed', val))

async function loadConditions() {
  try {
    conditions.value = await contractStore.fetchConditions(props.contractId, props.positionId)
  } catch { conditions.value = [] }
}

// RAO-P2-071: buildAutoDescription — generuje opis z inline data (używany przy zapisie)
function buildAutoDescriptionFrom(data: ReturnType<typeof emptyCondData>): string {
  const parts: string[] = []
  const rtName = rateTypes.value.find(rt => rt.id === data.rate_type_id)?.name
  if (rtName) parts.push(rtName)
  const r1 = data.rate1
  const r2 = data.rate2
  const hasR1 = r1 !== null && r1 !== '' && r1 !== undefined
  const hasR2 = r2 !== null && r2 !== '' && r2 !== undefined && Number(r2) > 0
  // RAO-P0-012: warunek "powyżej X dni" — tylko rate2, opis "powyżej N dni - 120,00 / doba"
  if (!hasR1 && hasR2 && !data.period_count) {
    const formatted = formatCurrency(r2 as number)
    parts.push(data.billing_label ? `powyżej — ${formatted}/${data.billing_label}` : `powyżej — ${formatted}`)
  } else {
    if (hasR1 || r1 === 0) {
      const formatted = formatCurrency(r1 as number)
      parts.push(data.billing_label ? `${formatted}/${data.billing_label}` : formatted)
    }
    if (hasR2) parts.push(`+ ${formatCurrency(r2 as number)}`)
    if (data.period_from && data.period_to) {
      parts.push(`${data.period_from}-${data.period_to} dni`)
    } else if (data.period_count) {
      parts.push(`do ${data.period_count}${data.billing_label ? ' ' + data.billing_label : ''}`)
    }
  }
  if (data.minimum) parts.push(`min. ${data.minimum}`)
  return parts.join(', ')
}

// RAO-P2-071: addCondition → dodaje pusty row w trybie inline-edit (zero modali)
function addCondition() {
  if (showNewCondRow.value || editingCondId.value !== null) return
  newCondData.value = emptyCondData()
  showNewCondRow.value = true
  nextTick(() => {
    newCondRateTypeSelect.value?.focus()
  })
}

// RAO-P2-071: startEditCond — inline edit istniejącego warunku (pattern jak startEditPos)
function startEditCond(cond: any) {
  if (showNewCondRow.value) return // nie edytuj gdy dodajemy nowy
  editingCondId.value = cond.id
  editingCondData.value = {
    rate_type_id: cond.rate_type_id ?? null,
    description: cond.description || '',
    rate1: cond.rate1 ?? null,
    rate2: cond.rate2 ?? null,
    billing_label: cond.billing_label || '',
    period_count: cond.period_count ?? null,
    period_from: cond.period_from ?? null,
    period_to: cond.period_to ?? null,
    minimum: cond.minimum ?? null,
  }
}

function cancelInlineCond() {
  editingCondId.value = null
  editingCondData.value = emptyCondData()
}

async function saveInlineCond() {
  if (!editingCondId.value) return
  if (savingCond.value) return // RAO-P0: guard przed double-click
  // RAO-P1-005: walidacja Od > Do
  if (editingCondData.value.period_from && editingCondData.value.period_to && editingCondData.value.period_from > editingCondData.value.period_to) {
    toastStore.error('Od musi być mniejsze lub równe Do')
    return
  }
  // RAO-P0-012: Stawka 1 wymagana TYLKO gdy nie podano Stawki 2.
  const hasRate1 = editingCondData.value.rate1 !== null && editingCondData.value.rate1 !== '' && editingCondData.value.rate1 !== undefined
  const hasRate2 = editingCondData.value.rate2 !== null && editingCondData.value.rate2 !== '' && editingCondData.value.rate2 !== undefined
  if (!hasRate1 && !hasRate2) {
    toastStore.warning('Podaj stawkę 1 lub stawkę 2')
    return
  }
  savingCond.value = true
  try {
    const payload = buildCondPayload(editingCondData.value)
    await contractStore.updateCondition(props.contractId, props.positionId, editingCondId.value, payload)
    await loadConditions()
    editingCondId.value = null
    editingCondData.value = emptyCondData()
    toastStore.success('Warunek zapisany')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd zapisu warunku')
  } finally {
    savingCond.value = false
  }
}

function cancelNewCondRow() {
  showNewCondRow.value = false
  newCondData.value = emptyCondData()
}

async function saveNewCondRow() {
  if (savingCond.value) return // RAO-P0: guard przed double-click
  // RAO-P1-005: walidacja Od > Do
  if (newCondData.value.period_from && newCondData.value.period_to && newCondData.value.period_from > newCondData.value.period_to) {
    toastStore.error('Od musi być mniejsze lub równe Do')
    return
  }
  // RAO-P0-012: Stawka 1 wymagana TYLKO gdy nie podano Stawki 2.
  const hasRate1 = newCondData.value.rate1 !== null && newCondData.value.rate1 !== '' && newCondData.value.rate1 !== undefined
  const hasRate2 = newCondData.value.rate2 !== null && newCondData.value.rate2 !== '' && newCondData.value.rate2 !== undefined
  if (!hasRate1 && !hasRate2) {
    toastStore.warning('Podaj stawkę 1 lub stawkę 2')
    return
  }
  savingCond.value = true
  try {
    const payload = buildCondPayload(newCondData.value)
    await contractStore.createCondition(props.contractId, props.positionId, payload)
    await loadConditions()
    showNewCondRow.value = false
    newCondData.value = emptyCondData()
    toastStore.success('Warunek dodany')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd zapisu warunku')
  } finally {
    savingCond.value = false
  }
}

// RAO-P2-071: buildCondPayload — normalizuje dane przed wysłaniem do API
function buildCondPayload(data: ReturnType<typeof emptyCondData>) {
  const payload: any = { ...data }
  if (!payload.billing_label) payload.billing_label = null
  if (!payload.rate1) payload.rate1 = null
  if (!payload.rate2) payload.rate2 = null
  if (!payload.period_from) payload.period_from = null
  if (!payload.period_to) payload.period_to = null
  if (!payload.minimum) payload.minimum = null
  // Auto-generuj opis jeśli pusty
  if (!payload.description) payload.description = buildAutoDescriptionFrom(data)
  return payload
}

// RAO-P2-071: removeCondition — zastąpiono confirm() modalnem potwierdzenia
async function removeCondition(cond: any) {
  requestConfirm(
    `Usunąć warunek rozliczenia (${cond.rate_type_name || '—'})?`,
    async () => {
      try {
        await contractStore.deleteCondition(props.contractId, props.positionId, cond.id)
        await loadConditions()
        toastStore.success('Warunek usunięty')
      } catch (e: any) {
        toastStore.error(e?.response?.data?.detail || 'Błąd usuwania warunku')
      }
    },
    'Usuń warunek',
    'Usuń',
  )
}

watch(() => props.positionId, loadConditions, { immediate: true })

// --- RAO-P1-001: Apply preset + auto-prefill ---
const showPresetPicker = ref(false)
const presetPickerLoading = ref(false)
const availablePresets = ref([])
const selectedPresetId = ref(null)
const applyReplace = ref(true)
const applyingPreset = ref(false)
const autoPrefillLoading = ref(false)

async function openPresetPicker() {
  if (!props.articleId) {
    toastStore.warning('Pozycja nie ma przypisanej maszyny')
    return
  }
  showPresetPicker.value = true
  selectedPresetId.value = null
  presetPickerLoading.value = true
  try {
    const { data } = await api.get(`/settings/articles/${props.articleId}/rate-presets`)
    availablePresets.value = data
    // Pre-wybierz domyślny
    const def = data.find(p => p.is_default)
    if (def) selectedPresetId.value = def.id
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd pobierania cenników')
  } finally {
    presetPickerLoading.value = false
  }
}

async function applySelectedPreset() {
  if (!selectedPresetId.value) return
  applyingPreset.value = true
  try {
    const result = await contractStore.applyRatePreset(
      props.contractId,
      props.positionId,
      selectedPresetId.value,
      applyReplace.value
    )
    toastStore.success(`Zastosowano cennik (${result.applied_count} warunków)`)
    showPresetPicker.value = false
    await loadConditions()
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd zastosowania cennika')
  } finally {
    applyingPreset.value = false
  }
}

async function autoPrefillFromLast() {
  if (!props.articleId) {
    toastStore.warning('Pozycja nie ma przypisanej maszyny')
    return
  }
  autoPrefillLoading.value = true
  try {
    const data = await contractStore.fetchLastConditionsForArticle(props.articleId)
    if (!data?.conditions?.length) {
      toastStore.info('Brak warunków w ostatniej umowie tej maszyny')
      return
    }
    // Skopiuj warunki jako nowe PositionCondition (dopisz, nie zastępuj)
    for (const cond of data.conditions) {
      await contractStore.createCondition(props.contractId, props.positionId, {
        rate_type_id: cond.rate_type_id,
        description: cond.description || null,
        rate1: cond.rate1,
        rate2: cond.rate2,
        billing_label: cond.billing_label || null,
        period_count: cond.period_count,
        minimum: cond.minimum,
      })
    }
    toastStore.success(`Wypełniono z umowy ${data.source_contract_number} (${data.conditions.length} warunków)`)
    await loadConditions()
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    if (err?.response?.status === 404) {
      toastStore.info('Brak historii umów dla tej maszyny')
    } else {
      toastStore.error(err?.response?.data?.detail || 'Błąd pobierania ostatnich warunków')
    }
  } finally {
    autoPrefillLoading.value = false
  }
}

defineExpose({ loadConditions, calculatedValue })
</script>

<style scoped>
.condition-panel { margin-top: 12px; }
.cond-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}
.cond-header-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-right: auto;
}
.cond-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}
.cond-hint {
  font-size: 11px;
  color: var(--color-text-muted);
}
.btn-link {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 13px;
  padding: 0;
  text-decoration: underline;
}
.btn-link:hover { text-decoration: none; }
.form-control-xs {
  font-size: 12px;
  padding: 4px 6px;
}
.row-editing {
  background: var(--color-bg-light);
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
.btn-auto-desc {
  background: none;
  border: 1px solid #CBD5E0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  padding: 1px 5px;
  margin-left: 6px;
  color: #5A6B7E;
  vertical-align: middle;
  transition: background 150ms;
}
.btn-auto-desc:hover { background: #EDF2F7; }


/* UX Help Section */
.help-section {
  margin-bottom: 12px;
}
.help-toggle {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  width: 100%;
  text-align: left;
  transition: all 150ms;
}
.help-toggle:hover {
  background: #EDF2F7;
}
.help-toggle-icon {
  float: right;
  font-size: 12px;
}
.help-content {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: 12px;
  margin-top: 8px;
  font-size: 12px;
}
.help-example {
  line-height: 1.6;
}
.help-example-item {
  margin: 8px 0;
  padding: 8px;
  background: var(--color-bg-white);
  border-radius: 8px;
}
.help-example-item code {
  background: #EDF2F7;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 13px;
}
.help-preview {
  margin-top: 4px;
  color: var(--color-text-body);
  font-size: 13px;
}
.help-slide-enter-active,
.help-slide-leave-active {
  transition: all 200ms ease;
}
.help-slide-enter-from,
.help-slide-leave-to {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}
.help-slide-enter-to,
.help-slide-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* Field Tooltip */
.field-tooltip {
  display: inline-block;
  margin-left: 6px;
  color: #5A6B7E;
  font-size: 12px;
  cursor: help;
}

/* Live Preview */
.live-preview {
  background: #F7FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  color: #2D3748;
  min-height: 40px;
}

/* RAO-P1-001: preset picker rows */
.preset-pick-row {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 150ms;
}
.preset-pick-row:hover {
  background: #F7FAFC;
  border-color: var(--color-primary);
}
.preset-pick-row.selected {
  background: #EBF4FF;
  border-color: var(--color-primary);
}
.checkbox-group {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}
</style>
