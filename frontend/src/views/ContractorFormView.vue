<template>
  <div style="display:flex;flex-direction:column;height:100%;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="goBack" title="Wstecz" aria-label="Wstecz">← Wstecz</button>
      <span class="toolbar-info">{{ isEdit ? `Edycja kontrahenta: ${form.name}` : 'Nowy kontrahent' }}</span>
      <button v-if="isEdit" class="btn btn-secondary btn-sm" @click="addContract" title="Dodaj umowę dla tego kontrahenta">+ Umowa</button>
      <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="saving">
        {{ saving ? '...' : 'Zapisz' }}
      </button>
    </div>

    <div class="content-area">
      <div v-if="loading" class="empty-state">Ładowanie...</div>
      <div v-else class="split-layout wide-left" style="height:calc(100vh - 48px - 32px);">
        <!-- LEFT: main form -->
        <div class="panel">
          <div class="panel-header">Dane kontrahenta</div>
          <div class="panel-body">
            <div v-if="errorMsg" style="color:var(--color-danger);font-size:13px;margin-bottom:12px;padding:8px;background:#FED7D7;border-radius:6px;" role="alert">{{ errorMsg }}</div>

            <div class="form-group">
              <label class="form-label" for="contractor-name">Pełna nazwa *</label>
              <input id="contractor-name" v-model="form.name" type="text" class="form-control" :class="{ error: fieldErrors.name }" :aria-invalid="!!fieldErrors.name" aria-describedby="contractor-name-error" placeholder="Nazwa firmy lub imię i nazwisko" required />
              <span v-if="fieldErrors.name" class="field-error" id="contractor-name-error" role="alert">{{ fieldErrors.name }}</span>
            </div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label" for="contractor-name-short">Nazwa skrócona</label>
                <input id="contractor-name-short" v-model="form.name_short" type="text" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label" for="contractor-nip">NIP
                  <button type="button" class="btn btn-sm" style="margin-left:8px;padding:2px 10px;font-size:11px;background:var(--color-primary);color:#fff;border-radius:12px;" @click="gusLookup" :disabled="gusLoading" aria-label="Pobierz dane z GUS po NIP">
                    {{ gusLoading ? '...' : 'GUS' }}
                  </button>
                </label>
                <input id="contractor-nip" v-model="form.nip" type="text" class="form-control" :class="{ error: fieldErrors.nip }" :aria-invalid="!!fieldErrors.nip" aria-describedby="contractor-nip-error" placeholder="0000000000" maxlength="20" />
                <span v-if="fieldErrors.nip" class="field-error" id="contractor-nip-error" role="alert">{{ fieldErrors.nip }}</span>
              </div>
            </div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label" for="contractor-regon">REGON</label>
                <input id="contractor-regon" v-model="form.regon" type="text" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label" for="contractor-pesel">PESEL</label>
                <input id="contractor-pesel" v-model="form.pesel" type="text" class="form-control" />
              </div>
            </div>

            <div class="section-title" style="font-size:13px;margin-top:16px;">Adres główny</div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label" for="contractor-postal">Kod pocztowy</label>
                <input id="contractor-postal" v-model="form.postal_code" type="text" class="form-control" placeholder="00-000" />
              </div>
              <div class="form-group">
                <label class="form-label" for="contractor-city">Miejscowość</label>
                <input id="contractor-city" v-model="form.city" type="text" class="form-control" />
              </div>
            </div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label" for="contractor-street">Ulica</label>
                <input id="contractor-street" v-model="form.street" type="text" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label" for="contractor-unit">Nr lokalu</label>
                <input id="contractor-unit" v-model="form.unit" type="text" class="form-control" />
              </div>
            </div>

            <div class="section-title" style="font-size:13px;margin-top:16px;">Kontakt</div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label" for="contractor-person1">Osoba kontaktowa 1</label>
                <input id="contractor-person1" v-model="form.contact_person1" type="text" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label" for="contractor-phone1">Telefon 1</label>
                <input id="contractor-phone1" v-model="form.phone1" type="text" class="form-control" />
              </div>
            </div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label" for="contractor-person2">Osoba kontaktowa 2</label>
                <input id="contractor-person2" v-model="form.contact_person2" type="text" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label" for="contractor-phone2">Telefon 2</label>
                <input id="contractor-phone2" v-model="form.phone2" type="text" class="form-control" />
              </div>
            </div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label" for="contractor-landline">Telefon stacjonarny</label>
                <input id="contractor-landline" v-model="form.landline_phone" type="text" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label" for="contractor-email">Email</label>
                <input id="contractor-email" v-model="form.email" type="email" class="form-control" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label" for="contractor-website">Strona WWW</label>
              <input id="contractor-website" v-model="form.website" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label" for="contractor-notes">Uwagi</label>
              <textarea id="contractor-notes" v-model="form.notes" class="form-control" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label class="checkbox-group">
                <input type="checkbox" v-model="form.is_supplier" />
                <span>Dostawca (maszyny zewnętrzne)</span>
              </label>
            </div>
          </div>
        </div>

        <!-- RIGHT: addresses -->
        <div v-if="isEdit" class="panel">
          <div class="panel-header">
            Adresy dostawy
            <button class="toolbar-btn" style="margin-left:auto;width:24px;height:24px;" @click="addAddress" aria-label="Dodaj adres dostawy" title="Dodaj adres dostawy">+</button>
          </div>
          <div class="panel-body" style="padding:0;">
            <div v-if="!contractor?.addresses?.length" class="empty-state">Brak adresów</div>
            <div
              v-for="addr in contractor?.addresses"
              :key="addr.id"
              :class="['address-item', { selected: selectedAddrId === addr.id }]"
              @click="selectAddress(addr)"
            >
              <div style="font-weight:600;font-size:13px;">{{ addr.name || addr.city || 'Adres' }}</div>
              <div style="font-size:11px;color:var(--color-text-muted);">{{ [addr.street, addr.postal_code, addr.city].filter(Boolean).join(', ') }}</div>
              <div style="font-size:11px;margin-top:2px;">
                <span v-if="addr.is_headquarters" class="badge badge-info" style="font-size:10px;">Siedziba</span>
                <span v-if="addr.is_default_delivery" class="badge badge-success" style="font-size:10px;margin-left:4px;">Domyślna dostawa</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="panel">
          <div class="panel-header">Adresy dostawy</div>
          <div class="panel-body empty-state">Zapisz kontrahenta, aby dodać adresy.</div>
        </div>
      </div>
    </div>

    <!-- Address form modal -->
    <Transition name="modal">
      <div v-if="showAddrModal" class="modal-overlay" @click.self="showAddrModal = false">
        <div class="modal-box" style="min-width:500px;" role="dialog" aria-modal="true" aria-labelledby="addr-modal-title">
          <div class="modal-title" id="addr-modal-title">{{ editingAddr ? 'Edytuj adres' : 'Nowy adres dostawy' }}</div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label" for="addr-name">Nazwa adresu</label>
              <input id="addr-name" v-model="addrForm.name" type="text" class="form-control" placeholder="np. Budowa Warszawa" />
            </div>
            <div class="form-group">
              <label class="form-label" for="addr-postal">Kod pocztowy</label>
              <input id="addr-postal" v-model="addrForm.postal_code" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label" for="addr-city">Miejscowość</label>
              <input id="addr-city" v-model="addrForm.city" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label" for="addr-street">Ulica</label>
              <input id="addr-street" v-model="addrForm.street" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label" for="addr-contact">Kontakt</label>
              <input id="addr-contact" v-model="addrForm.contact_person" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label" for="addr-phone">Telefon</label>
              <input id="addr-phone" v-model="addrForm.phone" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-group"><input type="checkbox" v-model="addrForm.is_headquarters" /> <span>Siedziba firmy</span></label>
          </div>
          <div class="form-group">
            <label class="checkbox-group"><input type="checkbox" v-model="addrForm.is_default_delivery" /> <span>Domyślna dostawa</span></label>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showAddrModal = false">Anuluj</button>
            <button v-if="editingAddr" class="btn btn-danger btn-sm" @click="deleteAddress">Usuń</button>
            <button class="btn btn-primary btn-sm" @click="saveAddress" :disabled="savingAddr">
              {{ savingAddr ? '...' : 'Zapisz' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useContractorStore } from '@/stores/contractors'
import { useToastStore } from '@/stores/toast'
import { extractErrorMessage } from '@/utils/validation'

const props = defineProps({ id: String })
const router = useRouter()
const store = useContractorStore()
const toastStore = useToastStore()

const isEdit = computed(() => !!props.id)
const loading = ref(false)
const saving = ref(false)
const gusLoading = ref(false)
const errorMsg = ref('')
// RAO-P2-050: walidacja per-pole (required name, NIP 10 cyfr)
const fieldErrors = ref({})
const contractor = ref(null)
const selectedAddrId = ref(null)
const showAddrModal = ref(false)
const editingAddr = ref(null)
const savingAddr = ref(false)

const form = ref({
  name: '', name_short: '', nip: '', regon: '', pesel: '',
  postal_code: '', city: '', street: '', unit: '', notes: '',
  is_supplier: false, email: '', contact_person1: '', phone1: '',
  contact_person2: '', phone2: '', landline_phone: '', website: '',
})

const addrForm = ref({ name: '', postal_code: '', city: '', street: '', contact_person: '', phone: '', email: '', is_headquarters: false, is_default_delivery: false, notes: '', country_code: 'PL' })

onMounted(async () => {
  if (isEdit.value) {
    loading.value = true
    try {
      const data = await store.fetchOne(Number(props.id))
      contractor.value = data
      Object.assign(form.value, data)
    } finally {
      loading.value = false
    }
  }
})

function goBack() {
  // RAO-P2-070 Faza 5: router.back() z fallbackiem do listy kontrahentów
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/dashboard/contractors')
  }
}

// NIP checksum validation (Polish NIP algorithm)
function isValidNIP(nip) {
  if (!nip || nip.length !== 10) return false
  if (!/^\d{10}$/.test(nip)) return false
  const weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
  let sum = 0
  for (let i = 0; i < 9; i++) {
    sum += parseInt(nip[i]) * weights[i]
  }
  const checkDigit = sum % 11
  return checkDigit === parseInt(nip[9])
}

// RAO-P2-050: walidacja po stronie klienta — required name, NIP 10 cyfr + checksum
function validateForm() {
  fieldErrors.value = {}
  const errors = {}
  if (!form.value.name || !form.value.name.trim()) {
    errors.name = 'Podaj pelna nazwe kontrahenta'
  }
  if (form.value.nip) {
    if (!/^\d{10}$/.test(form.value.nip)) {
      errors.nip = 'NIP musi miec 10 cyfr'
    } else if (!isValidNIP(form.value.nip)) {
      errors.nip = 'NIP nieprawidlowy (bledna suma kontrolna)'
    }
  }
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function handleSave() {
  // RAO-P2-050: blokuj submit gdy bledy walidacji
  if (!validateForm()) return
  saving.value = true
  errorMsg.value = ''
  try {
    if (isEdit.value) {
      await store.update(Number(props.id), form.value)
      contractor.value = await store.fetchOne(Number(props.id))
    } else {
      const result = await store.create(form.value)
      router.push(`/contractors/${result.id}/edit`)
    }
  } catch (e) {
    errorMsg.value = extractErrorMessage(e, 'Błąd zapisu kontrahenta')
  } finally {
    saving.value = false
  }
}

async function gusLookup() {
  if (!form.value.nip || form.value.nip.length !== 10) {
    toastStore.warning('Podaj 10-cyfrowy NIP')
    return
  }
  if (!isValidNIP(form.value.nip)) {
    toastStore.warning('NIP nieprawidłowy (błędna suma kontrolna)')
    return
  }
  gusLoading.value = true
  try {
    const data = await store.gusLookup(form.value.nip)
    if (data.name) form.value.name = data.name
    if (data.street) form.value.street = data.street + (data.building_number ? ' ' + data.building_number : '')
    if (data.postal_code) form.value.postal_code = data.postal_code
    if (data.city) form.value.city = data.city
    if (data.regon) form.value.regon = data.regon
    form.value.gus_date = new Date().toISOString().slice(0, 10)
    // Auto-create address from GUS data if editing
    if (isEdit.value && data.city) {
      try {
        await store.createAddress(Number(props.id), {
          name: 'Siedziba (GUS)',
          postal_code: data.postal_code || '',
          city: data.city || '',
          street: (data.street || '') + (data.building_number ? ' ' + data.building_number : ''),
          is_headquarters: true,
          is_default_delivery: false,
          country_code: 'PL',
        })
        contractor.value = await store.fetchOne(Number(props.id))
      } catch {}
    }
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd pobierania danych z GUS')
  } finally {
    gusLoading.value = false
  }
}

function addAddress() {
  editingAddr.value = null
  Object.assign(addrForm.value, { name: '', postal_code: '', city: '', street: '', contact_person: '', phone: '', email: '', is_headquarters: false, is_default_delivery: false, notes: '', country_code: 'PL' })
  showAddrModal.value = true
}

function selectAddress(addr) {
  selectedAddrId.value = addr.id
  editingAddr.value = addr
  Object.assign(addrForm.value, addr)
  showAddrModal.value = true
}

async function saveAddress() {
  savingAddr.value = true
  try {
    if (editingAddr.value) {
      await store.updateAddress(Number(props.id), editingAddr.value.id, addrForm.value)
    } else {
      await store.createAddress(Number(props.id), addrForm.value)
    }
    contractor.value = await store.fetchOne(Number(props.id))
    showAddrModal.value = false
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd zapisu adresu')
  } finally {
    savingAddr.value = false
  }
}

async function deleteAddress() {
  if (!confirm('Usunąć ten adres?')) return
  try {
    await store.removeAddress(Number(props.id), editingAddr.value.id)
    contractor.value = await store.fetchOne(Number(props.id))
    showAddrModal.value = false
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd usuwania')
  }
}

function addContract() {
  router.push({ path: '/contracts/new', query: { contractor_id: props.id } })
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
.address-item {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.address-item:hover { background: var(--color-bg-light); }
.address-item.selected { background: rgba(29,43,83,0.08); border-left: 3px solid var(--color-primary); }
</style>
