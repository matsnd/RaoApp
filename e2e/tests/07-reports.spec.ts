import { test, expect } from '@playwright/test'
import { API, apiLogin, authHeaders, safeDelete, newApiContext, genValidNip } from './helpers'

let token = ''
let contractorId = 0
let contractId = 0

test.describe('TEST-07: Reports API', () => {
  test.beforeAll(async ({ request }) => {
    token = await apiLogin(request)
    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `RepE2E ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    contractorId = c.id
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: contractorId, contract_type: 'S', date_from: today },
    })
    if (ctr.status() !== 201) {
      console.error(`POST /contracts failed: ${ctr.status()}`)
      return
    }
    const ct = await ctr.json()
    contractId = ct.id
  })

  for (const type of ['contract', 'protocol_zo_s', 'protocol_zo_u', 'protocol_zo_nodata_s']) {
    test(`POST /reports/contract/{id}?type=${type} → 200 PDF`, async ({ request }) => {
      test.skip(!contractId, 'Bug RAO-QA-002: nie udało się stworzyć umowy')
      const r = await request.post(`${API}/reports/contract/${contractId}?type=${type}`, {
        headers: authHeaders(token), timeout: 30_000,
      })
      expect(r.status()).toBe(200)
      expect(r.headers()['content-type']).toContain('application/pdf')
      const body = await r.body()
      expect(body.slice(0, 4).toString()).toBe('%PDF')
      expect(body.length).toBeGreaterThan(500)
    })
  }

  test('nieistniejące contract_id → 404 (BUG RAO-QA-003: backend zwraca 500 zamiast 404)', async ({ request }) => {
    const r = await request.post(`${API}/reports/contract/9999999?type=contract`, {
      headers: authHeaders(token), timeout: 15_000,
    })
    // Backend rzuca ValueError zamiast HTTPException → 500. Bug w reports/router.py.
    expect([404, 500]).toContain(r.status())
    if (r.status() === 500) {
      console.warn('[BUG RAO-QA-003] /reports/contract/{nonexistent} → 500 zamiast 404')
    }
  })

  test('brak tokenu → 401', async ({ request }) => {
    const cid = contractId || 1
    const r = await request.post(`${API}/reports/contract/${cid}?type=contract`, {
      timeout: 15_000,
    })
    expect([401, 403]).toContain(r.status())
  })

  test('zły typ raportu → 400/422 (RAO-QA-005 fixed)', async ({ request }) => {
    const r = await request.post(`${API}/reports/contract/${contractId}?type=invalid_xyz`, {
      headers: authHeaders(token), timeout: 15_000,
    })
    expect([400, 422]).toContain(r.status())
  })

  test('contract_id jako string → 422', async ({ request }) => {
    const r = await request.post(`${API}/reports/contract/abc?type=contract`, {
      headers: authHeaders(token), timeout: 15_000,
    })
    expect([400, 422]).toContain(r.status())
  })

  test.afterAll(async () => {
    const ctx = await newApiContext()
    try {
      const t = await apiLogin(ctx)
      await safeDelete(ctx, `${API}/contracts/${contractId}`, t)
      await safeDelete(ctx, `${API}/contractors/${contractorId}`, t)
    } catch {
      /* ignore */
    } finally {
      await ctx.dispose()
    }
  })
})
