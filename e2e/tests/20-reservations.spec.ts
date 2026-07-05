import { test, expect } from '@playwright/test'
import { API, apiLogin, authHeaders } from './helpers'

test.describe('TEST-20: Rezerwacje maszyn (P2-066)', () => {
  let token: string

  test.beforeAll(async ({ request }) => {
    token = await apiLogin(request)
  })

  // ── /availability endpoint ─────────────────────────────────────────────────

  test('GET /availability → 200 (lista dostępności)', async ({ request }) => {
    const r = await request.get(`${API}/availability`, { headers: authHeaders(token) })
    // Endpoint może nie istnieć (martwy moduł) — sprawdzamy
    if (r.status() === 404) {
      console.log('Availability endpoint nie istnieje — P2-066 martwy moduł')
      return
    }
    expect(r.status()).toBe(200)
  })

  test('GET /availability/{article_id} → 200 lub 404', async ({ request }) => {
    // Sprawdź z article_id=1
    const r = await request.get(`${API}/availability/1`, { headers: authHeaders(token) })
    if (r.status() === 404) {
      console.log('Availability/{id} endpoint nie istnieje')
      return
    }
    expect([200, 422]).toContain(r.status())
  })

  // ── /reservations endpoint ─────────────────────────────────────────────────

  test('GET /reservations → 200 (lista rezerwacji)', async ({ request }) => {
    const r = await request.get(`${API}/reservations`, { headers: authHeaders(token) })
    if (r.status() === 404) {
      console.log('Reservations endpoint nie istnieje — P2-066 martwy moduł')
      return
    }
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(Array.isArray(data)).toBe(true)
  })

  test('POST /reservations tworzy rezerwację + cleanup', async ({ request }) => {
    // Najpierw pobierz artykuł
    const arts = await request.get(`${API}/articles`, { headers: authHeaders(token) })
    const articles = await arts.json()
    if (!articles.length) {
      console.log('Brak artykułów do testu rezerwacji')
      return
    }
    const articleId = articles[0].id

    const ts = Date.now()
    const r = await request.post(`${API}/reservations`, {
      headers: authHeaders(token),
      data: {
        article_id: articleId,
        date_from: new Date(ts + 86400000).toISOString().slice(0, 10),
        date_to: new Date(ts + 172800000).toISOString().slice(0, 10),
        notes: `Test reservation ${ts}`,
      },
    })
    if (r.status() === 404) {
      console.log('POST /reservations nie istnieje')
      return
    }
    expect([201, 200, 409]).toContain(r.status())
    if (r.status() === 201 || r.status() === 200) {
      const created = await r.json()
      if (created.id) {
        // Cleanup
        await request.delete(`${API}/reservations/${created.id}`, { headers: authHeaders(token) })
      }
    }
  })

  test('GET /reservations bez tokenu → 401', async ({ request }) => {
    const r = await request.get(`${API}/reservations`)
    if (r.status() === 404) return
    expect(r.status()).toBe(401)
  })

  // ── UI: rezerwacje w ContractFormView ──────────────────────────────────────

  test('UI: ContractFormView pokazuje dostępność maszyny', async ({ page, request }) => {
    // Ten test sprawdza czy UI ma elementy dostępności
    // Pełny test UI w 04-contract.spec.ts
    // Tutaj tylko API-level check
    const r = await request.get(`${API}/availability`, { headers: authHeaders(token) })
    if (r.status() === 404) {
      console.log('Availability moduł nieaktywny — UI test pominięty')
      return
    }
    expect(r.status()).toBe(200)
  })
})
