<template>
  <div style="display:flex;flex-direction:column;height:100vh;overflow:hidden;">
    <div class="toolbar">
      <button class="toolbar-btn" @click="$router.push('/dashboard/contracts')">←</button>
      <span class="toolbar-info">Panel administracyjny — Użytkownicy</span>
      <button class="btn btn-primary btn-sm" @click="showAddModal = true">+ Nowy użytkownik</button>
    </div>
    <div class="content-area" style="padding:var(--spacing-md);">
      <div class="page-card">
        <table class="data-grid">
          <thead>
            <tr>
              <th>Login</th>
              <th>Imię</th>
              <th>Nazwisko</th>
              <th>Rola</th>
              <th>Aktywny</th>
              <th>Ostatnie logowanie</th>
              <th style="width:140px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7"><TableSkeleton :rows="5" :cols="7" layout="inline" label="Ladowanie uzytkownikow" /></td>
            </tr>
            <tr v-else-if="!users.length">
              <td colspan="7" class="empty-state">Brak użytkowników</td>
            </tr>
            <tr v-for="u in users" :key="u.id">
              <td style="font-weight:600;">{{ u.login }}</td>
              <td>{{ u.first_name || '—' }}</td>
              <td>{{ u.last_name || '—' }}</td>
              <td><span :class="['badge', u.role === 'admin' ? 'badge-warning' : 'badge-info']">{{ u.role }}</span></td>
              <td><span :class="['badge', u.is_active ? 'badge-success' : 'badge-muted']">{{ u.is_active ? 'Tak' : 'Nie' }}</span></td>
              <td style="font-size:11px;">{{ u.last_login ? new Date(u.last_login).toLocaleString('pl-PL') : '—' }}</td>
              <td>
                <button class="btn-icon" @click="toggleActive(u)" :title="u.is_active ? 'Dezaktywuj' : 'Aktywuj'">
                  {{ u.is_active ? '⏸' : '▶' }}
                </button>
                <button class="btn-icon" @click="forcePasswordReset(u)" aria-label="Wymuś zmianę hasła" title="Wymuś zmianę hasła">🔑</button>
                <button class="btn-icon" @click="editUser(u)" aria-label="Edytuj" title="Edytuj">✎</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add user modal -->
    <Transition name="modal">
      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal-box" style="min-width:480px;" role="dialog" aria-modal="true" aria-labelledby="add-user-title">
          <div class="modal-title" id="add-user-title">Nowy użytkownik</div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Login *</label>
              <input v-model="addForm.login" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Hasło *</label>
              <input v-model="addForm.password" type="password" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Imię</label>
              <input v-model="addForm.first_name" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Nazwisko</label>
              <input v-model="addForm.last_name" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Email</label>
              <input v-model="addForm.email" type="email" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Rola</label>
              <select v-model="addForm.role" class="form-control">
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showAddModal = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="createUser" :disabled="saving">{{ saving ? '...' : 'Utwórz' }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit user modal -->
    <Transition name="modal">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal-box" style="min-width:480px;" role="dialog" aria-modal="true" aria-labelledby="edit-user-title">
          <div class="modal-title" id="edit-user-title">Edycja użytkownika: {{ editForm.login }}</div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Imię</label>
              <input v-model="editForm.first_name" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Nazwisko</label>
              <input v-model="editForm.last_name" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label class="form-label">Email</label>
              <input v-model="editForm.email" type="email" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Rola</label>
              <select v-model="editForm.role" class="form-control">
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showEditModal = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="updateUser" :disabled="saving">{{ saving ? '...' : 'Zapisz' }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/composables/useApi'
import { useToastStore } from '@/stores/toast'
import TableSkeleton from '@/components/TableSkeleton.vue'

const users = ref([])
const loading = ref(false)
const saving = ref(false)
const showAddModal = ref(false)
const showEditModal = ref(false)
const toastStore = useToastStore()

const addForm = ref({ login: '', password: '', first_name: '', last_name: '', email: '', role: 'user' })
const editForm = ref({ id: null, login: '', first_name: '', last_name: '', email: '', role: 'user' })

async function fetchUsers() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/users')
    users.value = data
  } finally {
    loading.value = false
  }
}

onMounted(fetchUsers)

async function createUser() {
  if (!addForm.value.login || !addForm.value.password) { toastStore.warning('Login i hasło są wymagane'); return }
  saving.value = true
  try {
    await api.post('/admin/users', addForm.value)
    await fetchUsers()
    showAddModal.value = false
    addForm.value = { login: '', password: '', first_name: '', last_name: '', email: '', role: 'user' }
    toastStore.success('Użytkownik utworzony')
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd tworzenia użytkownika')
  } finally {
    saving.value = false
  }
}

function editUser(u) {
  editForm.value = { id: u.id, login: u.login, first_name: u.first_name || '', last_name: u.last_name || '', email: u.email || '', role: u.role }
  showEditModal.value = true
}

async function updateUser() {
  saving.value = true
  try {
    await api.put(`/admin/users/${editForm.value.id}`, {
      first_name: editForm.value.first_name,
      last_name: editForm.value.last_name,
      email: editForm.value.email,
      role: editForm.value.role,
    })
    await fetchUsers()
    showEditModal.value = false
    toastStore.success('Dane użytkownika zaktualizowane')
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd aktualizacji')
  } finally {
    saving.value = false
  }
}

async function toggleActive(u) {
  try {
    if (u.is_active) {
      await api.patch(`/admin/users/${u.id}/deactivate`)
    } else {
      await api.patch(`/admin/users/${u.id}/activate`)
    }
    await fetchUsers()
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd')
  }
}

async function forcePasswordReset(u) {
  if (!confirm(`Wymusić zmianę hasła dla ${u.login}?`)) return
  try {
    await api.post(`/admin/users/${u.id}/force-password-reset`)
    toastStore.success('Wymuszono zmianę hasła')
  } catch (e: any) {
    toastStore.error(e?.response?.data?.detail || 'Błąd')
  }
}
</script>

<style scoped>
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
</style>
