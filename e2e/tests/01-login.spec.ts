import { test, expect } from '@playwright/test'
import { waitForBackend, login } from './helpers'

test.describe('TEST-01: Logowanie', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
  })

  test('przekierowanie na /login gdy brak sesji', async ({ page }) => {
    await page.goto('/rao/', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page).toHaveURL(/\/rao\/login/, { timeout: 8_000 })
  })

  test('wyświetla formularz logowania', async ({ page }) => {
    await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('h2')).toContainText('Logowanie', { timeout: 8_000 })
    await expect(page.getByPlaceholder('Podaj login')).toBeVisible()
    await expect(page.getByPlaceholder('Podaj hasło')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Zaloguj się' })).toBeVisible()
  })

  test('błąd przy złych danych', async ({ page }) => {
    await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByPlaceholder('Podaj login').fill('bledny_user')
    await page.getByPlaceholder('Podaj hasło').fill('zle_haslo')
    await page.getByRole('button', { name: 'Zaloguj się' }).click()

    await expect(page.locator('.form-error')).toBeVisible({ timeout: 8_000 })
    await expect(page).toHaveURL(/\/rao\/login/, { timeout: 5_000 })
  })

  test('poprawne logowanie → dashboard', async ({ page }) => {
    await login(page)

    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
    await expect(page.locator('nav')).toBeVisible({ timeout: 5_000 })
    await expect(page.getByRole('button', { name: 'Umowy', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Kontrahenci', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Artykuły', exact: true })).toBeVisible()
  })

  test('wylogowanie czyści sesję', async ({ page }) => {
    await login(page)
    await page.getByRole('button', { name: 'Wyloguj' }).click()

    await expect(page).toHaveURL(/\/login/, { timeout: 8_000 })
    await expect(page.getByPlaceholder('Podaj login')).toBeVisible()
  })

  // ------- Rozszerzenie (RAO-P2-013) -------

  test('przycisk Zaloguj się jest disabled w trakcie logowania (spinner)', async ({ page }) => {
    await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByPlaceholder('Podaj login').fill('admin')
    await page.getByPlaceholder('Podaj hasło').fill('admin123')

    // Throttle network — żeby spinner zdążył się pojawić
    await page.route('**/auth/login', async (route) => {
      await new Promise((r) => setTimeout(r, 300))
      await route.continue()
    })

    const btn = page.getByRole('button', { name: /Zaloguj się|^$/ })
    await btn.click()
    // W trakcie loadingu przycisk ma atrybut disabled (spinner zamiast tekstu)
    await expect(page.locator('button[type="submit"][disabled]')).toBeVisible({ timeout: 2_000 })
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
  })

  test('Enter w polu hasła submittuje formularz', async ({ page }) => {
    await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByPlaceholder('Podaj login').fill('admin')
    await page.getByPlaceholder('Podaj hasło').fill('admin123')
    await page.getByPlaceholder('Podaj hasło').press('Enter')
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
  })

  test('po zalogowaniu w localStorage jest token JWT', async ({ page }) => {
    await login(page)
    const token = await page.evaluate(() => localStorage.getItem('rao_token'))
    expect(token).toBeTruthy()
    // JWT ma trzy segmenty oddzielone kropką
    expect(token!.split('.').length).toBe(3)
    const user = await page.evaluate(() => localStorage.getItem('rao_user'))
    expect(user).toContain('admin')
  })

  test('odświeżenie strony zachowuje sesję', async ({ page }) => {
    await login(page)
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 8_000 })
    await expect(page.locator('nav')).toBeVisible({ timeout: 5_000 })
  })

  test('wejście na /rao/ zalogowanego usera → /rao/home', async ({ page }) => {
    await login(page)
    await page.goto('/rao/', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page).toHaveURL(/\/rao\/home/, { timeout: 8_000 })
  })

  test('wejście na /rao/login zalogowanego usera → przekierowanie', async ({ page }) => {
    await login(page)
    await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    // Auth guard: zalogowany user nie może wejść na /login
    await expect(page).not.toHaveURL(/\/rao\/login$/, { timeout: 8_000 })
  })
})
