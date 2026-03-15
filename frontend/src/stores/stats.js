import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import api from '@/composables/useApi'

export const useStatsStore = defineStore('stats', () => {
  const loading = ref(false)
  const summary = ref(null)
  const topMachines = ref([])
  const currentlyRented = ref(null)
  const additionalFees = ref(null)
  const locations = ref([])

  async function fetchSummary(dateFrom, dateTo) {
    const params = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get('/stats/fleet-summary', { params })
    summary.value = data
    return data
  }

  async function fetchTopMachines(dateFrom, dateTo, limit = 10) {
    const params = { limit }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get('/stats/top-machines', { params })
    topMachines.value = data
    return data
  }

  async function fetchCurrentlyRented() {
    const { data } = await api.get('/stats/currently-rented')
    currentlyRented.value = data
    return data
  }

  async function fetchAdditionalFees(dateFrom, dateTo) {
    const params = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get('/stats/additional-fees', { params })
    additionalFees.value = data
    return data
  }

  async function fetchLocations(dateFrom, dateTo) {
    const params = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get('/stats/locations', { params })
    locations.value = data
    return data
  }

  async function fetchAll(dateFrom, dateTo) {
    loading.value = true
    try {
      await Promise.all([
        fetchSummary(dateFrom, dateTo),
        fetchTopMachines(dateFrom, dateTo),
        fetchCurrentlyRented(),
        fetchAdditionalFees(dateFrom, dateTo),
        fetchLocations(dateFrom, dateTo),
      ])
    } finally {
      loading.value = false
    }
  }

  return {
    loading, summary, topMachines, currentlyRented, additionalFees, locations,
    fetchSummary, fetchTopMachines, fetchCurrentlyRented, fetchAdditionalFees, fetchLocations, fetchAll,
  }
})
