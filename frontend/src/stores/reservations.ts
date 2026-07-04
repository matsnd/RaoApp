// RAO-P2-066: Pinia store dla rezerwacji maszyn (article_reservations).
// Moduł backend /reservations istniał (RAO-P1-015) ale nie miał UI — to pierwsza
// integracja frontendowa.
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export interface ArticleReservation {
  id: number
  article_id: number
  reserved_from: string  // ISO date
  reserved_to: string    // ISO date
  note: string | null
  created_by: number | null
  created_at: string
}

export interface ReservationPayload {
  article_id: number
  reserved_from: string
  reserved_to: string
  note?: string | null
}

export const useReservationsStore = defineStore('reservations', () => {
  const list = ref<ArticleReservation[]>([])
  const loading = ref(false)
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

  async function remove(reservationId: number): Promise<void> {
    error.value = null
    try {
      await api.delete(`/reservations/${reservationId}`)
      list.value = list.value.filter(r => r.id !== reservationId)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      error.value = err.response?.data?.detail || 'Błąd usuwania rezerwacji'
      throw e
    }
  }

  function reset() {
    list.value = []
    error.value = null
    loading.value = false
  }

  return { list, loading, error, fetchForArticle, create, remove, reset }
})
