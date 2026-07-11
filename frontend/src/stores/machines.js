import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

// Faza 4a: store dla maszyn (rozszczelenie articles → machines/services/additional_services)
// Wzorzec: articles.js. Endpoint: /machines
export const useMachineStore = defineStore('machines', () => {
  const list = ref([])
  const total = ref(0)
  const current = ref(null)
  const loading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/machines', { params })
      // Backend zwraca list[MachineListItem] (array), nie {items, total}
      list.value = Array.isArray(data) ? data : (data.items ?? [])
      total.value = Array.isArray(data) ? data.length : (data.total ?? 0)
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/machines/${id}`)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/machines', payload)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.put(`/machines/${id}`, payload)
    return data
  }

  async function remove(id) {
    await api.delete(`/machines/${id}`)
  }

  async function duplicate(id) {
    const { data } = await api.post(`/machines/${id}/duplicate`)
    return data
  }

  async function checkAvailability(id, dateFrom, dateTo, excludeContractId = null) {
    const params = { date_from: dateFrom, date_to: dateTo }
    if (excludeContractId) params.exclude_contract_id = excludeContractId
    const { data } = await api.get(`/machines/${id}/availability`, { params })
    return data
  }

  // Faza 4a: pobierz ostatnie warunki rozliczeniowe maszyny (do prefill w umowie)
  async function fetchLastConditions(id) {
    const { data } = await api.get(`/machines/${id}/last-conditions`)
    return data
  }

  return {
    list, total, current, loading,
    fetchList, fetchOne, create, update, remove, duplicate, checkAvailability, fetchLastConditions,
  }
})
