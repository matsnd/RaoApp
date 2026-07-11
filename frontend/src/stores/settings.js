import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useSettingsStore = defineStore('settings', () => {
  const company = ref(null)
  const salespeople = ref([])
  const categories = ref([])
  const categoriesTree = ref([])
  const branches = ref([])
  const rateTypes = ref([])
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

  // RAO-P3-002: upload logo firmy
  async function uploadLogo(file) {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/settings/company/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (company.value) {
      company.value = { ...company.value, logo_url: data.logo_url }
    }
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

  async function fetchCategoriesTree() {
    const { data } = await api.get('/settings/categories/tree')
    categoriesTree.value = data
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

  // --- RAO-P1-001: Cenniki warunków rozliczenia maszyn (MachineRatePreset) ---
  // RAO Faza 4b: endpoint zmieniony /settings/articles/{id}/rate-presets → /settings/machines/{id}/rate-presets
  const ratePresets = ref([])        // lista presetów dla aktualnie edytowanej maszyny
  const ratePresetsLoading = ref(false)

  async function fetchRatePresets(machineId) {
    ratePresetsLoading.value = true
    try {
      const { data } = await api.get(`/settings/machines/${machineId}/rate-presets`)
      ratePresets.value = data
      return data
    } finally {
      ratePresetsLoading.value = false
    }
  }

  async function fetchDefaultRatePreset(machineId) {
    // 200 z body=null gdy brak domyślnego
    const { data } = await api.get(`/settings/machines/${machineId}/rate-presets/default`)
    return data
  }

  async function createRatePreset(machineId, payload) {
    const { data } = await api.post(`/settings/machines/${machineId}/rate-presets`, payload)
    await fetchRatePresets(machineId)
    return data
  }

  async function updateRatePreset(presetId, payload) {
    const { data } = await api.put(`/settings/rate-presets/${presetId}`, payload)
    // Odśwież listę jeśli machine_id znany (z payload lub z aktualnej listy)
    const mId = data.machine_id ?? ratePresets.value[0]?.machine_id
    if (mId) await fetchRatePresets(mId)
    return data
  }

  async function deleteRatePreset(presetId) {
    await api.delete(`/settings/rate-presets/${presetId}`)
    const mId = ratePresets.value[0]?.machine_id
    if (mId) await fetchRatePresets(mId)
  }

  async function setDefaultRatePreset(presetId) {
    const { data } = await api.patch(`/settings/rate-presets/${presetId}/set-default`)
    const mId = data.machine_id ?? ratePresets.value[0]?.machine_id
    if (mId) await fetchRatePresets(mId)
    return data
  }

  async function addRatePresetItem(presetId, payload) {
    const { data } = await api.post(`/settings/rate-presets/${presetId}/items`, payload)
    const mId = ratePresets.value[0]?.machine_id
    if (mId) await fetchRatePresets(mId)
    return data
  }

  async function updateRatePresetItem(itemId, payload) {
    const { data } = await api.put(`/settings/rate-presets/items/${itemId}`, payload)
    const mId = ratePresets.value[0]?.machine_id
    if (mId) await fetchRatePresets(mId)
    return data
  }

  async function deleteRatePresetItem(itemId) {
    await api.delete(`/settings/rate-presets/items/${itemId}`)
    const mId = ratePresets.value[0]?.machine_id
    if (mId) await fetchRatePresets(mId)
  }

  async function fetchAll() {
    loading.value = true
    try {
      await Promise.all([
        fetchSalespeople(),
        fetchCategories(),
        fetchBranches(),
        fetchRateTypes(),
      ])
    } finally {
      loading.value = false
    }
  }

  return {
    company, salespeople, categories, categoriesTree, branches, rateTypes, loading,
    // RAO-P1-001: cenniki rozliczenia maszyn (MachineRatePreset)
    ratePresets, ratePresetsLoading,
    fetchCompany, updateCompany, uploadLogo,
    fetchSalespeople, updateSalesperson,
    fetchCategories, fetchCategoriesTree, updateCategory, deleteCategory,
    fetchBranches,
    fetchRateTypes, updateRateType, deleteRateType,
    fetchAll,
    // RAO-P1-001: cenniki rozliczenia maszyn (MachineRatePreset)
    fetchRatePresets, fetchDefaultRatePreset,
    createRatePreset, updateRatePreset, deleteRatePreset,
    setDefaultRatePreset,
    addRatePresetItem, updateRatePresetItem, deleteRatePresetItem,
  }
})
