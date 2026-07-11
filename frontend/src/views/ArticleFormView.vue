<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack" title="Wstecz" aria-label="Wstecz">← Wstecz</button>
      <span class="toolbar-info">{{ isEdit ? `Edycja artykułu: ${form.name}` : 'Nowy artykuł' }}</span>
      <button v-if="isEdit" class="toolbar-btn" title="Duplikuj" aria-label="Duplikuj artykuł" @click="handleDuplicate">⎘</button>
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
            <label class="form-label" for="article-name">Nazwa artykułu *</label>
            <input id="article-name" v-model="form.name" type="text" class="form-control" :class="{ error: fieldErrors.name }" :aria-invalid="!!fieldErrors.name" aria-describedby="article-name-error" placeholder="Np. Koparka gąsienicowa" required />
            <span v-if="fieldErrors.name" class="field-error" id="article-name-error" role="alert">{{ fieldErrors.name }}</span>
          </div>
          <div class="form-group">
            <label class="form-label" for="article-type">Typ artykułu</label>
            <select id="article-type" v-model="form.article_type" class="form-control">
              <option value="">— brak —</option>
              <option value="machine">Maszyna</option>
              <option value="vehicle">Pojazd</option>
              <option value="tool">Narzędzie</option>
              <option value="service">Usługa</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="checkbox-group">
            <input type="checkbox" v-model="form.is_service" />
            <span>Artykuł jest usługą (nie sprzętem)</span>
          </label>
          <label class="checkbox-group" style="margin-top:6px;">
            <input type="checkbox" v-model="form.is_external" />
            <span>Maszyna zewnętrzna (nie wliczana do floty własnej)</span>
          </label>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="article-internal">Nr wewnętrzny</label>
            <input id="article-internal" v-model="form.internal_number" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label" for="article-reg">Nr rejestracyjny</label>
            <input id="article-reg" v-model="form.registration_no" type="text" class="form-control" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="article-serial">Nr seryjny</label>
            <input id="article-serial" v-model="form.serial_no" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label" for="article-replacement">Wartość odtworzeniowa (zł)</label>
            <input id="article-replacement" v-model="form.replacement_value" type="number" step="0.01" class="form-control" :class="{ error: fieldErrors.replacement_value }" :aria-invalid="!!fieldErrors.replacement_value" aria-describedby="article-replacement-error" />
            <span v-if="fieldErrors.replacement_value" class="field-error" id="article-replacement-error" role="alert">{{ fieldErrors.replacement_value }}</span>
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="article-brand">Marka</label>
            <input id="article-brand" v-model="form.brand" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label" for="article-model">Model</label>
            <input id="article-model" v-model="form.model" type="text" class="form-control" />
          </div>
        </div>

        <div class="section-title" style="font-size:var(--font-size-sm);margin-top:var(--spacing-4);margin-bottom:var(--spacing-3);padding-bottom:var(--spacing-2);">Dane techniczne</div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="article-zasieg">Zasięg (m)</label>
            <input id="article-zasieg" v-model.number="form.zasieg_m" type="number" class="form-control" min="0" step="0.1" placeholder="np. 21.5" />
          </div>
          <div class="form-group">
            <label class="form-label" for="article-udzwig">Udźwig (t)</label>
            <input id="article-udzwig" v-model.number="form.udzwig_t" type="number" class="form-control" min="0" step="0.1" placeholder="np. 5.0" />
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="article-power-type">Typ zasilania</label>
            <select id="article-power-type" v-model="form.power_type" class="form-control" data-testid="article-power-type">
              <option value="diesel">Diesel</option>
              <option value="electric">Elektryk</option>
              <option value="other">Inny</option>
            </select>
          </div>
        </div>

        <!-- RAO-P2-058: Mapowanie artykułu z produktem Fakturownia -->
        <div class="section-title" style="font-size:var(--font-size-sm);margin-top:var(--spacing-4);margin-bottom:var(--spacing-3);padding-bottom:var(--spacing-2);">Integracja Fakturownia</div>
        <div class="form-group">
          <label class="form-label" for="article-fa-product">Produkt Fakturownia</label>
          <select id="article-fa-product" v-model="form.fakturownia_product_id" class="form-control" :disabled="faLoading">
            <option :value="null">— brak mapowania —</option>
            <option v-for="p in faProducts" :key="p.id" :value="p.id">
              {{ p.name }}{{ p.code ? ` (${p.code})` : '' }}{{ p.price_net ? ` — ${p.price_net} zł` : '' }}
            </option>
          </select>
          <small v-if="faError" style="color:var(--color-error);" role="alert">{{ faError }}</small>
          <small v-else-if="!faProducts.length && !faLoading" style="color:var(--color-text-muted);">
            Brak produktów w Fakturownia — dodaj produkty na matsnd.fakturownia.pl
          </small>
        </div>
        <div v-if="form.fakturownia_product_id" class="form-row-3">
          <div class="form-group">
            <label class="form-label">VAT (z FA)<GlossaryTip term="FA" definition="Faktura — dokument księgowy z Fakturownia" description="W RAO służy do rozliczania kosztów firmy. VAT pobierany z wybranego produktu Fakturownia." placement="top" :size="12" /></label>
            <input :value="form.fakturownia_tax_rate ? form.fakturownia_tax_rate + '%' : '—'" type="text" class="form-control" disabled />
          </div>
          <div class="form-group">
            <label class="form-label">GTU (z FA)<GlossaryTip term="FA" definition="Faktura — dokument księgowy z Fakturownia" description="GTU — kod grupy towarowej usługi, pobierany z produktu Fakturownia." placement="top" :size="12" /></label>
            <input :value="form.fakturownia_gtu_code || '—'" type="text" class="form-control" disabled />
          </div>
          <div class="form-group">
            <label class="form-label">PKWiU (z FA)<GlossaryTip term="FA" definition="Faktura — dokument księgowy z Fakturownia" description="PKWiU — Polska Klasyfikacja Wyrobów i Usług, pobierana z produktu Fakturownia." placement="top" :size="12" /></label>
            <input :value="form.fakturownia_pkwiu || '—'" type="text" class="form-control" disabled />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="article-dodatki">Dodatkowe wyposażenie</label>
          <textarea id="article-dodatki" v-model="form.dodatki" class="form-control" rows="3" placeholder="np. Kosz osobowy, wciągarka..."></textarea>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="article-cat-main">Kategoria</label>
            <div style="display:flex;flex-direction:column;gap:4px;">
              <select id="article-cat-main" v-model="catSelectedMain" class="form-control" @change="catSelectedSub1 = null; catSelectedSub2 = null">
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
            <label class="form-label" for="article-owner-display">Właściciel (dostawca)</label>
            <div style="display:flex;gap:8px;">
              <input id="article-owner-display" :value="ownerName" type="text" class="form-control" disabled placeholder="— własny —" style="flex:1;" />
              <button type="button" class="btn btn-secondary btn-sm" @click="showOwnerPicker = true">Wybierz</button>
              <button v-if="form.owner_id" type="button" class="btn btn-secondary btn-sm" @click="clearOwner" aria-label="Wyczyść właściciela">✕</button>
            </div>
          </div>
        </div>

        <div class="form-row-2">
          <div class="form-group">
            <label class="form-label" for="article-rental-days">Min. dni najmu</label>
            <input id="article-rental-days" v-model.number="form.rental_days" type="number" class="form-control" :class="{ error: fieldErrors.rental_days }" :aria-invalid="!!fieldErrors.rental_days" aria-describedby="article-rental-days-error" min="1" />
            <span v-if="fieldErrors.rental_days" class="field-error" id="article-rental-days-error" role="alert">{{ fieldErrors.rental_days }}</span>
          </div>
          <div class="form-group">
            <label class="form-label" for="article-branch">Filia</label>
            <select id="article-branch" v-model="form.branch_id" class="form-control">
              <option :value="null">— główna —</option>
              <option v-for="br in settingsStore.branches" :key="br.id" :value="br.id">{{ br.name }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="article-description">Opis</label>
          <textarea id="article-description" v-model="form.description" class="form-control" rows="3"></textarea>
        </div>

        <div class="form-group">
          <label class="form-label" for="article-notes">Uwagi</label>
          <textarea id="article-notes" v-model="form.notes" class="form-control" rows="2"></textarea>
        </div>

        <!-- RAO-P1-001: Cenniki rozliczenia maszyny -->
        <RatePresetSection
          v-if="isEdit && !form.is_service"
          :machine-id="Number(props.id)"
          :machine-name="form.name"
          @presets-changed="onPresetsChanged"
        />
      </div>
    </div>

    <!-- Owner picker modal -->
    <Transition name="modal">
      <div v-if="showOwnerPicker" class="modal-overlay" @click.self="showOwnerPicker = false">
        <div class="modal-box" style="min-width:580px;" role="dialog" aria-modal="true" aria-labelledby="owner-picker-title">
          <div class="modal-title" id="owner-picker-title">Wybierz właściciela (dostawcę)</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon" aria-hidden="true">⌕</span>
            <input v-model="pickerSearch" type="text" class="form-control" aria-label="Szukaj właściciela" placeholder="Szukaj..." @input="searchOwners" />
          </div>
          <div style="max-height:320px;overflow:auto;">
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>NIP</th><th>Miasto</th></tr></thead>
              <tbody>
                <tr v-for="c in pickerList" :key="c.id" @click="selectOwner(c)" style="cursor:pointer;">
                  <td>{{ c.name }}</td><td>{{ c.nip || '—' }}</td><td>{{ c.city || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showOwnerPicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useArticleStore } from '@/stores/articles'
import { useSettingsStore } from '@/stores/settings'
import { useFakturowniaStore } from '@/stores/fakturownia'
import { useToastStore } from '@/stores/toast'
import GlossaryTip from '@/components/GlossaryTip.vue'
import RatePresetSection from '@/components/articles/RatePresetSection.vue'
import api from '@/composables/useApi'

const props = defineProps({ id: String })
const router = useRouter()
const store = useArticleStore()
const settingsStore = useSettingsStore()
const fakturowniaStore = useFakturowniaStore()
const toastStore = useToastStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
// RAO-P2-050: walidacja per-pole (required name, cena/wartosc >= 0)
const fieldErrors = ref({})
const ownerName = ref('')

// RAO-P2-058: Fakturownia product mapping
const faProducts = computed(() => fakturowniaStore.products || [])
const faLoading = computed(() => fakturowniaStore.loading)
const faError = computed(() => fakturowniaStore.error)

const form = ref({
  name: '', is_service: false, internal_number: '', registration_no: '',
  serial_no: '', brand: '', model: '', replacement_value: null,
  category_id: null, owner_id: null, branch_id: null,
  description: '', notes: '', rental_days: null, article_type: '',
  zasieg_m: null, udzwig_t: null, dodatki: null,
  is_archival: false, is_external: false,  // RAO-P1-027
  power_type: 'other',  // RAO: typ zasilania maszyny (diesel|electric|other)
  fakturownia_product_id: null,  // RAO-P2-058
  fakturownia_tax_rate: null,    // RAO-P2-058: snapshot z FA
  fakturownia_gtu_code: null,    // RAO-P2-058: snapshot z FA
  fakturownia_pkwiu: null,       // RAO-P2-058: snapshot z FA
})

// RAO-P2-058: Auto-fill FA metadata when product selected
watch(() => form.value.fakturownia_product_id, (newId) => {
  if (!newId) {
    form.value.fakturownia_tax_rate = null
    form.value.fakturownia_gtu_code = null
    form.value.fakturownia_pkwiu = null
    return
  }
  const product = faProducts.value.find(p => p.id === newId)
  if (product) {
    form.value.fakturownia_tax_rate = product.tax || null
    form.value.fakturownia_gtu_code = product.gtu_code || null
    form.value.fakturownia_pkwiu = product.pkwiu || null
  }
})

const showOwnerPicker = ref(false)
const pickerSearch = ref('')
const pickerList = ref([])

// --- Cascade category pickers ---
const catSelectedMain = ref(null)
const catSelectedSub1 = ref(null)
const catSelectedSub2 = ref(null)

const catMainOptions = computed(() => settingsStore.categoriesTree)
const catSub1Options = computed(() => {
  if (!catSelectedMain.value) return []
  return catMainOptions.value.find(c => c.id === catSelectedMain.value)?.children || []
})
const catSub2Options = computed(() => {
  if (!catSelectedSub1.value) return []
  return catSub1Options.value.find(c => c.id === catSelectedSub1.value)?.children || []
})

// Aktualizuj form.category_id przy zmianie kaskady
watch([catSelectedMain, catSelectedSub1, catSelectedSub2], () => {
  form.value.category_id = catSelectedSub2.value ?? catSelectedSub1.value ?? catSelectedMain.value
})

// Pomocnicza: znajdz sciezke od root do node
function findCatPath(tree, id, path) {
  if (!path) path = []
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

// Ustaw kaskade po zaladowaniu artykulu
function setCategoryFromId(categoryId) {
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
  await Promise.all([settingsStore.fetchCategoriesTree(), settingsStore.fetchBranches(), settingsStore.fetchRateTypes()])

  const { data } = await api.get('/contractors', { params: { supplier: true, per_page: 50 } })
  pickerList.value = data.items

  // RAO-P2-058: Załaduj produkty Fakturownia do mapowania
  try { await fakturowniaStore.fetchProducts() } catch {}

  if (isEdit.value) {
    loading.value = true
    try {
      const data = await store.fetchOne(Number(props.id))
      Object.assign(form.value, data)
      if (data.owner_name) ownerName.value = data.owner_name
      setCategoryFromId(data.category_id)
      // RAO-P1-001: załaduj cenniki rozliczenia (tylko dla maszyn, nie usług)
      if (!data.is_service) {
        try {
          await settingsStore.fetchRatePresets(Number(props.id))
        } catch (e) {
          console.warn('Nie udało się pobrać cenników rozliczenia:', e)
        }
      }
    } finally {
      loading.value = false
    }
  }
})

function goBack() {
  // RAO-P2-070 Faza 5: router.back() z fallbackiem do listy artykułów
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/dashboard/articles')
  }
}

// RAO-P2-050: walidacja po stronie klienta — required name, wartosc odtworzeniowa >= 0
function validateForm() {
  fieldErrors.value = {}
  const errors = {}
  if (!form.value.name || !form.value.name.trim()) {
    errors.name = 'Podaj nazwe artykulu'
  }
  if (form.value.replacement_value !== null && form.value.replacement_value !== '' && form.value.replacement_value !== undefined) {
    const v = Number(form.value.replacement_value)
    if (Number.isNaN(v) || v < 0) {
      errors.replacement_value = 'Wartosc odtworzeniowa musi byc liczba nieujemna'
    }
  }
  if (form.value.rental_days !== null && form.value.rental_days !== '' && form.value.rental_days !== undefined) {
    const d = Number(form.value.rental_days)
    if (Number.isNaN(d) || d < 1) {
      errors.rental_days = 'Min. dni najmu musi byc liczba >= 1'
    }
  }
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function handleSave() {
  // RAO-P2-050: blokuj submit gdy bledy walidacji
  if (!validateForm()) return
  if (!form.value.name) { errorMsg.value = 'Podaj nazwę artykułu'; return }
  saving.value = true
  errorMsg.value = ''
  try {
    const payload = { ...form.value }
    if (!payload.replacement_value) payload.replacement_value = null
    if (!payload.rental_days) payload.rental_days = null
    if (!payload.article_type) payload.article_type = null
    if (!payload.zasieg_m) payload.zasieg_m = null
    if (!payload.udzwig_t) payload.udzwig_t = null
    if (!payload.dodatki) payload.dodatki = null

    if (isEdit.value && props.id) {
      await store.update(Number(props.id), payload)
    } else {
      const result = await store.create(payload)
      router.push(`/articles/${result.id}/edit`)
      return
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Błąd zapisu'
  } finally {
    saving.value = false
  }
}

async function handleDuplicate() {
  if (!isEdit.value) return
  try {
    const result = await store.duplicate(Number(props.id))
    router.push(`/articles/${result.id}/edit`)
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd duplikacji')
  }
}

let ownerTimer = null
async function searchOwners() {
  if (ownerTimer) clearTimeout(ownerTimer)
  ownerTimer = setTimeout(async () => {
    const { data } = await api.get('/contractors', { params: { search: pickerSearch.value, per_page: 50 } })
    pickerList.value = data.items
  }, 300)
}

// RAO-P1-043: cleanup timera pickera — zapobiega memory leakowi
onUnmounted(() => {
  if (ownerTimer) clearTimeout(ownerTimer)
})

function selectOwner(c) {
  form.value.owner_id = c.id
  ownerName.value = c.name
  showOwnerPicker.value = false
}

function clearOwner() {
  form.value.owner_id = null
  ownerName.value = ''
}

// --- RAO-P1-001: Cenniki rozliczenia maszyny ---
async function onPresetsChanged() {
  // Odśwież listę cenników po zmianach w RatePresetSection
  if (props.id && !form.value.is_service) {
    try {
      await settingsStore.fetchRatePresets(Number(props.id))
    } catch (e) {
      console.warn('Nie udało się odświeżyć cenników:', e)
    }
  }
}
</script>

<style scoped>
/* RAO-P2-050: widoczna walidacja per-pole (czerwony border + komunikat) */
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
