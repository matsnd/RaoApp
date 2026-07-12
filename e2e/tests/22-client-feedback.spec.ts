import { test, expect } from '@playwright/test'
import { API, apiLogin, authHeaders, genValidNip, generateAndSavePDF, login } from './helpers'

let token = ''

test.describe('TEST-22: Uwagi klienta — weryfikacja E2E (Faza 9)', () => {
  test.beforeAll(async ({ request }) => {
    token = await apiLogin(request)
  })

  // #1: Odhaczenie czy maszyna nasza czy zewnętrzna (is_external flag)
  test('#1: is_external flag istnieje na maszynach', async ({ request }) => {
    const r = await request.get(`${API}/machines?limit=1`, { headers: authHeaders(token) })
    expect(r.ok()).toBeTruthy()
    const data = await r.json()
    const machines = Array.isArray(data) ? data : data.items
    expect(machines.length).toBeGreaterThan(0)
    // is_external powinno być w schema (boolean)
    expect(machines[0]).toHaveProperty('is_external')
    expect(typeof machines[0].is_external).toBe('boolean')
  })

  // #3: Liczenie wynajmu 5, 6 lub 7 dni w tyg
  test('#3: working_days_per_week akceptuje 5, 6, 7', async ({ request }) => {
    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `Uwagi3 ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    const today = new Date().toISOString().slice(0, 10)

    for (const days of [5, 6, 7]) {
      const ctr = await request.post(`${API}/contracts`, {
        headers: authHeaders(token),
        data: {
          contractor_id: c.id,
          contract_type: 'S',
          date_from: today,
          working_days_per_week: days,
        },
      })
      expect(ctr.status()).toBe(201)
      const ct = await ctr.json()
      expect(ct.working_days_per_week).toBe(days)
      await request.delete(`${API}/contracts/${ct.id}`, { headers: authHeaders(token) })
    }
    await request.delete(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
  })

  // #4: Zapis "Naliczanie: X dni w tygodniu (pozostałe dni według zapisu GPS)"
  test('#4: PDF Umowa — zapis Naliczanie z GPS', async ({ request }) => {
    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `Uwagi4 ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: {
        contractor_id: c.id,
        contract_type: 'S',
        date_from: today,
        working_days_per_week: 5,
      },
    })
    const ct = await ctr.json()

    await generateAndSavePDF(request, ct.id, 'contract', 'uwagi-#4-naliczenie-gps.pdf')
    console.log('PDF zapisany — manual verification: "Naliczanie: 5 dni w tygodniu (pozostałe dni według zapisu GPS)"')

    await request.delete(`${API}/contracts/${ct.id}`, { headers: authHeaders(token) })
    await request.delete(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
  })

  // #6: Cenniki przeglądów (150 zł diesel, 35 zł elektryk) w additional_services
  // Uwaga klienta 6: diesel przegląd 150 zł, elektryk przegląd+ładowanie 35 zł
  // Nazwy usług są unified (bez "diesel"/"elektryk" w nazwie) — power_type maszyny
  // decyduje którą usługę wybrać w umowie. Test weryfikuje kwoty.
  test('#6: additional_services — cenniki przeglądów 150 i 35', async ({ request }) => {
    const r = await request.get(`${API}/additional-services`, { headers: authHeaders(token) })
    expect(r.ok()).toBeTruthy()
    const services = await r.json()
    const items = Array.isArray(services) ? services : services.items

    // Przegląd diesel (przegląd + czyszczenie, 150 zł)
    const diesel = items.find((s: any) =>
      s.name.toLowerCase().includes('przegląd techniczny i czyszczenie') &&
      Number(s.default_amount) === 150
    )
    expect(diesel, 'Brak cennika przeglądu diesel 150 zł').toBeTruthy()

    // Przegląd elektryk (przegląd + ładowanie + czyszczenie, 35 zł)
    const elektryk = items.find((s: any) =>
      s.name.toLowerCase().includes('ładowanie akumulatorów') &&
      Number(s.default_amount) === 35
    )
    expect(elektryk, 'Brak cennika przeglądu elektryk 35 zł').toBeTruthy()
  })

  // #9: Opiekun zamówienia na protokole
  test('#9: PDF Protokół — opiekun zamówienia widoczny', async ({ request }) => {
    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `Uwagi9 ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: c.id, contract_type: 'S', date_from: today },
    })
    const ct = await ctr.json()

    await generateAndSavePDF(request, ct.id, 'protocol_zo_s', 'uwagi-#9-opiekun.pdf')
    console.log('PDF zapisany — manual verification: "Opiekun zamówienia: ... tel. ..."')

    await request.delete(`${API}/contracts/${ct.id}`, { headers: authHeaders(token) })
    await request.delete(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
  })

  // #10: Brak pieczątki przy zwrocie na protokole
  test('#10: PDF Protokół — sekcja zwrotu bez pieczątki', async ({ request }) => {
    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `Uwagi10 ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: c.id, contract_type: 'S', date_from: today },
    })
    const ct = await ctr.json()

    await generateAndSavePDF(request, ct.id, 'protocol_zo_s', 'uwagi-#10-bez-pieczatki.pdf')
    console.log('PDF zapisany — manual verification: sekcja ZWROT bez pieczątki (tylko podpis Najemcy)')

    await request.delete(`${API}/contracts/${ct.id}`, { headers: authHeaders(token) })
    await request.delete(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
  })

  // #13: Nr wewnętrzny usunięty z formularzy usług
  test('#13: GUI — formularz usługi nie ma pola Nr wewnętrzny', async ({ page }) => {
    await login(page)

    // Przejdź do formularza nowej usługi
    await page.goto('/rao/services/new', { waitUntil: 'domcontentloaded' })

    // Sprawdź że nie ma label "Nr wewnętrzny"
    const internalLabel = page.locator('label:has-text("Nr wewnętrzny")')
    await expect(internalLabel).toHaveCount(0)

    // Sprawdź że nie ma input z id service-internal
    const internalInput = page.locator('#service-internal')
    await expect(internalInput).toHaveCount(0)
  })

  test('#13b: GUI — formularz usługi dodatkowej nie ma pola Nr wewnętrzny', async ({ page }) => {
    await login(page)

    await page.goto('/rao/additional-services/new', { waitUntil: 'domcontentloaded' })

    const internalLabel = page.locator('label:has-text("Nr wewnętrzny")')
    await expect(internalLabel).toHaveCount(0)

    const internalInput = page.locator('#as-internal')
    await expect(internalInput).toHaveCount(0)
  })

  // #15: Zmiana punktu 8b OWN — stawka 250 zł/roboczogodzina
  test('#15: PDF Umowa — OWN punkt 8b stawka 250 zł/rg', async ({ request }) => {
    const ts = Date.now()
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `Uwagi15 ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: c.id, contract_type: 'S', date_from: today },
    })
    const ct = await ctr.json()

    await generateAndSavePDF(request, ct.id, 'contract', 'uwagi-#15-own-250.pdf')
    console.log('PDF zapisany — manual verification: OWN 8b "250,00 zł netto za każdą rozpoczętą roboczogodzinę"')

    await request.delete(`${API}/contracts/${ct.id}`, { headers: authHeaders(token) })
    await request.delete(`${API}/contractors/${c.id}`, { headers: authHeaders(token) })
  })
})
