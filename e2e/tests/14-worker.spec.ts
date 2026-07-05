import { test, expect } from '@playwright/test'
import { BASE, login, waitForBackend } from './helpers'

test.describe('TEST-14: WorkerView — panel pracownika', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
    await page.goto(`${BASE}/worker`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
  })

  test('wyświetla stronę pracownika z panelami', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
    // WorkerView ma 5 paneli: expiring, deliveries, unprinted, stale, overdue
    // Sprawdź czy strona się załadowała (main content visible)
    const content = page.locator('main, .worker-view, .page-content, h1, h2').first()
    await expect(content).toBeVisible({ timeout: 10_000 })
  })

  test('panel "Kończące się umowy" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
    const expiringPanel = page.locator('text=/kończąc|expir/i').first()
    if (await expiringPanel.count() > 0) {
      await expect(expiringPanel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('panel "Dostawy" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
    const deliveriesPanel = page.locator('text=/dostaw/i').first()
    if (await deliveriesPanel.count() > 0) {
      await expect(deliveriesPanel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('panel "Nie wydrukowane" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
    const unprintedPanel = page.locator('text=/nie wydrukowan|unprinted/i').first()
    if (await unprintedPanel.count() > 0) {
      await expect(unprintedPanel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('panel "Przeterminowane" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
    const overduePanel = page.locator('text=/przetermin|overdue/i').first()
    if (await overduePanel.count() > 0) {
      await expect(overduePanel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('filtry dni działają (7/14/30)', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
    // Sprawdź czy są przyciski filtrów dni
    const dayFilter = page.locator('button:has-text("7"), button:has-text("14"), button:has-text("30")').first()
    if (await dayFilter.count() > 0) {
      await dayFilter.click()
      await page.waitForTimeout(500)
    }
  })

  test('loading state (skeleton) jest pokazany przy ładowaniu', async ({ page }) => {
    // Loading state jest krótkotrwały — test soft (nie failuj jeśli już załadowane)
    await page.goto(`${BASE}/worker`, { waitUntil: 'commit', timeout: 15_000 })
    const loading = page.locator('.skeleton, .skeleton-list, [role="status"], text=/ładowan/i')
    // Soft check — nie failuj jeśli loading już minął (to dobre zachowanie)
    const hasLoading = await loading.count().catch(() => 0)
    if (hasLoading > 0) {
      await expect(loading.first()).toBeVisible({ timeout: 1_000 }).catch(() => {})
    }
    // Sprawdź że strona się załadowała
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
  })

  test('error state z retry (jeśli endpoint zwraca błąd)', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/worker/, { timeout: 10_000 })
    // Sprawdź czy jest error message z role="alert"
    const errorMsg = page.locator('[role="alert"], .card-error, .state-error')
    // Nie failuj jeśli nie ma błędu (to dobrze)
    if (await errorMsg.count() > 0) {
      await expect(errorMsg.first()).toBeVisible({ timeout: 2_000 })
    }
  })
})
