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
  // RAO-P1-026: Nowe stany
  const loadingByPeriod = ref(false)
  const byPeriodData = ref(null)        // ByPeriodResponse
  const categoriesList = ref([])         // list[CategoriesListNode]
  // RAO-P2-032: toggle archival vs nowe — null=wszystkie, true=historyczne, false=nowe
  const isLegacy = ref(null)

  function _applyLegacy(params) {
    if (isLegacy.value !== null) params.is_legacy = isLegacy.value
  }

  async function fetchSummary(dateFrom, dateTo) {
    const params = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    _applyLegacy(params)
    const { data } = await api.get('/stats/fleet-summary', { params })
    summary.value = data
    return data
  }

  async function fetchTopMachines(dateFrom, dateTo, limit = 10) {
    const params = { limit }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    _applyLegacy(params)
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
    _applyLegacy(params)
    const { data } = await api.get('/stats/additional-fees', { params })
    additionalFees.value = data
    return data
  }

  async function fetchLocations(dateFrom, dateTo) {
    const params = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    _applyLegacy(params)
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

  // RAO-P1-017/026 — statystyki po kategoriach (rozszerzone filtry)
  // Archiwalne maszyny zawsze uwzględniane — stare umowy z migracji mają archiwalne artykuły
  async function fetchByCategory(
    level = 'main',
    dateFrom = null,
    dateTo = null,
    categoryMains = [],
    categorySubOne = null,
    categorySubTwo = null,
    articleType = 'all'
  ) {
    loadingByCategory.value = true
    try {
      const searchParams = new URLSearchParams()
      searchParams.set('level', level)
      if (dateFrom) searchParams.set('date_from', dateFrom)
      if (dateTo) searchParams.set('date_to', dateTo)
      if (articleType !== 'all') searchParams.set('article_type', articleType)
      categoryMains.forEach(m => searchParams.append('category_main', m))
      if (categorySubOne) searchParams.set('category_sub1', categorySubOne)
      if (categorySubTwo) searchParams.set('category_sub2', categorySubTwo)
      if (isLegacy.value !== null) searchParams.set('is_legacy', isLegacy.value)
      const { data } = await api.get('/stats/by-category?' + searchParams.toString())
      byCategoryData.value = data
      return data
    } finally {
      loadingByCategory.value = false
    }
  }

  // RAO-P1-026 — statystyki historyczne per-period
  // Archiwalne maszyny zawsze uwzględniane — spójne z fetchByCategory
  async function fetchByPeriod(
    granularity = 'month',
    dateFrom = null,
    dateTo = null,
    categoryMains = [],
    articleType = 'all'
  ) {
    loadingByPeriod.value = true
    try {
      const searchParams = new URLSearchParams()
      searchParams.set('granularity', granularity)
      if (dateFrom) searchParams.set('date_from', dateFrom)
      if (dateTo) searchParams.set('date_to', dateTo)
      if (articleType !== 'all') searchParams.set('article_type', articleType)
      categoryMains.forEach(m => searchParams.append('category_main', m))
      if (isLegacy.value !== null) searchParams.set('is_legacy', isLegacy.value)
      const { data } = await api.get('/stats/by-period?' + searchParams.toString())
      byPeriodData.value = data
      return data
    } finally {
      loadingByPeriod.value = false
    }
  }

  // RAO-P1-026 — lista kategorii z drzewem
  async function fetchCategoriesList() {
    const { data } = await api.get('/stats/categories-list')
    categoriesList.value = data
    return data
  }

  // RAO-P2-010 — statystyki pozycji z filtrem typu
  async function fetchPositions(type = 'all', dateFrom = null, dateTo = null) {
    const params = { type }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    _applyLegacy(params)
    const { data } = await api.get('/stats/positions', { params })
    positionsData.value = data
    return data
  }

  return {
    loading, loadingLive, loadingByCategory, loadingByPeriod,
    summary, topMachines, currentlyRented, additionalFees, locations,
    byCategoryData, positionsData, byPeriodData, categoriesList,
    isLegacy,
    fetchSummary, fetchTopMachines, fetchCurrentlyRented, fetchAdditionalFees, fetchLocations,
    fetchPeriod, fetchAll, fetchByCategory, fetchByPeriod, fetchCategoriesList, fetchPositions,
  }
})
