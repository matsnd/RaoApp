import { test, expect } from '@playwright/test'
import { waitForBackend, login, navigateTo } from './helpers'

const TS = Date.now()

test.describe('TEST-03: Artykuły', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('lista artykułów ładuje się poprawnie', async ({ page }) => {
    await navigateTo(page, 'articles')
    await expect(page.locator('table')).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Artykuły', { timeout: 5_000 })
  })

  test('otwiera formularz nowego artykułu', async ({ page }) => {
    await navigateTo(page, 'articles')
    await page.getByRole('button', { name: '+' }).click()

    await expect(page).toHaveURL(/\/articles\/new/, { timeout: 8_000 })
    await expect(page.getByPlaceholder('Np. Koparka gąsienicowa')).toBeVisible({ timeout: 5_000 })
  })

  test('tworzy artykuł i wraca do edycji', async ({ page }) => {
    await page.goto('/articles/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByPlaceholder('Np. Koparka gąsienicowa')).toBeVisible({ timeout: 8_000 })

    await page.getByPlaceholder('Np. Koparka gąsienicowa').fill(`Koparka E2E ${TS}`)
    await page.getByRole('button', { name: 'Zapisz' }).click()

    await expect(page).toHaveURL(/\/articles\/\d+\/edit/, { timeout: 10_000 })
    await expect(page.locator('.toolbar-info')).toContainText(`Koparka E2E ${TS}`, { timeout: 8_000 })
  })

  test('duplikacja artykułu tworzy kopię', async ({ page }) => {
    await page.goto('/articles/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByPlaceholder('Np. Koparka gąsienicowa').fill(`Oryginał ${TS}`)
    await page.getByRole('button', { name: 'Zapisz' }).click()
    await expect(page).toHaveURL(/\/articles\/\d+\/edit/, { timeout: 10_000 })

    const idBefore = page.url().match(/\/articles\/(\d+)\/edit/)?.[1]
    await page.locator('button[title="Duplikuj"]').click()

    await page.waitForURL(
      (url) => {
        const m = url.pathname.match(/\/articles\/(\d+)\/edit/)
        return !!m && m[1] !== idBefore
      },
      { timeout: 10_000 }
    )
    await expect(page.locator('.toolbar-info')).toContainText('kopia', { timeout: 8_000 })
  })

  test('walidacja — brak wymaganej nazwy', async ({ page }) => {
    await page.goto('/articles/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: 'Zapisz' }).click()
    await expect(page).toHaveURL(/\/articles\/new/, { timeout: 5_000 })
  })
})
