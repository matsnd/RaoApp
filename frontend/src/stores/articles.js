import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useArticleStore = defineStore('articles', () => {
  const list = ref([])
  const total = ref(0)
  const current = ref(null)
  const loading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/articles', { params })
      list.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/articles/${id}`)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/articles', payload)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.put(`/articles/${id}`, payload)
    return data
  }

  async function remove(id) {
    await api.delete(`/articles/${id}`)
  }

  async function duplicate(id) {
    const { data } = await api.post(`/articles/${id}/duplicate`)
    return data
  }

  async function checkAvailability(id, dateFrom, dateTo, excludeContractId = null) {
    const params = { date_from: dateFrom, date_to: dateTo }
    if (excludeContractId) params.exclude_contract_id = excludeContractId
    const { data } = await api.get(`/articles/${id}/availability`, { params })
    return data
  }

  return { list, total, current, loading, fetchList, fetchOne, create, update, remove, duplicate, checkAvailability }
})
