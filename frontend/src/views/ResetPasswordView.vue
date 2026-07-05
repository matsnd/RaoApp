<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">RAO</div>
      <h2 class="login-title">Ustaw nowe hasło</h2>
      <form @submit.prevent="handleReset">
        <div class="form-group">
          <label class="form-label" for="reset-new-password">Nowe hasło</label>
          <input id="reset-new-password" v-model="form.new_password" type="password" class="form-control" placeholder="Min. 6 znaków" required />
        </div>
        <div class="form-group">
          <label class="form-label" for="reset-confirm-password">Powtórz hasło</label>
          <input id="reset-confirm-password" v-model="form.confirm_password" type="password" class="form-control" required />
        </div>
        <div v-if="error" class="form-error" style="margin-bottom:12px;" role="alert">{{ error }}</div>
        <div v-if="success" style="color:var(--color-success);font-size:13px;margin-bottom:12px;" role="status">{{ success }}</div>
        <button type="submit" class="btn btn-primary" style="width:100%;" :disabled="loading">
          {{ loading ? '...' : 'Ustaw hasło' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const form = ref({ new_password: '', confirm_password: '' })
const error = ref('')
const success = ref('')
const loading = ref(false)
const token = ref('')

onMounted(() => { token.value = route.query.token || '' })

// RAO-P1-043: cleanup timera przekierowania — zapobiega memory leakowi
let redirectTimer = null
onUnmounted(() => {
  if (redirectTimer) clearTimeout(redirectTimer)
})

async function handleReset() {
  loading.value = true
  error.value = ''
  try {
    await api.post('/auth/reset-password', { token: token.value, ...form.value })
    success.value = 'Hasło ustawione. Przekierowanie...'
    redirectTimer = setTimeout(() => router.push('/login'), 2000)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Błąd resetu hasła'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height:100vh; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,var(--color-primary) 0%,var(--color-sidebar-active) 100%); }
.login-card { background:#fff; border-radius:var(--border-radius-lg); box-shadow:var(--shadow-modal); padding:48px 40px; width:360px; }
.login-logo { text-align:center; font-size:36px; font-weight:700; color:var(--color-primary); letter-spacing:4px; margin-bottom:8px; }
.login-title { text-align:center; font-size:var(--font-size-md); color:var(--color-text-muted); font-weight:400; margin-bottom:32px; }
</style>
