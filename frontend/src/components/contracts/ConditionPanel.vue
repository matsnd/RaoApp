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
        <button class="btn btn-secondary btn-sm" @click="autoPrefillFromLast" :disabled="!machineId || autoPrefillLoading || isSettled" title="Wypełnij z ostatniej umowy tej maszyny">
          {{ autoPrefillLoading ? '...' : '↻ Z ostatniej umowy' }}
        </button>
        <button class="btn btn-secondary btn-sm" @click="openPresetPicker" :disabled="!machineId || isSettled" title="Zastosuj predefiniowany cennik">
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
          <th style="width:80px;"></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(cond) in conditions" :key="cond.id">
          <!-- EDIT MODE (inline) -->
          <tr v-if="editingCondId === cond.id" class="row-editing">
            <td>
              <input v-model.number="editingCondData.period_from" type="number" min="0" class="form-control form-control-xs" :placeholder="isRental ? '1' : '0'" data-testid="period-from" :disabled="isSettled" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.period_to" type="number" min="0" class="form-control form-control-xs" :placeholder="isRental ? 'np. 3 (puste = powyżej)' : 'np. 8 (puste = powyżej)'" data-testid="period-to" :disabled="isSettled" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <input v-model.number="editingCondData.rate1" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="rate1" :disabled="isSettled" @keydown.enter="saveInlineCond" @keydown.esc="cancelInlineCond" />
            </td>
            <td>
              <span class="form-control-xs" style="display:inline-flex;align-items:center;height:28px;padding:2px 0;">{{ editingCondData.billing_label || defaultLabel }}</span>
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
              {{ cond.rate1 != null ? formatCurrency(cond.rate1) + (isRental ? ' / ' + shortUnit : '') : cond.rate2 != null ? formatCurrency(cond.rate2) + (isRental ? ' / ' + shortUnit : '') : '—' }}
            </td>
            <td>{{ cond.billing_label || defaultLabel }}</td>
            <td>
              <button class="btn-icon" aria-label="Edytuj" title="Edytuj" @click.stop="startEditCond(cond)" :disabled="isSettled" data-testid="edit-condition">✎</button>
              <button class="btn-icon" aria-label="Usuń" title="Usuń" @click.stop="removeCondition(cond)" :disabled="isSettled" data-testid="delete-condition">✕</button>
            </td>
          </tr>
        </template>
        <!-- NEW ROW (inline add) -->
        <tr v-if="showNewCondRow" class="row-editing">
          <td>
            <input ref="newCondPeriodFromInput" v-model.number="newCondData.period_from" type="number" min="0" class="form-control form-control-xs" :placeholder="isRental ? '1' : '0'" data-testid="new-period-from" :disabled="isSettled" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.period_to" type="number" min="0" class="form-control form-control-xs" :placeholder="isRental ? 'np. 3 (puste = powyżej)' : 'np. 8 (puste = powyżej)'" data-testid="new-period-to" :disabled="isSettled" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <input v-model.number="newCondData.rate1" type="number" step="0.01" class="form-control form-control-xs" placeholder="0.00" data-testid="new-rate1" :disabled="isSettled" @keydown.enter="saveNewCondRow" @keydown.esc="cancelNewCondRow" />
          </td>
          <td>
            <span class="form-control-xs" style="display:inline-flex;align-items:center;height:28px;padding:2px 0;">{{ newCondData.billing_label || defaultLabel }}</span>
          </td>
          <td>
            <button class="btn-icon" style="color:var(--color-success);" title="Zapisz (Enter)" @click.stop="saveNewCondRow" :disabled="savingCond || isSettled">✓</button>
            <button class="btn-icon" title="Anuluj (Esc)" @click.stop="cancelNewCondRow" :disabled="savingCond || isSettled">✕</button>
          </td>
        </tr>
        <tr v-if="gapError" class="row-error">
          <td colspan="5" style="color:var(--color-error);font-size:11px;padding:4px;">
            ⚠️ {{ gapError }}
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="5" style="font-weight:700;text-align:right;padding-top:8px;">
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
          {{ line }}
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
import { formatCurrency, formatRate } from '@/utils/format'
import api from '@/composables/useApi'

const props = defineProps({
  contractId: { type: Number, required: true },
  positionId: { type: Number, required: true },
  machineId: { type: Number, default: null },  // RAO-P1-001: do apply-preset + auto-prefill (Faza 4c: articleId → machineId)
  contractType: { type: String, default: 'S' },  // RAO-P1-100: 'S' = najem, 'U' = usługa
  mode: { type: String, default: null },  // RAO-P1-100: 'rental' | 'service'
  isSettled: { type: Boolean, default: false },  // RAO-P2-022: blokada edycji
  rentalDays: { type: Number, default: null },   // do kalkulacji wartości pozycji
  billingFrequency: { type: String, default: null },
})

const emit = defineEmits(['value-changed', 'conditions-changed'])

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
  }
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

// RAO-P1-005: jednolita kolejność kaskadowa — zamknięte przedziały rosnąco, potem otwarte
function sortForCascade<T extends { period_from?: number | null, period_to?: number | null, period_count?: number | null }>(list: T[]): T[] {
  return [...list].sort((a, b) => {
    const aOpen = a.period_to == null
    const bOpen = b.period_to == null
    if (aOpen !== bOpen) return aOpen ? 1 : -1
    const aFrom = a.period_from ?? 0
    const bFrom = b.period_from ?? 0
    if (aFrom !== bFrom) return aFrom - bFrom
    const aTo = a.period_to ?? a.period_count ?? Infinity
    const bTo = b.period_to ?? b.period_count ?? Infinity
    return aTo - bTo
  })
}

// RAO-P1-005: najbliższy wolny dzień dla nowego warunku (ignoruje otwarte, bo powinno być ostatnie)
function computeNextPeriodFrom(): number {
  const closed = sortForCascade(conditions.value).filter(c => c.period_to != null)
  let prevEnd = 0
  for (const c of closed) {
    const start = c.period_from ?? (isService.value ? 0 : 1)
    const end = c.period_to ?? c.period_count ?? Infinity
    if (start > end) continue
    if (start > prevEnd + 1) {
      return prevEnd + 1
    }
    prevEnd = Math.max(prevEnd, end)
  }
  return prevEnd + 1
}

// RAO-P1-005: poprawna kalkulacja kaskadowa (bez rate2; open-ended = pusty Do z rate1)
// Uwaga: efektywny koniec ograniczony jest totalPeriods, a nie remaining (liczba, a nie dzień).
function calculateCascadingValue(): number | null {
  const days = Number(props.rentalDays)
  if (!Number.isFinite(days) || days <= 0) return null
  const daysPerPeriod = getDaysPerPeriod(props.billingFrequency || 'dziennie')
  if (daysPerPeriod <= 0) return null
  const rawPeriods = Math.ceil(days / daysPerPeriod)

  // P1-101: minimum column removed — no global minimum enforcement in UI calc
  const totalPeriods = rawPeriods

  const sorted = sortForCascade(
    conditions.value.filter((c: any) => c.rate1 != null && c.rate1 !== undefined && Number(c.rate1) > 0)
  )
  if (!sorted.length) return null

  let value = 0
  let remaining = totalPeriods
  let previousEnd = 0
  let lastRate = 0

  for (const c of sorted) {
    if (remaining <= 0) break
    const rate = Number(c.rate1)
    if (rate > 0) lastRate = rate
    const start = c.period_from ?? (isService.value ? 0 : 1)
    const end = c.period_to ?? c.period_count ?? Infinity
    if (start > totalPeriods) break
    const effectiveStart = Math.max(start, previousEnd + 1)
    if (effectiveStart > end) continue
    const effectiveEnd = Math.min(end, totalPeriods)
    if (effectiveEnd < effectiveStart) continue
    let periods = effectiveEnd - effectiveStart + 1
    if (periods > remaining) periods = remaining
    value += periods * rate
    remaining -= periods
    previousEnd = effectiveEnd
  }

  // Jeśli po warunkach zostanie nierozliczony okres, użyj ostatniej stawki (np. minimum)
  if (remaining > 0 && lastRate > 0) {
    value += remaining * lastRate
  }
  return value
}

const calculatedValue = computed(() => calculateCascadingValue())

const calculatedValueDisplay = computed(() => {
  const v = calculatedValue.value
  if (v === null) return '—'
  return formatCurrency(v)
})

// RAO-P1-005: walidacja ciągłości warunków (closed first, potem otwarte)
function validateContinuity() {
  const sorted = sortForCascade(conditions.value)
  for (let i = 0; i < sorted.length - 1; i++) {
    const curr = sorted[i]
    const next = sorted[i + 1]
    const currOpen = curr.period_to == null
    const nextOpen = next.period_to == null
    if (currOpen && nextOpen) {
      gapError.value = 'Tylko jeden warunek otwarty może występować.'
      return
    }
    if (currOpen) {
      gapError.value = 'Warunek otwarty musi być ostatni.'
      return
    }
    const expected = (curr.period_to ?? 0) + 1
    const nextFrom = next.period_from ?? (isService.value ? 0 : 1)
    if (nextFrom < expected) {
      gapError.value = `Nakładanie: po ${curr.period_from || '—'}-${curr.period_to ?? '∞'} następny powinien zaczynać się od ${expected}`
      return
    }
    if (nextFrom > expected) {
      gapError.value = `Luka: po ${curr.period_from || '—'}-${curr.period_to ?? '∞'} brak ${expected}`
      return
    }
  }
  gapError.value = ''
}

watch(conditions, validateContinuity, { deep: true })

// RAO-P1-005 / RAO-P1-100: wierny podgląd PDF — zgodny z legacy WinForms + backend
// Legacy format (c:\Temp\legacy_pdfs\):
//   "1 - 3 dni - 800,00 / doba"        (closed range)
//   "powyżej 3 dni - 700,00 / doba"    (open-ended after closed)
//   "1 dzień - 630,00 / doba"          (single day)
//   "230,00 / doba"                    (flat rate — NO range prefix)
//   "0 - 2 godzin - 1450,00 / godzina"  (service cascading 0-X)
//   Minimum is NOT shown in condition line (legacy shows it in Uwagi)
function formatPreview(cond: any): string {
  if (cond.description) {
    return cond.description
      .replace(/\$1/g, formatRate(cond.rate1 ?? 0))
      .replace(/\$2/g, formatRate(cond.rate2 ?? 0))
  }
  const rate = cond.rate1 ?? cond.rate2
  const rateStr = formatRate(rate)
  const labels = unitLabels(cond.billing_label, isService.value)
  const pf = cond.period_from ?? (isService.value ? 0 : 1)
  const pt = cond.period_to
  // Legacy (c:\Temp\legacy_pdfs\): usługa (U) = ryczałt (kwota całkowita, BEZ / unit),
  // najem (S/N) = stawka per unit (Z / unit).
  //   "230,00zł / doba", "1 - 3 dni - 800,00zł / doba"
  //   "do 2 godzin - 1450,00zł"  (usługa ryczałt, pf=0)
  //   "0 - 2 godzin - 1450,00zł / godzina"  (najem z billing_label=godzina, pf=0 — 1 przypadek w 515 PDF)
  const isFlat = isService.value
  const rateText = isFlat ? `${rateStr}zł` : `${rateStr}zł / ${labels.rate}`

  if (pt == null) {
    // Flat rate (pf <= 1): no range prefix — legacy: "230,00zł / doba"
    if (pf <= 1) return rateText
    // P1-206: umowa U (usługa) open-ended w godzinach → "każda kolejna {rate}zł / h"
    // zamiast "powyżej X godzin - {rate}zł" (ryczałt bez / unit). Grid bez zmian.
    if (isFlat && labels.count === 'godzin') {
      return `każda kolejna ${rateStr}zł / h`
    }
    // Open-ended after closed tier: "powyżej X dni"
    const threshold = pf - 1
    return `powyżej ${threshold} ${formatCount(threshold, labels.count)} - ${rateText}`
  }
  // Usługa (ryczałt) z pf=0 → "do X godzin" (zgodne z legacy i backendem)
  if (isFlat && pf === 0) {
    return `do ${pt} ${formatCount(pt, labels.count)} - ${rateText}`
  }
  if (pf === pt) {
    return `${pf} ${formatCount(1, labels.count)} - ${rateText}`
  }
  return `${pf} - ${pt} ${formatCount(pt - pf + 1, labels.count)} - ${rateText}`
}

const pdfPreviewLines = computed(() => {
  return sortForCascade(conditions.value)
    .filter((c: any) => c.rate1 != null || c.rate2 != null || c.description)
    .map(c => formatPreview(c))
})

watch(calculatedValue, (val) => emit('value-changed', val))

function unitLabels(label: string | null, service: boolean): { count: string, rate: string } {
  const l = (label || '').toLowerCase()
  if (l.includes('godz')) return { count: 'godzin', rate: 'godzina' }
  if (l.includes('mies')) return { count: 'mies.', rate: 'mies.' }
  if (l.includes('tyg')) return { count: 'tyg.', rate: 'tyg.' }
  if (service) return { count: 'godzin', rate: 'godzina' }
  return { count: 'dni', rate: 'doba' }
}

function formatCount(count: number, unit: string): string {
  if (count === 1 && unit === 'dni') return 'dzień'
  return unit
}

function unitShort(unit: string): string {
  if (unit === 'dziennie' || unit === 'dzień' || unit === 'doba') return 'doba'
  if (unit === 'godzinowo' || unit === 'godzina' || unit === 'godz.') return 'godz.'
  return unit || 'doba'
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
  newCondData.value.period_from = computeNextPeriodFrom()
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
    emit('conditions-changed')
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
    emit('conditions-changed')
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
        emit('conditions-changed')
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

// P1-117: Auto-apply ostatniego cennika po wybraniu maszyny (gdy brak warunków)
watch(() => props.machineId, async (newMachineId, oldMachineId) => {
  if (!newMachineId || newMachineId === oldMachineId) return
  if (props.isSettled) return
  // Poczekaj aż loadConditions się zakończy (positionId może się zmienić równocześnie)
  await nextTick()
  if (conditions.value.length === 0) {
    // Auto-prefill z ostatniej umowy tej maszyny — cichy tryb (bez toast jeśli brak historii)
    autoPrefillLoading.value = true
    try {
      const data = await contractStore.fetchLastConditionsForMachine(newMachineId)
      if (data?.conditions?.length) {
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
          }))
        }
        toastStore.success(`Auto-apply cennika z umowy ${data.source_contract_number} (${data.conditions.length} warunków)`)
        await loadConditions()
      }
    } catch {
      // Cichy błąd — auto-apply jest opcjonalny, user może kliknąć przycisk ręcznie
    } finally {
      autoPrefillLoading.value = false
    }
  }
})

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
  if (!props.machineId) {
    toastStore.warning('Pozycja nie ma przypisanej maszyny')
    return
  }
  showPresetPicker.value = true
  selectedPresetId.value = null
  presetPickerLoading.value = true
  try {
    const { data } = await api.get(`/settings/machines/${props.machineId}/rate-presets`)
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
    emit('conditions-changed')
  } catch (e) {
    const err = e as { response?: { data?: { detail?: string } } }
    toastStore.error(err?.response?.data?.detail || 'Błąd zastosowania cennika')
  } finally {
    applyingPreset.value = false
  }
}

async function autoPrefillFromLast() {
  if (props.isSettled) return
  if (!props.machineId) {
    toastStore.warning('Pozycja nie ma przypisanej maszyny')
    return
  }
  autoPrefillLoading.value = true
  try {
    const data = await contractStore.fetchLastConditionsForMachine(props.machineId)
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
      }))
    }
    toastStore.success(`Wypełniono z umowy ${data.source_contract_number} (${data.conditions.length} warunków)`)
    await loadConditions()
    emit('conditions-changed')
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
    emit('conditions-changed')
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
