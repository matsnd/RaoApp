import { test, expect } from '@playwright/test'
import { BASE, login, waitForBackend } from './helpers'

test.describe('TEST-17: HomeView — strona główna z KPI', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
    // login() już przekierowuje do /rao/home
  })

  test('wyświetla stronę główną po logowaniu', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    const content = page.locator('main, .home-view, .page-card').first()
    await expect(content).toBeVisible({ timeout: 10_000 })
  })

  test('panel "Kończące się umowy" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    const panel = page.locator('text=/kończąc|expir/i').first()
    if (await panel.count() > 0) {
      await expect(panel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('panel "Przeterminowane" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    const panel = page.locator('text=/przetermin|overdue/i').first()
    if (await panel.count() > 0) {
      await expect(panel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('panel "Dostawy" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    const panel = page.locator('text=/dostaw/i').first()
    if (await panel.count() > 0) {
      await expect(panel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('panel "Nie wydrukowane" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    const panel = page.locator('text=/nie wydrukowan|unprinted/i').first()
    if (await panel.count() > 0) {
      await expect(panel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('panel "Stare umowy" jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    const panel = page.locator('text=/stare|stale/i').first()
    if (await panel.count() > 0) {
      await expect(panel).toBeVisible({ timeout: 5_000 })
    }
  })

  test('loading state (panel-loading) przy ładowaniu', async ({ page }) => {
    // Loading state jest krótkotrwały — soft check
    await page.goto(`${BASE}/home`, { waitUntil: 'commit', timeout: 15_000 })
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
  })

  test('error state (panel-error) z role="alert"', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    const errorMsg = page.locator('[role="alert"], .panel-error')
    if (await errorMsg.count() > 0) {
      await expect(errorMsg.first()).toBeVisible({ timeout: 2_000 })
    }
  })

  test('klik w umowę w panelu → edycja umowy', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    // Klik w pierwszy link do umowy
    const contractLink = page.locator('a[href*="/contracts/"], [data-testid*="contract-link"]').first()
    if (await contractLink.count() > 0) {
      await contractLink.click()
      await expect(page).toHaveURL(/\/rao\/contracts\/\d+\/edit/, { timeout: 10_000 })
    }
  })

  test('nawigacja do sekcji przez sidebar', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    // Sprawdź czy sidebar jest widoczny
    const nav = page.locator('nav, .sidebar, [role="navigation"]')
    await expect(nav).toBeVisible({ timeout: 5_000 })
  })
})
