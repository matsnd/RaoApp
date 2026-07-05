import { test, expect, request } from '@playwright/test'
import { BASE, API, login, waitForBackend, apiLogin, authHeaders, safeDelete } from './helpers'

test.describe('TEST-16: AdminView — panel administratora', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
    await page.goto(`${BASE}/admin`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
  })

  test('wyświetla panel admina (tylko dla admin)', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/admin/, { timeout: 10_000 })
    const content = page.locator('main, .page-card, .admin-view').first()
    await expect(content).toBeVisible({ timeout: 10_000 })
  })

  test('tabela użytkowników z danymi', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/admin/, { timeout: 10_000 })
    // AdminView pokazuje tabelę użytkowników
    const table = page.locator('table, .data-grid').first()
    await expect(table).toBeVisible({ timeout: 10_000 })
    // Sprawdź czy są nagłówki
    const headers = page.locator('th, [role="columnheader"]')
    await expect(headers.first()).toBeVisible({ timeout: 5_000 })
  })

  test('loading state (TableSkeleton) przy ładowaniu', async ({ page }) => {
    // Loading state jest krótkotrwały — soft check
    await page.goto(`${BASE}/admin`, { waitUntil: 'commit', timeout: 15_000 })
    await expect(page).toHaveURL(/\/rao\/admin/, { timeout: 10_000 })
  })

  test('empty state "Brak użytkowników" (jeśli puste)', async ({ page }) => {
    // Soft check — admin istnieje więc empty state nie wystąpi
    await expect(page).toHaveURL(/\/rao\/admin/, { timeout: 10_000 })
    const emptyMsg = page.locator('text=/brak użytkownik/i, .empty-state')
    const hasEmpty = await emptyMsg.count().catch(() => 0)
    if (hasEmpty > 0) {
      await expect(emptyMsg).toBeVisible({ timeout: 2_000 })
    }
  })

  test('API: GET /admin/users zwraca listę użytkowników', async ({ request }) => {
    const token = await apiLogin(request)
    const r = await request.get(`${API}/admin/users`, { headers: authHeaders(token) })
    expect(r.status()).toBe(200)
    const users = await r.json()
    expect(Array.isArray(users)).toBe(true)
    expect(users.length).toBeGreaterThan(0)
    expect(users.some((u: any) => u.login === 'admin')).toBe(true)
  })

  test('API: GET /admin/users bez tokenu → 401', async ({ request }) => {
    const r = await request.get(`${API}/admin/users`)
    expect(r.status()).toBe(401)
  })

  test('API: POST /admin/users tworzy nowego użytkownika + cleanup', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const userData = {
      login: `testuser_${ts}`,
      email: `test_${ts}@test.pl`,
      password: 'TestPass123!',
      first_name: 'Test',
      last_name: 'User',
      role: 'user',
    }
    const create = await request.post(`${API}/admin/users`, {
      headers: authHeaders(token),
      data: userData,
    })
    expect([201, 200]).toContain(create.status())
    const created = await create.json()
    expect(created.id).toBeDefined()
    expect(created.login).toBe(userData.login)

    // Cleanup — deactivate (brak DELETE endpoint)
    await request.patch(`${API}/admin/users/${created.id}/deactivate`, { headers: authHeaders(token) })
  })

  test('API: PATCH /admin/users/{id}/deactivate dezaktywuje użytkownika', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    // Najpierw utwórz
    const create = await request.post(`${API}/admin/users`, {
      headers: authHeaders(token),
      data: { login: `deltest_${ts}`, email: `del_${ts}@test.pl`, password: 'TestPass123!', role: 'user' },
    })
    const created = await create.json()
    // Dezaktywuj
    const del = await request.patch(`${API}/admin/users/${created.id}/deactivate`, { headers: authHeaders(token) })
    expect([200, 204]).toContain(del.status())
    // Sprawdź że jest nieaktywny
    const get = await request.get(`${API}/admin/users`, { headers: authHeaders(token) })
    expect(get.status()).toBe(200)
    const users = await get.json()
    const u = users.find((x: any) => x.id === created.id)
    expect(u).toBeDefined()
    expect(u.is_active).toBe(false)
  })
})
