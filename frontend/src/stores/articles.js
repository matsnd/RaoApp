import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

// Faza 5: backward-compat store — deleguje do /machines lub /services w zależności od is_service.
// Używany przez: DashboardView, ReservationsView, SettingsView, ContractFormView, ArticleFormView.
// Nowy kod powinien używać bezpośrednio useMachineStore / useServiceStore.
export const useArticleStore = defineStore('articles', () => {
  const list = ref([])
  const total = ref(0)
  const current = ref(null)
  const loading = ref(false)

  function _endpoint(params = {}) {
    // is_service=true → /services, w przeciwnym razie → /machines
    return params.is_service === true ? '/services' : '/machines'
  }

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const ep = _endpoint(params)
      const { data } = await api.get(ep, { params })
      // Backend zwraca list[...] (array), nie {items, total}
      list.value = Array.isArray(data) ? data : (data.items ?? [])
      total.value = Array.isArray(data) ? data.length : (data.total ?? 0)
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      // Spróbuj /machines, jeśli 404 spróbuj /services
      try {
        const { data } = await api.get(`/machines/${id}`)
        current.value = data
        return data
      } catch (e) {
        if (e.response?.status !== 404) throw e
        const { data } = await api.get(`/services/${id}`)
        current.value = data
        return data
      }
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const ep = _endpoint(payload)
    const { data } = await api.post(ep, payload)
    return data
  }

  async function update(id, payload) {
    const ep = _endpoint(payload)
    const { data } = await api.put(`${ep}/${id}`, payload)
    return data
  }

  async function remove(id) {
    // Spróbuj /machines, jeśli 404 spróbuj /services
    try {
      await api.delete(`/machines/${id}`)
    } catch (e) {
      if (e.response?.status !== 404) throw e
      await api.delete(`/services/${id}`)
    }
  }

  async function duplicate(id) {
    // Tylko maszyny mają duplikację
    const { data } = await api.post(`/machines/${id}/duplicate`)
    return data
  }

  async function checkAvailability(id, dateFrom, dateTo, excludeContractId = null) {
    const params = { date_from: dateFrom, date_to: dateTo }
    if (excludeContractId) params.exclude_contract_id = excludeContractId
    const { data } = await api.get(`/machines/${id}/availability`, { params })
    return data
  }

  return { list, total, current, loading, fetchList, fetchOne, create, update, remove, duplicate, checkAvailability }
})
