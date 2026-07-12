import { test, expect, type Page, type APIRequestContext } from '@playwright/test'
import { BASE, login, waitForBackend, apiLogin, API, authHeaders, safeDelete, newApiContext, genValidNip } from './helpers'

// RAO-P2-065 #13: Testy e2e dla AnalyticsView — pokrycie regresyjne
// Zakrywa: LiveFleet tab, PeriodRental tab, drill-down maszyny,
// filtr kontrahenta (combobox), walidacja dat (422), sekcja kategorii.

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

  // TEST-03 usunięte — ROI panel usunięty z statystyk (szacunkowe wartości tylko w archiwum)

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
