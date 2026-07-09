<template>
  <div class="condition-panel">
    <!-- RAO-P2-071: helper text + akcje nad gridem (inline editing, zero modali ustawień) -->
    <div class="cond-header">
      <div class="cond-header-left">
        <span class="cond-title">Warunki rozliczenia</span>
        <span class="cond-hint">Kliknij wiersz aby edytować • Enter = zapisz • Esc = anuluj</span>
      </div>
      <div class="cond-header-right">
        <select v-if="rangeTemplateOptions.length" v-model="selectedRangeTemplate" @change="applyRangeTemplate" class="form-control form-control-xs" title="Dodaje gotowe przedziały dni lub godzin do cennika" :disabled="isSettled">
          <option :value="null">Gotowe przedziały…</option>
          <option v-for="opt in rangeTemplateOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
        </select>
        <button class="btn btn-secondary btn-sm" @click="autoPrefillFromLast" :disabled="!articleId || autoPrefillLoading || isSettled" title="Wypełnij z ostatniej umowy tej maszyny">
          {{ autoPrefillLoading ? '...' : '↻ Z ostatniej umowy' }}
        </button>
        <button class="btn btn-secondary btn-sm" @click="openPresetPicker" :disabled="!articleId || isSettled" title="Zastosuj predefiniowany cennik">
          📋 Zastosuj cennik
        </button>
        <button class="btn btn-primary btn-sm" @click="addCondition" :disabled="showNewCondRow || editingCondId !== null || isSettled" data-testid="add-condition">+ Dodaj warunek</button>
      </div>
    </div>

    <table class="data-grid" v-if="conditions.length || showNewCondRow">
      <thead>
        <tr>
          <th>{{ isRental ? 'Od (dni)' : 'Od (godz.)' }}</th>
          <th>{{ isRental ? 'Do (dni)' : 'Do (godz.)' }}</th>
          <th>Stawka (zł)</th>
          <th>Jednostka</th>
          <th>Minimum</th>
          <th style="width:80px;"></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(cond) in conditions" :key="cond.id">
          <!-- EDIT MODE (inline) -->
          <tr v-if="editingCondId === cond.id" class="row-editing">
            <td>
              <input v-model.number="editingCondData.period_from" type="number" :min="isRental ? 1 : 0" class="form-control form-control-xs" :placeholder="isRental ? '1' : '0'" data-testid="period-from" :disabled="isSettled" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.period_to" type="number" :min="isRental ? 1 : 0" class="form-control form-control-xs" :placeholder="isRental ? 'np. 3' : 'np. 8'" data-testid="period-to" :disabled="isSettled" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.rate1" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="rate1" :disabled="isSettled" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <span class="form-control-xs" style="display:inline-flex;align-items:center;height:28px;padding:2px 0;">{{ editingCondData.billing_label || defaultLabel }}</span>
            </td>
            <td>
              <input v-model.number="editingCondData.minimum" type="number" min="0" class="form-control form-control-xs" placeholder="0" :disabled="isSettled" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click.stop="saveInlineCond" :disabled="savingCond || isSettled">✓</button>
              <button class="btn-icon" title="Anuluj (Esc)" @click.stop="cancelInlineCond" :disabled="savingCond || isSettled">✕</button>
            </td>
          </tr>
          <!-- DISPLAY MODE -->
          <tr
            v-else
            :class="{ selected: selectedCondId === cond.id, 'row-error': cond._error }"
            :style="{ cursor: isSettled ? 'default' : 'pointer' }"
            @click="selectedCondId = cond.id"
            @dblclick="!isSettled && startEditCond(cond)"
          >
            <td>{{ cond.period_from != null ? cond.period_from : '—' }}</td>
            <td>{{ cond.period_to != null ? cond.period_to : '—' }}</td>
            <td style="font-weight:600;">
              {{ cond.rate1 != null ? formatCurrency(cond.rate1) + ' / ' + shortUnit : cond.rate2 != null ? formatCurrency(cond.rate2) + ' / ' + shortUnit : '—' }}
            </td>
            <td>{{ cond.billing_label || defaultLabel }}</td>
            <td>{{ cond.minimum ? cond.minimum : '—' }}</td>
            <td>
              <button class="btn-icon" aria-label="Edytuj" title="Edytuj" @click.stop="startEditCond(cond)" :disabled="isSettled" data-testid="edit-condition">✎</button>
              <button class="btn-icon" aria-label="Usuń" title="Usuń" @click.stop="removeCondition(cond)" :disabled="isSettled" data-testid="delete-condition">✕</button>
            </td>
          </tr>
        </template>
        <!-- NEW ROW (inline add) -->
        <tr v-if="showNewCondRow" class="row-editing">
          <td>
            <input ref="newCondPeriodFromInput" v-model.number="newCondData.period_from" type="number" :min="isRental ? 1 : 0" class="form-control form-control-xs" :placeholder="isRental ? '1' : '0'" data-testid="new-period-from" :disabled="isSettled" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.period_to" type="number" :min="isRental ? 1 : 0" class="form-control form-control-xs" :placeholder="isRental ? 'np. 3' : 'np. 8'" data-testid="new-period-to" :disabled="isSettled" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.rate1" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="new-rate1" :disabled="isSettled" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <span class="form-control-xs" style="display:inline-flex;align-items:center;height:28px;padding:2px 0;">{{ newCondData.billing_label || defaultLabel }}</span>
          </td>
          <td>
            <input v-model.number="newCondData.minimum" type="number" min="0" class="form-control form-control-xs" placeholder="0" :disabled="isSettled" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click.stop="saveNewCondRow" :disabled="savingCond || isSettled">✓</button>
            <button class="btn-icon" title="Anuluj (Esc)" @click.stop="cancelNewCondRow" :disabled="savingCond || isSettled">✕</button>
          </td>
        </tr>
        <tr v-if="gapError" class="row-error">
          <td colspan="6" style="color:var(--color-error);font-size:11px;padding:4px;">
            ⚠️ {{ gapError }}
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="6" style="font-weight:700;text-align:right;padding-top:8px;">
            Wartość pozycji: {{ calculatedValueDisplay }}
          </td>
        </tr>
      </tfoot>
    </table>
    <!-- RAO-P1-100: wierny podgląd warunków rozliczenia (dokładnie to, co trafi do PDF) -->
    <div v-if="pdfPreviewLines.length" class="cond-pdf-preview">
      <div class="cond-pdf-label">Podgląd PDF:</div>
      <div class="cond-pdf-list">
        <div v-for="(line, idx) in pdfPreviewLines" :key="idx" class="cond-pdf-line">
          {{ idx + 1 }}. {{ line }}
        </div>
      </div>
    </div>
    <!-- EMPTY STATE z CTA — tylko gdy nie dodajemy (RAO-P2-071) -->
    <div v-else class="empty-state" style="padding:16px;">
      <template v-if="isSettled">Brak warunków</template>
      <template v-else>
        Brak warunków — <button class="btn-link" @click="addCondition"><strong>dodaj warunek rozliczenia</strong></button>
      </template>
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
                <span style="font-size:11px;color:var(--color-text-muted);">({{ preset.items.length }} warunków)</span>
              </div>
              <div v-if="preset.description" style="font-size:11px;color:var(--color-text-muted);margin-top:2px;">{{ preset.description }}</div>
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
  contractType: { type: String, default: 'S' },  // RAO-P1-100: 'S' = najem, 'U' = usługa
  mode: { type: String, default: null },  // RAO-P1-100: 'rental' | 'service'
  isSettled: { type: Boolean, default: false },  // RAO-P2-022: blokada edycji
  rentalDays: { type: Number, default: null },   // do kalkulacji wartości pozycji
  billingFrequency: { type: String, default: null },
})

const emit = defineEmits(['value-changed'])

const contractStore = useContractStore()
const settingsStore = useSettingsStore()
const toastStore = useToastStore()
const rateTypes = computed(() => settingsStore.rateTypes || [])

const panelMode = computed<'rental' | 'service'>(() => {
  if (props.mode === 'rental' || props.mode === 'service') return props.mode
  return props.contractType === 'U' ? 'service' : 'rental'
})
const isRental = computed(() => panelMode.value === 'rental')
const isService = computed(() => panelMode.value === 'service')
const defaultLabel = computed(() => (isService.value ? 'godzina' : 'doba'))
const shortUnit = computed(() => (isService.value ? 'godz.' : 'doba'))
const defaultRateTypeId = computed(() => {
  const target = isService.value ? 'godz' : 'dob'
  const found = rateTypes.value.find(rt => rt.name && rt.name.toLowerCase().includes(target))
  return found?.id ?? null
})

const conditions = ref([])
const selectedCondId = ref(null)
const savingCond = ref(false)

// RAO-P2-071: inline editing w gridzie (pattern z ContractFormView.vue — zero modali ustawień)
const editingCondId = ref<number | null>(null)
const editingCondData = ref(emptyCondData())
const showNewCondRow = ref(false)
const newCondData = ref(emptyCondData())
const newCondPeriodFromInput = ref<HTMLInputElement | null>(null)

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
    rate_type_id: defaultRateTypeId.value as number | null,
    description: '' as string,
    rate1: null as number | null,
    rate2: null as number | null,
    billing_label: defaultLabel.value,
    period_count: null as number | null,
    period_from: isService.value ? 0 : 1,
    period_to: null as number | null,
    minimum: null as number | null,
  }
}

const calculatedValue = computed(() => calculateCascadingValue())

const calculatedValueDisplay = computed(() => {
  const v = calculatedValue.value
  if (v === null) return '—'
  return formatCurrency(v)
})

// RAO-P1-005: poprawna kalkulacja kaskadowa (bez rate2; open-ended = pusty Do z rate1)
// TODO: po zmianie API przekaź full position (billing_frequency, quantity) – obecnie używa props
function calculateCascadingValue(): number | null {
  const days = Number(props.rentalDays)
  if (!Number.isFinite(days) || days <= 0) return null
  const daysPerPeriod = getDaysPerPeriod(props.billingFrequency || 'dziennie')
  if (daysPerPeriod <= 0) return null
  const totalPeriods = Math.ceil(days / daysPerPeriod)

  const sorted = [...conditions.value]
    .filter(c => c.rate1 !== null && c.rate1 !== undefined)
    .sort((a, b) => (a.period_from || 0) - (b.period_from || 0))

  if (!sorted.length) return null

  let value = 0
  let remaining = totalPeriods
  let previousEnd = 0

  for (const c of sorted) {
    if (remaining <= 0) break
    const start = c.period_from || 1
    // period_count (legacy) determines end when period_to is open-ended
    const end = c.period_to ?? c.period_count ?? Infinity
    // pomiń przerwy/nakładania — liczymy tylko okresy objęte warunkiem
    if (start > remaining) break
    const effectiveStart = Math.max(start, previousEnd + 1)
    if (effectiveStart > end) continue
    const effectiveEnd = Math.min(end, remaining)
    if (effectiveEnd < effectiveStart) continue
    const periods = effectiveEnd - effectiveStart + 1
    value += periods * (Number(c.rate1) || 0)
    remaining -= periods
    previousEnd = effectiveEnd
  }
  return value
}

function getDaysPerPeriod(billingFrequency: string | null): number {
  const map: Record<string, number> = {
    dziennie: 1,
    tygodniowo: 7,
    dwutygodniowo: 14,
    miesięcznie: 30,
    godzinowo: 1,
    jednorazowo: 1,
  }
  return map[billingFrequency || ''] ?? 1
}

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

// RAO-P1-005 / RAO-P1-100: wierny podgląd PDF — zgodny z backendowym format_position_conditions_cascading
function formatPreview(cond: any): string {
  if (cond.description) {
    return cond.description
      .replace(/\$1/g, formatCurrency(cond.rate1 ?? 0))
      .replace(/\$2/g, formatCurrency(cond.rate2 ?? 0))
  }
  const rate = cond.rate1 ?? cond.rate2
  const rateStr = formatCurrency(rate)
  const unit = cond.billing_label === 'dziennie' ? 'doba' : (cond.billing_label || (isService.value ? 'godzina' : 'doba'))
  const rangeUnit = getPeriodRangeUnit(unit)

  if (cond.period_from != null && cond.period_to != null) {
    const count = cond.period_to - cond.period_from + 1
    return `${cond.period_from} - ${cond.period_to} ${getPeriodLabel(count, rangeUnit)} - ${rateStr} / ${unitShort(unit)}`
  }
  if (cond.period_from != null && cond.period_to == null) {
    const count = cond.period_from - 1
    return `powyżej ${count} ${getPeriodLabel(count, rangeUnit)} - ${rateStr} / ${unitShort(unit)}`
  }
  return `${rateStr} / ${unitShort(unit)}`
}

const pdfPreviewLines = computed(() => {
  return [...conditions.value]
    .filter(c => c.rate1 !== null || c.rate2 !== null || c.description)
    .sort((a, b) => {
      const aFrom = a.period_from === null || a.period_from === undefined ? Infinity : Number(a.period_from)
      const bFrom = b.period_from === null || b.period_from === undefined ? Infinity : Number(b.period_from)
      return aFrom - bFrom
    })
    .map(c => formatPreview(c))
})

watch(calculatedValue, (val) => emit('value-changed', val))

function unitShort(unit: string): string {
  if (unit === 'dziennie' || unit === 'dzień' || unit === 'doba') return 'doba'
  if (unit === 'godzinowo' || unit === 'godzina' || unit === 'godz.') return 'godz.'
  return unit || 'doba'
}

function getPeriodRangeUnit(unit: string): string {
  if (unit === 'dziennie' || unit === 'dzień' || unit === 'doba') return 'dzień'
  if (unit === 'godzinowo' || unit === 'godzina' || unit === 'godz.') return 'godzina'
  return unit || 'dzień'
}

function getPeriodLabel(count: number, unit: string): string {
  if (count < 0) count = 0
  if (unit === 'tydzień' || unit === 'tyg.') {
    if (count === 1) return 'tydzień'
    if (count >= 2 && count <= 4) return 'tygodnie'
    return 'tygodni'
  }
  if (unit === 'doba' || unit === 'dzień') {
    if (count === 1) return 'dzień'
    return 'dni'
  }
  if (unit === 'godzina' || unit === 'godz.') {
    if (count === 1) return 'godzina'
    if (count >= 2 && count <= 4) return 'godziny'
    return 'godzin'
  }
  if (unit === 'miesiąc' || unit === 'mies.') {
    if (count === 1) return 'miesiąc'
    if (count >= 2 && count <= 4) return 'miesiące'
    return 'miesięcy'
  }
  return unit || 'dni'
}

async function loadConditions() {
  try {
    conditions.value = await contractStore.fetchConditions(props.contractId, props.positionId)
  } catch { conditions.value = [] }
}

// RAO-P2-071: addCondition → dodaje pusty row w trybie inline-edit (zero modali)
function addCondition() {
  if (props.isSettled || showNewCondRow.value || editingCondId.value !== null) return
  newCondData.value = emptyCondData()
  showNewCondRow.value = true
  nextTick(() => {
    newCondPeriodFromInput.value?.focus()
  })
}

// RAO-P2-071: startEditCond — inline edit istniejącego warunku (pattern jak startEditPos)
function startEditCond(cond: any) {
  if (props.isSettled || showNewCondRow.value) return // nie edytuj gdy dodajemy nowy
  const desc = cond.description || ''
  editingCondId.value = cond.id
  editingCondData.value = {
    rate_type_id: cond.rate_type_id ?? defaultRateTypeId.value,
    description: /\$[12]/.test(desc) ? desc : '',
    rate1: cond.rate1 ?? null,
    rate2: cond.rate2 ?? null,
    billing_label: cond.billing_label || defaultLabel.value,
    period_count: cond.period_count ?? null,
    period_from: cond.period_from ?? (isService.value ? 0 : 1),
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
  if (props.isSettled) return
  if (savingCond.value) return // RAO-P0: guard przed double-click
  // RAO-P1-005: walidacja Od > Do
  if (editingCondData.value.period_from != null && editingCondData.value.period_to != null && editingCondData.value.period_from > editingCondData.value.period_to) {
    toastStore.error('Od musi być mniejsze lub równe Do')
    return
  }
  // RAO-P1-005: jedna stawka (rate1) — pusty Do = open-ended
  const rate = Number(editingCondData.value.rate1)
  if (!Number.isFinite(rate) || rate <= 0) {
    toastStore.warning('Podaj stawkę')
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
  if (props.isSettled) return
  if (savingCond.value) return // RAO-P0: guard przed double-click
  // RAO-P1-005: walidacja Od > Do
  if (newCondData.value.period_from != null && newCondData.value.period_to != null && newCondData.value.period_from > newCondData.value.period_to) {
    toastStore.error('Od musi być mniejsze lub równe Do')
    return
  }
  // RAO-P1-005: jedna stawka (rate1) — pusty Do = open-ended
  const rate = Number(newCondData.value.rate1)
  if (!Number.isFinite(rate) || rate <= 0) {
    toastStore.warning('Podaj stawkę')
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
  if (payload.billing_label === '' || payload.billing_label === undefined || payload.billing_label === null) payload.billing_label = defaultLabel.value
  if (payload.rate1 === '' || payload.rate1 === undefined) payload.rate1 = null
  if (payload.rate2 === '' || payload.rate2 === undefined) payload.rate2 = null
  if (payload.period_from === '' || payload.period_from === undefined) payload.period_from = null
  if (payload.period_to === '' || payload.period_to === undefined) payload.period_to = null
  if (payload.minimum === '' || payload.minimum === undefined) payload.minimum = null
  if (payload.description === '') payload.description = null
  if (payload.rate_type_id == null && defaultRateTypeId.value) payload.rate_type_id = defaultRateTypeId.value
  // period_count (legacy) is derived from period_to when closed, left null when open-ended
  if (payload.period_to != null) payload.period_count = payload.period_to
  else payload.period_count = null
  // Phase 2: rate2 is not used by the new UI; leave it null.
  // Legacy open-ended tiers are now represented by rate1 with period_to=null.
  payload.rate2 = null
  return payload
}

// RAO-P2-071: removeCondition — zastąpiono confirm() modalnem potwierdzenia
async function removeCondition(cond: any) {
  if (props.isSettled) return
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
  if (props.isSettled) return
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
  if (props.isSettled) return
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
  if (props.isSettled) return
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
      await contractStore.createCondition(props.contractId, props.positionId, buildCondPayload({
        rate_type_id: cond.rate_type_id ?? defaultRateTypeId.value,
        description: cond.description || null,
        rate1: cond.rate1,
        rate2: cond.rate2,
        billing_label: cond.billing_label || defaultLabel.value,
        period_count: cond.period_count,
        period_from: cond.period_from ?? null,
        period_to: cond.period_to ?? null,
        minimum: cond.minimum,
      }))
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

// RAO-P1-100: szablony widełek cenowych
const selectedRangeTemplate = ref<string | null>(null)

interface RangeTemplateOption { key: string; label: string }
const rangeTemplateOptions = computed<RangeTemplateOption[]>(() => {
  if (isService.value) {
    return [
      { key: 'service-do-2', label: 'do 2 godzin' },
      { key: 'service-do-3', label: 'do 3 godzin' },
      { key: 'service-do-8', label: 'do 8 godzin' },
      { key: 'service-0-2-3-8-over8', label: '0 - 2 / 3 - 8 / >8 godzin' },
      { key: 'service-each-additional', label: 'każda kolejna' },
    ]
  }
  return [
    { key: 'rental-1-3', label: '1 - 3 dni' },
    { key: 'rental-1-8', label: '1 - 8 dni' },
    { key: 'rental-1-2-3-5-over5', label: '1 - 2 / 3 - 5 / >5 dni' },
    { key: 'rental-over-3', label: '>3 dni' },
    { key: 'rental-over-8', label: '>8 dni' },
    { key: 'rental-over-16', label: '>16 dni' },
    { key: 'rental-over-20', label: '>20 dni' },
    { key: 'rental-1-day', label: '1 dzień' },
  ]
})

const TEMPLATE_ROWS: Record<string, any[]> = {
  'rental-1-3': [{ period_from: 1, period_to: 3, billing_label: 'doba' }],
  'rental-1-8': [{ period_from: 1, period_to: 8, billing_label: 'doba' }],
  'rental-1-2-3-5-over5': [
    { period_from: 1, period_to: 2, billing_label: 'doba' },
    { period_from: 3, period_to: 5, billing_label: 'doba' },
    { period_from: 6, period_to: null, billing_label: 'doba' },
  ],
  'rental-over-3': [{ period_from: 4, period_to: null, billing_label: 'doba' }],
  'rental-over-8': [{ period_from: 9, period_to: null, billing_label: 'doba' }],
  'rental-over-16': [{ period_from: 17, period_to: null, billing_label: 'doba' }],
  'rental-over-20': [{ period_from: 21, period_to: null, billing_label: 'doba' }],
  'rental-1-day': [{ period_from: 1, period_to: null, billing_label: 'doba', period_count: 1, description: '1 dzień - $1 zł' }],
  'service-do-2': [{ period_from: 0, period_to: 2, billing_label: 'godzina', description: 'do 2 godzin - $1 zł' }],
  'service-do-3': [{ period_from: 0, period_to: 3, billing_label: 'godzina', description: 'do 3 godzin - $1 zł' }],
  'service-do-8': [{ period_from: 0, period_to: 8, billing_label: 'godzina', description: 'do 8 godzin - $1 zł' }],
  'service-0-2-3-8-over8': [
    { period_from: 0, period_to: 2, billing_label: 'godzina' },
    { period_from: 3, period_to: 8, billing_label: 'godzina' },
    { period_from: 9, period_to: null, billing_label: 'godzina' },
  ],
  'service-each-additional': [{ period_from: null, period_to: null, billing_label: 'godzina', description: 'każda kolejna $1 zł' }],
}

async function applyRangeTemplate() {
  if (props.isSettled) return
  const key = selectedRangeTemplate.value
  if (!key) return
  const opt = rangeTemplateOptions.value.find(o => o.key === key)
  if (!opt) return
  const rows = TEMPLATE_ROWS[key]
  if (!rows?.length) return
  savingCond.value = true
  try {
    for (const row of rows) {
      await contractStore.createCondition(props.contractId, props.positionId, buildCondPayload({
        ...emptyCondData(),
        ...row,
        rate1: 0,
      }))
    }
    await loadConditions()
    toastStore.success(`Dodano przedział „${opt.label}”`)
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd dodawania warunku')
  } finally {
    savingCond.value = false
    selectedRangeTemplate.value = null
  }
}

defineExpose({ loadConditions, calculatedValue })
</script>

<style scoped>
.condition-panel { margin-top: 12px; }
.condition-panel table.data-grid thead th { text-transform: none; letter-spacing: normal; }
.cond-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}
.cond-header-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-right: auto;
}
.cond-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-heading);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0;
}
.cond-hint {
  font-size: var(--font-size-xs);
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
  background: var(--color-bg-editing);
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
  border: 1px solid var(--color-border-hover);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  padding: 1px 5px;
  margin-left: 6px;
  color: var(--color-text-muted);
  vertical-align: middle;
  transition: background 150ms;
}
.btn-auto-desc:hover { background: var(--color-bg-light); }


/* Field Tooltip */
.field-tooltip {
  display: inline-block;
  margin-left: 6px;
  color: var(--color-text-muted);
  font-size: 12px;
  cursor: help;
}

/* Live Preview */
.live-preview {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  color: var(--color-text-body);
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
  background: var(--color-bg-light);
  border-color: var(--color-primary);
}
.preset-pick-row.selected {
  background: var(--color-bg-light);
  border-color: var(--color-primary);
}
.checkbox-group {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.cond-header-right {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.cond-pdf-preview {
  margin-top: 8px;
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
}
.cond-pdf-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-bottom: 4px;
}
.cond-pdf-list {
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  line-height: 1.5;
}
.cond-pdf-line {
  margin-bottom: 2px;
}
</style>
