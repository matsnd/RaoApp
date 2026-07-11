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
          <!-- #13 uwagi klienta: Nr wewnętrzny wyeliminowany z usług dodatkowych -->
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="as-cat-main">Kategoria</label>
            <div style="display:flex;flex-direction:column;gap:4px;">
              <select id="as-cat-main" v-model="catSelectedMain" class="form-control" @change="catSelectedSub1 = null; catSelectedSub2 = null">
                <option :value="null">— brak kategorii —</option>
                <option v-for="c in catMainOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
              <select v-if="catSub1Options.length" v-model="catSelectedSub1" class="form-control" aria-label="Podkategoria poziom 1" @change="catSelectedSub2 = null">
                <option :value="null">— (poziom główny) —</option>
                <option v-for="c in catSub1Options" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
              <select v-if="catSub2Options.length" v-model="catSelectedSub2" class="form-control" aria-label="Podkategoria poziom 2">
                <option :value="null">— (poziom podrzędny) —</option>
                <option v-for="c in catSub2Options" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label" for="as-branch">Filia</label>
            <select id="as-branch" v-model="form.branch_id" class="form-control">
              <option :value="null">— główna —</option>
              <option v-for="br in settingsStore.branches" :key="br.id" :value="br.id">{{ br.name }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="as-description">Opis</label>
          <textarea id="as-description" v-model="form.description" class="form-control" rows="3"></textarea>
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
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAdditionalServiceStore } from '@/stores/additional_services'
import { useSettingsStore } from '@/stores/settings'

const props = defineProps({ id: String })
const router = useRouter()
const store = useAdditionalServiceStore()
const settingsStore = useSettingsStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const fieldErrors = ref<Record<string, string>>({})

const form = ref({
  name: '',
  // #13 uwagi klienta: internal_number usunięte z usług dodatkowych
  category_id: null as number | null,
  branch_id: null as number | null,
  description: '',
  notes: '',
})

// --- Cascade category pickers ---
const catSelectedMain = ref<number | null>(null)
const catSelectedSub1 = ref<number | null>(null)
const catSelectedSub2 = ref<number | null>(null)

const catMainOptions = computed(() => settingsStore.categoriesTree)
const catSub1Options = computed(() => {
  if (!catSelectedMain.value) return []
  return catMainOptions.value.find(c => c.id === catSelectedMain.value)?.children || []
})
const catSub2Options = computed(() => {
  if (!catSelectedSub1.value) return []
  return catSub1Options.value.find(c => c.id === catSelectedSub1.value)?.children || []
})

watch([catSelectedMain, catSelectedSub1, catSelectedSub2], () => {
  form.value.category_id = catSelectedSub2.value ?? catSelectedSub1.value ?? catSelectedMain.value
})

function findCatPath(tree: any[], id: number, path: any[] = []): any[] | null {
  for (const node of tree) {
    const newPath = [...path, node]
    if (node.id === id) return newPath
    if (node.children?.length) {
      const found = findCatPath(node.children, id, newPath)
      if (found) return found
    }
  }
  return null
}

function setCategoryFromId(categoryId: number | null) {
  if (!categoryId || !settingsStore.categoriesTree.length) {
    catSelectedMain.value = null
    catSelectedSub1.value = null
    catSelectedSub2.value = null
    return
  }
  const path = findCatPath(settingsStore.categoriesTree, categoryId)
  if (!path) return
  catSelectedMain.value = path[0]?.id || null
  catSelectedSub1.value = path[1]?.id || null
  catSelectedSub2.value = path[2]?.id || null
}

onMounted(async () => {
  await Promise.all([settingsStore.fetchCategoriesTree(), settingsStore.fetchBranches()])

  if (isEdit.value) {
    loading.value = true
    try {
      const data = await store.fetchOne(Number(props.id))
      Object.assign(form.value, data)
      setCategoryFromId(data.category_id)
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
    errorMsg.value = e.response?.data?.detail || 'Błąd zapisu'
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
