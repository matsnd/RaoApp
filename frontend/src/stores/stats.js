import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useStatsStore = defineStore('stats', () => {
  const loading = ref(false)              // period loading
  const loadingLive = ref(false)          // live section loading
  const loadingByCategory = ref(false)    // RAO-P1-017: category stats loading
  const summary = ref(null)
  const topMachines = ref([])
  const currentlyRented = ref(null)
  const additionalFees = ref(null)
  const locations = ref([])
  const byCategoryData = ref(null)        // RAO-P1-017: CategoryStatsResponse
  const positionsData = ref(null)         // RAO-P2-010: PositionStatsResponse

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
    loadingLive.value = true
    try {
      const { data } = await api.get('/stats/currently-rented')
      currentlyRented.value = data
      return data
    } finally {
      loadingLive.value = false
    }
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

  async function fetchPeriod(dateFrom, dateTo) {
    loading.value = true
    try {
      await Promise.all([
        fetchSummary(dateFrom, dateTo),
        fetchTopMachines(dateFrom, dateTo),
        fetchAdditionalFees(dateFrom, dateTo),
        fetchLocations(dateFrom, dateTo),
      ])
    } finally {
      loading.value = false
    }
  }

  async function fetchAll(dateFrom, dateTo) {
    await Promise.all([
      fetchCurrentlyRented(),
      fetchPeriod(dateFrom, dateTo),
    ])
  }

  // RAO-P1-017 — statystyki po kategoriach
  async function fetchByCategory(level = 'main', dateFrom = null, dateTo = null, includeArchival = false) {
    loadingByCategory.value = true
    try {
      const params = { level, include_archival: includeArchival }
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      const { data } = await api.get('/stats/by-category', { params })
      byCategoryData.value = data
      return data
    } finally {
      loadingByCategory.value = false
    }
  }

  // RAO-P2-010 — statystyki pozycji z filtrem typu
  async function fetchPositions(type = 'all', dateFrom = null, dateTo = null) {
    const params = { type }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get('/stats/positions', { params })
    positionsData.value = data
    return data
  }

  return {
    loading, loadingLive, loadingByCategory,
    summary, topMachines, currentlyRented, additionalFees, locations, byCategoryData, positionsData,
    fetchSummary, fetchTopMachines, fetchCurrentlyRented, fetchAdditionalFees, fetchLocations,
    fetchPeriod, fetchAll, fetchByCategory, fetchPositions,
  }
})
