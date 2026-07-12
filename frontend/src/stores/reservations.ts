// RAO-P2-066: Pinia store dla rezerwacji maszyn (machine_reservations).
// Moduł backend /reservations istniał (RAO-P1-015) ale nie miał UI — to pierwsza
// integracja frontendowa.
// RAO-P3 (Phase 3): rozszerzony o CalendarEvent, fetchCalendar, update,
// contractor_id/contractor_name/status.
// RAO Faza 4b: ArticleReservation → MachineReservation, endpointy /article→/machine, /with-articles→/with-machines.
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export interface MachineReservation {
  id: number
  machine_id: number
  article_id?: number  // backward-compat alias (backend coalesce)
  reserved_from: string  // ISO date
  reserved_to: string    // ISO date
  note: string | null
  contractor_id: number | null
  contractor_name: string | null
  salesperson_id: number | null  // P1-119
  salesperson_name: string | null  // P1-119
  created_by: number | null
  created_at: string
}

export interface ReservationWithMachine extends MachineReservation {
  machine_name: string | null
  article_name: string | null  // backward-compat alias (backend coalesce)
  internal_number: string | null
}

// RAO Faza 4c: backward-compat aliases — ReservationsView.vue nadal używa starych nazw
export type ArticleReservation = MachineReservation
export type ReservationWithArticle = ReservationWithMachine

export interface ReservationPayload {
  machine_id: number
  reserved_from: string
  reserved_to: string
  note?: string | null
  contractor_id?: number | null
  salesperson_id?: number | null  // P1-119
}

// RAO-P3: partial update payload (PUT /reservations/{id})
export interface ReservationUpdatePayload {
  reserved_from?: string
  reserved_to?: string
  note?: string | null
  contractor_id?: number | null
  salesperson_id?: number | null  // P1-119
}

// RAO-P3: event kalendarza (rezerwacja lub umowa)
export interface CalendarEvent {
  source: 'reservation' | 'contract'
  source_id: number
  machine_id: number
  machine_name: string | null
  article_name: string | null  // backward-compat alias (backend coalesce)
  article_id?: number  // backward-compat alias (backend coalesce)
  internal_number: string | null
  contractor_id: number | null
  contractor_name: string | null
  salesperson_id: number | null  // P1-119
  salesperson_name: string | null  // P1-119
  date_from: string  // ISO date
  date_to: string    // ISO date
  note: string | null
}

export const useReservationsStore = defineStore('reservations', () => {
  const list = ref<MachineReservation[]>([])
  const allList = ref<ReservationWithMachine[]>([])
  const calendarEvents = ref<CalendarEvent[]>([])
  const loading = ref(false)
  const loadingAll = ref(false)
  const loadingCalendar = ref(false)
  const error = ref<string | null>(null)

  async function fetchForMachine(machineId: number): Promise<MachineReservation[]> {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get<MachineReservation[]>(
        `/reservations/machine/${machineId}`,
      )
      list.value = data
      return data
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd pobierania rezerwacji'
      list.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchAllWithMachines(): Promise<ReservationWithMachine[]> {
    loadingAll.value = true
    error.value = null
    try {
      const { data } = await api.get<ReservationWithMachine[]>('/reservations/with-machines')
      allList.value = data
      return data
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd pobierania rezerwacji'
      allList.value = []
      return []
    } finally {
      loadingAll.value = false
    }
  }

  // RAO-P3: pobierz eventy kalendarza (rezerwacje + umowy) dla zakresu dat
  async function fetchCalendar(
    dateFrom: string,
    dateTo: string,
    machineId?: number,
  ): Promise<CalendarEvent[]> {
    loadingCalendar.value = true
    error.value = null
    try {
      const params: Record<string, string | number> = {
        date_from: dateFrom,
        date_to: dateTo,
      }
      if (machineId != null) params.machine_id = machineId
      const { data } = await api.get<CalendarEvent[]>('/reservations/calendar', { params })
      calendarEvents.value = data
      return data
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd pobierania kalendarza rezerwacji'
      calendarEvents.value = []
      return []
    } finally {
      loadingCalendar.value = false
    }
  }

  async function create(payload: ReservationPayload): Promise<MachineReservation> {
    error.value = null
    try {
      const { data } = await api.post<MachineReservation>('/reservations', payload)
      // Odśwież listę lokalnie — dodaj nową rezerwację
      list.value = [...list.value, data].sort(
        (a, b) => a.reserved_from.localeCompare(b.reserved_from),
      )
      return data
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd tworzenia rezerwacji'
      throw e
    }
  }

  // RAO-P3: aktualizuj rezerwację (partial update)
  async function update(
    reservationId: number,
    payload: ReservationUpdatePayload,
  ): Promise<MachineReservation> {
    error.value = null
    try {
      const { data } = await api.put<MachineReservation>(`/reservations/${reservationId}`, payload)
      // Odśwież listy lokalnie
      list.value = list.value
        .map((r) => (r.id === reservationId ? data : r))
        .sort((a, b) => a.reserved_from.localeCompare(b.reserved_from))
      allList.value = allList.value.map((r) =>
        r.id === reservationId ? { ...r, ...data } : r,
      )
      return data
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd aktualizacji rezerwacji'
      throw e
    }
  }

  async function remove(reservationId: number): Promise<void> {
    error.value = null
    try {
      await api.delete(`/reservations/${reservationId}`)
      list.value = list.value.filter((r) => r.id !== reservationId)
      allList.value = allList.value.filter((r) => r.id !== reservationId)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd usuwania rezerwacji'
      throw e
    }
  }

  function reset() {
    list.value = []
    allList.value = []
    calendarEvents.value = []
    error.value = null
    loading.value = false
  }

  // RAO Faza 4c: backward-compat aliases — ReservationsView.vue nadal używa starych nazw
  const fetchForArticle = fetchForMachine
  const fetchAllWithArticles = fetchAllWithMachines

  return {
    list,
    allList,
    calendarEvents,
    loading,
    loadingAll,
    loadingCalendar,
    error,
    fetchForMachine,
    fetchAllWithMachines,
    fetchForArticle,
    fetchAllWithArticles,
    fetchCalendar,
    create,
    update,
    remove,
    reset,
  }
})
