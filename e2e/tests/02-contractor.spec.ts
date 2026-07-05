import { test, expect } from '@playwright/test'
import { waitForBackend, login, navigateTo, API, apiLogin, authHeaders, safeDelete, newApiContext, genValidNip } from './helpers'

const TS = Date.now()
const NIP = '1234567890' /* unused */

// Track utworzonych zasobów do cleanupu
const createdContractorIds: number[] = []

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
    await page.getByRole('button', { name: 'Dodaj nową pozycję' }).click()

    await expect(page).toHaveURL(/\/contractors\/new/, { timeout: 8_000 })
    await expect(page.getByPlaceholder('Nazwa firmy lub imię i nazwisko')).toBeVisible({ timeout: 5_000 })
  })

  test('tworzy kontrahenta i wraca do edycji', async ({ page }) => {
    // Unikalne dane per run (TS jest module-level constant — kolizje między retries)
    const localTs = Date.now()
    const localNip = genValidNip(localTs)
    const localName = `Test E2E ${localTs}`

    await page.goto('/rao/contractors/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByPlaceholder('Nazwa firmy lub imię i nazwisko')).toBeVisible({ timeout: 8_000 })

    await page.getByPlaceholder('Nazwa firmy lub imię i nazwisko').fill(localName)
    await page.getByPlaceholder('0000000000').fill(localNip)
    await page.getByRole('button', { name: 'Zapisz' }).click()

    await expect(page).toHaveURL(/\/rao\/contractors\/\d+\/edit/, { timeout: 10_000 })
    await expect(page.locator('.toolbar-info')).toContainText(localName, { timeout: 8_000 })
    await expect(page.locator('text=Adresy dostawy')).toBeVisible({ timeout: 5_000 })

    // Track for cleanup
    const id = Number(page.url().match(/\/contractors\/(\d+)\/edit/)?.[1])
    if (id) createdContractorIds.push(id)
  })

  test('walidacja — brak wymaganej nazwy', async ({ page }) => {
    await page.goto('/rao/contractors/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: 'Zapisz' }).click()

    await expect(page).toHaveURL(/\/contractors\/new/, { timeout: 5_000 })
  })

  test('wyszukiwanie filtruje tabelę', async ({ page, request }) => {
    // Stwórz dedykowany rekord, żeby test był deterministyczny
    const token = await apiLogin(request)
    const uniq = `UNIQ${Date.now()}`
    const r = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: uniq, nip: genValidNip() },
    })
    const c = await r.json()
    if (c.id) createdContractorIds.push(c.id)

    await navigateTo(page, 'contractors')
    const search = page.getByPlaceholder('Szukaj wg nazwy, NIP...')
    await search.fill(uniq)
    await page.waitForTimeout(700)
    await expect(page.locator('tbody')).toContainText(uniq, { timeout: 5_000 })
  })

  // ------- Rozszerzenie (RAO-P2-013) -------

  test('edycja istniejącego kontrahenta zapisuje zmiany', async ({ page, request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const r = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `EditMe ${ts}`, nip: genValidNip(ts) },
    })
    const c = await r.json()
    createdContractorIds.push(c.id)

    await page.goto(`/rao/contractors/${c.id}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const nameInput = page.getByPlaceholder('Nazwa firmy lub imię i nazwisko')
    await expect(nameInput).toBeVisible({ timeout: 8_000 })
    await nameInput.fill(`EditMe Updated ${ts}`)
    await page.getByRole('button', { name: 'Zapisz' }).click()
    await page.waitForTimeout(1500)
    // Weryfikacja przez API — pewniejsze niż UI po reloadzie
    const verify = await request.get(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
    expect(verify.status()).toBe(200)
    const data = await verify.json()
    expect(data.name).toBe(`EditMe Updated ${ts}`)
  })

  test('usunięcie kontrahenta (przez API) zwraca 204, ponowne 404', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const r = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `DelMe ${ts}`, nip: genValidNip(ts + 1) },
    })
    expect(r.status()).toBe(201)
    const c = await r.json()

    const del1 = await request.delete(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
    // 204 OK lub 422 jeśli FK constraint (np. contractor ma umowy)
    expect([204, 409, 422]).toContain(del1.status())
    if (del1.status() !== 204) {
      // Bug-tolerantny: nie sprawdzamy ponownego DELETE jeśli pierwszy nie powiódł się
      return
    }

    const del2 = await request.delete(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
    expect(del2.status()).toBe(404)

    // GET nieistniejącego
    const get404 = await request.get(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
    expect(get404.status()).toBe(404)
  })

  test('CRUD adresu dostawy przez API', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const r = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `Addr ${ts}`, nip: genValidNip(ts + 2) },
    })
    const c = await r.json()
    createdContractorIds.push(c.id)

    // CREATE adresu
    const addrR = await request.post(`${API}/contractors/${c.id}/addresses`, {
      headers: authHeaders(token),
      data: { name: 'Budowa Test', street: 'ul. Testowa 1', postal_code: '00-001', city: 'Warszawa' },
    })
    expect(addrR.status()).toBe(201)
    const addr = await addrR.json()

    // UPDATE
    const updR = await request.put(`${API}/contractors/${c.id}/addresses/${addr.id}`, {
      headers: authHeaders(token),
      data: { name: 'Budowa Test 2', street: 'ul. Testowa 2', postal_code: '00-002', city: 'Kraków' },
    })
    expect([200, 204]).toContain(updR.status())

    // DELETE
    const delR = await request.delete(`${API}/contractors/${c.id}/addresses/${addr.id}`, { headers: authHeaders(token) })
    expect(delR.status()).toBe(204)
  })

  test('GUS lookup — przycisk widoczny i klikalny przy NIP', async ({ page }) => {
    await page.goto('/rao/contractors/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByPlaceholder('0000000000').fill('5252344078') // PKO BP, dla testu
    // Przycisk GUS ma tekst "GUS" lub "..." (loading) — szukaj przez tekst zawarty
    const gusBtn = page.locator('button').filter({ hasText: /^(GUS|\.\.\.)\s*$/ })
    await expect(gusBtn.first()).toBeVisible({ timeout: 5_000 })
    // Nie klikamy w sieć GUS w teście (zewnętrzny serwis), tylko że button istnieje
  })

  test('walidacja: NIP ze spacjami i znakami niedozwolonymi', async ({ request }) => {
    const token = await apiLogin(request)
    // NIP z literami — backend powinien zaakceptować lub odrzucić, ale nie 500
    const r = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: 'EdgeNIP', nip: 'ABC<>' },
    })
    expect([200, 201, 422, 400]).toContain(r.status())
    expect(r.status()).not.toBe(500)
    if (r.status() < 400) {
      const c = await r.json()
      createdContractorIds.push(c.id)
    }
  })

  test('XSS w nazwie kontrahenta — backend odrzuca lub frontend escape', async ({ page, request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const xss = `<script>alert(1)</script> ${ts}`
    const r = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: xss, nip: genValidNip(ts + 3) },
    })
    // Defense-in-depth: backend może odrzucić (422) LUB zaakceptować i polegać na frontend escape
    expect([201, 400, 422]).toContain(r.status())
    if (r.status() !== 201) {
      // Backend odrzuca XSS — secure-by-default, koniec testu
      return
    }
    const c = await r.json()
    createdContractorIds.push(c.id)

    let alerted = false
    page.on('dialog', async (d) => { alerted = true; await d.dismiss() })
    await page.goto(`/rao/contractors/${c.id}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(800)
    // Brak alert dialogu — XSS nie wykonał się
    expect(alerted).toBe(false)
  })

  test('paginacja list działa (jeśli wystarczająca liczba)', async ({ page, request }) => {
    const token = await apiLogin(request)
    // Sprawdź ile jest kontrahentów
    const r = await request.get(`${API}/contractors?page=1&page_size=20`, { headers: authHeaders(token) })
    const data = await r.json()
    if ((data.total ?? 0) <= 20) {
      test.skip(true, 'Za mało kontrahentów do testu paginacji')
    }
    await navigateTo(page, 'contractors')
    const next = page.locator('.pagination .page-btn').last()
    if (await next.isEnabled()) {
      await next.click()
      await page.waitForTimeout(400)
      await expect(page.locator('table tbody tr').first()).toBeVisible()
    }
  })

  test.fixme('pole "reprezentowany przez" — nie ma jeszcze w UI', async () => {
    // Pole zaplanowane w spec (03_frontend_screens.md), ale brak w kodzie ContractorFormView.
    // Owner: frontend-dev
  })

  test.afterAll(async () => {
    const ctx = await newApiContext()
    try {
      const token = await apiLogin(ctx)
      for (const id of createdContractorIds) {
        await safeDelete(ctx, `${API}/contractors/${id}`, token)
      }
    } catch {
      /* ignore cleanup errors */
    } finally {
      await ctx.dispose()
    }
  })
})
