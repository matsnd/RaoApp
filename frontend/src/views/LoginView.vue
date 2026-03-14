<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">RAO</div>
      <h2 class="login-title">Logowanie</h2>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Login</label>
          <input v-model="form.login" type="text" class="form-control" :class="{ error: !!authStore.error }" placeholder="Podaj login" required autofocus />
        </div>
        <div class="form-group">
          <label class="form-label">Hasło</label>
          <input v-model="form.password" type="password" class="form-control" :class="{ error: !!authStore.error }" placeholder="Podaj hasło" required />
        </div>

        <div v-if="authStore.error" class="form-error" style="margin-bottom: 12px;">
          {{ authStore.error }}
        </div>

        <button type="submit" class="btn btn-primary" style="width:100%;" :disabled="authStore.loading">
          <span v-if="authStore.loading" class="spinner" style="width:14px;height:14px;"></span>
          <span v-else>Zaloguj się</span>
        </button>

        <div style="text-align:center;margin-top:16px;">
          <a href="#" @click.prevent="showForgot = true" style="font-size:13px;color:var(--color-primary);">Nie pamiętam hasła</a>
        </div>
      </form>
    </div>

    <!-- Forgot password modal -->
    <Transition name="modal">
      <div v-if="showForgot" class="modal-overlay" @click.self="showForgot = false">
        <div class="modal-box" style="min-width:340px;">
          <div class="modal-title">Reset hasła</div>
          <div class="form-group">
            <label class="form-label">Adres email</label>
            <input v-model="forgotEmail" type="email" class="form-control" placeholder="email@firma.pl" />
          </div>
          <div v-if="forgotMsg" style="color:var(--color-success);font-size:13px;margin-bottom:12px;">{{ forgotMsg }}</div>
          <div class="modal-actions">
            <button class="btn btn-secondary btn-sm" @click="showForgot = false">Anuluj</button>
            <button class="btn btn-primary btn-sm" @click="handleForgot" :disabled="forgotLoading">
              {{ forgotLoading ? '...' : 'Wyślij link' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/composables/useApi'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({ login: '', password: '' })
const showForgot = ref(false)
const forgotEmail = ref('')
const forgotMsg = ref('')
const forgotLoading = ref(false)

async function handleLogin() {
  try {
    const result = await authStore.login(form.value.login, form.value.password)
    if (result.must_change_password) {
      router.push('/change-password')
    } else {
      router.push('/')
    }
  } catch {}
}

async function handleForgot() {
  forgotLoading.value = true
  try {
    await api.post('/auth/forgot-password', { email: forgotEmail.value })
    forgotMsg.value = 'Link do resetu hasła został wysłany.'
  } catch {
    forgotMsg.value = 'Błąd. Sprawdź adres email.'
  } finally {
    forgotLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-sidebar-active) 100%);
}
.login-card {
  background: #fff;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-modal);
  padding: 48px 40px;
  width: 360px;
}
.login-logo {
  text-align: center;
  font-size: 36px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 4px;
  margin-bottom: 8px;
}
.login-title {
  text-align: center;
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  font-weight: 400;
  margin-bottom: 32px;
}
</style>
