// RAO-P2-066: Pinia store dla rezerwacji maszyn (article_reservations).
// Moduł backend /reservations istniał (RAO-P1-015) ale nie miał UI — to pierwsza
// integracja frontendowa.
// RAO-P3 (Phase 3): rozszerzony o CalendarEvent, fetchCalendar, update,
// contractor_id/contractor_name/status.
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export interface ArticleReservation {
  id: number
  article_id: number
  reserved_from: string  // ISO date
  reserved_to: string    // ISO date
  note: string | null
  contractor_id: number | null
  contractor_name: string | null
  status: string | null  // "confirmed" | "provisional" | null
  created_by: number | null
  created_at: string
}

export interface ReservationWithArticle extends ArticleReservation {
  article_name: string | null
  internal_number: string | null
}

export interface ReservationPayload {
  article_id: number
  reserved_from: string
  reserved_to: string
  note?: string | null
  contractor_id?: number | null
  status?: string | null
}

// RAO-P3: partial update payload (PUT /reservations/{id})
export interface ReservationUpdatePayload {
  reserved_from?: string
  reserved_to?: string
  note?: string | null
  contractor_id?: number | null
  status?: string | null
}

// RAO-P3: event kalendarza (rezerwacja lub umowa)
export interface CalendarEvent {
  source: 'reservation' | 'contract'
  source_id: number
  article_id: number
  article_name: string | null
  internal_number: string | null
  contractor_id: number | null
  contractor_name: string | null
  date_from: string  // ISO date
  date_to: string    // ISO date
  note: string | null
  status: string | null  // "confirmed" | "provisional" | null (dla umow)
}

export const useReservationsStore = defineStore('reservations', () => {
  const list = ref<ArticleReservation[]>([])
  const allList = ref<ReservationWithArticle[]>([])
  const calendarEvents = ref<CalendarEvent[]>([])
  const loading = ref(false)
  const loadingAll = ref(false)
  const loadingCalendar = ref(false)
  const error = ref<string | null>(null)

  async function fetchForArticle(articleId: number): Promise<ArticleReservation[]> {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get<ArticleReservation[]>(
        `/reservations/article/${articleId}`,
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

  async function fetchAllWithArticles(): Promise<ReservationWithArticle[]> {
    loadingAll.value = true
    error.value = null
    try {
      const { data } = await api.get<ReservationWithArticle[]>('/reservations/with-articles')
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
    articleId?: number,
  ): Promise<CalendarEvent[]> {
    loadingCalendar.value = true
    error.value = null
    try {
      const params: Record<string, string | number> = {
        date_from: dateFrom,
        date_to: dateTo,
      }
      if (articleId != null) params.article_id = articleId
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

  async function create(payload: ReservationPayload): Promise<ArticleReservation> {
    error.value = null
    try {
      const { data } = await api.post<ArticleReservation>('/reservations', payload)
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
  ): Promise<ArticleReservation> {
    error.value = null
    try {
      const { data } = await api.put<ArticleReservation>(`/reservations/${reservationId}`, payload)
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

  return {
    list,
    allList,
    calendarEvents,
    loading,
    loadingAll,
    loadingCalendar,
    error,
    fetchForArticle,
    fetchAllWithArticles,
    fetchCalendar,
    create,
    update,
    remove,
    reset,
  }
})
