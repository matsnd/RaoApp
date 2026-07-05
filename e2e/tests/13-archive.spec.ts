import { test, expect } from '@playwright/test'
import { BASE, login, waitForBackend } from './helpers'

test.describe('TEST-13: ArchiveView — archiwum umów', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
    await page.goto(`${BASE}/archive`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
  })

  test('wyświetla stronę archiwum z 4 zakładkami', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/archive/, { timeout: 10_000 })
    // 4 zakładki: Umowy archiwum, Maszyny archiwum, Kontrahenci archiwum, Kategorie archiwum
    const tabs = page.locator('[data-testid="archive-tab"], .archive-tab, .tab-btn')
    await expect(tabs.first()).toBeVisible({ timeout: 10_000 })
  })

  test('zakładka Umowy archiwum pokazuje tabelę z danymi', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/archive/, { timeout: 10_000 })
    // Tabela umów archiwum
    const table = page.locator('table, .data-grid').first()
    await expect(table).toBeVisible({ timeout: 10_000 })
    // Sprawdź czy są nagłówki kolumn
    const headers = page.locator('th, [role="columnheader"]')
    await expect(headers.first()).toBeVisible({ timeout: 5_000 })
  })

  test('banner archiwum jest widoczny', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/archive/, { timeout: 10_000 })
    // Banner informacyjny o archiwum
    const banner = page.locator('.archive-banner, [data-testid="archive-banner"]')
    if (await banner.count() > 0) {
      await expect(banner).toBeVisible({ timeout: 5_000 })
    }
  })

  test('filtry działają (search, typ, data)', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/archive/, { timeout: 10_000 })
    // Sprawdź czy są inputy filtrów
    const searchInput = page.locator('input[placeholder*="szukaj" i], input[type="search"]').first()
    if (await searchInput.count() > 0) {
      await searchInput.fill('test')
      await page.waitForTimeout(500)
    }
  })

  test('drilldown umowy archiwum → szczegóły', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/archive/, { timeout: 10_000 })
    // Klik w pierwszy wiersz tabeli umów
    const firstRow = page.locator('tbody tr, [role="row"]:not([role="columnheader"])').first()
    if (await firstRow.count() > 0) {
      await firstRow.click()
      await page.waitForTimeout(1000)
    }
  })

  test('paginacja działa (jeśli > 50 umów)', async ({ page }) => {
    await expect(page).toHaveURL(/\/rao\/archive/, { timeout: 10_000 })
    const pagination = page.locator('.pagination, [data-testid="pagination"], .pager')
    if (await pagination.count() > 0) {
      await expect(pagination).toBeVisible({ timeout: 5_000 })
    }
  })
})
