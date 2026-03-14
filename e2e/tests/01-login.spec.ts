import { test, expect } from '@playwright/test'
import { waitForBackend, login } from './helpers'

test.describe('TEST-01: Logowanie', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
  })

  test('przekierowanie na /login gdy brak sesji', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page).toHaveURL(/\/login/, { timeout: 8_000 })
  })

  test('wyświetla formularz logowania', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('h2')).toContainText('Logowanie', { timeout: 8_000 })
    await expect(page.getByPlaceholder('Podaj login')).toBeVisible()
    await expect(page.getByPlaceholder('Podaj hasło')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Zaloguj się' })).toBeVisible()
  })

  test('błąd przy złych danych', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByPlaceholder('Podaj login').fill('bledny_user')
    await page.getByPlaceholder('Podaj hasło').fill('zle_haslo')
    await page.getByRole('button', { name: 'Zaloguj się' }).click()

    await expect(page.locator('.form-error')).toBeVisible({ timeout: 8_000 })
    await expect(page).toHaveURL(/\/login/, { timeout: 5_000 })
  })

  test('poprawne logowanie → dashboard', async ({ page }) => {
    await login(page)

    await expect(page).toHaveURL(/\/dashboard\/contracts/, { timeout: 10_000 })
    await expect(page.locator('nav')).toBeVisible({ timeout: 5_000 })
    await expect(page.getByRole('button', { name: 'Umowy' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Kontrahenci' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Artykuły' })).toBeVisible()
  })

  test('wylogowanie czyści sesję', async ({ page }) => {
    await login(page)
    await page.getByRole('button', { name: 'Wyloguj' }).click()

    await expect(page).toHaveURL(/\/login/, { timeout: 8_000 })
    await expect(page.getByPlaceholder('Podaj login')).toBeVisible()
  })
})
