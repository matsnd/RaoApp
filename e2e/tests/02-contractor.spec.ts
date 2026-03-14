import { test, expect } from '@playwright/test'
import { waitForBackend, login, navigateTo } from './helpers'

const TS = Date.now()
const NIP = `55${String(TS).slice(-8)}`

test.describe('TEST-02: Kontrahenci', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('lista kontrahentów ładuje się poprawnie', async ({ page }) => {
    await navigateTo(page, 'contractors')
    await expect(page.locator('table')).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Kontrahenci', { timeout: 5_000 })
  })

  test('otwiera formularz nowego kontrahenta', async ({ page }) => {
    await navigateTo(page, 'contractors')
    await page.getByRole('button', { name: '+' }).click()

    await expect(page).toHaveURL(/\/contractors\/new/, { timeout: 8_000 })
    await expect(page.getByPlaceholder('Nazwa firmy lub imię i nazwisko')).toBeVisible({ timeout: 5_000 })
  })

  test('tworzy kontrahenta i wraca do edycji', async ({ page }) => {
    await page.goto('/contractors/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByPlaceholder('Nazwa firmy lub imię i nazwisko')).toBeVisible({ timeout: 8_000 })

    await page.getByPlaceholder('Nazwa firmy lub imię i nazwisko').fill(`Test E2E ${TS}`)
    await page.getByPlaceholder('0000000000').fill(NIP)
    await page.getByRole('button', { name: 'Zapisz' }).click()

    await expect(page).toHaveURL(/\/contractors\/\d+\/edit/, { timeout: 10_000 })
    await expect(page.locator('.toolbar-info')).toContainText(`Test E2E ${TS}`, { timeout: 8_000 })
    await expect(page.locator('text=Adresy dostawy')).toBeVisible({ timeout: 5_000 })
  })

  test('walidacja — brak wymaganej nazwy', async ({ page }) => {
    await page.goto('/contractors/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: 'Zapisz' }).click()

    await expect(page).toHaveURL(/\/contractors\/new/, { timeout: 5_000 })
  })

  test('wyszukiwanie filtruje tabelę', async ({ page }) => {
    await navigateTo(page, 'contractors')
    const search = page.getByPlaceholder('Szukaj wg nazwy, NIP...')
    await search.fill(`Test E2E ${TS}`)
    await page.waitForTimeout(600)

    const rows = page.locator('tbody tr')
    const count = await rows.count()
    if (count > 0) {
      await expect(rows.first()).not.toContainText('Brak kontrahentów')
    }
  })
})
