// P1-205 Faza 2: Pinia store dla kalendarza dostaw (deliveries).
// Endpoint backend: GET /deliveries/calendar?date_from&date_to&machine_id&contractor_id
// Zwraca DeliveryCalendarEvent[] — dostawy z umów S (najem) i U (usługa).
// Wzorzec: frontend/src/stores/reservations.ts (fetchCalendar, loading, error).
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export interface DeliveryCalendarEvent {
  source: 'contract'
  source_id: number // contract_id
  contract_number: string
  contract_type: 'S' | 'U'
  machine_id: number | null
  machine_name: string | null
  internal_number: string | null
  contractor_id: number
  contractor_name: string
  delivery_date: string // ISO date
  delivery_address: string | null
  city: string | null
  salesperson_id: number | null
  salesperson_name: string | null
}

export const useDeliveriesStore = defineStore('deliveries', () => {
  const calendarEvents = ref<DeliveryCalendarEvent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCalendar(
    dateFrom: string,
    dateTo: string,
    machineId?: number,
    contractorId?: number,
  ): Promise<DeliveryCalendarEvent[]> {
    loading.value = true
    error.value = null
    try {
      const params: Record<string, string | number> = {
        date_from: dateFrom,
        date_to: dateTo,
      }
      if (machineId != null) params.machine_id = machineId
      if (contractorId != null) params.contractor_id = contractorId
      const { data } = await api.get<DeliveryCalendarEvent[]>('/deliveries/calendar', { params })
      calendarEvents.value = data
      return data
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd pobierania kalendarza dostaw'
      calendarEvents.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  function reset() {
    calendarEvents.value = []
    error.value = null
    loading.value = false
  }

  return { calendarEvents, loading, error, fetchCalendar, reset }
})
