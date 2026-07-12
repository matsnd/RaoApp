<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack" title="Wstecz" aria-label="Wstecz">← Wstecz</button>
      <span class="toolbar-info">{{ isEdit ? `Edycja usługi: ${form.name}` : 'Nowa usługa' }}</span>
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
            <label class="form-label" for="service-name">Nazwa usługi *</label>
            <input id="service-name" v-model="form.name" type="text" class="form-control" :class="{ error: fieldErrors.name }" :aria-invalid="!!fieldErrors.name" aria-describedby="service-name-error" placeholder="Np. Usługa operatora" required />
            <span v-if="fieldErrors.name" class="field-error" id="service-name-error" role="alert">{{ fieldErrors.name }}</span>
          </div>
          <!-- #13 uwagi klienta: Nr wewnętrzny wyeliminowany z usług -->
        </div>

        <div class="form-group">
          <label class="form-label" for="service-description">Opis</label>
          <textarea id="service-description" v-model="form.description" class="form-control" rows="3"></textarea>
        </div>

        <div class="form-group">
          <label class="form-label" for="service-notes">Uwagi</label>
          <textarea id="service-notes" v-model="form.notes" class="form-control" rows="2"></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useServiceStore } from '@/stores/services'
import { useToastStore } from '@/stores/toast'
import { extractErrorMessage } from '@/utils/validation'

const props = defineProps({ id: String })
const router = useRouter()
const store = useServiceStore()
const toastStore = useToastStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const fieldErrors = ref<Record<string, string>>({})

const form = ref({
  name: '',
  // #13 uwagi klienta: internal_number usunięte z usług
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
    router.push('/services')
  }
}

function validateForm() {
  fieldErrors.value = {}
  const errors: Record<string, string> = {}
  if (!form.value.name || !form.value.name.trim()) {
    errors.name = 'Podaj nazwę usługi'
  }
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function handleSave() {
  if (!validateForm()) return
  if (!form.value.name) { errorMsg.value = 'Podaj nazwę usługi'; return }
  saving.value = true
  errorMsg.value = ''
  try {
    const payload: Record<string, any> = { ...form.value }

    if (isEdit.value && props.id) {
      await store.update(Number(props.id), payload)
    } else {
      const result = await store.create(payload)
      router.push(`/services/${result.id}/edit`)
      return
    }
  } catch (e: any) {
    errorMsg.value = extractErrorMessage(e, 'Błąd zapisu usługi')
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
</style>
