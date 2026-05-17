import { Page, expect } from '@playwright/test'

export const BASE = 'http://localhost:5174/rao'
export const API  = 'http://localhost:8001/rao/api'
export const CREDS = { login: 'admin', password: 'admin123' }

export async function waitForBackend(page: Page) {
  const deadline = Date.now() + 10_000
  while (Date.now() < deadline) {
    try {
      const res = await page.request.get(`${API}/health`, { timeout: 2_000 })
      if (res.ok()) return
    } catch {}
    await page.waitForTimeout(500)
  }
  throw new Error('Backend nie odpowiada po 10 s')
}

export async function login(page: Page) {
  await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
  await expect(page.locator('h2')).toContainText('Logowanie', { timeout: 8_000 })

  await page.getByPlaceholder('Podaj login').fill(CREDS.login)
  await page.getByPlaceholder('Podaj hasło').fill(CREDS.password)
  await page.getByRole('button', { name: 'Zaloguj się' }).click()

  await expect(page).toHaveURL(/\/rao\/home/, { timeout: 10_000 })
  await expect(page.locator('nav')).toBeVisible({ timeout: 5_000 })
}

export async function navigateTo(page: Page, section: 'contracts' | 'contractors' | 'articles') {
  const labels: Record<string, string> = {
    contracts: 'Umowy',
    contractors: 'Kontrahenci',
    articles: 'Artykuły',
  }
  await page.getByRole('button', { name: labels[section], exact: true }).click()
  await expect(page).toHaveURL(new RegExp(`/rao/dashboard/${section}`), { timeout: 8_000 })
}
