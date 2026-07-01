/**
 * RAO-P2-062 Faza 2 — Pinia store dla archiwum.
 *
 * Mirror endpointów /rao/api/archive/* (Faza 1 — backend commit db5c2cc).
 * Read-only dla umów; PATCH category_id na artykułach (admin); CRUD kategorii (admin).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

// ── Typy (mirror backend/archive/schemas.py) ────────────────────────────────
export interface ArchiveContractListItem {
  id: number
  contractor_id: number
  contractor_name: string | null
  number: string
  contract_type: string
  type_label: string
  delivery_address: string | null
  postal_code: string | null
  city: string | null
  date_from: string | null
  date_to: string | null
  prepayment_amount: string | null
  invoice_amount: string | null
  notes: string | null
  email: string | null
  contact_person1: string | null
  contact_phone1: string | null
  phone: string | null
  is_settled: boolean
  settled_at: string | null
  position_count: number | null
  duration_days: number | null
  revenue_estimate: string
  created_at: string
}

export interface ArchiveCondition {
  id: number
  position_id: number
  rate_type_id: number | null
  rate_type_name: string | null
  description: string | null
  rate1: string | null
  rate2: string | null
  billing_label: string | null
  period_count: number | null
  minimum: number | null
}

export interface ArchivePosition {
  id: number
  contract_id: number
  article_id: number
  article_name: string | null
  rental_type: string | null
  description: string | null
  rental_days: number | null
  quantity: number | null
  unit_price: string | null
  costs: string | null
  rate_type_id: number | null
  rate_type_name: string | null
  billing_frequency: string | null
  billing_unit: string | null
  supplier_id: number | null
  delivery_date: string | null
  conditions: ArchiveCondition[]
}

export interface ArchiveServiceFee {
  id: number
  contract_id: number
  sort_order: number
  name: string
  amount_from: string | null
  amount_to: string | null
  unit: string | null
  description: string | null
  is_active: boolean
  article_id: number | null
  default_price: string | null
}

export interface ArchiveSettlement {
  id: number
  contract_id: number
  position_id: number | null
  service_fee_id: number | null
  cost_client: string | null
  cost_company: string | null
  notes: string | null
  settled_at: string | null
  source: string | null
  created_at: string
  updated_at: string | null
}

export interface ArchiveContractDetail extends ArchiveContractListItem {
  branch_id: number | null
  salesperson_id: number | null
  auto_number: number | null
  latitude: string | null
  longitude: string | null
  prepayment_document: string | null
  invoice_document: string | null
  contact_person2: string | null
  contact_phone2: string | null
  show_person1: boolean
  show_person2: boolean
  print_date: string | null
  updated_at: string | null
  positions: ArchivePosition[]
  service_fees: ArchiveServiceFee[]
  settlements: ArchiveSettlement[]
}

export interface ArchiveArticle {
  id: number
  name: string
  is_service: boolean
  internal_number: string | null
  registration_no: string | null
  serial_no: string | null
  brand: string | null
  model: string | null
  replacement_value: string | null
  category_id: number | null
  owner_id: number | null
  branch_id: number | null
  description: string | null
  notes: string | null
  rental_days: number | null
  article_type: string | null
  category_main: string | null
  category_sub1: string | null
  category_sub2: string | null
  category_sub3: string | null
  is_archival: boolean
  is_external: boolean
  zasieg_m: string | null
  udzwig_t: string | null
  dodatki: string | null
  created_at: string
  updated_at: string | null
  contracts_count?: number
}

export interface ArchiveCategory {
  id: number
  name: string
  code: string | null
  description: string | null
  parent_id: number | null
  level: string
}

export interface ArchiveCategoryTreeNode extends ArchiveCategory {
  children: ArchiveCategoryTreeNode[]
}

export interface ArchiveStatsSummary {
  date_from: string | null
  date_to: string | null
  contracts_count: number
  positions_count: number
  revenue_estimate: string
}

export interface ArchiveTopMachineItem {
  article_id: number
  article_name: string
  internal_number: string | null
  contracts_count: number
  rented_days: number
  revenue_estimate: string
}

export interface ArchiveCategoryStatItem {
  category_id: number | null
  category_name: string
  contracts_count: number
  positions_count: number
  revenue_estimate: string
}

export interface ArchiveMachineRoi {
  article_id: number
  name: string
  internal_number: string | null
  replacement_value: string | null
  revenue_estimate: string
  contracts_count: number
  rented_days: number
  roi_pct: number | null
}

export interface ArchiveCityStatItem {
  city: string
  contracts_count: number
  positions_count: number
  revenue_estimate: string
  postal_codes_count: number
}

interface Paginated<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

export interface ArchiveContractFilters {
  search?: string
  contractor_id?: number | null
  date_from?: string | null
  date_to?: string | null
  contract_type?: 'S' | 'U' | null
  city?: string | null
  article_id?: number | null
  page?: number
  per_page?: number
}

export interface ArchiveArticleFilters {
  search?: string
  category_id?: number | null
  page?: number
  per_page?: number
}

export interface ArchiveCategoryPayload {
  name: string
  code?: string | null
  description?: string | null
  parent_id?: number | null
  level: 'main' | 'sub1' | 'sub2' | 'sub3'
}

// ── Store ────────────────────────────────────────────────────────────────────
export const useArchiveStore = defineStore('archive', () => {
  // Umowy
  const contracts = ref<ArchiveContractListItem[]>([])
  const contractsTotal = ref(0)
  const contractsPage = ref(1)
  const contractsPerPage = ref(50)
  const contractsLoading = ref(false)
  const contractsError = ref<string | null>(null)
  const currentContract = ref<ArchiveContractDetail | null>(null)
  const currentContractLoading = ref(false)

  // Artykuły
  const articles = ref<ArchiveArticle[]>([])
  const articlesTotal = ref(0)
  const articlesPage = ref(1)
  const articlesPerPage = ref(50)
  const articlesLoading = ref(false)
  const articlesError = ref<string | null>(null)

  // Kategorie
  const categories = ref<ArchiveCategory[]>([])
  const categoriesTree = ref<ArchiveCategoryTreeNode[]>([])
  const categoriesLoading = ref(false)

  // Stats
  const statsSummary = ref<ArchiveStatsSummary | null>(null)
  const topMachines = ref<ArchiveTopMachineItem[]>([])
  const byCategory = ref<ArchiveCategoryStatItem[]>([])
  const byCity = ref<ArchiveCityStatItem[]>([])
  const machineRoi = ref<ArchiveMachineRoi | null>(null)
  const statsLoading = ref(false)
  const statsError = ref<string | null>(null)

  // Drill-down (lokalny stan, nie globalny)
  const drillDownContracts = ref<ArchiveContractListItem[]>([])
  const drillDownTotal = ref(0)
  const drillDownLoading = ref(false)
  const drillDownError = ref<string | null>(null)

  // Gettery
  const totalContracts = computed(() => contractsTotal.value)
  const totalArticles = computed(() => articlesTotal.value)
  const hasCategories = computed(() => categories.value.length > 0)

  // ── Umowy ──────────────────────────────────────────────────────────────────
  async function fetchContracts(filters: ArchiveContractFilters = {}) {
    contractsLoading.value = true
    contractsError.value = null
    try {
      const params: Record<string, unknown> = {
        page: filters.page ?? contractsPage.value,
        per_page: filters.per_page ?? contractsPerPage.value,
      }
      if (filters.search) params.search = filters.search
      if (filters.contractor_id) params.contractor_id = filters.contractor_id
      if (filters.date_from) params.date_from = filters.date_from
      if (filters.date_to) params.date_to = filters.date_to
      if (filters.contract_type) params.contract_type = filters.contract_type
      if (filters.city) params.city = filters.city
      if (filters.article_id) params.article_id = filters.article_id
      const { data } = await api.get<Paginated<ArchiveContractListItem>>('/archive/contracts', { params })
      contracts.value = data.items
      contractsTotal.value = data.total
      contractsPage.value = data.page
      contractsPerPage.value = data.per_page
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      contractsError.value = err?.response?.data?.detail ?? 'Błąd pobierania umów archiwum'
      throw e
    } finally {
      contractsLoading.value = false
    }
  }

  async function fetchContract(id: number) {
    currentContractLoading.value = true
    try {
      const { data } = await api.get<ArchiveContractDetail>(`/archive/contracts/${id}`)
      currentContract.value = data
      return data
    } finally {
      currentContractLoading.value = false
    }
  }

  // ── Artykuły ───────────────────────────────────────────────────────────────
  async function fetchArticles(filters: ArchiveArticleFilters = {}) {
    articlesLoading.value = true
    articlesError.value = null
    try {
      const params: Record<string, unknown> = {
        page: filters.page ?? articlesPage.value,
        per_page: filters.per_page ?? articlesPerPage.value,
      }
      if (filters.search) params.search = filters.search
      if (filters.category_id) params.category_id = filters.category_id
      const { data } = await api.get<Paginated<ArchiveArticle>>('/archive/articles', { params })
      articles.value = data.items
      articlesTotal.value = data.total
      articlesPage.value = data.page
      articlesPerPage.value = data.per_page
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      articlesError.value = err?.response?.data?.detail ?? 'Błąd pobierania maszyn archiwum'
      throw e
    } finally {
      articlesLoading.value = false
    }
  }

  async function fetchArticle(id: number) {
    const { data } = await api.get<ArchiveArticle>(`/archive/articles/${id}`)
    return data
  }

  async function updateArticleCategory(id: number, categoryId: number | null) {
    const { data } = await api.patch<ArchiveArticle>(`/archive/articles/${id}/category`, {
      category_id: categoryId,
    })
    const idx = articles.value.findIndex((a) => a.id === id)
    if (idx >= 0) articles.value[idx] = data
    return data
  }

  // ── Kategorie ──────────────────────────────────────────────────────────────
  async function fetchCategories() {
    categoriesLoading.value = true
    try {
      const { data } = await api.get<ArchiveCategory[]>('/archive/categories')
      categories.value = data
      return data
    } finally {
      categoriesLoading.value = false
    }
  }

  async function fetchCategoriesTree() {
    categoriesLoading.value = true
    try {
      const { data } = await api.get<ArchiveCategoryTreeNode[]>('/archive/categories/tree')
      categoriesTree.value = data
      return data
    } finally {
      categoriesLoading.value = false
    }
  }

  async function createCategory(payload: ArchiveCategoryPayload) {
    const { data } = await api.post<ArchiveCategory>('/archive/categories', payload)
    await fetchCategoriesTree()
    return data
  }

  async function updateCategory(id: number, payload: ArchiveCategoryPayload) {
    const { data } = await api.put<ArchiveCategory>(`/archive/categories/${id}`, payload)
    await fetchCategoriesTree()
    return data
  }

  async function deleteCategory(id: number) {
    await api.delete(`/archive/categories/${id}`)
    await fetchCategoriesTree()
  }

  // ── Stats ──────────────────────────────────────────────────────────────────
  async function fetchStatsSummary(dateFrom?: string | null, dateTo?: string | null) {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<ArchiveStatsSummary>('/archive/stats/summary', { params })
    statsSummary.value = data
    return data
  }

  async function fetchTopMachines(dateFrom?: string | null, dateTo?: string | null, limit = 10) {
    const params: Record<string, unknown> = { limit }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<ArchiveTopMachineItem[]>('/archive/stats/top-machines', { params })
    topMachines.value = data
    return data
  }

  async function fetchStatsByCategory(dateFrom?: string | null, dateTo?: string | null) {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<ArchiveCategoryStatItem[]>('/archive/stats/by-category', { params })
    byCategory.value = data
    return data
  }

  async function fetchMachineRoi(articleId: number, dateFrom?: string | null, dateTo?: string | null) {
    const params: Record<string, unknown> = { article_id: articleId }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<ArchiveMachineRoi>('/archive/stats/machine-roi', { params })
    machineRoi.value = data
    return data
  }

  async function fetchByCity(dateFrom?: string | null, dateTo?: string | null, limit = 20) {
    const params: Record<string, unknown> = { limit }
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const { data } = await api.get<ArchiveCityStatItem[]>('/archive/stats/by-city', { params })
    byCity.value = data
    return data
  }

  async function fetchContractsForDrillDown(filters: ArchiveContractFilters = {}) {
    drillDownLoading.value = true
    drillDownError.value = null
    try {
      const params: Record<string, unknown> = {
        page: filters.page ?? 1,
        per_page: filters.per_page ?? 50,
      }
      if (filters.search) params.search = filters.search
      if (filters.date_from) params.date_from = filters.date_from
      if (filters.date_to) params.date_to = filters.date_to
      if (filters.city) params.city = filters.city
      if (filters.article_id) params.article_id = filters.article_id
      const { data } = await api.get<Paginated<ArchiveContractListItem>>('/archive/contracts', { params })
      drillDownContracts.value = data.items
      drillDownTotal.value = data.total
      return data
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      drillDownError.value = err?.response?.data?.detail ?? 'Błąd pobierania umów'
      throw e
    } finally {
      drillDownLoading.value = false
    }
  }

  async function fetchAllStats(dateFrom?: string | null, dateTo?: string | null) {
    statsLoading.value = true
    statsError.value = null
    try {
      await Promise.all([
        fetchStatsSummary(dateFrom, dateTo),
        fetchTopMachines(dateFrom, dateTo),
        fetchStatsByCategory(dateFrom, dateTo),
        fetchByCity(dateFrom, dateTo),
      ])
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      statsError.value = err?.response?.data?.detail ?? 'Błąd pobierania statystyk archiwum'
      throw e
    } finally {
      statsLoading.value = false
    }
  }

  return {
    // state
    contracts, contractsTotal, contractsPage, contractsPerPage,
    contractsLoading, contractsError, currentContract, currentContractLoading,
    articles, articlesTotal, articlesPage, articlesPerPage,
    articlesLoading, articlesError,
    categories, categoriesTree, categoriesLoading,
    statsSummary, topMachines, byCategory, byCity, machineRoi,
    statsLoading, statsError,
    drillDownContracts, drillDownTotal, drillDownLoading, drillDownError,
    // getters
    totalContracts, totalArticles, hasCategories,
    // actions
    fetchContracts, fetchContract,
    fetchArticles, fetchArticle, updateArticleCategory,
    fetchCategories, fetchCategoriesTree,
    createCategory, updateCategory, deleteCategory,
    fetchStatsSummary, fetchTopMachines, fetchStatsByCategory, fetchMachineRoi,
    fetchByCity, fetchContractsForDrillDown,
    fetchAllStats,
  }
})
