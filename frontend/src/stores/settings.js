import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useSettingsStore = defineStore('settings', () => {
  const company = ref(null)
  const salespeople = ref([])
  const categories = ref([])
  const branches = ref([])
  const rateTypes = ref([])
  const feeTemplates = ref([])
  const loading = ref(false)

  async function fetchCompany() {
    const { data } = await api.get('/settings/company')
    company.value = data
    return data
  }

  async function updateCompany(payload) {
    const { data } = await api.put('/settings/company', payload)
    company.value = data
    return data
  }

  async function fetchSalespeople() {
    const { data } = await api.get('/settings/salespeople')
    salespeople.value = data
    return data
  }

  async function fetchCategories() {
    const { data } = await api.get('/settings/categories')
    categories.value = data
    return data
  }

  async function updateCategory(id, payload) {
    const { data } = await api.put(`/settings/categories/${id}`, payload)
    await fetchCategories()
    return data
  }

  async function deleteCategory(id) {
    await api.delete(`/settings/categories/${id}`)
    await fetchCategories()
  }

  async function fetchBranches() {
    const { data } = await api.get('/settings/branches')
    branches.value = data
    return data
  }

  async function fetchRateTypes() {
    const { data } = await api.get('/settings/rate-types')
    rateTypes.value = data
    return data
  }

  async function updateRateType(id, payload) {
    const { data } = await api.put(`/settings/rate-types/${id}`, payload)
    await fetchRateTypes()
    return data
  }

  async function deleteRateType(id) {
    await api.delete(`/settings/rate-types/${id}`)
    await fetchRateTypes()
  }

  async function updateSalesperson(id, payload) {
    const { data } = await api.put(`/settings/salespeople/${id}`, payload)
    await fetchSalespeople()
    return data
  }

  async function fetchFeeTemplates() {
    const { data } = await api.get('/settings/service-fee-templates')
    feeTemplates.value = data
    return data
  }

  async function seedFeeTemplates(force = false) {
    const { data } = await api.post(`/settings/service-fee-templates/seed?force=${force}`)
    await fetchFeeTemplates()
    return data
  }

  async function fetchAll() {
    loading.value = true
    try {
      await Promise.all([
        fetchSalespeople(),
        fetchCategories(),
        fetchBranches(),
        fetchRateTypes(),
        fetchFeeTemplates(),
      ])
    } finally {
      loading.value = false
    }
  }

  return {
    company, salespeople, categories, branches, rateTypes, feeTemplates, loading,
    fetchCompany, updateCompany,
    fetchSalespeople, updateSalesperson,
    fetchCategories, updateCategory, deleteCategory,
    fetchBranches,
    fetchRateTypes, updateRateType, deleteRateType,
    fetchFeeTemplates, seedFeeTemplates, fetchAll,
  }
})
