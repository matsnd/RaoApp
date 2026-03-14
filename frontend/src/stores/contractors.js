import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useContractorStore = defineStore('contractors', () => {
  const list = ref([])
  const total = ref(0)
  const current = ref(null)
  const loading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/contractors', { params })
      list.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/contractors/${id}`)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/contractors', payload)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.put(`/contractors/${id}`, payload)
    return data
  }

  async function remove(id) {
    await api.delete(`/contractors/${id}`)
  }

  async function createAddress(contractorId, payload) {
    const { data } = await api.post(`/contractors/${contractorId}/addresses`, payload)
    return data
  }

  async function updateAddress(contractorId, addressId, payload) {
    const { data } = await api.put(`/contractors/${contractorId}/addresses/${addressId}`, payload)
    return data
  }

  async function removeAddress(contractorId, addressId) {
    await api.delete(`/contractors/${contractorId}/addresses/${addressId}`)
  }

  async function gusLookup(nip) {
    const { data } = await api.post('/contractors/gus-lookup', { nip })
    return data
  }

  return { list, total, current, loading, fetchList, fetchOne, create, update, remove, createAddress, updateAddress, removeAddress, gusLookup }
})
