<template>
  <div class="condition-panel">
    <div class="cond-header">
      <span class="cond-title">Warunki rozliczenia</span>
      <button class="btn btn-primary btn-sm" @click="addCondition">+ Dodaj warunek</button>
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
          <td style="font-weight:600;">{{ cond.rate1 ? Number(cond.rate1).toFixed(2) + ' zł' : '—' }}</td>
          <td>{{ cond.rate2 ? Number(cond.rate2).toFixed(2) + ' zł' : '—' }}</td>
          <td>{{ cond.billing_label || '—' }}</td>
          <td>{{ cond.period_count || '—' }}</td>
          <td>{{ cond.minimum || '—' }}</td>
          <td style="font-size:11px;color:#718096;">{{ cond.description || '—' }}</td>
          <td>
            <button class="btn-icon" title="Edytuj" @click.stop="editCondition(cond)">✎</button>
            <button class="btn-icon" title="Usuń" @click.stop="removeCondition(cond)">✕</button>
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="8" style="font-weight:700;text-align:right;padding-top:8px;">
            Wartość pozycji: {{ formatMoney(calculatedValue) }}
          </td>
        </tr>
      </tfoot>
    </table>
    <div v-else class="empty-state" style="padding:16px;">Brak warunków — dodaj warunek rozliczenia</div>

    <!-- Condition form modal -->
    <Transition name="modal">
      <div v-if="showCondModal" class="modal-overlay" @click.self="showCondModal = false">
        <div class="modal-box" style="min-width:520px;">
          <div class="modal-title">{{ editingCond ? 'Edycja warunku' : 'Nowy warunek' }}</div>
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
              <label class="form-label">Stawka 2 (zł)</label>
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
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showCondModal = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="saveCondition" :disabled="savingCond">{{ savingCond ? '...' : 'Zapisz' }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import { useContractStore } from '@/stores/contracts'
import { useSettingsStore } from '@/stores/settings'

const props = defineProps({
  contractId: { type: Number, required: true },
  positionId: { type: Number, required: true },
})

const emit = defineEmits(['value-changed'])

const contractStore = useContractStore()
const settingsStore = useSettingsStore()
const rateTypes = computed(() => settingsStore.rateTypes || [])

const conditions = ref([])
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
    const formatted = Number(r1).toFixed(2) + ' zł'
    parts.push(condForm.value.billing_label ? `${formatted}/${condForm.value.billing_label}` : formatted)
  }
  const r2 = condForm.value.rate2
  if (r2 && Number(r2) > 0) parts.push(`+ ${Number(r2).toFixed(2)} zł`)
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
    alert('Podaj stawkę 1')
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
    alert(e.response?.data?.detail || 'Błąd zapisu warunku')
  } finally {
    savingCond.value = false
  }
}

async function removeCondition(cond) {
  if (!confirm('Usunąć ten warunek?')) return
  try {
    await contractStore.deleteCondition(props.contractId, props.positionId, cond.id)
    await loadConditions()
  } catch (e) {
    alert(e.response?.data?.detail || 'Błąd')
  }
}

function formatMoney(v) {
  if (!v && v !== 0) return '0,00 zł'
  return Number(v).toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł'
}

watch(() => props.positionId, loadConditions, { immediate: true })

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
  font-size: 10px;
  padding: 1px 5px;
  margin-left: 6px;
  color: #718096;
  vertical-align: middle;
  transition: background 150ms;
}
.btn-auto-desc:hover { background: #EDF2F7; }
</style>
