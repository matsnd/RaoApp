import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

interface InvoiceLine {
  fakturownia_product_id: number
  fakturownia_product_name: string
  quantity: number
  price_net: number
  total_net: number
  invoice_number: string | null
}

interface Invoice {
  invoice_number: string
  lines: InvoiceLine[]
  total_net: number
}

export const useFakturowniaStore = defineStore('fakturownia', () => {
  const invoices = ref<Invoice[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchInvoicesByOid(oid: string) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get(`/fakturownia/invoices?oid=${oid}`)
      invoices.value = data
    } catch (e: any) {
      error.value = 'Błąd pobierania faktur z Fakturownia'
      console.error('Fakturownia API error:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    invoices,
    loading,
    error,
    fetchInvoicesByOid
  }
})