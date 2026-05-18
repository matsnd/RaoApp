import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useServiceHourStore = defineStore('serviceHours', () => {
  const list = ref([])
  const loading = ref(false)

  async function fetchByPosition(positionId) {
    loading.value = true
    try {
      const { data } = await api.get(`/contracts/positions/${positionId}/service-hours`)
      list.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(positionId, payload) {
    const { data } = await api.post(`/contracts/positions/${positionId}/service-hours`, payload)
    list.value.push(data)
    return data
  }

  async function update(positionId, hourId, payload) {
    const { data } = await api.put(`/contracts/positions/${positionId}/service-hours/${hourId}`, payload)
    const index = list.value.findIndex(h => h.id === hourId)
    if (index !== -1) {
      list.value[index] = data
    }
    return data
  }

  async function remove(positionId, hourId) {
    await api.delete(`/contracts/positions/${positionId}/service-hours/${hourId}`)
    list.value = list.value.filter(h => h.id !== hourId)
  }

  function clear() {
    list.value = []
  }

  return {
    list,
    loading,
    fetchByPosition,
    create,
    update,
    remove,
    clear
  }
})