<template>
  <div class="page-card" style="max-width:480px;margin:40px auto;">
    <h2 class="section-title" style="margin-bottom:24px;">Zmiana hasła</h2>
    <form @submit.prevent="handleChange">
      <div class="form-group">
        <label class="form-label">Aktualne hasło</label>
        <input v-model="form.current_password" type="password" class="form-control" required />
      </div>
      <div class="form-group">
        <label class="form-label">Nowe hasło (min. 6 znaków)</label>
        <input v-model="form.new_password" type="password" class="form-control" required minlength="6" />
      </div>
      <div class="form-group">
        <label class="form-label">Powtórz nowe hasło</label>
        <input v-model="form.confirm_password" type="password" class="form-control" required />
      </div>
      <div v-if="error" class="form-error" style="margin-bottom:12px;">{{ error }}</div>
      <div v-if="success" style="color:var(--color-success);font-size:13px;margin-bottom:12px;">{{ success }}</div>
      <div style="display:flex;gap:12px;">
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Zapisywanie...' : 'Zmień hasło' }}
        </button>
        <button type="button" class="btn btn-secondary" @click="$router.push('/home')">
          Anuluj
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/composables/useApi'

const router = useRouter()
const form = ref({ current_password: '', new_password: '', confirm_password: '' })
const error = ref('')
const success = ref('')
const loading = ref(false)

// RAO-P1-043: cleanup timera przekierowania — zapobiega memory leakowi
let redirectTimer = null
onUnmounted(() => {
  if (redirectTimer) clearTimeout(redirectTimer)
})

async function handleChange() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    await api.put('/auth/change-password', form.value)
    success.value = 'Hasło zmienione pomyślnie. Przekierowanie...'
    redirectTimer = setTimeout(() => router.push('/home'), 1500)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Błąd zmiany hasła'
  } finally {
    loading.value = false
  }
}
</script>
