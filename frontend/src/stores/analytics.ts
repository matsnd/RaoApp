import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

// ── Typy odpowiedzi backendu (mirror schemas.py + explorer/router.py) ──────────
// Decimal z FastAPI przychodzi jako string; formatCurrency obsługuje string|number.

export interface FleetSummary {
  total_rented: number
  total_machines: number
  utilization_pct: number
  period_revenue: string | number
  top_machine_name: string | null
  top_machine_revenue: string | number | null
  contracts_in_period: number
}

export interface TopMachineItem {
  // RAO Faza 2a (opcja E): backend zwraca bucket "Inne (niezmapowane z FA)"
  // z machine_id=null dla settlementów FA bez zmapowanej pozycji umowy.
  // RAO Faza 4b: article_id → machine_id (backend stats zwraca machine_id).
  machine_id: number | null
  article_id: number | null  // backward-compat alias
  name: string
  internal_number: string | null
  revenue: string | number
  rented_days: number
  contracts_count: number
}

export interface CurrentlyRentedItem {
  machine_id: number
  article_id: number  // backward-compat alias
  name: string
  internal_number: string | null
  category_main: string | null
  contract_number: string
  contractor_name: string | null
  return_date: string | null
}

export interface CurrentlyRentedResponse {
  total_rented: number
  total_machines: number
  utilization_pct: number
  items: CurrentlyRentedItem[]
}

export interface ServiceFeeItem {
  service_id: number | null  // RAO Faza 4c: service_id dla usług dodatkowych
  machine_id: number  // backward-compat alias (phase 4b)
  article_id: number  // backward-compat alias
  service_name: string
  total_revenue: string | number
  times_billed: number
  contracts_count: number
}

export interface AdditionalFeesResponse {
  date_from: string
  date_to: string
  total_services_revenue: string | number
  breakdown: ServiceFeeItem[]
}

export interface LocationStatItem {
  city: string
  postal_code: string | null
  gmina: string | null
  powiat: string | null
  wojewodztwo: string | null
  rentals_count: number
  total_revenue: string | number
}

export interface PositionStatItem {
  machine_id: number
  service_id: number | null  // RAO Faza 4c: service_id dla pozycji-usług (is_service=true)
  article_id: number  // backward-compat alias
  machine_name: string
  article_name: string  // backward-compat alias (backend coalesce)
  internal_number: string | null
  is_service: boolean
  category_main: string | null
  revenue: string | number
  rented_days: number
  contracts_count: number
  times_billed: number
}

export interface PositionStatsResponse {
  date_from: string
  date_to: string
  type: string
  total_revenue: string | number
  total_machines_revenue: string | number
  total_services_revenue: string | number
  items: PositionStatItem[]
}

export interface CategoryStatItem {
  category_name: string
  articles_count: number
  rented_days: number
  revenue: string | number
  contracts_count: number
}

export interface CategoryStatsResponse {
  date_from: string
  date_to: string
  level: string
  total_revenue: string | number
  items: CategoryStatItem[]
}

export interface ByPeriodItem {
  period: string
  category_name: string
  revenue: string | number
  contracts_count: number
  rented_days: number
}

export interface ByPeriodResponse {
  date_from: string
  date_to: string
  granularity: string
  items: ByPeriodItem[]
}

export interface CategoriesListNode {
  id: number
  name: string
  level: string
  articles_count: number
  children: CategoriesListNode[]
}

export interface MachineRentalRow {
  contract_id: number
  contract_number: string
  date_from: string | null
  date_to: string | null
  days: number
  contractor_name: string | null
  revenue: number
}

export interface MachineDetailsResponse {
  machine: { id: number; name: string; internal_number: string | null; category: string | null }
  period: { from: string | null; to: string | null }
  metrics: {
    total_revenue: number
    total_days: number
    rental_count: number
    avg_daily_revenue: number
    utilization_percentage: number | null
  }
  rentals: MachineRentalRow[]
}

export interface LocationRankingItem {
  rank: number
  city: string
  postal_code: string | null
  gmina: string | null
  powiat: string | null
  wojewodztwo: string | null
  rentals_count: number
  total_revenue: number
}

export interface LocationsRankingResponse {
  locations: LocationRankingItem[]
  count: number
  group_by?: 'city' | 'pna'
  period: { from: string | null; to: string | null }
}

export interface LocationDetailsResponse {
  postal_code: string | null
  city: string
  gmina?: string | null
  powiat?: string | null
  wojewodztwo?: string | null
  metrics: {
    contracts_count: number
    unique_contractors: number
    total_revenue: number
    avg_revenue_per_contract: number
    pna_count?: number
  }
  pna_breakdown?: { postal_code: string; rentals_count: number; total_revenue: number }[]
  top_machines: { name: string; rental_count: number; total_revenue: number }[]
  top_contractors: { contractor_name: string; contract_count: number; total_revenue: number }[]
  monthly_trend: unknown[]
}

// ── Drill-down state ──────────────────────────────────────────────────────────
export type DrillDownKind = 'machine' | 'location' | 'service' | 'category'

// RAO-P1-014: drilldown usługi — odpowiedź /explorer/services/{article_id}
export interface ServiceDetailsResponse {
  service: { id: number; name: string }
  metrics: { times_billed: number; total_revenue: number }
  top_contractors: { contractor_name: string; contract_count: number; total_revenue: number }[]
  location_breakdown: { city: string; postal_code: string | null; contract_count: number; total_revenue: number }[]
}

export interface DrillDownState {
  open: boolean
  kind: DrillDownKind | null
  id: number | string | null
  name: string
  title: string
  subtitle: string
}

const emptyDrillDown: DrillDownState = {
  open: false,
  kind: null,
  id: null,
  name: '',
  title: '',
  subtitle: '',
}

// ── Filtry ────────────────────────────────────────────────────────────────────
export interface AnalyticsFiltersPayload {
  dateFrom: string
  dateTo: string
  contractorId: number | null
  city: string
  internalNumber?: string
  articleType?: 'all' | 'machine' | 'service'
}

// ── Store ─────────────────────────────────────────────────────────────────────
export const useAnalyticsStore = defineStore('analytics', () => {
  const loading = ref(false)
  const loadingLive = ref(false)
  const drillLoading = ref(false)
  const drillError = ref<string | null>(null)

  const summary = ref<FleetSummary | null>(null)
  const currentlyRented = ref<CurrentlyRentedResponse | null>(null)
  const topMachines = ref<TopMachineItem[]>([])
  const additionalFees = ref<AdditionalFeesResponse | null>(null)
  const locations = ref<LocationStatItem[]>([])
  const positionsData = ref<PositionStatsResponse | null>(null)
  const byCategoryData = ref<CategoryStatsResponse | null>(null)
  const byPeriodData = ref<ByPeriodResponse | null>(null)
  const categoriesList = ref<CategoriesListNode[]>([])

  const locationsRanking = ref<LocationRankingItem[]>([])
  const loadingLocations = ref(false)

  const machineDetails = ref<MachineDetailsResponse | null>(null)
  const locationDetails = ref<LocationDetailsResponse | null>(null)
  const serviceDetails = ref<ServiceDetailsResponse | null>(null)
  const categoryDetails = ref<PositionStatsResponse | null>(null)

  const drillDown = ref<DrillDownState>({ ...emptyDrillDown })

  // ── Getters ────────────────────────────────────────────────────────────────
  const liveUtilPct = computed(() => currentlyRented.value?.utilization_pct ?? 0)

  // ── Actions ────────────────────────────────────────────────────────────────
  async function fetchCurrentlyRented(): Promise<CurrentlyRentedResponse> {
    loadingLive.value = true
    try {
      const { data } = await api.get<CurrentlyRentedResponse>('/stats/currently-rented')
      currentlyRented.value = data
      return data
    } finally {
      loadingLive.value = false
    }
  }

  // RAO-P0-001/BUG-1: fetchSummary przyjmuje pełne filtry (contractorId/city/articleType)
  async function fetchSummary(
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
  ): Promise<FleetSummary> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.internalNumber) params.internal_number = filters.internalNumber
    if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
    if (filters?.city) params.city = filters.city
    if (filters?.articleType && filters.articleType !== 'all') params.article_type = filters.articleType
    const { data } = await api.get<FleetSummary>('/stats/fleet-summary', { params })
    summary.value = data
    return data
  }

  async function fetchTopMachines(
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
    limit = 10,
  ): Promise<TopMachineItem[]> {
    const params: Record<string, string | number> = { limit }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.contractorId) params.contractor_id = filters.contractorId
    if (filters?.city) params.city = filters.city
    if (filters?.internalNumber) params.internal_number = filters.internalNumber
    const { data } = await api.get<TopMachineItem[]>('/stats/top-machines', { params })
    topMachines.value = data
    return data
  }

  // RAO-P1-BUG-5: fetchAdditionalFees przyjmuje pełne filtry (city dodane)
  async function fetchAdditionalFees(
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
  ): Promise<AdditionalFeesResponse> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
    if (filters?.city) params.city = filters.city
    const { data } = await api.get<AdditionalFeesResponse>('/stats/additional-fees', { params })
    additionalFees.value = data
    return data
  }

  // RAO-P1-BUG-5: fetchLocations wysyła city (nie tylko contractorId/internalNumber)
  async function fetchLocations(
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
  ): Promise<LocationStatItem[]> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
    if (filters?.city) params.city = filters.city
    if (filters?.internalNumber) params.internal_number = filters.internalNumber
    const { data } = await api.get<LocationStatItem[]>('/stats/locations', { params })
    locations.value = data
    return data
  }

  async function fetchPositions(
    type: 'all' | 'machines' | 'services',
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
    sortBy?: string,
    sortDir: 'asc' | 'desc' = 'desc',
    contractType?: 'S' | 'U',
  ): Promise<PositionStatsResponse> {
    const params: Record<string, string> = { type }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
    if (filters?.city) params.city = filters.city
    if (contractType) params.contract_type = contractType
    if (sortBy) {
      params.sort_by = sortBy
      params.sort_dir = sortDir
    }
    const { data } = await api.get<PositionStatsResponse>('/stats/positions', { params })
    positionsData.value = data
    return data
  }

  // RAO-P1-BUG-3: fetchByCategory przyjmuje contractorId/city (nie tylko articleType)
  async function fetchByCategory(
    level: string,
    dateFrom: string,
    dateTo: string,
    categoryMain: string[] = [],
    articleType: 'all' | 'machine' | 'service' = 'all',
    filters?: AnalyticsFiltersPayload,
  ): Promise<CategoryStatsResponse> {
    const sp = new URLSearchParams()
    sp.set('level', level)
    if (dateFrom) sp.set('date_from', dateFrom)
    if (dateTo) sp.set('date_to', dateTo)
    if (articleType !== 'all') sp.set('article_type', articleType)
    if (filters?.contractorId) sp.set('contractor_id', String(filters.contractorId))
    if (filters?.city) sp.set('city', filters.city)
    categoryMain.forEach((m) => sp.append('category_main', m))
    const { data } = await api.get<CategoryStatsResponse>('/stats/by-category?' + sp.toString())
    byCategoryData.value = data
    return data
  }

  async function fetchByPeriod(
    granularity: 'month' | 'year',
    dateFrom: string,
    dateTo: string,
    categoryMain: string[] = [],
    articleType: 'all' | 'machine' | 'service' = 'all',
  ): Promise<ByPeriodResponse> {
    const sp = new URLSearchParams()
    sp.set('granularity', granularity)
    if (dateFrom) sp.set('date_from', dateFrom)
    if (dateTo) sp.set('date_to', dateTo)
    if (articleType !== 'all') sp.set('article_type', articleType)
    categoryMain.forEach((m) => sp.append('category_main', m))
    const { data } = await api.get<ByPeriodResponse>('/stats/by-period?' + sp.toString())
    byPeriodData.value = data
    return data
  }

  async function fetchCategoriesList(): Promise<CategoriesListNode[]> {
    const { data } = await api.get<CategoriesListNode[]>('/stats/categories-list')
    categoriesList.value = data
    return data
  }

  // RAO-P2-065 4b / RAO-P2-069: ranking miast (toggle miasto/PNA)
  // RAO-P0-001/BUG-4: fetchLocationsRanking przyjmuje pełne filtry
  async function fetchLocationsRanking(
    dateFrom: string,
    dateTo: string,
    limit = 50,
    groupBy: 'city' | 'pna' = 'city',
    filters?: AnalyticsFiltersPayload,
  ): Promise<LocationRankingItem[]> {
    loadingLocations.value = true
    try {
      const params: Record<string, string | number> = { limit, group_by: groupBy }
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
      if (filters?.city) params.city = filters.city
      if (filters?.articleType && filters.articleType !== 'all') params.article_type = filters.articleType
      const { data } = await api.get<LocationsRankingResponse>('/explorer/locations', { params })
      locationsRanking.value = data.locations || []
      return locationsRanking.value
    } finally {
      loadingLocations.value = false
    }
  }

  // RAO Faza 4b: parametr articleId → machineId (endpoint /explorer/machines/{machine_id})
  async function fetchMachineDetails(
    machineId: number,
    dateFrom: string,
    dateTo: string,
  ): Promise<MachineDetailsResponse> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<MachineDetailsResponse>(
      `/explorer/machines/${machineId}`,
      { params },
    )
    machineDetails.value = data
    return data
  }

  async function fetchLocationDetails(
    postalCode: string,
    dateFrom: string,
    dateTo: string,
  ): Promise<LocationDetailsResponse | { error: string }> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<LocationDetailsResponse | { error: string }>(
      `/explorer/locations/${encodeURIComponent(postalCode)}`,
      { params },
    )
    if (data && 'error' in data) {
      locationDetails.value = null
    } else {
      locationDetails.value = data as LocationDetailsResponse
    }
    return data
  }

  // RAO-P2-069: drill-down po mieście (sumuje wszystkie PNA w mieście)
  async function fetchCityDetails(
    city: string,
    dateFrom: string,
    dateTo: string,
  ): Promise<LocationDetailsResponse | { error: string }> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<LocationDetailsResponse | { error: string }>(
      `/explorer/locations/city/${encodeURIComponent(city)}`,
      { params },
    )
    if (data && 'error' in data) {
      locationDetails.value = null
    } else {
      locationDetails.value = data as LocationDetailsResponse
    }
    return data
  }

  // RAO-P1-014: drilldown usługi — /explorer/services/{article_id}
  async function fetchServiceDetails(
    articleId: number,
    dateFrom: string,
    dateTo: string,
  ): Promise<ServiceDetailsResponse> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<ServiceDetailsResponse>(
      `/explorer/services/${articleId}`,
      { params },
    )
    serviceDetails.value = data
    return data
  }

  // RAO-P1-014: drilldown kategorii — /stats/positions?type=machines&category_main=...
  async function fetchCategoryDetails(
    categoryName: string,
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
  ): Promise<PositionStatsResponse> {
    const params: Record<string, string> = { type: 'machines' }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
    if (filters?.city) params.city = filters.city
    // category_main jako multi-value parametr
    const sp = new URLSearchParams(params)
    sp.append('category_main', categoryName)
    const { data } = await api.get<PositionStatsResponse>(
      '/stats/positions?' + sp.toString(),
    )
    categoryDetails.value = data
    return data
  }

  // ── Drill-down orchestration ───────────────────────────────────────────────
  async function openDrillDown(
    kind: DrillDownKind,
    id: number | string,
    name: string,
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
  ): Promise<void> {
    // RAO-P2-069: 'location' z id numerycznym/city → miasto; PNA string → PNA
    // Konwencja: jeśli id zaczyna się od "city:" → drill po mieście
    const isCityDrill = typeof id === 'string' && id.startsWith('city:')
    const drillKind: DrillDownKind = isCityDrill ? 'location' : kind

    const titleByKind: Record<DrillDownKind, string> = {
      machine: `🏗️ ${name}`,
      location: `📍 ${name}`,
      service: `🔧 ${name}`,
      category: `🏷️ ${name}`,
    }
    const subtitleByKind: Record<DrillDownKind, string> = {
      machine: 'Historia wynajmów maszyny',
      location: isCityDrill ? 'Umowy w mieście (wszystkie PNA)' : 'Umowy w lokalizacji (PNA)',
      service: 'Umowy z tą usługą',
      category: 'Maszyny w tej kategorii',
    }

    drillDown.value = {
      open: true,
      kind: drillKind,
      id,
      name,
      title: titleByKind[kind],
      subtitle: subtitleByKind[kind],
    }
    drillLoading.value = true
    drillError.value = null
    machineDetails.value = null
    locationDetails.value = null
    serviceDetails.value = null
    categoryDetails.value = null
    try {
      if (kind === 'machine') {
        // ROI panel usunięte — tylko details
        await fetchMachineDetails(Number(id), dateFrom, dateTo)
      } else if (kind === 'service') {
        await fetchServiceDetails(Number(id), dateFrom, dateTo)
      } else if (kind === 'category') {
        await fetchCategoryDetails(String(id), dateFrom, dateTo, filters)
      } else if (isCityDrill) {
        await fetchCityDetails(String(id).slice(5), dateFrom, dateTo)
      } else {
        await fetchLocationDetails(String(id), dateFrom, dateTo)
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      drillError.value = err?.response?.data?.detail ?? err?.message ?? 'Nieznany błąd'
    } finally {
      drillLoading.value = false
    }
  }

  function closeDrillDown(): void {
    drillDown.value = { ...emptyDrillDown }
    drillError.value = null
    machineDetails.value = null
    locationDetails.value = null
    serviceDetails.value = null
    categoryDetails.value = null
  }

  return {
    // state
    loading,
    loadingLive,
    drillLoading,
    drillError,
    summary,
    currentlyRented,
    topMachines,
    additionalFees,
    locations,
    positionsData,
    byCategoryData,
    byPeriodData,
    categoriesList,
    locationsRanking,
    loadingLocations,
    machineDetails,
    locationDetails,
    serviceDetails,
    categoryDetails,
    drillDown,
    // getters
    liveUtilPct,
    // actions
    fetchCurrentlyRented,
    fetchSummary,
    fetchTopMachines,
    fetchAdditionalFees,
    fetchLocations,
    fetchPositions,
    fetchByCategory,
    fetchByPeriod,
    fetchCategoriesList,
    fetchLocationsRanking,
    fetchMachineDetails,
    fetchLocationDetails,
    fetchCityDetails,
    fetchServiceDetails,
    fetchCategoryDetails,
    openDrillDown,
    closeDrillDown,
  }
})
