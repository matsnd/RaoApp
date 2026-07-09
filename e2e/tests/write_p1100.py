content = """import { test, expect } from '@playwright/test'
import { waitForBackend, login, API, CREDS, apiLogin, authHeaders, safeDelete, genValidNip } from './helpers'

let contractorId = 0
let equipmentArticleId = 0
let serviceArticleId = 0
let sContractId = 0
let uContractId = 0
let sPositionId = 0
let uPositionId = 0
let ratePresetId = 0
const createdContracts: number[] = []
const createdContractors: number[] = []
const createdArticles: number[] = []
const createdRatePresets: number[] = []

test.describe('TEST-05-P1-100: Usługi dodatkowe, warunki, cennik, przedpłata, tryb usługi', () => {
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

    const artEq = await request.post(`${API}/articles`, { headers, data: { name: `E2E P1-100 equip ${ts}`, is_service: false }, timeout: 10_000 })
    if (artEq.status() !== 201) throw new Error(`create equipment article failed: ${artEq.status()}`)
    const eqArt = await artEq.json()
    equipmentArticleId = eqArt.id
    createdArticles.push(equipmentArticleId)

    const artSrv = await request.post(`${API}/articles`, { headers, data: { name: `E2E P1-100 service ${ts}`, is_service: true }, timeout: 10_000 })
    if (artSrv.status() === 201) {
      const srvArt = await artSrv.json()
      serviceArticleId = srvArt.id
      createdArticles.push(serviceArticleId)
    }

    const today = new Date().toISOString().slice(0, 10)
    const ctrS = await request.post(`${API}/contracts`, { headers, data: { contractor_id: contractorId, contract_type: 'S', date_from: today }, timeout: 10_000 })
    if (ctrS.status() !== 201) throw new Error(`create S contract failed: ${ctrS.status()}`)
    const sCtr = await ctrS.json()
    sContractId = sCtr.id
    createdContracts.push(sContractId)

    const posS = await request.post(`${API}/contracts/${sContractId}/positions`, { headers, data: { article_id: equipmentArticleId, quantity: 1, unit_price: 500, rental_days: 10 }, timeout: 10_000 })
    if (posS.status() !== 201) throw new Error(`create position failed: ${posS.status()}`)
    const pos = await posS.json()
    sPositionId = pos.id

    const rp = await request.post(`${API}/settings/articles/${equipmentArticleId}/rate-presets`, { headers, data: { name: `Test 1-3/4-16/>16 ${ts}`, is_default: true, items: [ { period_count: 3, rate1: 540, billing_label: 'doba' }, { period_count: 16, rate1: 410, billing_label: 'doba' }, { rate2: 350, billing_label: 'doba' } ] }, timeout: 10_000 })
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
      if (serviceArticleId) {
        const posU = await request.post(`${API}/contracts/${uContractId}/positions`, { headers, data: { article_id: serviceArticleId, quantity: 1 }, timeout: 10_000 })
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
    for (const aid of createdArticles) await safeDelete(request, `${API}/articles/${aid}`, token)
    for (const crid of createdContractors) await safeDelete(request, `${API}/contractors/${crid}`, token)
  })

  test('nowa umowa najmu: sekcja Usługi dodatkowe jest pusta na starcie', async ({ page }) => {
    await page.goto(`/rao/contracts/new?contractor_id=${contractorId}`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('[data-testid="date-from-input"]')).toBeVisible({ timeout: 5_000 })
    await page.locator('[data-testid="date-from-input"]').fill(new Date().toISOString().slice(0, 10))
    await page.getByRole('button', { name: 'Zapisz' }).click()
    await expect(page).toHaveURL(/\//rao\/contracts\/\d+\/edit/, { timeout: 10_000 })
    const feeSection = page.locator('.page-card:has-text("Usługi dodatkowe")')
    await expect(feeSection.getByText('Brak usług dodatkowych')).toBeVisible({ timeout: 8_000 })
  })
})
"""
open('05-p1100.spec.ts', 'w', encoding='utf-8').write(content)
