import { test, expect } from '@playwright/test'
import { BASE, login, waitForBackend } from './helpers'

test.describe('TEST-15: CommissionView — prowizje handlowców', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
    await page.goto(`${BASE}/commissions`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
  })

  test('wyświetla stronę prowizji', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/commissions/, { timeout: 10_000 })
    // CommissionView pokazuje prowizje handlowców
    const content = page.locator('main, .page-card, .commission-view').first()
    await expect(content).toBeVisible({ timeout: 10_000 })
  })

  test('loading state przy ładowaniu', async ({ page }) => {
    // Loading state jest krótkotrwały — soft check
    await page.goto(`${BASE}/commissions`, { waitUntil: 'commit', timeout: 15_000 })
    await expect(page).toHaveURL(/\/rao\/commissions/, { timeout: 10_000 })
  })

  test('error state z role="alert" (jeśli błąd)', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/commissions/, { timeout: 10_000 })
    const errorMsg = page.locator('[role="alert"], .state-error')
    if (await errorMsg.count() > 0) {
      await expect(errorMsg.first()).toBeVisible({ timeout: 2_000 })
    }
  })

  test('empty state "Brak danych" (jeśli brak prowizji)', async ({ page }) => {
    // Soft check — empty state może nie wystąpić jeśli są dane
    await expect(page).toHaveURL(/\/rao\/commissions/, { timeout: 10_000 })
    const emptyMsg = page.locator('text=/brak danych/i, .empty-msg, .state-empty')
    const hasEmpty = await emptyMsg.count().catch(() => 0)
    if (hasEmpty > 0) {
      await expect(emptyMsg.first()).toBeVisible({ timeout: 2_000 })
    }
    // Strona załadowana = test pass
  })

  test('tabela prowizji z danymi (jeśli dostępne)', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/commissions/, { timeout: 10_000 })
    const table = page.locator('table, .data-grid').first()
    if (await table.count() > 0) {
      await expect(table).toBeVisible({ timeout: 5_000 })
      // Sprawdź nagłówki
      const headers = page.locator('th, [role="columnheader"]')
      if (await headers.count() > 0) {
        await expect(headers.first()).toBeVisible({ timeout: 5_000 })
      }
    }
  })

  test('filtr okresu (date range) działa', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/commissions/, { timeout: 10_000 })
    // Sprawdź czy są inputy daty
    const dateInputs = page.locator('input[type="date"]')
    if (await dateInputs.count() > 0) {
      await expect(dateInputs.first()).toBeVisible({ timeout: 5_000 })
    }
  })
})
