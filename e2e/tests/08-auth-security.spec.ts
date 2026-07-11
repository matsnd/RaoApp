import { test, expect } from '@playwright/test'
import { waitForBackend, login, API, apiLogin, authHeaders } from './helpers'

test.describe('TEST-08: Auth & Security', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
  })

  // ---------- Frontend route guards ----------

  for (const route of [
    '/rao/home',
    '/rao/contractors/new',
    '/rao/contractors/1/edit',
    '/rao/contracts/new',
    '/rao/contracts/1/edit',
    '/rao/articles/new',       // backward compat — legacy route
    '/rao/machines/new',       // Faza 5: nowy routing
    '/rao/services/new',       // Faza 5: nowy routing
    '/rao/additional-services/new', // Faza 5: nowy routing
    '/rao/settings',
    '/rao/dashboard/contracts',
  ]) {
    test(`bez tokenu wejście na ${route} → /login`, async ({ page }) => {
      // Ensure no session
      await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await page.evaluate(() => {
        localStorage.removeItem('rao_token')
        localStorage.removeItem('rao_user')
      })
      await page.goto(route, { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page).toHaveURL(/\/rao\/login/, { timeout: 8_000 })
    })
  }

  // ---------- Backend endpoints bez tokenu ----------

  for (const ep of [
    { method: 'get', path: '/contractors' },
    { method: 'get', path: '/contracts' },
    { method: 'get', path: '/articles' },           // backward compat
    { method: 'get', path: '/machines' },            // Faza 5
    { method: 'get', path: '/services' },            // Faza 5
    { method: 'get', path: '/additional-services' }, // Faza 5
    { method: 'get', path: '/settings/company' },
    { method: 'get', path: '/auth/profile' },
  ]) {
    test(`${ep.method.toUpperCase()} ${ep.path} bez tokenu → 401`, async ({ request }) => {
      const r = await (request as any)[ep.method](`${API}${ep.path}`, { timeout: 8_000 })
      expect([401, 403]).toContain(r.status())
    })
  }

  test('POST /contractors bez tokenu → 401', async ({ request }) => {
    const r = await request.post(`${API}/contractors`, { data: { name: 'X' }, timeout: 8_000 })
    expect([401, 403]).toContain(r.status())
  })

  test('POST /contracts bez tokenu → 401', async ({ request }) => {
    const r = await request.post(`${API}/contracts`, {
      data: { contractor_id: 1, contract_type: 'S', date_from: '2025-01-01' },
      timeout: 8_000,
    })
    expect([401, 403]).toContain(r.status())
  })

  // ---------- Token tampering ----------

  test('zmodyfikowany token → 401', async ({ request }) => {
    const real = await apiLogin(request)
    const tampered = real.slice(0, -5) + 'AAAAA'
    const r = await request.get(`${API}/auth/profile`, {
      headers: { Authorization: `Bearer ${tampered}` },
      timeout: 8_000,
    })
    expect([401, 403]).toContain(r.status())
  })

  test('Bearer bez tokenu → 401', async ({ request }) => {
    const r = await request.get(`${API}/auth/profile`, {
      headers: { Authorization: 'Bearer ' },
      timeout: 8_000,
    })
    expect([401, 403]).toContain(r.status())
  })

  // ---------- Change password ----------

  test('zmiana hasła: błędne stare hasło → 4xx', async ({ request }) => {
    const token = await apiLogin(request)
    const r = await request.put(`${API}/auth/change-password`, {
      headers: authHeaders(token),
      data: {
        current_password: 'WRONG_OLD_PASSWORD',
        new_password: 'NewPass123!',
        confirm_password: 'NewPass123!',
      },
      timeout: 10_000,
    })
    expect(r.status()).toBeGreaterThanOrEqual(400)
    expect(r.status()).toBeLessThan(500)
  })

  test('zmiana hasła: confirm != new → 4xx', async ({ request }) => {
    const token = await apiLogin(request)
    const r = await request.put(`${API}/auth/change-password`, {
      headers: authHeaders(token),
      data: {
        current_password: 'admin123',
        new_password: 'AAAaaa111',
        confirm_password: 'BBBbbb222',
      },
      timeout: 10_000,
    })
    expect(r.status()).toBeGreaterThanOrEqual(400)
    expect(r.status()).toBeLessThan(500)
  })

  test('zmiana hasła happy path + revert', async ({ request }) => {
    const token = await apiLogin(request)
    const newPass = 'TempPass#' + Date.now()

    const r1 = await request.put(`${API}/auth/change-password`, {
      headers: authHeaders(token),
      data: {
        current_password: 'admin123',
        new_password: newPass,
        confirm_password: newPass,
      },
      timeout: 10_000,
    })
    expect([200, 204]).toContain(r1.status())

    // Revert — żeby kolejne testy działały
    const login2 = await request.post(`${API}/auth/login`, {
      data: { login: 'admin', password: newPass }, timeout: 10_000,
    })
    expect(login2.status()).toBe(200)
    const { access_token } = await login2.json()
    const r2 = await request.put(`${API}/auth/change-password`, {
      headers: authHeaders(access_token),
      data: {
        current_password: newPass,
        new_password: 'admin123',
        confirm_password: 'admin123',
      },
      timeout: 10_000,
    })
    expect([200, 204]).toContain(r2.status())
  })

  // ---------- Logowanie po wyczyszczeniu localStorage ----------

  test('po wylogowaniu localStorage jest wyczyszczony', async ({ page }) => {
    await login(page)
    await page.getByRole('button', { name: 'Wyloguj' }).click()
    await expect(page).toHaveURL(/\/login/, { timeout: 8_000 })
    const token = await page.evaluate(() => localStorage.getItem('rao_token'))
    expect(token).toBeNull()
  })
})
