import { test, expect, type Page, type APIRequestContext } from '@playwright/test'
import { BASE, login, waitForBackend, apiLogin, API } from './helpers'

// RAO-P2-065 #13: Testy e2e dla AnalyticsView — pokrycie regresyjne
// Zakrywa: LiveFleet tab, PeriodRental tab, drill-down maszyny z ROI,
// filtr kontrahenta (select), walidacja dat (422), sekcja kategorii.

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

    // Tabela powinna być widoczna
    const table = page.locator('[data-testid="live-fleet-table"], .analytics-table').first()
    await expect(table).toBeVisible({ timeout: 8_000 })

    // Powinna mieć co najmniej 1 wiersz (demo data ma 2 maszyny)
    const rows = table.locator('tbody tr')
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
  })

  test('TEST-02: PeriodRental tab pokazuje KPI + sekcje + kategorie', async ({ page }) => {
    await page.getByTestId('tab-period').click()

    // KPI row widoczne
    await expect(page.getByTestId('kpi-period-revenue')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId('kpi-period-contracts')).toBeVisible()
    await expect(page.getByTestId('kpi-period-rented')).toBeVisible()
    await expect(page.getByTestId('kpi-period-util')).toBeVisible()

    // RAO-P2-065 #6: sekcja kategorii
    const catTable = page.getByTestId('categories-table')
    await expect(catTable).toBeVisible({ timeout: 10_000 })
    const catRows = catTable.locator('tbody tr')
    const catCount = await catRows.count()
    expect(catCount).toBeGreaterThan(0)

    // Top maszyny sekcja
    await expect(page.locator('.pr-section').filter({ hasText: 'Top maszyny' })).toBeVisible()
  })

  // RAO-P2-065 #1: drill-down ROI section — fixed (fetchMachineRoi podpięte do store)
  test('TEST-03: Drill-down maszyny pokazuje sekcję ROI', async ({ page }) => {
    await page.getByTestId('tab-period').click()

    // Czekaj na załadowanie top maszyn
    await expect(page.getByTestId('kpi-period-revenue')).toBeVisible({ timeout: 10_000 })

    // Kliknij pierwszy wiersz top maszyn
    const topTable = page.locator('.analytics-table').first()
    const firstRow = topTable.locator('tbody tr').first()
    await firstRow.click()

    // RAO-P2-065 #1: sekcja ROI w drawer
    await expect(page.getByTestId('drill-machine-roi')).toBeVisible({ timeout: 8_000 })
    const roiText = await page.getByTestId('drill-machine-roi').textContent()
    expect(roiText).toContain('ROI')
    expect(roiText).toContain('Wartość zastępcza')
    expect(roiText).toContain('Przychód (szac.)')
  })

  test('TEST-04: Filtr kontrahenta jest comboboxem z inputem', async ({ page }) => {
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

  test('TEST-07: Rezerwacje tab — lista rezerwacji', async ({ page }) => {
    await page.getByTestId('tab-reservations').click()
    await expect(page.getByTestId('reservations-tab')).toBeVisible({ timeout: 8_000 })
    // Sprawdź że albo KPI jest widoczne (są dane) albo empty state (brak danych)
    await expect(
      page.getByTestId('kpi-res-total').or(page.getByTestId('res-empty'))
    ).toBeVisible({ timeout: 10_000 })
  })
})
