import axios from 'axios'

const api = axios.create({
  // RAO-P1-042: baseURL z env (produkcyjny .env.production ma VITE_API_URL)
  baseURL: import.meta.env.VITE_API_URL || '/rao/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rao_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthEndpoint = error.config?.url?.startsWith('/auth/')
    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('rao_token')
      localStorage.removeItem('rao_user')
      // RAO-P1-042: poprawny path do login (nie /rao/login) + redirect param
      const current = window.location.pathname + window.location.search
      window.location.href = `/login?redirect=${encodeURIComponent(current)}`
    }
    return Promise.reject(error)
  }
)

export default api
