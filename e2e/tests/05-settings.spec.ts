import { test, expect } from '@playwright/test'
import { waitForBackend, login } from './helpers'

test.describe('TEST-05: Ustawienia', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('otwiera widok ustawień', async ({ page }) => {
    await page.getByRole('button', { name: 'Ustawienia' }).click()
    await expect(page).toHaveURL(/\/settings/, { timeout: 8_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Ustawienia', { timeout: 5_000 })
  })

  test('zakładka Dane firmy ładuje dane z bazy', async ({ page }) => {
    await page.goto('/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByRole('button', { name: 'Dane firmy' })).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('text=Dane firmy').first()).toBeVisible()
    await expect(page.getByRole('button', { name: 'Zapisz dane firmy' })).toBeVisible({ timeout: 5_000 })
  })

  test('przełącza zakładki poprawnie', async ({ page }) => {
    await page.goto('/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const panel = page.locator('.panel').first()

    await panel.getByRole('button', { name: 'Handlowcy' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Handlowcy', { timeout: 5_000 })

    await panel.getByRole('button', { name: 'Kategorie' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Kategorie', { timeout: 5_000 })

    await panel.getByRole('button', { name: 'Typy stawek' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Typy stawek', { timeout: 5_000 })

    await panel.getByRole('button', { name: 'Szablony usług' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Szablony usług', { timeout: 5_000 })
  })

  test('zapisuje dane firmy bez błędu', async ({ page }) => {
    await page.goto('/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByRole('button', { name: 'Zapisz dane firmy' })).toBeVisible({ timeout: 8_000 })

    await page.getByRole('button', { name: 'Zapisz dane firmy' }).click()
    await expect(page.locator('text=\u2713 Zapisano')).toBeVisible({ timeout: 8_000 })
  })
})
