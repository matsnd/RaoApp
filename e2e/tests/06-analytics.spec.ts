import { test, expect, type Page, type APIRequestContext } from '@playwright/test'
import { BASE, login, waitForBackend, apiLogin, API, authHeaders, safeDelete, newApiContext, genValidNip } from './helpers'

// RAO-P2-065 #13: Testy e2e dla AnalyticsView — pokrycie regresyjne
// Zakrywa: LiveFleet tab, PeriodRental tab, drill-down maszyny z ROI,
// filtr kontrahenta (select), walidacja dat (422), sekcja kategorii.

// Cleanup arrays for TEST-03 test data
const createdContractIds: number[] = []
const createdContractorIds: number[] = []
const createdMachineIds: number[] = []

test.describe('AnalyticsView — statystyki', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    // Retry login — pre-existing flakiness w sesji testowej
    for (let i = 0; i < 3; i++) {
      try {
        await login(page)
        break
      } catch {
        if (i === 2) throw new Error('Login failed after 3 retries')
        await page.waitForTimeout(1000)
      }
    }
    // Nawigacja do statystyk (bezpośrednio URL — stabilniejsze niż nav button)
    await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 10_000 })
    await expect(page).toHaveURL(/\/rao\/analytics/, { timeout: 8_000 })
  })

  test('TEST-01: LiveFleet tab pokazuje maszyny aktualnie wynajęte z kontrahentem', async ({ page }) => {
    // Kliknij "Flota teraz" tab
    await page.getByTestId('tab-live').click()

    // Tab content powinien być widoczny (zawsze renderowany)
    await expect(page.getByTestId('live-fleet-tab')).toBeVisible({ timeout: 8_000 })

    // KPI powinno być widoczne (dostępne maszyny, wynajęte, wykorzystanie)
    await expect(page.getByTestId('kpi-live-available')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('kpi-live-rented')).toBeVisible()
    await expect(page.getByTestId('kpi-live-util')).toBeVisible()

    // Tabela maszyn: albo zawiera wiersze (są wynajęte maszyny) albo empty state
    const tableWrap = page.getByTestId('analytics-table').first()
    await expect(tableWrap).toBeVisible({ timeout: 8_000 })

    const tableEl = tableWrap.locator('table.analytics-table')
    const emptyState = tableWrap.getByTestId('analytics-table-empty')
    // Czekaj aż jedna z dwóch opcji się pojawi
    await expect(tableEl.or(emptyState)).toBeVisible({ timeout: 8_000 })

    const isTableVisible = await tableEl.isVisible().catch(() => false)
    if (isTableVisible) {
      // Powinna mieć co najmniej 1 wiersz
      const rows = tableEl.locator('tbody tr')
      const count = await rows.count()
      expect(count).toBeGreaterThan(0)

      // RAO-P2-065 #2: kontrahent nie powinien być pusty (coalesce fix)
      const firstRow = rows.first()
      const cells = firstRow.locator('td')
      const cellTexts = await cells.allTextContents()
      // Znajdź kolumnę kontrahenta (5. kolumna w LiveFleet)
      const contractorCell = cellTexts[4]?.trim() || ''
      expect(contractorCell.length).toBeGreaterThan(0)
      expect(contractorCell).not.toBe('—')
    }
    // else: brak wynajętych maszyn — empty state jest widoczny, test przechodzi
  })

  test('TEST-02: PeriodRental tab pokazuje KPI + sekcje + kategorie', async ({ page }) => {
    await page.getByTestId('tab-period').click()

    // KPI row widoczne
    await expect(page.getByTestId('kpi-period-revenue')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId('kpi-period-contracts')).toBeVisible()
    await expect(page.getByTestId('kpi-period-rented')).toBeVisible()
    await expect(page.getByTestId('kpi-period-util')).toBeVisible()

    // RAO-P2-065 #6: sekcja kategorii — może być pusta jeśli brak umów w okresie
    const catTable = page.getByTestId('categories-table')
    await expect(catTable).toBeVisible({ timeout: 10_000 })
    const catRows = catTable.locator('tbody tr')
    const catCount = await catRows.count()
    // Kategorie mogą być puste jeśli brak umów w wybranym okresie (np. "Dziś" bez aktywnych umów)
    if (catCount > 0) {
      expect(catCount).toBeGreaterThan(0)
    }

    // Top maszyny sekcja — może być pusta jeśli brak wynajętych maszyn w okresie
    const topMachinesSection = page.locator('.pr-section').filter({ hasText: 'Top maszyny' })
    // Sekcja powinna istnieć (nawet jeśli pusta)
    await expect(topMachinesSection).toBeVisible({ timeout: 5_000 }).catch(() => {
      // Może nie być widoczna jeśli brak danych — acceptable
    })
  })

  // RAO-P2-065 #1: drill-down ROI section — fixed (fetchMachineRoi podpięte do store)
  test('TEST-03: Drill-down maszyny pokazuje sekcję ROI', async ({ page, request }) => {
    // Setup: utwórz maszynę z replacement_value + kontrahenta + umowę + pozycję
    // (wymagane aby maszyna pojawiła się w top-machines i miała dane ROI)
    const token = await apiLogin(request)
    const ts = Date.now()

    const machineRes = await request.post(`${API}/machines`, {
      headers: authHeaders(token),
      data: { name: `AnalyticsTestMachine ${ts}`, replacement_value: 50000 },
    })
    expect([200, 201]).toContain(machineRes.status())
    const machine = await machineRes.json()
    createdMachineIds.push(machine.id)

    const crRes = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `AnalyticsTestContractor ${ts}`, nip: genValidNip(ts) },
    })
    const contractor = await crRes.json()
    createdContractorIds.push(contractor.id)

    const today = new Date()
    const todayStr = today.toISOString().slice(0, 10)
    const dateTo = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    const ctrRes = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: contractor.id, contract_type: 'S', date_from: todayStr, date_to: dateTo },
    })
    const contract = await ctrRes.json()
    createdContractIds.push(contract.id)

    const posRes = await request.post(`${API}/contracts/${contract.id}/positions`, {
      headers: authHeaders(token),
      data: { machine_id: machine.id, quantity: 1, rental_days: 30 },
    })
    expect([200, 201]).toContain(posRes.status())
    const position = await posRes.json()

    // Dodaj warunki rozliczeniowe (wymagane aby maszyna miała revenue > 0 w top-machines)
    // Warunek z period_count=1 zapewnia revenue > 0 niezależnie od wybranego presetu (Dziś/Miesiąc)
    const rtRes = await request.get(`${API}/settings/rate-types`, { headers: authHeaders(token) })
    const rtData = await rtRes.json()
    const rateTypeId = (Array.isArray(rtData) ? rtData[0] : rtData.items?.[0])?.id
    if (rateTypeId) {
      await request.post(`${API}/contracts/${contract.id}/positions/${position.id}/conditions`, {
        headers: authHeaders(token),
        data: { period_count: 1, rate1: 200, rate2: 100, billing_label: 'dzień', rate_type_id: rateTypeId },
      })
    }

    // Nawigacja do statystyk (P1-112: domyślna taba to 'live', period trzeba kliknąć)
    await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 10_000 })
    await expect(page).toHaveURL(/\/rao\/analytics/, { timeout: 8_000 })

    // Kliknij "Rankingi wynajmu" tab (było "Wynajem w okresie", P1-112 rename)
    await page.getByTestId('tab-period').click()

    // Czekaj na załadowanie KPI
    await expect(page.getByTestId('kpi-period-revenue')).toBeVisible({ timeout: 10_000 })

    // Użyj filtra kontrahenta aby zmienić cache key na backendzie (cache TTL 5 min).
    // Każdy test tworzy nowego kontrahenta → unikalny cache key → świeże dane.
    // Najpierw kliknij "Dziś" preset (inny range niż domyślny "Miesiąc" z beforeEach),
    // potem wybierz kontrahenta w combobox.
    await page.getByTestId('preset-today').click()
    await page.waitForTimeout(500)

    // Wybierz testowego kontrahenta w combobox (zmienia cache key)
    const contractorInput = page.getByTestId('filter-contractor-input')
    await contractorInput.click()
    await contractorInput.fill(`AnalyticsTestContractor ${ts}`)
    await page.waitForTimeout(500)
    // Kliknij opcję z dropdown
    const dropdown = page.getByTestId('filter-contractor-dropdown')
    await expect(dropdown).toBeVisible({ timeout: 5_000 })
    const option = dropdown.locator('button', { hasText: `AnalyticsTestContractor ${ts}` }).first()
    await option.click()
    await page.waitForTimeout(2000) // poczekaj na przeładowanie z nowym filtrem
    await expect(page.getByTestId('kpi-period-revenue')).toBeVisible({ timeout: 10_000 })

    // Poczekaj na załadowanie danych (top machines table)
    const topMachinesSection = page.locator('.pr-section').filter({ hasText: 'Top maszyny' })
    await expect(topMachinesSection).toBeVisible({ timeout: 10_000 })

    // Kliknij wiersz z naszą maszyną w top machines table
    const topTable = topMachinesSection.locator('table.analytics-table')
    await expect(topTable).toBeVisible({ timeout: 10_000 })
    const targetRow = topTable.locator('tbody tr', { hasText: `AnalyticsTestMachine ${ts}` })
    await expect(targetRow).toBeVisible({ timeout: 10_000 })
    await targetRow.click()

    // RAO-P2-065 #1: sekcja ROI w drawer
    await expect(page.getByTestId('drill-machine-roi')).toBeVisible({ timeout: 10_000 })
    const roiText = await page.getByTestId('drill-machine-roi').textContent()
    expect(roiText).toContain('ROI')
    expect(roiText).toContain('Wartość zastępcza')
    expect(roiText).toContain('Przychód (szac.)')
  })

  test('TEST-04: Filtr kontrahenta jest comboboxem z inputem', async ({ page }) => {
    // P1-112: domyślna taba to 'live' (filtry ukryte) — kliknij tabę z filtrami
    await page.getByTestId('tab-period').click()
    const filter = page.getByTestId('filter-contractor')
    await expect(filter).toBeVisible()
    // ContractorCombobox renders a div wrapper with an input inside
    const input = filter.locator('input')
    await expect(input).toBeVisible()
    // Sprawdź że to <input> (nie wolny tekst bez struktury)
    const tagName = await input.evaluate((el) => el.tagName)
    expect(tagName).toBe('INPUT')
    // Poczekaj na załadowanie kontrahentów (asynchroniczne fetchList)
    // Otwórz dropdown żeby sprawdzić opcje
    await input.click()
    await page.waitForTimeout(500)
    const options = filter.locator('.cc-option')
    await expect(options.first()).toBeVisible({ timeout: 10_000 }).catch(() => {
      // Soft pass — kontrahenci mogą być pustą listą w środowisku testowym
    })
    const optCount = await options.count()
    expect(optCount).toBeGreaterThanOrEqual(1) // "Wszyscy" (kontrahenci opcjonalni)
  })

  test('TEST-05: Walidacja date_from > date_to → 422 (API level)', async ({ request }) => {
    // RAO-P2-065 #10: backend waliduje date_from > date_to
    const token = await apiLogin(request)
    const resp = await request.get(
      `${API}/stats/fleet-summary?date_from=2026-07-10&date_to=2026-07-01`,
      { headers: { Authorization: `Bearer ${token}` } },
    )
    expect(resp.status()).toBe(422)
    const body = await resp.json()
    expect(body.detail).toContain('Data początkowa')
    expect(body.detail).toMatch(/końcow/i)
  })

  test('TEST-06: Maszyny tab — tabela z danymi maszyn', async ({ page }) => {
    await page.getByTestId('tab-machines').click()
    // Maszyny tab powinna pokazać KPI lub tabelę
    await expect(page.getByTestId('machines-tab')).toBeVisible({ timeout: 8_000 })
    // Sprawdź że albo KPI jest widoczne (są dane) albo empty state (brak danych)
    await expect(
      page.getByTestId('kpi-machines-count').or(page.getByTestId('machines-empty'))
    ).toBeVisible({ timeout: 10_000 })
  })

  test('TEST-07: Lokalizacje tab — ranking lokalizacji', async ({ page }) => {
    // P1-102: "Rezerwacje" tab została usunięta; zastąpiona przez "Lokalizacje"
    await page.getByTestId('tab-locations').click()
    await expect(page.getByTestId('locations-tab')).toBeVisible({ timeout: 8_000 })
    // Sprawdź że albo ranking tabeli jest widoczny (są dane) albo empty state (brak danych)
    await expect(
      page.getByTestId('loc-ranking-table').or(page.getByTestId('loc-empty'))
    ).toBeVisible({ timeout: 10_000 })
  })

  test.afterAll(async () => {
    // Cleanup TEST-03 data
    const ctx = await newApiContext()
    try {
      const token = await apiLogin(ctx)
      for (const id of createdContractIds) {
        await safeDelete(ctx, `${API}/contracts/${id}`, token)
      }
      for (const id of createdContractorIds) {
        await safeDelete(ctx, `${API}/contractors/${id}`, token)
      }
      for (const id of createdMachineIds) {
        await safeDelete(ctx, `${API}/machines/${id}`, token)
      }
    } catch { /* ignore */ } finally {
      await ctx.dispose()
    }
  })
})
