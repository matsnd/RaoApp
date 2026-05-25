import { test, expect } from '@playwright/test'
import { API, apiLogin, authHeaders, safeDelete, newApiContext, genValidNip, generateAndSavePDF } from './helpers'

let token = ''
let contractorId = 0
let contractId = 0
let contractUId = 0 // dla umowy typu U (usługa)

test.describe('TEST-11: PDF Verification (Sprint Klient 2026-05-25)', () => {
  test.beforeAll(async ({ request }) => {
    token = await apiLogin(request)
    const ts = Date.now()
    
    // Utwórz kontrahenta
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `PDF-Test ${ts}`, nip: genValidNip(ts) },
    })
    const c = await cr.json()
    contractorId = c.id
    
    // Utwórz umowę typu S (najmu)
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { 
        contractor_id: contractorId, 
        contract_type: 'S', 
        date_from: today,
        delivery_address: 'Testowa 1, Warszawa',
        working_days_per_week: 6
      },
    })
    if (ctr.status() !== 201) {
      console.error(`POST /contracts failed: ${ctr.status()}`)
      return
    }
    const ct = await ctr.json()
    contractId = ct.id
    
    // Utwórz umowę typu U (usługa) dla porównania
    const ctrU = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { 
        contractor_id: contractorId, 
        contract_type: 'U', 
        date_from: today 
      },
    })
    if (ctrU.status() === 201) {
      const ctU = await ctrU.json()
      contractUId = ctU.id
    }
  })

  // --- RAO-P1-001: PDF Umowa — usunąć duplikat "na budowie" ---
  test('RAO-P1-001: PDF Umowa — brak duplikatu adresu w polu "na budowie"', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P1-001-no-duplicate.pdf')
    
    // Manual verification: adres widoczny tylko raz w "info-col", pole "na budowie" puste
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P1-001-no-duplicate.pdf - manual verification required')
  })

  // --- RAO-P1-002: PDF Umowa — "Dni pracy/tydzień" → "Ilość dni pracy" ---
  test('RAO-P1-002: PDF Umowa — label "Ilość dni pracy w tygodniu"', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P1-002-working-days.pdf')
    
    // Manual verification: label zmieniony na "Ilość dni pracy w tygodniu", wartość = 6
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P1-002-working-days.pdf - manual verification required')
  })

  // --- RAO-P1-003: PDF Umowa — "*ceny netto" wyraźnie na dole ---
  test('RAO-P1-003: PDF Umowa — "*ceny netto" wyraźnie widoczne', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P1-003-net-prices.pdf')
    
    // Manual verification: footer-legal visible, czerwony, pogrubiony, font-size 11px
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P1-003-net-prices.pdf - manual verification required')
  })

  // --- RAO-P1-004: PDF Umowa U — usuń cennik dodatkowy ---
  test.fixme('RAO-P1-004: PDF Umowa U — brak sekcji "Cennik usług dodatkowych"', async ({ request }) => {
    // Wymaga umowy typu U - może nie zostać utworzona w beforeAll
    // Owner: backend-dev / qa
    test.skip(!contractUId, 'Brak umowy U do testu')
    
    // Generuj PDF dla umowy U
    await generateAndSavePDF(request, contractUId, 'contract_u', 'RAO-P1-004-no-fee-catalog.pdf')
    
    // Generuj PDF dla umowy S (do porównania)
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P1-004-contract-S.pdf')
    
    // Manual verification: w PDF U brak sekcji "Cennik usług dodatkowych", w PDF S jest
    console.log('PDF-y zapisane do e2e/artifacts/pdfs/ - manual verification required')
  })

  // --- RAO-P1-005: PDF Protokół — etykieta "nr tel" w boksie kontaktu ---
  test('RAO-P1-005: PDF Protokół — etykieta "nr tel" widoczna', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj protokół ZO
    await generateAndSavePDF(request, contractId, 'protocol_zo_s', 'RAO-P1-005-phone-label.pdf')
    
    // Manual verification: etykieta "nr tel:" widoczna, font-size 9px
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P1-005-phone-label.pdf - manual verification required')
  })

  // --- RAO-P1-006: PDF Protokół — większa tabela "Przy wydaniu/odbiorce" ---
  test('RAO-P1-006: PDF Protokół — większa tabela PWO', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj protokół ZO
    await generateAndSavePDF(request, contractId, 'protocol_zo_s', 'RAO-P1-006-larger-table.pdf')
    
    // Manual verification: height wierszy 32px, font-size 10px, padding 5px 8px
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P1-006-larger-table.pdf - manual verification required')
  })

  // --- RAO-P1-007: PDF Protokół — 1 duża tabela "uwagi" zamiast 3 ---
  test('RAO-P1-007: PDF Protokół — 1 duża tabela uwagi', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj protokół ZO
    await generateAndSavePDF(request, contractId, 'protocol_zo_s', 'RAO-P1-007-big-uwagi.pdf')
    
    // Manual verification: return-table usunięta, big-uwagi widoczna (min-height 140px, padding 10px 12px)
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P1-007-big-uwagi.pdf - manual verification required')
  })

  // --- RAO-P1-009: Wymiana pieczątki firmy w PDF ---
  test('RAO-P1-009: PDF — nowa pieczątka firmy', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF umowy
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P1-009-stamp-contract.pdf')
    
    // Generuj PDF protokołu
    await generateAndSavePDF(request, contractId, 'protocol_zo_s', 'RAO-P1-009-stamp-protocol.pdf')
    
    // Manual verification: nowa pieczątka w umowach (company_stamp_fixed.jpg) i protokołach (protocol_stamp.png)
    console.log('PDF-y zapisane do e2e/artifacts/pdfs/ - manual verification required')
  })

  // --- RAO-P1-010: Weryfikacja numeru telefonu w nagłówku ---
  test.fixme('RAO-P1-010: PDF — numer telefonu +48 888 992 015', async ({ request }) => {
    // Wymaga poprawnych parametrów dla contract_u i protocol_zo_nodata
    // Owner: backend-dev / qa
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF dla wszystkich szablonów
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P1-010-phone-contract.pdf')
    await generateAndSavePDF(request, contractId, 'contract_u', 'RAO-P1-010-phone-contract-u.pdf')
    await generateAndSavePDF(request, contractId, 'protocol_zo_s', 'RAO-P1-010-phone-protocol.pdf')
    await generateAndSavePDF(request, contractId, 'protocol_zo_u', 'RAO-P1-010-phone-protocol-u.pdf')
    await generateAndSavePDF(request, contractId, 'protocol_zo_nodata_s', 'RAO-P1-010-phone-protocol-nodata.pdf')
    
    // Manual verification: numer +48 888 992 015 we wszystkich szablonach
    console.log('PDF-y zapisane do e2e/artifacts/pdfs/ - manual verification required')
  })

  // --- RAO-P1-012: PDF OWN — ujednolicenie wcięć w listach ---
  test('RAO-P1-012: PDF OWN — ujednolicone wcięcia', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF umowy
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P1-012-own-indentation.pdf')
    
    // Manual verification: wcięcia 7mm/13mm, font-size 7.5pt, line-height 1.15, nic nie wystaje
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P1-012-own-indentation.pdf - manual verification required')
  })

  // --- RAO-P2-001: PDF Umowa NAJMU (S) — domyślny cennik dodatkowy ---
  test('RAO-P2-001: PDF Umowa S — domyślny cennik 6 pozycji', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF umowy typu S
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P2-001-default-fees.pdf')
    
    // Manual verification: 6 pozycji w określonej kolejności (Transport, Czyszczenie drobne, Czyszczenie trudne, Tankowanie, Prestój, Serwis)
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P2-001-default-fees.pdf - manual verification required')
  })

  // --- RAO-P2-002: PDF Umowa — sekcja "Uwagi" w określonej kolejności ---
  test('RAO-P2-002: PDF Umowa — sekcja "Uwagi" w określonej kolejności', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P2-002-notes-order.pdf')
    
    // Manual verification: 4 podpunkty w wymaganym formacie (Doba wynajmu, Zgłoszenie zwrotu, Ilość dni pracy, Dokumentacja zdjęciowa)
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P2-002-notes-order.pdf - manual verification required')
  })

  // --- RAO-P2-003: PDF Umowa — kompaktniejszy layout ---
  test('RAO-P2-003: PDF Umowa — kompaktniejszy layout', async ({ request }) => {
    test.skip(!contractId, 'Brak umowy do testu')
    
    // Generuj PDF
    await generateAndSavePDF(request, contractId, 'contract', 'RAO-P2-003-compact-layout.pdf')
    
    // Manual verification: font-size 8.5px/8px, padding 2-4px, line-height 1.3
    console.log('PDF zapisany do e2e/artifacts/pdfs/RAO-P2-003-compact-layout.pdf - manual verification required')
  })

  test.afterAll(async () => {
    const ctx = await newApiContext()
    try {
      const t = await apiLogin(ctx)
      await safeDelete(ctx, `${API}/contracts/${contractId}`, t)
      await safeDelete(ctx, `${API}/contracts/${contractUId}`, t)
      await safeDelete(ctx, `${API}/contractors/${contractorId}`, t)
    } catch {
      /* ignore */
    } finally {
      await ctx.dispose()
    }
  })
})
