import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'
import { useFileDownload } from '@/composables/useFileDownload'
import { useToastStore } from '@/stores/toast'

export const useContractStore = defineStore('contracts', () => {
  const list = ref([])
  const total = ref(0)
  const current = ref(null)
  const positions = ref([])
  const serviceFees = ref([])
  const loading = ref(false)

  const { saveToFolder } = useFileDownload()
  const toastStore = useToastStore()

  const overdueList = ref([])
  const overdueTotal = ref(0)
  const overdueLoading = ref(false)

  async function fetchOverdueList(params = {}) {
    overdueLoading.value = true
    try {
      const { data } = await api.get('/contracts/overdue', { params })
      overdueList.value = data.items
      overdueTotal.value = data.total
    } finally {
      overdueLoading.value = false
    }
  }

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

  // RAO-P1-001: Apply predefiniowany cennik do pozycji (snapshot)
  async function applyRatePreset(contractId, posId, presetId, replace = true) {
    const { data } = await api.post(
      `/contracts/${contractId}/positions/${posId}/conditions/apply-preset`,
      { preset_id: presetId, replace }
    )
    return data
  }

  // RAO-P1-001: Auto-prefill — warunki z ostatniej umowy tej maszyny
  // Zwraca { source_contract_number, source_contract_date, source_position_id, conditions[] }
  // Rzuca błąd 404 gdy brak historii (axios throw)
  // RAO Faza 4b: endpoint zmieniony /articles/{id}/last-conditions → /machines/{id}/last-conditions
  async function fetchLastConditionsForMachine(machineId) {
    const { data } = await api.get(`/machines/${machineId}/last-conditions`)
    return data
  }
  // Backward-compat alias — ConditionPanel.vue nadal używa starej nazwy
  const fetchLastConditionsForArticle = fetchLastConditionsForMachine

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
    // Mapowanie typu raportu na podfolder
    const docType = type === 'contract' ? 'umowy' : type.startsWith('protocol_zo') ? 'protokoly' : 'zestawienia'
    // Parsowanie nazwy pliku z Content-Disposition (RFC 5987)
    let filename = 'Umowa.pdf'
    const rfc5987 = cd.match(/filename\*=UTF-8''([^;]+)/i)
    if (rfc5987) {
      try { filename = decodeURIComponent(rfc5987[1]) } catch { }
    } else {
      const classic = cd.match(/filename="?([^";\n]+)"?/i)
      if (classic) filename = classic[1].trim()
    }
    // RAO-TECH-003: branchId z current contract dla mapowania folderów per-oddział
    const branchId = current.value?.branch_id ?? null
    const saved = await saveToFolder(response.data, cd, filename, docType, branchId)
    if (saved) {
      toastStore.showToast(`${filename} zapisany do folderu PDF`, 'success')
    }
    // RAO: odśwież stan umowy w store — print_date + is_print_current po wydruku
    if (current.value && current.value.id === contractId) {
      current.value = { ...current.value, print_date: new Date().toISOString(), is_print_current: true }
    }
    // RAO: odśwież wpis na liście — print_date + is_print_current
    const idx = list.value.findIndex(c => c.id === contractId)
    if (idx >= 0) {
      list.value[idx] = { ...list.value[idx], print_date: new Date().toISOString(), is_print_current: true }
    }
  }

  return {
    list, total, current, positions, serviceFees, loading,
    overdueList, overdueTotal, overdueLoading, fetchOverdueList,
    fetchList, fetchOne, create, update, remove,
    fetchPositions, createPosition, updatePosition, deletePosition,
    fetchConditions, createCondition, updateCondition, deleteCondition,
    applyRatePreset, fetchLastConditionsForMachine, fetchLastConditionsForArticle,
    fetchServiceFees, generateReport,
  }
})
