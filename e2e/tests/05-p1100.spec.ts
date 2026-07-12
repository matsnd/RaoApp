import { test, expect } from '@playwright/test'
import { waitForBackend, login, API, CREDS, apiLogin, authHeaders, safeDelete, genValidNip } from './helpers'

let contractorId = 0
let equipmentMachineId = 0  // Faza 5: było equipmentArticleId
let serviceId = 0           // Faza 5: było serviceArticleId (is_service: true → /services)
let sContractId = 0
let uContractId = 0
let sPositionId = 0
let uPositionId = 0
let ratePresetId = 0
const createdContracts: number[] = []
const createdContractors: number[] = []
const createdMachines: number[] = []   // Faza 5: było createdArticles
const createdServices: number[] = []   // Faza 5: usługi przez /services
const createdRatePresets: number[] = []

test.describe('TEST-05-P1-100: Opłaty dodatkowe, warunki, cennik, przedpłata, tryb usługi', () => {
  test.beforeAll(async ({ request }) => {
    const loginRes = await request.post(`${API}/auth/login`, { data: CREDS, timeout: 10_000 })
    if (!loginRes.ok()) throw new Error('beforeAll login failed')
    const { access_token } = await loginRes.json()
    const headers = { Authorization: `Bearer ${access_token}` }
    const ts = Date.now()

    const cr = await request.post(`${API}/contractors`, { headers, data: { name: `E2E P1-100 ${ts}`, nip: genValidNip(ts) }, timeout: 10_000 })
    if (!cr.ok()) throw new Error(`create contractor failed: ${cr.status()}`)
    const c = await cr.json()
    contractorId = c.id
    createdContractors.push(contractorId)

    // Faza 5: /articles (is_service: false) → /machines
    const artEq = await request.post(`${API}/machines`, { headers, data: { name: `E2E P1-100 equip ${ts}` }, timeout: 10_000 })
    if (artEq.status() !== 201) throw new Error(`create equipment machine failed: ${artEq.status()}`)
    const eqArt = await artEq.json()
    equipmentMachineId = eqArt.id
    createdMachines.push(equipmentMachineId)

    // Faza 5: /articles (is_service: true) → /services
    const artSrv = await request.post(`${API}/services`, { headers, data: { name: `E2E P1-100 service ${ts}` }, timeout: 10_000 })
    if (artSrv.status() === 201) {
      const srvArt = await artSrv.json()
      serviceId = srvArt.id
      createdServices.push(serviceId)
    }

    const today = new Date().toISOString().slice(0, 10)
    const ctrS = await request.post(`${API}/contracts`, { headers, data: { contractor_id: contractorId, contract_type: 'S', date_from: today }, timeout: 10_000 })
    if (ctrS.status() !== 201) throw new Error(`create S contract failed: ${ctrS.status()}`)
    const sCtr = await ctrS.json()
    sContractId = sCtr.id
    createdContracts.push(sContractId)

    // Faza 5: article_id → machine_id
    const posS = await request.post(`${API}/contracts/${sContractId}/positions`, { headers, data: { machine_id: equipmentMachineId, quantity: 1, unit_price: 500, rental_days: 10 }, timeout: 10_000 })
    if (posS.status() !== 201) throw new Error(`create position failed: ${posS.status()}`)
    const pos = await posS.json()
    sPositionId = pos.id

    // Faza 5: /settings/articles/{id}/rate-presets → /settings/machines/{id}/rate-presets
    const rp = await request.post(`${API}/settings/machines/${equipmentMachineId}/rate-presets`, { headers, data: { name: `Test 1-3/4-16/>16 ${ts}`, is_default: true, items: [ { period_count: 3, rate1: 540, billing_label: 'doba' }, { period_count: 16, rate1: 410, billing_label: 'doba' }, { rate2: 350, billing_label: 'doba' } ] }, timeout: 10_000 })
    if (rp.status() === 201) {
      const rpd = await rp.json()
      ratePresetId = rpd.id
      createdRatePresets.push(ratePresetId)
    } else {
      console.error('rate preset create status', rp.status())
    }

    const ctrU = await request.post(`${API}/contracts`, { headers, data: { contractor_id: contractorId, contract_type: 'U', date_from: today }, timeout: 10_000 })
    if (ctrU.status() === 201) {
      const uCtr = await ctrU.json()
      uContractId = uCtr.id
      createdContracts.push(uContractId)
      if (serviceId) {
        // Faza 5: article_id → service_id (is_service: true → /services)
        const posU = await request.post(`${API}/contracts/${uContractId}/positions`, { headers, data: { service_id: serviceId, quantity: 1 }, timeout: 10_000 })
        if (posU.status() === 201) { const pu = await posU.json(); uPositionId = pu.id }
      }
    }
  })

  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test.afterAll(async ({ request }) => {
    const token = await apiLogin(request)
    for (const cid of createdContracts) await safeDelete(request, `${API}/contracts/${cid}`, token)
    for (const rpid of createdRatePresets) await safeDelete(request, `${API}/settings/rate-presets/${rpid}`, token)
    // Faza 5: cleanup przez /machines i /services (było /articles)
    for (const mid of createdMachines) await safeDelete(request, `${API}/machines/${mid}`, token)
    for (const sid of createdServices) await safeDelete(request, `${API}/services/${sid}`, token)
    for (const crid of createdContractors) await safeDelete(request, `${API}/contractors/${crid}`, token)
  })

  test('nowa umowa najmu: sekcja Opłaty dodatkowe zawiera domyślne opłaty', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('.toolbar-info')).toContainText('Umowa:', { timeout: 10_000 })
    const feeSection = page.locator('.page-card:has-text("Opłaty dodatkowe")').first()
    await expect(feeSection.getByRole('cell', { name: 'Transport', exact: true }).first()).toBeVisible({ timeout: 8_000 })
  })

  test('zastosowanie zestawu Diesel: podgląd PDF pokazuje przegląd za 150 zł', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('.page-card:has-text("Opłaty dodatkowe")').first()).toBeVisible({ timeout: 8_000 })
    const presetSelect = page.locator('select:has-text("Wybierz zestaw…")')
    await expect(presetSelect).toBeVisible({ timeout: 5_000 })
    await presetSelect.selectOption({ label: 'Najem — Diesel' })
    await page.locator('button:has-text("Zastosuj")').first().click()
    const feeSection = page.locator('.page-card:has-text("Opłaty dodatkowe")').first()
    await expect(feeSection.getByText(/Przegląd techniczny.*150/).first()).toBeVisible({ timeout: 10_000 })
    await expect(feeSection).not.toContainText('$')
  })

  test('przełączenie na zestaw Elektryk: przegląd za 35 zł', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const feeSection = page.locator('.page-card:has-text("Opłaty dodatkowe")').first()
    const presetSelect = page.locator('select:has-text("Wybierz zestaw…")')
    await expect(presetSelect).toBeVisible({ timeout: 8_000 })
    await presetSelect.selectOption({ label: 'Najem — Diesel' })
    await page.locator('button:has-text("Zastosuj")').first().click()
    await feeSection.getByText(/Przegląd techniczny.*150/).first().waitFor({ state: 'visible', timeout: 10_000 })
    await presetSelect.selectOption({ label: 'Najem — Elektryk' })
    await page.locator('button:has-text("Zastosuj")').first().click()
    await expect(feeSection.getByText(/Przegląd techniczny.*35/).first()).toBeVisible({ timeout: 10_000 })
    await expect(feeSection).not.toContainText('$')
  })

  test('powrót do zestawu Domyślny: ładuje stary domyślny zestaw', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const feeSection = page.locator('.page-card:has-text("Opłaty dodatkowe")').first()
    const presetSelect = page.locator('select:has-text("Wybierz zestaw…")')
    await expect(presetSelect).toBeVisible({ timeout: 8_000 })
    await presetSelect.selectOption({ label: 'Najem — Diesel' })
    await page.locator('button:has-text("Zastosuj")').first().click()
    await feeSection.getByText(/Przegląd techniczny.*150/).first().waitFor({ state: 'visible', timeout: 10_000 })
    await presetSelect.selectOption({ label: 'Najem — Wspólny' })
    await page.locator('button:has-text("Zastosuj")').first().click()
    await expect(feeSection.getByText(/Tankowanie|Transport/).first()).toBeVisible({ timeout: 10_000 })
  })

  test('usunięcie pozycji usługi usuwa ją z podglądu PDF', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const feeSection = page.locator('.page-card:has-text("Opłaty dodatkowe")').first()
    const presetSelect = page.locator('select:has-text("Wybierz zestaw…")')
    await expect(presetSelect).toBeVisible({ timeout: 8_000 })
    await presetSelect.selectOption({ label: 'Najem — Diesel' })
    await page.locator('button:has-text("Zastosuj")').first().click()
    const transportRow = feeSection.getByText(/Transport:.*1 200/).first()
    await transportRow.waitFor({ state: 'visible', timeout: 10_000 })
    // kliknij przycisk Usuń w wierszu z Transportem
    await feeSection.locator('tr', { hasText: /Transport/ }).first().getByRole('button', { name: '✕' }).first().click()
    await page.getByRole('button', { name: /Usuń/ }).first().click()
    await expect(transportRow).not.toBeVisible({ timeout: 8_000 })
  })

  test('ustawienie dni roboczych = 7 jest odzwierciedlone w UI', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: '7', exact: true }).click()
    // weryfikacja stanu przycisku selected
    const btn7 = page.getByRole('button', { name: '7', exact: true })
    await expect(btn7).toHaveClass(/selected/, { timeout: 5_000 })
  })

  test('tryb usługi U: brak pola Numer wewnętrzny w formularzu nowej usługi', async ({ page }) => {
    test.skip(!uContractId, 'Brak umowy U')
    await page.goto(`/rao/contracts/${uContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: '+ Dodaj usługę' }).click()
    await expect(page.locator('.modal-box:has-text("Wybierz usługę")')).toBeVisible({ timeout: 8_000 })
    await page.getByRole('button', { name: /Dodaj nową usługę/ }).click()
    const modal = page.locator('.modal-box:visible')
    await expect(modal.getByText('Nr wewnętrzny')).not.toBeVisible({ timeout: 5_000 })
  })

  test('ConditionPanel: zastosowanie cennika dodaje 3 wiersze z widełkami', async ({ page }) => {
    test.skip(!ratePresetId, 'Brak cennika testowego')
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByText(`E2E P1-100 equip`).first().click()
    const condPanel = page.locator('.condition-panel')
    await expect(condPanel).toBeVisible({ timeout: 8_000 })
    await condPanel.getByRole('button', { name: /Zastosuj cennik/ }).click()
    await expect(page.locator('.modal-box:has-text("Zastosuj cennik rozliczenia")')).toBeVisible({ timeout: 8_000 })
    await page.getByRole('button', { name: 'Zastosuj', exact: true }).click()
    // oczekuj co najmniej 3 wiersze warunków w tabeli
    await expect(condPanel.locator('table tbody tr')).toHaveCount(3, { timeout: 10_000 })
  })

  test('Rozliczenie "Pobierz z umowy" nie generuje duplikatów', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'load', timeout: 15_000 })
    const settlementSection = page.locator('.page-card:has-text("Rozliczenie umowy")').first()
    await settlementSection.getByRole('button', { name: /Pobierz z umowy/ }).click()
    await expect(settlementSection.getByRole('button', { name: /Odśwież z umowy/ })).toBeVisible({ timeout: 10_000 })
    const firstCount = await settlementSection.locator('table tbody tr').count()
    await settlementSection.getByRole('button', { name: /Odśwież z umowy/ }).click()
    await expect(settlementSection.locator('table tbody tr')).toHaveCount(firstCount, { timeout: 10_000 })
  })

  test('brak znaku $ w opisach i kwotach na podglądzie usług', async ({ page }) => {
    await page.goto(`/rao/contracts/${sContractId}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    const feeSection = page.locator('.page-card:has-text("Opłaty dodatkowe")').first()
    const presetSelect = page.locator('select:has-text("Wybierz zestaw…")')
    await expect(presetSelect).toBeVisible({ timeout: 8_000 })
    await presetSelect.selectOption({ label: 'Najem — Diesel' })
    await page.locator('button:has-text("Zastosuj")').first().click()
    await feeSection.getByText(/Przegląd techniczny.*150/).first().waitFor({ state: 'visible', timeout: 10_000 })
    await expect(feeSection).not.toContainText('$')
  })
})
