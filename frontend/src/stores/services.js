import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

// Faza 4a: store dla usług (rozszczelenie articles → machines/services/additional_services)
// Wzorzec: articles.js. Endpoint: /services. Bez duplicate/availability.
export const useServiceStore = defineStore('services', () => {
  const list = ref([])
  const total = ref(0)
  const current = ref(null)
  const loading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/services', { params })
      // Backend zwraca list[ServiceListItem] (array), nie {items, total}
      list.value = Array.isArray(data) ? data : (data.items ?? [])
      total.value = Array.isArray(data) ? data.length : (data.total ?? 0)
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/services/${id}`)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/services', payload)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.put(`/services/${id}`, payload)
    return data
  }

  async function remove(id) {
    await api.delete(`/services/${id}`)
  }

  return { list, total, current, loading, fetchList, fetchOne, create, update, remove }
})
