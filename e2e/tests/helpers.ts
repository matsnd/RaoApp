import { APIRequestContext, Page, expect, request } from '@playwright/test'

export const BASE = 'http://localhost:5173/rao'
export const API  = 'http://localhost:8000/rao/api'
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

/**
 * Pobiera token JWT przez API. Pozwala na operacje cleanup poza kontekstem przeglądarki.
 */
export async function apiLogin(req: APIRequestContext): Promise<string> {
  const res = await req.post(`${API}/auth/login`, { data: CREDS, timeout: 10_000 })
  if (!res.ok()) throw new Error(`apiLogin failed: ${res.status()}`)
  const { access_token } = await res.json()
  return access_token
}

export function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` }
}

/**
 * Cleanup helper: best-effort delete (ignoruje 404 / błędy).
 */
export async function safeDelete(
  req: APIRequestContext,
  url: string,
  token: string,
): Promise<void> {
  try {
    await req.delete(url, { headers: authHeaders(token), timeout: 10_000 })
  } catch {
    /* ignore */
  }
}

/**
 * Tworzy świeży API context (bez stanu przeglądarki) — przydatny w afterAll hook.
 */
export async function newApiContext(): Promise<APIRequestContext> {
  return await request.newContext({ baseURL: API })
}

/**
 * Generuje poprawny NIP (z poprawną sumą kontrolną) dla testów.
 * Pierwsze 9 cyfr są pseudolosowe na bazie seed; 10-ta cyfra to checksum.
 * Backend RAO waliduje checksum NIP-u (Pydantic validator).
 */
export function genValidNip(seed?: number): string {
  const s = seed ?? Date.now()
  // 9 cyfr jako baza
  const base = String(s).padStart(9, '0').slice(-9)
  const weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
  let sum = 0
  for (let i = 0; i < 9; i++) sum += parseInt(base[i], 10) * weights[i]
  const check = sum % 11
  if (check === 10) {
    // Suma 10 nie jest dozwolona — spróbuj z innym seedem
    return genValidNip(s + 1)
  }
  return base + String(check)
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
