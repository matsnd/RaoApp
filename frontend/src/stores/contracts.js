import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'
import { useFileDownload } from '@/composables/useFileDownload'

export const useContractStore = defineStore('contracts', () => {
  const list = ref([])
  const total = ref(0)
  const current = ref(null)
  const positions = ref([])
  const serviceFees = ref([])
  const loading = ref(false)

  const { downloadBlob } = useFileDownload()

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await api.get('/contracts', { params })
      list.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/contracts/${id}`)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/contracts', payload)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.put(`/contracts/${id}`, payload)
    return data
  }

  async function remove(id) {
    await api.delete(`/contracts/${id}`)
  }

  async function fetchPositions(contractId) {
    const { data } = await api.get(`/contracts/${contractId}/positions`)
    positions.value = data
    return data
  }

  async function createPosition(contractId, payload) {
    const { data } = await api.post(`/contracts/${contractId}/positions`, payload)
    return data
  }

  async function updatePosition(contractId, posId, payload) {
    const { data } = await api.put(`/contracts/${contractId}/positions/${posId}`, payload)
    return data
  }

  async function deletePosition(contractId, posId) {
    await api.delete(`/contracts/${contractId}/positions/${posId}`)
  }

  async function fetchConditions(contractId, posId) {
    const { data } = await api.get(`/contracts/${contractId}/positions/${posId}/conditions`)
    return data
  }

  async function createCondition(contractId, posId, payload) {
    const { data } = await api.post(`/contracts/${contractId}/positions/${posId}/conditions`, payload)
    return data
  }

  async function updateCondition(contractId, posId, condId, payload) {
    const { data } = await api.put(`/contracts/${contractId}/positions/${posId}/conditions/${condId}`, payload)
    return data
  }

  async function deleteCondition(contractId, posId, condId) {
    await api.delete(`/contracts/${contractId}/positions/${posId}/conditions/${condId}`)
  }

  async function fetchServiceFees(contractId) {
    const { data } = await api.get(`/contracts/${contractId}/service-fees`)
    serviceFees.value = data
    return data
  }

  async function generateReport(contractId, type = 'contract') {
    const response = await api.post(`/reports/contract/${contractId}`, null, {
      params: { type },
      responseType: 'blob',
    })
    const cd = response.headers['content-disposition'] || ''
    downloadBlob(response.data, cd, `raport_${contractId}.pdf`)
  }

  return {
    list, total, current, positions, serviceFees, loading,
    fetchList, fetchOne, create, update, remove,
    fetchPositions, createPosition, updatePosition, deletePosition,
    fetchConditions, createCondition, updateCondition, deleteCondition,
    fetchServiceFees, generateReport,
  }
})
