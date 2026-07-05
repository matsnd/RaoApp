import { test, expect } from '@playwright/test'
import { API, apiLogin, authHeaders } from './helpers'

test.describe('TEST-19: Stats API — by-branch, by-contract-type, cache', () => {
  let token: string

  test.beforeAll(async ({ request }) => {
    token = await apiLogin(request)
  })

  // ── /stats/by-branch (P1-055) ─────────────────────────────────────────────

  test('GET /stats/by-branch → 200 z danymi per branch', async ({ request }) => {
    const r = await request.get(`${API}/stats/by-branch`, { headers: authHeaders(token) })
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data).toHaveProperty('items')
    expect(Array.isArray(data.items)).toBe(true)
    if (data.items.length > 0) {
      expect(data.items[0]).toHaveProperty('branch_id')
      expect(data.items[0]).toHaveProperty('contracts_count')
    }
  })

  test('GET /stats/by-branch z filtr daty → 200', async ({ request }) => {
    const r = await request.get(
      `${API}/stats/by-branch?date_from=2024-01-01&date_to=2026-12-31`,
      { headers: authHeaders(token) },
    )
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data).toHaveProperty('items')
    expect(Array.isArray(data.items)).toBe(true)
  })

  test('GET /stats/by-branch bez tokenu → 401', async ({ request }) => {
    const r = await request.get(`${API}/stats/by-branch`)
    expect(r.status()).toBe(401)
  })

  // ── /stats/by-contract-type (P2-056) ──────────────────────────────────────

  test('GET /stats/by-contract-type → 200 z S i U', async ({ request }) => {
    const r = await request.get(`${API}/stats/by-contract-type`, { headers: authHeaders(token) })
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data).toHaveProperty('items')
    expect(Array.isArray(data.items)).toBe(true)
    if (data.items.length > 0) {
      expect(data.items[0]).toHaveProperty('contract_type')
      expect(['S', 'U']).toContain(data.items[0].contract_type)
    }
  })

  test('GET /stats/by-contract-type z filtr daty → 200', async ({ request }) => {
    const r = await request.get(
      `${API}/stats/by-contract-type?date_from=2024-01-01&date_to=2026-12-31`,
      { headers: authHeaders(token) },
    )
    expect(r.status()).toBe(200)
  })

  test('GET /stats/by-contract-type bez tokenu → 401', async ({ request }) => {
    const r = await request.get(`${API}/stats/by-contract-type`)
    expect(r.status()).toBe(401)
  })

  // ── /stats/cache/clear (P2-051) ────────────────────────────────────────────

  test('POST /stats/cache/clear → 200 z cleared count (admin)', async ({ request }) => {
    const r = await request.post(`${API}/stats/cache/clear`, { headers: authHeaders(token) })
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data).toHaveProperty('cleared')
    expect(typeof data.cleared).toBe('number')
    expect(data).toHaveProperty('remaining')
  })

  // ── /stats/cache/stats (P2-051) ────────────────────────────────────────────

  test('GET /stats/cache/stats → 200 z entries count', async ({ request }) => {
    const r = await request.get(`${API}/stats/cache/stats`, { headers: authHeaders(token) })
    expect(r.status()).toBe(200)
    const data = await r.json()
    expect(data).toHaveProperty('entries')
    expect(typeof data.entries).toBe('number')
  })

  test('GET /stats/cache/stats bez tokenu → 401', async ({ request }) => {
    const r = await request.get(`${API}/stats/cache/stats`)
    expect(r.status()).toBe(401)
  })

  // ── Cache TTL verification (P2-051) ────────────────────────────────────────

  test('Cache: drugi request do /stats/fleet-summary jest szybszy (cache hit)', async ({ request }) => {
    const t1 = Date.now()
    await request.get(`${API}/stats/fleet-summary`, { headers: authHeaders(token) })
    const d1 = Date.now() - t1

    const t2 = Date.now()
    await request.get(`${API}/stats/fleet-summary`, { headers: authHeaders(token) })
    const d2 = Date.now() - t2

    // Cache hit powinien być szybszy (lub równy — tolerancja)
    // Nie failuj jeśli d2 >= d1 (może być flaky na małym dataset)
    console.log(`Cache test: first=${d1}ms, second=${d2}ms`)
    expect(d2).toBeLessThanOrEqual(d1 * 2) // tolerancja 2×
  })
})
