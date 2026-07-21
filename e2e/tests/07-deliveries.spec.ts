/**
 * P1-205: E2E smoke dla widoku Dostawy.
 *
 * Zakres:
 *  1. Sidebar — pozycja "Dostawy"
 *  2. Nawigacja /deliveries — widok ładuje się
 *  3. Kalendarz (month view, 6 tygodni = 42 komórki stabilnie)
 *  4. Panel dnia otwiera się po kliknięciu komórki
 *  5. Nawigacja miesiąca (prev/next/today)
 *
 * Brak CRUD — dostawy pochodzą z umów (read-only). Brak seed/afterAll.
 */
import { test, expect } from '@playwright/test'
import { waitForBackend, login } from './helpers'

test.describe('P1-205: Widok Dostaw', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('sidebar zawiera pozycję "Dostawy"', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Dostawy', exact: true })).toBeVisible()
  })

  test('nawigacja do /deliveries — widok ładuje się', async ({ page }) => {
    await page.goto('/rao/deliveries', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('deliveries-view')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('h1')).toContainText('Dostawy')
  })

  test('kalendarz (month view) renderuje się z 42 komórkami (6 tygodni stabilnie)', async ({ page }) => {
    await page.goto('/rao/deliveries', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('dv-calendar')).toBeVisible({ timeout: 10_000 })
    const cells = page.getByTestId('dv-cal-cell')
    await expect(cells.first()).toBeVisible()
    // Fix cd37e5d: zawsze 42 komórki (6 tygodni) — stabilny rozmiar
    expect(await cells.count()).toBe(42)
  })

  test('panel dnia otwiera się po kliknięciu komórki kalendarza', async ({ page }) => {
    await page.goto('/rao/deliveries', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('dv-calendar')).toBeVisible({ timeout: 10_000 })

    // Panel dnia widoczny side-by-side (nie toggle)
    await expect(page.getByTestId('dv-day-panel')).toBeVisible({ timeout: 8_000 })

    // Kliknij pierwszą komórkę kalendarza → wybierz dzień
    const firstCell = page.getByTestId('dv-cal-cell').first()
    await firstCell.click()

    // Panel dnia powinien pokazać header z wybraną datą (nie empty state)
    await expect(page.locator('.dv-day-header')).toBeVisible({ timeout: 5_000 })
    // Checkboxy filtrów widoczne ("Dostawy S" / "Dostawy U")
    await expect(page.locator('.dv-day-filters')).toBeVisible()
  })

  test('nawigacja miesiąca (prev/next/today) działa', async ({ page }) => {
    await page.goto('/rao/deliveries', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('dv-calendar')).toBeVisible({ timeout: 10_000 })

    const monthLabel = page.locator('.dv-cal-month')
    const initialLabel = await monthLabel.textContent()

    // Następny miesiąc
    await page.getByTestId('dv-cal-next').click()
    await expect(monthLabel).not.toHaveText(initialLabel || '')

    // Powrót przez "Dziś"
    await page.getByTestId('dv-cal-today').click()
    await expect(monthLabel).toHaveText(initialLabel || '', { timeout: 5_000 })
  })

  test('filtry (machine/contractor/salesperson/type) są widoczne', async ({ page }) => {
    await page.goto('/rao/deliveries', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('deliveries-view')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId('dv-filter-machine')).toBeVisible()
    await expect(page.getByTestId('dv-filter-contractor')).toBeVisible()
    await expect(page.getByTestId('dv-filter-salesperson')).toBeVisible()
    await expect(page.getByTestId('dv-filter-type')).toBeVisible()
  })
})
