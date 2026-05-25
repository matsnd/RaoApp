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

/**
 * Generuje PDF i zapisuje do artifacts dla manual verification
 * (RAO-P1 tasks - PDF verification)
 */
export async function generateAndSavePDF(
  req: APIRequestContext,
  contractId: number,
  type: string,
  filename: string
): Promise<Buffer> {
  const token = await apiLogin(req)
  const r = await req.post(`${API}/reports/contract/${contractId}?type=${type}`, {
    headers: authHeaders(token),
    timeout: 30_000,
  })
  expect(r.status()).toBe(200)
  const buffer = await r.body()
  
  // Zapisz do artifacts
  const fs = await import('fs')
  const path = await import('path')
  const artifactsDir = path.join(process.cwd(), 'e2e', 'artifacts', 'pdfs')
  await fs.promises.mkdir(artifactsDir, { recursive: true })
  await fs.promises.writeFile(path.join(artifactsDir, filename), buffer)
  
  return buffer
}

/**
 * Quick add contractor z picker (RAO-P2-005)
 */
export async function quickAddContractor(
  page: Page,
  data: { name: string; nip: string; address?: string }
): Promise<void> {
  // Kliknij "➕ Dodaj nowego kontrahenta"
  await page.getByRole('button', { name: /dodaj nowego kontrahenta/i }).click()
  
  // Wypełnij modal
  await page.getByPlaceholder(/nazwa/i).fill(data.name)
  await page.getByPlaceholder(/nip/i).fill(data.nip)
  if (data.address) {
    await page.getByPlaceholder(/adres/i).fill(data.address)
  }
  
  // Zapisz
  await page.getByRole('button', { name: /zapisz/i }).click()
  
  // Sprawdź toast
  await expect(page.locator('.toast-success')).toContainText('utworzony')
}

/**
 * Quick add article z picker (RAO-P2-006)
 */
export async function quickAddArticle(
  page: Page,
  data: { name: string; serial_number?: string; category?: string }
): Promise<void> {
  await page.getByRole('button', { name: /dodaj nową maszynę/i }).click()
  await page.getByPlaceholder(/nazwa/i).fill(data.name)
  if (data.serial_number) {
    await page.getByPlaceholder(/numer seryjny/i).fill(data.serial_number)
  }
  if (data.category) {
    await page.getByRole('combobox', { name: /kategoria/i }).selectOption(data.category)
  }
  await page.getByRole('button', { name: /zapisz/i }).click()
  await expect(page.locator('.toast-success')).toContainText('utworzony')
}

/**
 * Tworzy umowę z kaskadowymi warunkami (RAO-P1-008)
 */
export async function createContractWithCascadingConditions(
  req: APIRequestContext,
  contractorId: number,
  conditions: Array<{ period_count?: number; rate1?: number; rate2?: number; billing_label: string }>
): Promise<number> {
  const token = await apiLogin(req)
  
  // 1. Utwórz umowę
  const ctr = await req.post(`${API}/contracts`, {
    headers: authHeaders(token),
    data: { contractor_id: contractorId, contract_type: 'S', date_from: new Date().toISOString().slice(0, 10) },
  })
  const contract = await ctr.json()
  
  // 2. Utwórz artykuł
  const ts = Date.now()
  const ar = await req.post(`${API}/articles`, {
    headers: authHeaders(token),
    data: { name: `TestArt ${ts}`, is_service: false },
  })
  const article = await ar.json()
  
  // 3. Utwórz pozycję
  const pos = await req.post(`${API}/contracts/${contract.id}/positions`, {
    headers: authHeaders(token),
    data: { article_id: article.id, quantity: 1 },
  })
  const position = await pos.json()
  
  // 4. Dodaj warunki kaskadowe
  for (const cond of conditions) {
    await req.post(`${API}/contracts/${contract.id}/positions/${position.id}/conditions`, {
      headers: authHeaders(token),
      data: { ...cond, rate_type_id: 1 }, // Zakładamy rate_type_id=1 dla "dobowa"
    })
  }
  
  return contract.id
}
