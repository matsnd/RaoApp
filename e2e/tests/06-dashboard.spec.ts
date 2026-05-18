import { test, expect } from '@playwright/test'
import { waitForBackend, login, navigateTo, API, apiLogin, authHeaders, safeDelete, newApiContext, genValidNip } from './helpers'

const createdContractors: number[] = []
const createdContracts: number[] = []

test.describe('TEST-06: Dashboard / Home', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('Home: KPI strip widoczny po zalogowaniu', async ({ page }) => {
    await page.goto('/rao/home', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('.kpi-strip')).toBeVisible({ timeout: 8_000 })
    // Co najmniej 2 karty KPI
    const cards = page.locator('.kpi-card')
    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(2)
  })

  test('Home: karta "Maszyny w terenie" pokazuje liczby', async ({ page }) => {
    await page.goto('/rao/home', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('.kpi-strip').getByText('Maszyny w terenie')).toBeVisible({ timeout: 8_000 })
  })

  test('Dashboard kontrakty: tabela widoczna lub "Brak umów"', async ({ page }) => {
    await navigateTo(page, 'contracts')
    await expect(page.locator('table.data-grid')).toBeVisible({ timeout: 8_000 })
    // Albo wiersze z umowami, albo empty-state
    const empty = page.locator('.empty-state')
    const rows = page.locator('tbody tr:not(.empty-state)')
    const hasRows = await rows.count() > 0
    const hasEmpty = await empty.count() > 0
    expect(hasRows || hasEmpty).toBe(true)
  })

  test('Dashboard: filtr typu (S/U) przeładowuje listę', async ({ page }) => {
    await navigateTo(page, 'contracts')
    await page.locator('select.form-control').first().selectOption('S')
    await page.waitForTimeout(500)
    // Brak crash + tabela nadal widoczna
    await expect(page.locator('table.data-grid')).toBeVisible()
  })

  test('Dashboard: filtr dat date_from / date_to nie crashuje', async ({ page }) => {
    await navigateTo(page, 'contracts')
    const dateInputs = page.locator('input[type="date"]')
    await dateInputs.nth(0).fill('2020-01-01')
    await dateInputs.nth(1).fill('2030-12-31')
    await page.waitForTimeout(500)
    await expect(page.locator('table.data-grid')).toBeVisible()
  })

  test('Dashboard: dwuklik wiersza umowy → /contracts/{id}/edit', async ({ page, request }) => {
    // Stwórz umowę by mieć pewność że jest wiersz
    const token = await apiLogin(request)
    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `DashE2E ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    createdContractors.push(c.id)
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: c.id, contract_type: 'S', date_from: today },
    })
    test.skip(ctr.status() !== 201, `BUG RAO-QA-002: POST /contracts → ${ctr.status()}`)
    const ct = await ctr.json()
    createdContracts.push(ct.id)

    await navigateTo(page, 'contracts')
    await page.getByPlaceholder('Szukaj wg numeru, kontrahenta...').fill(`DashE2E ${ts}`)
    await page.waitForTimeout(700)
    const row = page.locator('tbody tr.contract-row').first()
    await expect(row).toBeVisible({ timeout: 5_000 })
    await row.dblclick()
    await expect(page).toHaveURL(/\/rao\/contracts\/\d+\/edit/, { timeout: 8_000 })
  })

  test.afterAll(async () => {
    const ctx = await newApiContext()
    try {
      const token = await apiLogin(ctx)
      for (const id of createdContracts) await safeDelete(ctx, `${API}/contracts/${id}`, token)
      for (const id of createdContractors) await safeDelete(ctx, `${API}/contractors/${id}`, token)
    } catch {
      /* ignore */
    } finally {
      await ctx.dispose()
    }
  })
})
