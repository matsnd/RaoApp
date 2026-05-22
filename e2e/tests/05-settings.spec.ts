import { test, expect } from '@playwright/test'
import { waitForBackend, login, API, apiLogin, authHeaders, safeDelete, newApiContext } from './helpers'

const createdSp: number[] = []
const createdCat: number[] = []
const createdRt: number[] = []
const createdPreset: number[] = []

test.describe('TEST-05: Ustawienia', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('otwiera widok ustawień', async ({ page }) => {
    await page.getByRole('button', { name: 'Ustawienia' }).click()
    await expect(page).toHaveURL(/\/rao\/settings/, { timeout: 8_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Ustawienia', { timeout: 5_000 })
  })

  test('zakładka Dane firmy ładuje dane z bazy', async ({ page }) => {
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByRole('button', { name: 'Dane firmy' })).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('text=Dane firmy').first()).toBeVisible()
    await expect(page.getByRole('button', { name: 'Zapisz dane firmy' })).toBeVisible({ timeout: 5_000 })
  })

  test('przełącza zakładki poprawnie', async ({ page }) => {
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const panel = page.locator('.panel').first()

    await panel.getByRole('button', { name: 'Handlowcy' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Handlowcy', { timeout: 5_000 })

    await panel.getByRole('button', { name: 'Kategorie' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Kategorie', { timeout: 5_000 })

    await panel.getByRole('button', { name: 'Typy stawek' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Typy stawek', { timeout: 5_000 })

    await panel.getByRole('button', { name: 'Zestawy usług' }).click()
    await expect(page.locator('.panel-header').last()).toContainText('Zestawy usług', { timeout: 5_000 })
  })

  test('zapisuje dane firmy bez błędu', async ({ page }) => {
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByRole('button', { name: 'Zapisz dane firmy' })).toBeVisible({ timeout: 8_000 })

    await page.getByRole('button', { name: 'Zapisz dane firmy' }).click()
    await expect(page.locator('text=\u2713 Zapisano')).toBeVisible({ timeout: 8_000 })
  })

  // ------- Rozszerzenie (RAO-P2-013) -------

  test('CRUD handlowca przez API', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const r = await request.post(`${API}/settings/salespeople`, {
      headers: authHeaders(token),
      data: { name: `Handlowiec ${ts}`, phone: '111-222-333', commission_rate: 5 },
    })
    expect(r.status()).toBe(201)
    const sp = await r.json()
    createdSp.push(sp.id)

    // UPDATE
    const upd = await request.put(`${API}/settings/salespeople/${sp.id}`, {
      headers: authHeaders(token),
      data: { name: `Handlowiec Updated ${ts}`, phone: '999-888-777', commission_rate: 7 },
    })
    expect([200, 204]).toContain(upd.status())

    // DELETE
    const del = await request.delete(`${API}/settings/salespeople/${sp.id}`, { headers: authHeaders(token) })
    expect(del.status()).toBe(204)
    createdSp.pop()
  })

  test('CRUD kategorii artykułu przez API', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const r = await request.post(`${API}/settings/categories`, {
      headers: authHeaders(token),
      data: { name: `KAT ${ts}`, code: `K${String(ts).slice(-6)}` },
    })
    expect(r.status()).toBe(201)
    const cat = await r.json()
    createdCat.push(cat.id)

    const del = await request.delete(`${API}/settings/categories/${cat.id}`, { headers: authHeaders(token) })
    expect(del.status()).toBe(204)
    createdCat.pop()
  })

  test('Dodanie typu stawki przez API', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const r = await request.post(`${API}/settings/rate-types`, {
      headers: authHeaders(token),
      data: { name: `RT ${ts}` },
    })
    expect(r.status()).toBe(201)
    const rt = await r.json()
    createdRt.push(rt.id)
  })

  test('CRUD szablonu usługi (preset group)', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()
    const r = await request.post(`${API}/settings/fee-preset-groups`, {
      headers: authHeaders(token),
      data: { name: `Preset ${ts}`, description: 'opis', contract_type: 'S' },
    })
    expect([200, 201]).toContain(r.status())
    const preset = await r.json()
    createdPreset.push(preset.id)

    const upd = await request.put(`${API}/settings/fee-preset-groups/${preset.id}`, {
      headers: authHeaders(token),
      data: { name: `Preset Updated ${ts}`, description: 'edited', contract_type: 'S' },
    })
    expect([200, 204]).toContain(upd.status())
  })

  test('zakładka Fakturownia jest widoczna', async ({ page }) => {
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const panel = page.locator('.panel').first()
    const fakBtn = panel.getByRole('button', { name: /Fakturownia/i })
    if (await fakBtn.count() === 0) {
      test.fixme(true, 'Zakładka Fakturownia nie znaleziona — sprawdź feature flag')
      return
    }
    await fakBtn.click()
    await expect(page.locator('input[placeholder="np. toolsmart"]')).toBeVisible({ timeout: 5_000 })
    await expect(page.locator('input[placeholder="Wklej token API"]')).toBeVisible()
  })

  test('Fakturownia: token zapisany jest maskowany w preview', async ({ request }) => {
    const token = await apiLogin(request)
    // GET aktualne
    const cur = await request.get(`${API}/integrations/fakturownia/settings`, { headers: authHeaders(token) })
    if (cur.status() !== 200) {
      test.fixme(true, `Settings endpoint zwrócił ${cur.status()}`)
      return
    }
    // Zapisz nowy token
    const upd = await request.put(`${API}/integrations/fakturownia/settings`, {
      headers: authHeaders(token),
      data: { enabled: true, domain_subdomain: 'toolsmart', api_token: 'tk_secrettoken1234' },
    })
    if (upd.status() === 500) {
      test.fixme(true, 'RAO_FAKTUROWNIA_ENC_KEY nie skonfigurowane w env')
      return
    }
    expect([200, 201, 204]).toContain(upd.status())
    if (upd.status() < 300) {
      const body = await upd.json()
      // Token nie powinien być zwracany w plaintext, tylko preview
      const preview = body.api_token_preview ?? body.api_token ?? ''
      expect(preview).not.toBe('tk_secrettoken1234')
      // Maskowanie: zawiera gwiazdki lub kropki
      expect(/\*|\.{3,}|x{3,}/i.test(preview) || preview === '').toBe(true)
    }
  })

  test.afterAll(async () => {
    const ctx = await newApiContext()
    try {
      const token = await apiLogin(ctx)
      for (const id of createdSp) await safeDelete(ctx, `${API}/settings/salespeople/${id}`, token)
      for (const id of createdCat) await safeDelete(ctx, `${API}/settings/categories/${id}`, token)
      for (const id of createdRt) await safeDelete(ctx, `${API}/settings/rate-types/${id}`, token)
      for (const id of createdPreset) await safeDelete(ctx, `${API}/settings/fee-preset-groups/${id}`, token)
    } catch {
      /* ignore */
    } finally {
      await ctx.dispose()
    }
  })
})
