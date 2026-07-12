/**
 * RAO-L (Phase 6 QA): E2E tests dla feature'a rezerwacji maszyn + analytics bugfixes.
 *
 * Zakres:
 *  1. Widok /reservations — ładowanie, kalendarz, toggle lista, modal dodawania
 *  2. Sidebar — pozycja "Rezerwacje"
 *  3. Analytics — ReservationsTab usunięty, LocationsTab ma filtry, ServicesTab bez "Nr wewnętrzny"
 */
import { test, expect } from '@playwright/test'
import { waitForBackend, login, apiLogin, authHeaders, API } from './helpers'

let reservationId = 0

test.describe('RAO-L: Widok Rezerwacji', () => {
  test.beforeAll(async ({ request }) => {
    // Seed: dodaj rezerwację aby lista/kalendarz miały dane
    const token = await apiLogin(request)
    const today = new Date()
    const from = today.toISOString().slice(0, 10)
    const to = new Date(today.getTime() + 7 * 86400000).toISOString().slice(0, 10)
    // Znajdź pierwszą maszynę
    const mr = await request.get(`${API}/machines?limit=1`, { headers: authHeaders(token) })
    const machines = await mr.json()
    const machineArr = Array.isArray(machines) ? machines : machines.items
    if (machineArr.length > 0) {
      const rr = await request.post(`${API}/reservations`, {
        headers: authHeaders(token),
        data: { machine_id: machineArr[0].id, reserved_from: from, reserved_to: to, note: 'E2E seed' },
      })
      if (rr.status() === 201) {
        const r = await rr.json()
        reservationId = r.id
      }
    }
  })

  test.afterAll(async ({ request }) => {
    if (reservationId) {
      const token = await apiLogin(request)
      await request.delete(`${API}/reservations/${reservationId}`, { headers: authHeaders(token) })
    }
  })

  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('sidebar zawiera pozycję "Rezerwacje"', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Rezerwacje', exact: true })).toBeVisible()
  })

  test('nawigacja do /reservations — widok ładuje się', async ({ page }) => {
    await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('reservations-view')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('h1')).toContainText('Rezerwacje maszyn')
  })

  test('kalendarz (month view) renderuje się z gridem dni', async ({ page }) => {
    await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('rv-calendar')).toBeVisible({ timeout: 10_000 })
    // Przynajmniej 28 komórek kalendarza (nawet pusty miesiąc ma 28+)
    const cells = page.getByTestId('rv-cal-cell')
    await expect(cells.first()).toBeVisible()
    expect(await cells.count()).toBeGreaterThanOrEqual(28)
  })

  test('panel dnia otwiera się po kliknięciu komórki kalendarza (P1-111)', async ({ page }) => {
    await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('rv-calendar')).toBeVisible({ timeout: 10_000 })

    // P1-111: kalendarz i panel dnia side-by-side (nie toggle)
    // Panel dnia powinien być widoczny (empty state przed wyborem dnia)
    await expect(page.getByTestId('rv-day-panel')).toBeVisible({ timeout: 8_000 })

    // Kliknij pierwszą komórkę kalendarza → wybierz dzień
    const firstCell = page.getByTestId('rv-cal-cell').first()
    await firstCell.click()

    // Panel dnia powinien pokazać header z wybraną datą (nie empty state)
    await expect(page.locator('.rv-day-header')).toBeVisible({ timeout: 5_000 })
    // Checkboxes filtrów widoczne
    await expect(page.locator('.rv-day-filters')).toBeVisible()
  })

  test('modal dodawania rezerwacji otwiera się', async ({ page }) => {
    await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('reservations-view')).toBeVisible({ timeout: 10_000 })

    // Kliknij "+ Dodaj rezerwację"
    await page.getByTestId('rv-add-btn').click()
    // Modal powinien być widoczny — sprawdzamy po nagłówku h2
    await expect(page.getByRole('heading', { name: 'Nowa rezerwacja' })).toBeVisible({ timeout: 5_000 })
  })

  test('nawigacja miesiąca (prev/next/today) działa', async ({ page }) => {
    await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('rv-calendar')).toBeVisible({ timeout: 10_000 })

    const monthLabel = page.locator('.rv-cal-month')
    const initialLabel = await monthLabel.textContent()

    // Następny miesiąc
    await page.getByTestId('rv-cal-next').click()
    await expect(monthLabel).not.toHaveText(initialLabel || '')

    // Powrót przez "Dziś"
    await page.getByTestId('rv-cal-today').click()
    await expect(monthLabel).toHaveText(initialLabel || '', { timeout: 5_000 })
  })
})

test.describe('RAO-L: Analytics — bugfixes weryfikacja', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('ReservationsTab NIE występuje w analityce', async ({ page }) => {
    await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('analytics-tabs')).toBeVisible({ timeout: 10_000 })

    // Lista tabów — nie powinno być tab-rezervations
    const tabButtons = page.locator('[data-testid^="tab-"]')
    const count = await tabButtons.count()
    expect(count).toBeGreaterThan(0)

    // Sprawdź że żaden tab nie ma label "Rezerwacje"
    const labels = await tabButtons.allTextContents()
    for (const label of labels) {
      expect(label.toLowerCase()).not.toContain('rezerwacj')
    }
  })

  test('LocationsTab — filtry (contractor/city/articleType) są widoczne', async ({ page }) => {
    await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('analytics-tabs')).toBeVisible({ timeout: 10_000 })

    // Przejdź do tab Lokalizacje
    await page.getByTestId('tab-locations').click()

    // Filtry współdzielone powinny być widoczne — contractor, city, articleType
    await expect(page.getByTestId('filter-contractor')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('filter-city')).toBeVisible()
    await expect(page.getByTestId('filter-article-type')).toBeVisible()
  })

  test('ServicesAdditionalTab — brak kolumny "Nr wewnętrzny"', async ({ page }) => {
    await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('analytics-tabs')).toBeVisible({ timeout: 10_000 })

    // Przejdź do tab Usługi dodatkowe
    await page.getByTestId('tab-services-s').click()

    // Poczekaj na załadowanie zawartości taba
    await page.waitForTimeout(2000)

    // Sprawdź nagłówki tabeli — nie powinno być "Nr wewnętrzny"
    const headers = page.locator('thead th')
    const headerTexts = await headers.allTextContents()
    for (const h of headerTexts) {
      expect(h.toLowerCase()).not.toContain('nr wewnętrzny')
    }
  })

  test('ServicesRegularTab — brak kolumny "Nr wewnętrzny"', async ({ page }) => {
    await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByTestId('analytics-tabs')).toBeVisible({ timeout: 10_000 })

    // Przejdź do tab Usługi zwykłe
    await page.getByTestId('tab-services-u').click()

    await page.waitForTimeout(2000)

    const headers = page.locator('thead th')
    const headerTexts = await headers.allTextContents()
    for (const h of headerTexts) {
      expect(h.toLowerCase()).not.toContain('nr wewnętrzny')
    }
  })
})
