import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

interface FakturowniaSettings {
  id: number
  enabled: boolean
  api_token_preview: string | null
  domain_subdomain: string | null
  api_token_updated_at: string | null
  api_token_updated_by: number | null
}

interface FakturowniaProduct {
  id: number
  name: string
  code: string | null
  price_net: number | null
  currency: string | null
  tax: string | null
  gtu_code: string | null
  pkwiu: string | null
}

interface RaoArticleRef {
  id: number
  name: string
}

interface ResolvedInvoiceLine {
  fakturownia_product_id: number
  fakturownia_product_name: string
  quantity: number
  price_net: number
  total_net: number
  invoice_number: string
  rao_articles: RaoArticleRef[]
}

interface ResolvedInvoice {
  invoice_number: string
  lines: ResolvedInvoiceLine[]
  total_net: number
  mapped_total_net: number
  unmapped_count: number
}

export const useFakturowniaStore = defineStore('fakturownia', () => {
  const settings = ref<FakturowniaSettings | null>(null)
  const products = ref<FakturowniaProduct[]>([])
  const invoices = ref<ResolvedInvoice[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSettings() {
    try {
      const { data } = await api.get('/integrations/fakturownia/settings')
      settings.value = data
    } catch (e: any) {
      error.value = 'Błąd pobierania ustawień Fakturownia'
      console.error('Fakturownia settings error:', e)
    }
  }

  async function updateSettings(payload: {
    enabled: boolean
    api_token?: string
    domain_subdomain?: string
  }) {
    try {
      const { data } = await api.put('/integrations/fakturownia/settings', payload)
      settings.value = data
    } catch (e: any) {
      error.value = 'Błąd aktualizacji ustawień Fakturownia'
      console.error('Fakturownia settings update error:', e)
      throw e
    }
  }

  async function fetchProducts() {
    loading.value = true
    try {
      const { data } = await api.get('/integrations/fakturownia/products')
      products.value = data
    } catch (e: any) {
      error.value = 'Błąd pobierania produktów z Fakturownia'
      console.error('Fakturownia products error:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchInvoicesByContractId(contractId: number) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get(`/integrations/fakturownia/invoices?contract_id=${contractId}`)
      invoices.value = data
    } catch (e: any) {
      error.value = 'Błąd pobierania faktur z Fakturownia'
      console.error('Fakturownia invoices error:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    settings,
    products,
    invoices,
    loading,
    error,
    fetchSettings,
    updateSettings,
    fetchProducts,
    fetchInvoicesByContractId
  }
})