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
  revenue_actual: string | number | null
  revenue_estimate: string | number | null
  revenue_source_label: string | null
}

export interface TopMachineItem {
  article_id: number
  name: string
  internal_number: string | null
  revenue: string | number
  rented_days: number
  contracts_count: number
}

export interface CurrentlyRentedItem {
  article_id: number
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
  article_id: number
  service_name: string
  total_revenue: string | number
  times_billed: number
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
  article_id: number
  article_name: string
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

export interface ExplorerResultItem {
  type: string
  type_label: string
  id: number
  article_id: number
  name: string
  internal_number: string | null
  contract_number: string
  contractor_name: string | null
  date: string | null
  city: string | null
  amount: number
}

export interface ExplorerSearchResponse {
  items: ExplorerResultItem[]
  total: number
  summary: { count: number; revenue: number }
  offset: number
  limit: number
}

export interface MachineRentalRow {
  contract_id: number
  contract_number: string
  date_from: string | null
  date_to: string | null
  days: number
  contractor_name: string | null
  revenue: number
  revenue_source: string | null
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

// RAO-P2-065 #1: ROI maszyny — mirror backend MachineRoiResponse
export interface MachineRoi {
  article_id: number
  name: string
  internal_number: string | null
  category_main: string | null
  replacement_value: number | null
  total_rented_days: number
  estimated_revenue: number
  contracts_count: number
  roi_pct: number | null
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
export type DrillDownKind = 'machine' | 'location'

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
  const loadingExplorer = ref(false)
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

  const explorerResults = ref<ExplorerResultItem[]>([])
  const explorerSummary = ref<{ count: number; revenue: number }>({ count: 0, revenue: 0 })

  const locationsRanking = ref<LocationRankingItem[]>([])
  const loadingLocations = ref(false)

  const machineDetails = ref<MachineDetailsResponse | null>(null)
  const machineRoi = ref<MachineRoi | null>(null)
  const locationDetails = ref<LocationDetailsResponse | null>(null)

  const drillDown = ref<DrillDownState>({ ...emptyDrillDown })

  // ── Getters ────────────────────────────────────────────────────────────────
  const liveUtilPct = computed(() => currentlyRented.value?.utilization_pct ?? 0)

  const revenueSourceClass = computed(() => {
    const label = summary.value?.revenue_source_label
    if (label === 'rzeczywiste') return 'source-actual'
    if (label === 'szacunek') return 'source-estimate'
    if (label === 'mieszane') return 'source-mixed'
    return 'source-empty'
  })

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

  async function fetchSummary(
    dateFrom: string,
    dateTo: string,
    internalNumber?: string,
  ): Promise<FleetSummary> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (internalNumber) params.internal_number = internalNumber
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

  async function fetchAdditionalFees(
    dateFrom: string,
    dateTo: string,
    contractorId?: number | null,
  ): Promise<AdditionalFeesResponse> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (contractorId) params.contractor_id = String(contractorId)
    const { data } = await api.get<AdditionalFeesResponse>('/stats/additional-fees', { params })
    additionalFees.value = data
    return data
  }

  async function fetchLocations(
    dateFrom: string,
    dateTo: string,
    filters?: AnalyticsFiltersPayload,
  ): Promise<LocationStatItem[]> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
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
  ): Promise<PositionStatsResponse> {
    const params: Record<string, string> = { type }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters?.contractorId) params.contractor_id = String(filters.contractorId)
    if (filters?.city) params.city = filters.city
    if (sortBy) {
      params.sort_by = sortBy
      params.sort_dir = sortDir
    }
    const { data } = await api.get<PositionStatsResponse>('/stats/positions', { params })
    positionsData.value = data
    return data
  }

  async function fetchByCategory(
    level: string,
    dateFrom: string,
    dateTo: string,
    categoryMain: string[] = [],
    articleType: 'all' | 'machine' | 'service' = 'all',
  ): Promise<CategoryStatsResponse> {
    const sp = new URLSearchParams()
    sp.set('level', level)
    if (dateFrom) sp.set('date_from', dateFrom)
    if (dateTo) sp.set('date_to', dateTo)
    if (articleType !== 'all') sp.set('article_type', articleType)
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

  async function searchExplorer(
    q: string,
    dateFrom: string,
    dateTo: string,
    limit = 50,
  ): Promise<ExplorerSearchResponse> {
    loadingExplorer.value = true
    try {
      const params: Record<string, string | number> = { q, limit }
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      const { data } = await api.get<ExplorerSearchResponse>('/explorer/search', { params })
      explorerResults.value = data.items || []
      explorerSummary.value = data.summary || { count: 0, revenue: 0 }
      return data
    } finally {
      loadingExplorer.value = false
    }
  }

  // RAO-P2-065 4b / RAO-P2-069: ranking miast (toggle miasto/PNA)
  async function fetchLocationsRanking(
    dateFrom: string,
    dateTo: string,
    limit = 50,
    groupBy: 'city' | 'pna' = 'city',
  ): Promise<LocationRankingItem[]> {
    loadingLocations.value = true
    try {
      const params: Record<string, string | number> = { limit, group_by: groupBy }
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      const { data } = await api.get<LocationsRankingResponse>('/explorer/locations', { params })
      locationsRanking.value = data.locations || []
      return locationsRanking.value
    } finally {
      loadingLocations.value = false
    }
  }

  async function fetchMachineDetails(
    articleId: number,
    dateFrom: string,
    dateTo: string,
  ): Promise<MachineDetailsResponse> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<MachineDetailsResponse>(
      `/explorer/machines/${articleId}`,
      { params },
    )
    machineDetails.value = data
    return data
  }

  // RAO-P2-065 #1: ROI maszyny — główne wymaganie klienta, podpięte do drill-down
  async function fetchMachineRoi(
    articleId: number,
    dateFrom: string,
    dateTo: string,
  ): Promise<MachineRoi> {
    const params: Record<string, string> = { article_id: String(articleId) }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<MachineRoi>('/stats/machine-roi', { params })
    machineRoi.value = data
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

  // ── Drill-down orchestration ───────────────────────────────────────────────
  async function openDrillDown(
    kind: DrillDownKind,
    id: number | string,
    name: string,
    dateFrom: string,
    dateTo: string,
    internalNumber?: string | null,
  ): Promise<void> {
    // RAO-P2-069: 'location' z id numerycznym/city → miasto; PNA string → PNA
    // Konwencja: jeśli id zaczyna się od "city:" → drill po mieście
    const isCityDrill = typeof id === 'string' && id.startsWith('city:')
    const drillKind: DrillDownKind = isCityDrill ? 'location' : kind

    // RAO-P2-065 #7: dodaj nr wewnętrzny do tytułu/subtitle maszyny
    const machineTitle = internalNumber
      ? `🏗️ ${name} (${internalNumber})`
      : `🏗️ ${name}`

    drillDown.value = {
      open: true,
      kind: drillKind,
      id,
      name,
      title: kind === 'machine' ? machineTitle : `📍 ${name}`,
      subtitle:
        kind === 'machine'
          ? 'Historia wynajmów maszyny'
          : isCityDrill
            ? 'Umowy w mieście (wszystkie PNA)'
            : 'Umowy w lokalizacji (PNA)',
    }
    drillLoading.value = true
    drillError.value = null
    machineDetails.value = null
    machineRoi.value = null
    locationDetails.value = null
    try {
      if (kind === 'machine') {
        // RAO-P2-065 #1: równolegle details + ROI (niezależne endpointy)
        await Promise.all([
          fetchMachineDetails(Number(id), dateFrom, dateTo),
          fetchMachineRoi(Number(id), dateFrom, dateTo).catch((e: unknown) => {
            // ROI best-effort: 404 dla archiwalnych bez include_archival — nie blokuj details
            const err = e as { response?: { status?: number } }
            if (err?.response?.status !== 404) throw e
            return null
          }),
        ])
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
    machineRoi.value = null
    locationDetails.value = null
  }

  return {
    // state
    loading,
    loadingLive,
    loadingExplorer,
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
    explorerResults,
    explorerSummary,
    locationsRanking,
    loadingLocations,
    machineDetails,
    machineRoi,
    locationDetails,
    drillDown,
    // getters
    liveUtilPct,
    revenueSourceClass,
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
    searchExplorer,
    fetchLocationsRanking,
    fetchMachineDetails,
    fetchMachineRoi,
    fetchLocationDetails,
    fetchCityDetails,
    openDrillDown,
    closeDrillDown,
  }
})
