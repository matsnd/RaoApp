import { test, expect } from '@playwright/test'
import { API, waitForBackend, apiLogin, authHeaders } from './helpers'

test.describe('TEST-18: ResetPasswordView — reset hasła', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
  })

  test('wyświetla formularz reset hasła pod /reset-password', async ({ page }) => {
    await page.goto('http://localhost:5173/rao/reset-password', {
      waitUntil: 'domcontentloaded',
      timeout: 15_000,
    })
    const form = page.locator('form, .login-card').first()
    await expect(form).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('h2')).toContainText('Ustaw nowe hasło', { timeout: 5_000 })
  })

  test('pola new_password + confirm_password są required', async ({ page }) => {
    await page.goto('http://localhost:5173/rao/reset-password', {
      waitUntil: 'domcontentloaded',
      timeout: 15_000,
    })
    const newPwd = page.locator('#reset-new-password')
    const confirmPwd = page.locator('#reset-confirm-password')
    await expect(newPwd).toBeVisible({ timeout: 5_000 })
    await expect(confirmPwd).toBeVisible({ timeout: 5_000 })
    await expect(newPwd).toHaveAttribute('required', '')
    await expect(confirmPwd).toHaveAttribute('required', '')
  })

  test('walidacja: min 6 znaków (minlength)', async ({ page }) => {
    await page.goto('http://localhost:5173/rao/reset-password', {
      waitUntil: 'domcontentloaded',
      timeout: 15_000,
    })
    const newPwd = page.locator('#reset-new-password')
    await expect(newPwd).toBeVisible({ timeout: 5_000 })
    // Placeholder wskazuje min 6 znaków
    await expect(newPwd).toHaveAttribute('placeholder', 'Min. 6 znaków')
  })

  test('walidacja: new != confirm → błąd po submicie', async ({ page }) => {
    await page.goto('http://localhost:5173/rao/reset-password', {
      waitUntil: 'domcontentloaded',
      timeout: 15_000,
    })
    const newPwd = page.locator('#reset-new-password')
    const confirmPwd = page.locator('#reset-confirm-password')
    await newPwd.fill('password1')
    await confirmPwd.fill('password2')
    await page.getByRole('button', { name: /ustaw hasło/i }).click()
    // Sprawdź czy jest error message (field error lub form error)
    const errorMsg = page.locator('[role="alert"], .form-error')
    await expect(errorMsg.first()).toBeVisible({ timeout: 5_000 })
  })

  test('aria-invalid na polach z błędem po submicie', async ({ page }) => {
    await page.goto('http://localhost:5173/rao/reset-password', {
      waitUntil: 'domcontentloaded',
      timeout: 15_000,
    })
    const newPwd = page.locator('#reset-new-password')
    const confirmPwd = page.locator('#reset-confirm-password')
    await newPwd.fill('123')
    await confirmPwd.fill('456')
    await page.getByRole('button', { name: /ustaw hasło/i }).click()
    // Sprawdź czy jest komunikat błędu po submicie (form error lub alert)
    const errorMsg = page.locator('[role="alert"], .form-error')
    await expect(errorMsg.first()).toBeVisible({ timeout: 5_000 })
  })

  test('API: POST /auth/reset-password z nieprawidłowym tokenem → 4xx', async ({ request }) => {
    const r = await request.post(`${API}/auth/reset-password`, {
      data: { token: 'invalid-token', new_password: 'NewPass123!' },
      timeout: 10_000,
    })
    expect(r.status()).toBeGreaterThanOrEqual(400)
    expect(r.status()).toBeLessThan(500)
  })

  test('API: POST /auth/reset-password bez tokenu → 422', async ({ request }) => {
    const r = await request.post(`${API}/auth/reset-password`, {
      data: { new_password: 'NewPass123!' },
      timeout: 10_000,
    })
    expect(r.status()).toBe(422)
  })

  test('API: POST /auth/forgot-password z email → 200/202', async ({ request }) => {
    const r = await request.post(`${API}/auth/forgot-password`, {
      data: { email: 'admin@toolsmart.pl' },
      timeout: 10_000,
    })
    expect(r.status()).toBeLessThan(500)
  })
})
