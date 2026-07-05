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

    <div class="cond-header">
      <span class="cond-title">Warunki rozliczenia</span>
      <div style="display:flex;gap:6px;">
        <button class="btn btn-secondary btn-sm" @click="openPresetPicker" :disabled="!articleId" title="Zastosuj predefiniowany cennik">
          📋 Zastosuj cennik
        </button>
        <button class="btn btn-secondary btn-sm" @click="autoPrefillFromLast" :disabled="!articleId || autoPrefillLoading" title="Wypełnij z ostatniej umowy tej maszyny">
          {{ autoPrefillLoading ? '...' : '↻ Z ostatniej umowy' }}
        </button>
        <button class="btn btn-primary btn-sm" @click="addCondition">+ Dodaj warunek</button>
      </div>
    </div>
    <table class="data-grid" v-if="conditions.length">
      <thead>
        <tr>
          <th>Typ stawki</th>
          <th>Stawka 1 (zł)</th>
          <th>Stawka 2 (zł)</th>
          <th>Jednostka</th>
          <th>Okresy</th>
          <th>Minimum</th>
          <th>Opis</th>
          <th style="width:80px;"></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="cond in conditions"
          :key="cond.id"
          :class="{ selected: selectedCondId === cond.id }"
          @click="selectedCondId = cond.id"
          @dblclick="editCondition(cond)"
        >
          <td>{{ cond.rate_type_name || '—' }}</td>
          <td style="font-weight:600;">{{ cond.rate1 ? formatCurrency(cond.rate1) : '—' }}</td>
          <td>{{ cond.rate2 ? formatCurrency(cond.rate2) : '—' }}</td>
          <td>{{ cond.billing_label || '—' }}</td>
          <td>{{ cond.period_count || '—' }}</td>
          <td>{{ cond.minimum || '—' }}</td>
          <td style="font-size:11px;color:#5A6B7E;">{{ cond.description || '—' }}</td>
          <td>
            <button class="btn-icon" aria-label="Edytuj" title="Edytuj" @click.stop="editCondition(cond)">✎</button>
            <button class="btn-icon" aria-label="Usuń" title="Usuń" @click.stop="removeCondition(cond)">✕</button>
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
    <div v-else class="empty-state" style="padding:16px;">Brak warunków — dodaj warunek rozliczenia</div>

    <!-- Condition form modal -->
    <Transition name="modal">
      <div v-if="showCondModal" class="modal-overlay" @click.self="showCondModal = false">
        <div class="modal-box" style="min-width:520px;" role="dialog" aria-modal="true" aria-labelledby="cond-modal-title">
          <div class="modal-title" id="cond-modal-title">{{ editingCond ? 'Edycja warunku' : 'Nowy warunek' }}</div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Typ stawki</label>
              <select v-model="condForm.rate_type_id" class="form-control">
                <option :value="null">— brak —</option>
                <option v-for="rt in rateTypes" :key="rt.id" :value="rt.id">{{ rt.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Jednostka rozliczeniowa</label>
              <select v-model="condForm.billing_label" class="form-control">
                <option value="">— brak —</option>
                <option value="doba">doba</option>
                <option value="tydzień">tydzień</option>
                <option value="2 tygodnie">2 tygodnie</option>
                <option value="miesiąc">miesiąc</option>
                <option value="godzina">godzina</option>
                <option value="jednorazowo">jednorazowo</option>
              </select>
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Stawka 1 (zł) *</label>
              <input v-model="condForm.rate1" type="number" step="0.01" class="form-control" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label class="form-label">Stawka 2 (zł)</label> <span class="field-tooltip" title="ostatni warunek (powyżej) — pozostaw period_count puste">ⓘ</span>
              <input v-model="condForm.rate2" type="number" step="0.01" class="form-control" placeholder="0.00" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Liczba okresów</label>
              <input v-model.number="condForm.period_count" type="number" class="form-control" placeholder="np. 5" />
            </div>
            <div class="form-group">
              <label class="form-label">Minimum (okresów)</label>
              <input v-model.number="condForm.minimum" type="number" class="form-control" placeholder="np. 1" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Opis <button type="button" class="btn-auto-desc" title="Generuj opis automatycznie" @click="condForm.description = buildAutoDescription()">↻ auto</button></label>
            <input v-model="condForm.description" type="text" class="form-control" placeholder="np. stawka 5000 zł/tyg. do 5 tygodni" />
          </div>
                    <!-- Live Preview -->
          <div class="form-group" v-if="condForm.rate1 || condForm.rate2">
            <label class="form-label">Podgląd formatu kaskadowego</label>
            <div class="live-preview">{{ formatCascadingPreview() }}</div>
          </div>
<div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showCondModal = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="saveCondition" :disabled="savingCond">{{ savingCond ? '...' : 'Zapisz' }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- RAO-P1-001: Apply preset picker -->
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
const showCondModal = ref(false)
const editingCond = ref(null)
const savingCond = ref(false)
const condForm = ref({
  rate_type_id: null, description: '', rate1: null, rate2: null,
  billing_label: '', period_count: null, minimum: null,
})

const calculatedValue = computed(() => {
  return conditions.value.reduce((sum, c) => {
    return sum + (Number(c.rate1) || 0) * (Number(c.period_count) || 0)
  }, 0)
})

watch(calculatedValue, (val) => emit('value-changed', val))

async function loadConditions() {
  try {
    conditions.value = await contractStore.fetchConditions(props.contractId, props.positionId)
  } catch { conditions.value = [] }
}

function buildAutoDescription() {
  const parts = []
  const rtName = rateTypes.value.find(rt => rt.id === condForm.value.rate_type_id)?.name
  if (rtName) parts.push(rtName)
  const r1 = condForm.value.rate1
  if (r1 || r1 === 0) {
    const formatted = formatCurrency(r1)
    parts.push(condForm.value.billing_label ? `${formatted}/${condForm.value.billing_label}` : formatted)
  }
  const r2 = condForm.value.rate2
  if (r2 && Number(r2) > 0) parts.push(`+ ${formatCurrency(r2)}`)
  if (condForm.value.period_count) {
    parts.push(`do ${condForm.value.period_count}${condForm.value.billing_label ? ' ' + condForm.value.billing_label : ''}`)
  }
  if (condForm.value.minimum) parts.push(`min. ${condForm.value.minimum}`)
  return parts.join(', ')
}

// Auto-fill description for new conditions when fields change
watch(
  () => [condForm.value.rate_type_id, condForm.value.rate1, condForm.value.rate2, condForm.value.billing_label, condForm.value.period_count],
  () => {
    if (!showCondModal.value || editingCond.value) return
    condForm.value.description = buildAutoDescription()
  }
)

function addCondition() {
  editingCond.value = null
  Object.assign(condForm.value, {
    rate_type_id: null, description: '', rate1: null, rate2: null,
    billing_label: '', period_count: null, minimum: null,
  })
  showCondModal.value = true
}

function editCondition(cond) {
  editingCond.value = cond
  Object.assign(condForm.value, {
    rate_type_id: cond.rate_type_id,
    description: cond.description || '',
    rate1: cond.rate1,
    rate2: cond.rate2,
    billing_label: cond.billing_label || '',
    period_count: cond.period_count,
    minimum: cond.minimum,
  })
  showCondModal.value = true
}

async function saveCondition() {
  if (!condForm.value.rate1 && condForm.value.rate1 !== 0) {
    toastStore.warning('Podaj stawkę 1')
    return
  }
  savingCond.value = true
  try {
    const payload = { ...condForm.value }
    if (!payload.billing_label) payload.billing_label = null
    if (!payload.rate2) payload.rate2 = null
    if (editingCond.value) {
      await contractStore.updateCondition(props.contractId, props.positionId, editingCond.value.id, payload)
    } else {
      await contractStore.createCondition(props.contractId, props.positionId, payload)
    }
    await loadConditions()
    showCondModal.value = false
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd zapisu warunku')
  } finally {
    savingCond.value = false
  }
}

async function removeCondition(cond) {
  if (!confirm('Usunąć ten warunek?')) return
  try {
    await contractStore.deleteCondition(props.contractId, props.positionId, cond.id)
    await loadConditions()
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd')
  }
}



function formatCascadingPreview() {
  // Frontend version of format_position_conditions_cascading from backend
  const tempConds = []
  if (condForm.value.rate1 !== null && condForm.value.rate1 !== undefined && condForm.value.rate1 !== '') {
    tempConds.push({
      rate1: Number(condForm.value.rate1),
      rate2: condForm.value.rate2 ? Number(condForm.value.rate2) : null,
      billing_label: condForm.value.billing_label || 'doba',
      period_count: condForm.value.period_count
    })
  }
  
  if (!tempConds.length) return ''
  
  const sorted = [...tempConds].sort((a, b) => {
    if (a.period_count === null || a.period_count === undefined) return 1
    if (b.period_count === null || b.period_count === undefined) return -1
    return a.period_count - b.period_count
  })
  
  const lines = []
  let prevPeriod = 0
  
  for (const c of sorted) {
    const label = c.billing_label || 'doba'
    if (c.period_count !== null && c.period_count !== undefined && c.rate1 !== null) {
      const start = prevPeriod + 1
      const end = c.period_count
      let rangeText = ''
      if (start === end) {
        rangeText = `${start} ${label}`
      } else {
        rangeText = `${start} - ${end} dni`
      }
      const rateText = c.rate1.toFixed(2).replace('.', ',')
      lines.push(`${rangeText} - ${rateText} / ${label}`)
      prevPeriod = c.period_count
    } else if (c.rate2 !== null && prevPeriod > 0) {
      const rateText = c.rate2.toFixed(2).replace('.', ',')
      lines.push(`powyżej ${prevPeriod} dni - ${rateText} / ${label}`)
    }
  }

  return lines.join('\n') || 'Wypełnij pola, aby zobaczyć podgląd'
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
}
.cond-title {
  font-size: 13px;
  font-weight: 700;
  color: #0F234E;
  margin-right: auto;
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
