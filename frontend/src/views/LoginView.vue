<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">RAO</div>
      <h2 class="login-title">Logowanie</h2>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Login</label>
          <div class="input-with-icon">
            <span class="input-icon">👤</span>
            <input v-model="form.login" type="text" class="form-control" :class="{ error: !!authStore.error }" placeholder="Podaj login" required autofocus />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Hasło</label>
          <div class="input-with-icon">
            <span class="input-icon">🔒</span>
            <input v-model="form.password" :type="showPassword ? 'text' : 'password'" class="form-control" :class="{ error: !!authStore.error }" placeholder="Podaj hasło" required />
            <button type="button" class="password-toggle" @click="showPassword = !showPassword">
              {{ showPassword ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>

        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input v-model="rememberMe" type="checkbox" />
            <span>Zapamiętaj mnie</span>
          </label>
        </div>

        <div v-if="authStore.error" class="form-error">
          <span class="error-icon">⚠️</span>
          <span>{{ authStore.error }}</span>
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="authStore.loading" :class="{ shaking: shakeAnimation }">
          <span v-if="authStore.loading" class="spinner"></span>
          <span v-else>Zaloguj się</span>
        </button>

        <div class="forgot-password">
          <a href="#" @click.prevent="showForgot = true">Nie pamiętam hasła</a>
        </div>
      </form>
    </div>

    <!-- Forgot password modal -->
    <Transition name="modal">
      <div v-if="showForgot" class="modal-overlay" @click.self="showForgot = false">
        <div class="modal-box">
          <div class="modal-title">Reset hasła</div>
          <div class="form-group">
            <label class="form-label">Adres email</label>
            <input v-model="forgotEmail" type="email" class="form-control" placeholder="email@firma.pl" />
          </div>
          <div v-if="forgotMsg" class="success-message">{{ forgotMsg }}</div>
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
const showPassword = ref(false)
const rememberMe = ref(false)
const shakeAnimation = ref(false)

async function handleLogin() {
  try {
    const result = await authStore.login(form.value.login, form.value.password)
    if (result.must_change_password) {
      router.push('/change-password')
    } else {
      router.push('/')
    }
  } catch {
    // Shake animation on error
    shakeAnimation.value = true
    setTimeout(() => shakeAnimation.value = false, 300)
  }
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
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
}
.login-card {
  background: #fff;
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-modal);
  padding: 48px 40px;
  width: 360px;
}
.login-logo {
  text-align: center;
  font-size: 36px;
  font-weight: 800;
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

.form-group {
  margin-bottom: 20px;
}
.form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-heading);
  margin-bottom: 8px;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}
.input-icon {
  position: absolute;
  left: 12px;
  font-size: 16px;
  color: var(--color-text-muted);
}
.form-control {
  width: 100%;
  padding: 10px 14px;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background: var(--color-bg-white);
  color: var(--color-text-body);
  transition: all 0.2s;
}
.input-with-icon .form-control {
  padding-left: 40px;
}
.input-with-icon .password-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.input-with-icon .password-toggle:hover {
  opacity: 1;
}
.form-control:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(29,43,83,0.1);
}
.form-control.error {
  border-color: var(--color-error);
  background: #FFF5F5;
}

.checkbox-group {
  margin-bottom: 24px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  cursor: pointer;
}
.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.form-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #FFF5F5;
  border: 1px solid var(--color-error);
  border-radius: var(--border-radius-sm);
  color: var(--color-error);
  font-size: var(--font-size-sm);
  font-weight: 500;
  margin-bottom: 20px;
}
.error-icon {
  font-size: 16px;
}

.btn {
  padding: 10px 28px;
  font-family: var(--font-family);
  font-weight: 600;
  font-size: var(--font-size-base);
  border: none;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  box-shadow: var(--shadow-button);
}
.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(29,43,83,0.3);
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-block {
  width: 100%;
}
.btn-secondary {
  background: var(--color-bg-light);
  color: var(--color-text-body);
  border: 1px solid var(--color-border);
}
.btn-secondary:hover {
  background: var(--color-border);
}
.btn-sm {
  padding: 6px 16px;
  font-size: var(--font-size-sm);
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.shaking {
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
}
@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

.forgot-password {
  text-align: center;
  margin-top: 16px;
}
.forgot-password a {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  text-decoration: none;
  transition: opacity 0.2s;
}
.forgot-password a:hover {
  opacity: 0.7;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-box {
  background: #fff;
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-modal);
  padding: 24px;
  min-width: 340px;
}
.modal-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-heading);
  margin-bottom: 20px;
}
.success-message {
  color: var(--color-success);
  font-size: var(--font-size-sm);
  margin-bottom: 12px;
}
.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 20px;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
