import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('rao_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('rao_user') || 'null'))
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  // NOTE (2026-07-11): IDOR WYŁĄCZONY — single-user mode. Wszyscy zalogowani mają pełny dostęp.
  // isAdmin zawsze true jeśli zalogowany (wyłącza guardy UI w AppSidebar, ArchiveView, router).
  // Pełny RBAC wdrożony gdy pojawią się wymagania wieloużytkownikowe.
  const isAdmin = computed(() => !!token.value)
  const mustChangePassword = computed(() => user.value?.must_change_password)

  async function login(login, password) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/login', { login, password })
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem('rao_token', data.access_token)
      localStorage.setItem('rao_user', JSON.stringify(data.user))
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Błąd logowania'
      throw e
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('rao_token')
    localStorage.removeItem('rao_user')
  }

  async function changePassword(currentPassword, newPassword, confirmPassword) {
    await api.put('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    })
    if (user.value) {
      user.value.must_change_password = false
      localStorage.setItem('rao_user', JSON.stringify(user.value))
    }
  }

  async function refreshProfile() {
    const { data } = await api.get('/auth/profile')
    user.value = data
    localStorage.setItem('rao_user', JSON.stringify(data))
  }

  return { token, user, loading, error, isAuthenticated, isAdmin, mustChangePassword, login, logout, changePassword, refreshProfile }
})
