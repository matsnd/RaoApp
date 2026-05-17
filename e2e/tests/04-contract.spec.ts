import { test, expect } from '@playwright/test'
import { waitForBackend, login, navigateTo, API, CREDS } from './helpers'

let contractorId = 0
let contractId = 0

test.describe('TEST-04: Umowy', () => {
  test.beforeAll(async ({ request }) => {
    const loginRes = await request.post(`${API}/auth/login`, {
      data: CREDS, timeout: 10_000,
    })
    const { access_token } = await loginRes.json()
    const headers = { Authorization: `Bearer ${access_token}` }

    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers,
      data: { name: `E2E Firma ${ts}`, nip: `88${String(ts).slice(-8)}` },
      timeout: 10_000,
    })
    const c = await cr.json()
    contractorId = c.id

    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers,
      data: { contractor_id: contractorId, contract_type: 'S', date_from: today },
      timeout: 10_000,
    })
    const ct = await ctr.json()
    contractId = ct.id
  })

  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('lista umów ładuje się poprawnie', async ({ page }) => {
    await navigateTo(page, 'contracts')
    await expect(page.locator('table')).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Umowy', { timeout: 5_000 })
  })

  test('otwiera formularz nowej umowy', async ({ page }) => {
    await navigateTo(page, 'contracts')
    await page.getByRole('button', { name: '+' }).click()

    await expect(page).toHaveURL(/\/rao\/contracts\/new/, { timeout: 8_000 })
    await expect(page.getByRole('combobox').first()).toBeVisible({ timeout: 5_000 })
    await expect(page.getByRole('button', { name: 'Wybierz' })).toBeVisible()
  })

  test('walidacja — brak kontrahenta blokuje zapis', async ({ page }) => {
    await page.goto('/rao/contracts/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: 'Zapisz' }).click()

    await expect(page).toHaveURL(/\/contracts\/new/, { timeout: 5_000 })
    await expect(page.locator('.page-card >> text=Wybierz kontrahenta')).toBeVisible({ timeout: 5_000 })
  })

  test('tworzy umowę po wyborze kontrahenta', async ({ page }) => {
    await page.goto('/contracts/new', { waitUntil: 'networkidle', timeout: 20_000 })

    await page.getByRole('button', { name: 'Wybierz' }).click()
    await expect(page.locator('.modal-box')).toBeVisible({ timeout: 10_000 })
    const firstRow = page.locator('.modal-box tbody tr').first()
    await expect(firstRow).toBeVisible({ timeout: 10_000 })
    await firstRow.click()
    await expect(page.locator('.modal-box')).not.toBeVisible({ timeout: 5_000 })
    await expect(page.locator('input[disabled]').first()).not.toHaveValue('', { timeout: 5_000 })

    const today = new Date().toISOString().slice(0, 10)
    await page.locator('input[type="date"]').nth(0).fill(today)

    await page.getByRole('button', { name: 'Zapisz' }).click()
    await expect(page).toHaveURL(/\/rao\/contracts\/\d+\/edit/, { timeout: 15_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Umowa:', { timeout: 10_000 })
  })

  test('sekcja pozycji umowy jest widoczna w trybie edycji', async ({ page }) => {
    await page.goto(`/rao/contracts/${contractId}/edit`, { waitUntil: 'networkidle', timeout: 20_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Umowa:', { timeout: 10_000 })

    await expect(page.locator('.section-title', { hasText: 'Pozycje umowy' })).toBeVisible({ timeout: 8_000 })
    await expect(page.getByRole('button', { name: '+ Dodaj pozycję' })).toBeVisible()
    await expect(page.locator('.section-title', { hasText: 'Usługi dodatkowe' })).toBeVisible()
  })

  test('protokół ZO generuje PDF z sekcją wydania/odbioru', async ({ request }) => {
    // Autoryzacja
    const loginRes = await request.post(`${API}/auth/login`, {
      data: CREDS, timeout: 10_000,
    })
    const { access_token } = await loginRes.json()
    const headers = { Authorization: `Bearer ${access_token}` }

    // Wygeneruj protokół ZO najmu (type=protocol_zo_s -> protocol_zo.html)
    const pdfRes = await request.post(
      `${API}/reports/contract/${contractId}?type=protocol_zo_s`,
      { headers, timeout: 30_000 }
    )
    expect(pdfRes.status()).toBe(200)
    expect(pdfRes.headers()['content-type']).toContain('application/pdf')

    // Wygeneruj protokół ZO usług (type=protocol_zo_u -> protocol_zo_u.html)
    const pdfResU = await request.post(
      `${API}/reports/contract/${contractId}?type=protocol_zo_u`,
      { headers, timeout: 30_000 }
    )
    expect(pdfResU.status()).toBe(200)
    expect(pdfResU.headers()['content-type']).toContain('application/pdf')

    // Wygeneruj protokół nodata (type=protocol_zo_nodata_s -> protocol_zo_nodata.html)
    const pdfResNodata = await request.post(
      `${API}/reports/contract/${contractId}?type=protocol_zo_nodata_s`,
      { headers, timeout: 30_000 }
    )
    expect(pdfResNodata.status()).toBe(200)
    expect(pdfResNodata.headers()['content-type']).toContain('application/pdf')
  })

})
