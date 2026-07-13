<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack" title="Wstecz" aria-label="Wstecz">← Wstecz</button>
      <span class="toolbar-info">{{ isEdit ? `Edycja usługi dodatkowej: ${form.name}` : 'Nowa usługa dodatkowa' }}</span>
      <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="saving">
        {{ saving ? '...' : 'Zapisz' }}
      </button>
    </div>

    <div class="content-area">
      <div v-if="loading" class="empty-state">Ładowanie...</div>
      <div v-else class="page-card" style="max-width:800px;">
        <div v-if="errorMsg" style="color:var(--color-danger);padding:8px;background:#FED7D7;border-radius:6px;margin-bottom:12px;font-size:13px;" role="alert">{{ errorMsg }}</div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="as-name">Nazwa usługi dodatkowej *</label>
            <input id="as-name" v-model="form.name" type="text" class="form-control" :class="{ error: fieldErrors.name }" :aria-invalid="!!fieldErrors.name" aria-describedby="as-name-error" placeholder="Np. Transport maszyny" required />
            <span v-if="fieldErrors.name" class="field-error" id="as-name-error" role="alert">{{ fieldErrors.name }}</span>
          </div>
          <div class="form-group">
            <label class="form-label" for="as-display-name">Nazwa na umowie (długa)</label>
            <input id="as-display-name" v-model="form.display_name" type="text" class="form-control" placeholder="Długa nazwa wyświetlana na umowie/PDF (opcjonalnie)" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="as-default-amount">Kwota domyślna (zł)</label>
            <input id="as-default-amount" v-model.number="form.default_amount" type="number" step="0.01" min="0" class="form-control" placeholder="Np. 1200.00" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="as-description">Opis</label>
          <textarea id="as-description" v-model="form.description" class="form-control" rows="3" :placeholder="FEE_DESCRIPTION_HINT"></textarea>
          <div class="fee-desc-preview">
            <span class="fee-desc-preview-label">Podgląd: </span>{{ formatFeeDescription(form.description, form.default_amount, null, form.name) }}
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="as-notes">Uwagi</label>
          <textarea id="as-notes" v-model="form.notes" class="form-control" rows="2"></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAdditionalServiceStore } from '@/stores/additional_services'
import { extractErrorMessage } from '@/utils/validation'
import { formatFeeDescription, FEE_DESCRIPTION_HINT } from '@/composables/useFeeDescription'

const props = defineProps({ id: String })
const router = useRouter()
const store = useAdditionalServiceStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const fieldErrors = ref<Record<string, string>>({})

const form = ref({
  name: '',
  display_name: '',
  default_amount: null as number | null,
  description: '',
  notes: '',
})

onMounted(async () => {
  if (isEdit.value) {
    loading.value = true
    try {
      const data = await store.fetchOne(Number(props.id))
      Object.assign(form.value, data)
    } finally {
      loading.value = false
    }
  }
})

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/additional-services')
  }
}

function validateForm() {
  fieldErrors.value = {}
  const errors: Record<string, string> = {}
  if (!form.value.name || !form.value.name.trim()) {
    errors.name = 'Podaj nazwę usługi dodatkowej'
  }
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function handleSave() {
  if (!validateForm()) return
  if (!form.value.name) { errorMsg.value = 'Podaj nazwę usługi dodatkowej'; return }
  saving.value = true
  errorMsg.value = ''
  try {
    const payload: Record<string, any> = { ...form.value }

    if (isEdit.value && props.id) {
      await store.update(Number(props.id), payload)
    } else {
      const result = await store.create(payload)
      router.push(`/additional-services/${result.id}/edit`)
      return
    }
  } catch (e: any) {
    errorMsg.value = extractErrorMessage(e, 'Błąd zapisu usługi dodatkowej')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.field-error {
  display: block;
  color: var(--color-error);
  font-size: 12px;
  margin-top: 4px;
  font-weight: 500;
}
.form-control.error {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}
.fee-desc-preview {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
  padding: 6px 8px;
  background: var(--color-bg-light);
  border-radius: 4px;
  line-height: 1.4;
}
.fee-desc-preview-label {
  font-weight: 600;
  color: var(--color-text-secondary);
}
</style>
