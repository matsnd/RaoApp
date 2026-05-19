<template>
  <div>
    <!-- Add reservation form -->
    <div style="margin-bottom:20px;padding:16px;background:#f7f8ff;border-radius:8px;border:1px solid var(--color-border);">
      <h4 style="margin:0 0 12px;font-size:14px;font-weight:600;">Nowa rezerwacja</h4>
      <div v-if="formError" style="color:#e53e3e;background:#fff5f5;border:1px solid #fed7d7;border-radius:6px;padding:8px 12px;font-size:13px;margin-bottom:8px;">
        {{ formError }}
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
        <div class="form-group" style="margin:0;">
          <label class="form-label">Artykuł *</label>
          <div style="display:flex;gap:6px;">
            <input :value="selectedArticleName" type="text" class="form-control" disabled placeholder="Wybierz artykuł..." style="flex:1;font-size:12px;" />
            <button type="button" class="btn btn-secondary btn-sm" @click="showPicker = true">Wybierz</button>
          </div>
        </div>
        <div class="form-group" style="margin:0;">
          <label class="form-label">Notatka</label>
          <input v-model="form.note" type="text" class="form-control" maxlength="300" placeholder="Opcjonalna..." style="font-size:12px;" />
        </div>
        <div class="form-group" style="margin:0;">
          <label class="form-label">Data od *</label>
          <input v-model="form.reserved_from" type="date" class="form-control" style="font-size:12px;" />
        </div>
        <div class="form-group" style="margin:0;">
          <label class="form-label">Data do *</label>
          <input v-model="form.reserved_to" type="date" class="form-control" style="font-size:12px;" />
        </div>
      </div>

      <button class="btn btn-primary btn-sm" :disabled="saving" @click="addReservation">
        {{ saving ? '...' : '+ Dodaj rezerwację' }}
      </button>
    </div>

    <!-- Reservations list -->
    <div v-if="loading" class="empty-state">Ładowanie...</div>
    <div v-else-if="!reservations.length" class="empty-state">Brak rezerwacji.</div>
    <table v-else class="data-grid">
      <thead>
        <tr>
          <th>Artykuł</th>
          <th>Od</th>
          <th>Do</th>
          <th>Notatka</th>
          <th style="width:60px;">Akcje</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in reservations" :key="r.id">
          <td>{{ articleName(r.article_id) }}</td>
          <td>{{ formatDate(r.reserved_from) }}</td>
          <td>{{ formatDate(r.reserved_to) }}</td>
          <td>{{ r.note || '—' }}</td>
          <td>
            <button class="btn-icon" title="Usuń" @click="deleteReservation(r.id)">🗑</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Article picker modal -->
    <Transition name="modal">
      <div v-if="showPicker" class="modal-overlay" @click.self="showPicker = false">
        <div class="modal-box" style="min-width:580px;">
          <div class="modal-title">Wybierz artykuł (maszyna)</div>
          <div class="search-input-wrap" style="margin-bottom:12px;">
            <span class="search-icon">⌕</span>
            <input v-model="pickerSearch" type="text" class="form-control" placeholder="Szukaj..." @input="searchArticles" />
          </div>
          <div style="max-height:300px;overflow:auto;">
            <table class="data-grid">
              <thead><tr><th>Nazwa</th><th>Nr rej.</th><th>Marka</th></tr></thead>
              <tbody>
                <tr v-for="a in pickerList" :key="a.id" style="cursor:pointer;" @click="selectArticle(a)">
                  <td>{{ a.name }}</td>
                  <td>{{ a.registration_no || '—' }}</td>
                  <td>{{ a.brand || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showPicker = false">Anuluj</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/composables/useApi'

const loading = ref(false)
const saving = ref(false)
const formError = ref('')
const reservations = ref<any[]>([])
const articlesMap = ref<Record<number, string>>({})

const form = ref({ article_id: null as number | null, reserved_from: '', reserved_to: '', note: '' })
const selectedArticleName = ref('')

const showPicker = ref(false)
const pickerSearch = ref('')
const pickerList = ref<any[]>([])

onMounted(async () => {
  await Promise.all([loadReservations(), loadArticlesMap(), loadPickerList()])
})

async function loadReservations() {
  loading.value = true
  try {
    const { data } = await api.get('/reservations')
    reservations.value = data
  } catch (e) {
    console.error('Failed to load reservations', e)
  } finally {
    loading.value = false
  }
}

async function loadArticlesMap() {
  try {
    const { data } = await api.get('/articles', { params: { per_page: 300 } })
    for (const a of data.items) {
      articlesMap.value[a.id] = a.name
    }
  } catch (e) {
    console.error('loadArticlesMap error', e)
  }
}

async function loadPickerList() {
  const { data } = await api.get('/articles', { params: { per_page: 50, is_service: false } })
  pickerList.value = data.items
}

function articleName(id: number): string {
  return articlesMap.value[id] || `Artykuł #${id}`
}

function formatDate(d: string): string {
  if (!d) return '—'
  const [year, month, day] = d.split('-')
  return `${day}.${month}.${year}`
}

async function addReservation() {
  formError.value = ''
  if (!form.value.article_id) { formError.value = 'Wybierz artykuł'; return }
  if (!form.value.reserved_from) { formError.value = 'Podaj datę od'; return }
  if (!form.value.reserved_to) { formError.value = 'Podaj datę do'; return }
  saving.value = true
  try {
    await api.post('/reservations', {
      article_id: form.value.article_id,
      reserved_from: form.value.reserved_from,
      reserved_to: form.value.reserved_to,
      note: form.value.note || null,
    })
    form.value = { article_id: null, reserved_from: '', reserved_to: '', note: '' }
    selectedArticleName.value = ''
    await loadReservations()
  } catch (e: any) {
    formError.value = e.response?.data?.detail || 'Błąd zapisu'
  } finally {
    saving.value = false
  }
}

async function deleteReservation(id: number) {
  if (!confirm('Usunąć tę rezerwację?')) return
  try {
    await api.delete(`/reservations/${id}`)
    await loadReservations()
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Błąd usuwania')
  }
}

let timer: ReturnType<typeof setTimeout> | null = null
async function searchArticles() {
  if (timer) clearTimeout(timer)
  timer = setTimeout(async () => {
    const { data } = await api.get('/articles', {
      params: { search: pickerSearch.value, per_page: 50, is_service: false },
    })
    pickerList.value = data.items
  }, 300)
}

function selectArticle(a: any) {
  form.value.article_id = a.id
  selectedArticleName.value = a.name
  showPicker.value = false
  pickerSearch.value = ''
}
</script>
