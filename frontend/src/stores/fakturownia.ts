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
  const useMock = ref(true) // Mock mode dla testów UI

  async function fetchInvoicesByOid(oid: string) {
    loading.value = true
    error.value = null
    try {
      if (useMock.value) {
        // Mock data response
        await new Promise(resolve => setTimeout(resolve, 500)) // Symulacja opóźnienia API
        invoices.value = [
          {
            invoice_number: `FV/2026/${oid}`,
            lines: [
              {
                fakturownia_product_id: 12345,
                fakturownia_product_name: 'Koparka CAT 320',
                quantity: 1,
                price_net: 12000.00,
                total_net: 12000.00,
                invoice_number: `FV/2026/${oid}`
              },
              {
                fakturownia_product_id: 12346,
                fakturownia_product_name: 'Transport',
                quantity: 1,
                price_net: 400.00,
                total_net: 400.00,
                invoice_number: `FV/2026/${oid}`
              }
            ],
            total_net: 12400.00
          }
        ]
      } else {
        const { data } = await api.get(`/fakturownia/invoices?oid=${oid}`)
        invoices.value = data
      }
    } catch (e: any) {
      error.value = 'Błąd pobierania faktur z Fakturownia'
      console.error('Fakturownia API error:', e)
    } finally {
      loading.value = false
    }
  }

  function setMockMode(enabled: boolean) {
    useMock.value = enabled
  }

  return {
    invoices,
    loading,
    error,
    useMock,
    fetchInvoicesByOid,
    setMockMode
  }
})