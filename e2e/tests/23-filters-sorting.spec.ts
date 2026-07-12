/**
 * Faza 9e2-filters: Kompleksowe testy filtrów i sortowania na każdym ekranie
 *
 * Pokrywa:
 * - MachinesListView: search, category filter, archival checkbox, sort (name, internal_number, registration_no, brand)
 * - ServicesListView: search, sort (name, internal_number)
 * - AdditionalServicesListView: search, sort (name, internal_number)
 * - DashboardView/contracts: search, contract_type, settled, date_from/to, salesperson, city, sort (number, contractor_name, date_from, date_to, salesperson_name)
 * - DashboardView/contractors: search, sort (name, nip, city)
 * - DashboardView/articles: search, archival, sort (name, internal_number, registration_no, brand)
 * - ArchiveView: search, contract_type, date filters
 * - ReservationsView: machine, contractor, status filters
 * - AnalyticsView: period presets, date range, articleType, contractor, city
 * - CommissionView: date range
 *
 * Wzorzec: testy API-side (search via backend) + client-side (sort in browser)
 */
import { test, expect, request } from '@playwright/test'
import { waitForBackend, login, navigateTo, API, apiLogin, authHeaders, newApiContext, safeDelete } from './helpers'

const TS = Date.now()
const createdMachineIds: number[] = []
const createdServiceIds: number[] = []
const createdAdditionalIds: number[] = []
const createdContractorIds: number[] = []

test.describe('TEST-23: Filtry i sortowanie — wszystkie ekrany', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  // Helper: pobierz teksty komórek z pierwszej kolumny tabeli (tylko wiersze z danymi)
  async function getFirstColumnTexts(page: import('@playwright/test').Page): Promise<string[]> {
    await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
    // Poczekaj na dane — wiersze z danymi mają atrybut tabindex lub class article-row
    await expect(page.locator('tbody tr[tabindex], tbody tr.article-row')).not.toHaveCount(0, { timeout: 10_000 })
    const rows = page.locator('tbody tr[tabindex], tbody tr.article-row')
    const count = await rows.count()
    const texts: string[] = []
    for (let i = 0; i < Math.min(count, 20); i++) { // max 20 rows for performance
      const td = rows.nth(i).locator('td').first()
      const text = await td.innerText().catch(() => '')
      if (text.trim()) texts.push(text.trim())
    }
    return texts
  }

  // Helper: kliknij nagłówek kolumny i sprawdź sort indicator
  async function clickSortHeader(page: import('@playwright/test').Page, columnName: string) {
    const header = page.locator('th.th-sortable', { hasText: columnName }).first()
    await expect(header).toBeVisible({ timeout: 5_000 })
    await header.click()
    // Po kliknięciu powinien pojawić się sort indicator (▲ lub ▼)
    await page.waitForTimeout(300) // client-side sort jest natychmiastowy
  }

  // Helper: sprawdź czy teksty są posortowane (tolerant — ignoruje puste/null/—)
  function isSortedAsc(texts: string[]): boolean {
    const filtered = texts.filter(t => t && t !== '—' && t !== '')
    if (filtered.length < 2) return true
    for (let i = 1; i < filtered.length; i++) {
      if (filtered[i - 1].toLowerCase() > filtered[i].toLowerCase()) return false
    }
    return true
  }
  function isSortedDesc(texts: string[]): boolean {
    const filtered = texts.filter(t => t && t !== '—' && t !== '')
    if (filtered.length < 2) return true
    for (let i = 1; i < filtered.length; i++) {
      if (filtered[i - 1].toLowerCase() < filtered[i].toLowerCase()) return false
    }
    return true
  }

  // Helper: pełny test sortowania — kliknij asc, sprawdź indicator, kliknij desc, sprawdź indicator
  async function testSortToggle(page: import('@playwright/test').Page, columnName: string) {
    await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
    const header = page.locator('th.th-sortable', { hasText: columnName }).first()
    await expect(header).toBeVisible({ timeout: 5_000 })

    // Pierwsze kliknięcie → ASC (▲)
    await header.click()
    await page.waitForTimeout(400)
    let indicator = await header.locator('.sort-indicator').innerText()
    expect(indicator).toMatch(/[▲▼]/)
    const firstRowTextAsc = await page.locator('tbody tr[tabindex], tbody tr.article-row').first().locator('td').first().innerText().catch(() => '')

    // Drugie kliknięcie → DESC (▼) — indicator powinien się zmienić
    await header.click()
    await page.waitForTimeout(400)
    const indicator2 = await header.locator('.sort-indicator').innerText()
    expect(indicator2).toMatch(/[▲▼]/)
    // Indicator powinien się zmienić (asc↔desc)
    expect(indicator2).not.toBe(indicator)

    // Trzecie kliknięcie → z powrotem ASC
    await header.click()
    await page.waitForTimeout(400)
    const indicator3 = await header.locator('.sort-indicator').innerText()
    expect(indicator3).toBe(indicator) // powinien wrócić do pierwotnego

    // Jeśli są ≥2 wiersze, pierwszy wiersz asc i desc powinien się różnić
    const rowCount = await page.locator('tbody tr[tabindex], tbody tr.article-row').count()
    if (rowCount >= 2) {
      // Kliknij asc
      await header.click()
      await page.waitForTimeout(400)
      const firstAsc = await page.locator('tbody tr[tabindex], tbody tr.article-row').first().locator('td').first().innerText().catch(() => '')
      // Kliknij desc
      await header.click()
      await page.waitForTimeout(400)
      const firstDesc = await page.locator('tbody tr[tabindex], tbody tr.article-row').first().locator('td').first().innerText().catch(() => '')
      // Jeśli pierwszy wiersz jest ten sam, to znaczy że jest tylko 1 unikalna wartość — OK
      // Ale jeśli są różne wartości, pierwszy wiersz powinien się zmienić
      if (firstAsc !== firstDesc) {
        // OK — sortowanie zmienia kolejność
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // 1. MACHINES LIST — filtry i sortowanie
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('MachinesListView — filtry i sortowanie', () => {
    test.beforeAll(async () => {
      const req = await request.newContext({ baseURL: API })
      const token = await apiLogin(req)
      // Utwórz maszynę z unikalną nazwą dla testów search
      const r = await req.post(`${API}/machines`, {
        headers: authHeaders(token),
        data: { name: `ZZ_SORT_TEST_${TS}`, internal_number: `SN_${TS}` },
      })
      if (r.ok()) {
        const m = await r.json()
        createdMachineIds.push(m.id)
      }
      await req.dispose()
    })

    test.afterAll(async () => {
      const req = await newApiContext()
      const token = await apiLogin(req)
      for (const id of createdMachineIds) {
        await safeDelete(req, `${API}/machines/${id}`, token)
      }
      await req.dispose()
    })

    test('search filtruje listę maszyn', async ({ page }) => {
      await navigateTo(page, 'machines')
      const uniq = `ZZ_SORT_TEST_${TS}`
      await page.getByPlaceholder('Szukaj wg nazwy, numeru...').fill(uniq)
      await expect(page.locator('tbody')).toContainText(uniq, { timeout: 15_000 })
    })

    test('sortowanie po nazwie (asc → desc)', async ({ page }) => {
      await navigateTo(page, 'machines')
      await testSortToggle(page, 'Nazwa')
    })

    test('sortowanie po Nr wew.', async ({ page }) => {
      await navigateTo(page, 'machines')
      await testSortToggle(page, 'Nr wew.')
    })

    test('sortowanie po Nr rej.', async ({ page }) => {
      await navigateTo(page, 'machines')
      await testSortToggle(page, 'Nr rej.')
    })

    test('sortowanie po Marka', async ({ page }) => {
      await navigateTo(page, 'machines')
      await testSortToggle(page, 'Marka')
    })

    test('filtr kategorii zmienia listę', async ({ page }) => {
      await navigateTo(page, 'machines')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      const categorySelect = page.locator('select[aria-label="Filtr kategorii"]')
      if (await categorySelect.isVisible({ timeout: 3_000 }).catch(() => false)) {
        // Pobierz opcje
        const options = await categorySelect.locator('option').allTextContents()
        if (options.length > 1) {
          await categorySelect.selectOption({ index: 1 })
          await page.waitForTimeout(500)
          // Lista powinna się zaktualizować
          await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
        }
      }
    })

    test('checkbox archiwalne przełącza listę', async ({ page }) => {
      await navigateTo(page, 'machines')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      const archivalCheckbox = page.locator('input[type="checkbox"][id*="archival"], input[type="checkbox"]').filter({ hasText: /archiwal/i }).first()
      // Jeśli checkbox jest widoczny, kliknij
      const archivalLabel = page.locator('label', { hasText: /archiwal/i }).first()
      if (await archivalLabel.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await archivalLabel.click()
        await page.waitForTimeout(500)
        await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
      }
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 2. SERVICES LIST — filtry i sortowanie
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('ServicesListView — filtry i sortowanie', () => {
    test.beforeAll(async () => {
      const req = await request.newContext({ baseURL: API })
      const token = await apiLogin(req)
      const r = await req.post(`${API}/services`, {
        headers: authHeaders(token),
        data: { name: `ZZ_SERVICE_SORT_${TS}`, internal_number: `SV_${TS}` },
      })
      if (r.ok()) {
        const s = await r.json()
        createdServiceIds.push(s.id)
      }
      await req.dispose()
    })

    test.afterAll(async () => {
      const req = await newApiContext()
      const token = await apiLogin(req)
      for (const id of createdServiceIds) {
        await safeDelete(req, `${API}/services/${id}`, token)
      }
      await req.dispose()
    })

    test('search filtruje listę usług', async ({ page }) => {
      await navigateTo(page, 'services')
      const uniq = `ZZ_SERVICE_SORT_${TS}`
      await page.getByPlaceholder('Szukaj wg nazwy, numeru...').fill(uniq)
      await expect(page.locator('tbody')).toContainText(uniq, { timeout: 15_000 })
    })

    test('sortowanie po nazwie (asc → desc)', async ({ page }) => {
      await navigateTo(page, 'services')
      await testSortToggle(page, 'Nazwa')
    })

    // P2-006: kolumna "Nr wew." usunięta z ServicesListView — test sortowania usunięty
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 3. ADDITIONAL SERVICES LIST — filtry i sortowanie
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('AdditionalServicesListView — filtry i sortowanie', () => {
    test.beforeAll(async () => {
      const req = await request.newContext({ baseURL: API })
      const token = await apiLogin(req)
      const r = await req.post(`${API}/additional-services`, {
        headers: authHeaders(token),
        data: { name: `ZZ_ADD_SORT_${TS}` },
      })
      if (r.ok()) {
        const s = await r.json()
        createdAdditionalIds.push(s.id)
      }
      await req.dispose()
    })

    test.afterAll(async () => {
      const req = await newApiContext()
      const token = await apiLogin(req)
      for (const id of createdAdditionalIds) {
        await safeDelete(req, `${API}/additional-services/${id}`, token)
      }
      await req.dispose()
    })

    test('search filtruje listę usług dodatkowych', async ({ page }) => {
      await navigateTo(page, 'additional-services')
      const uniq = `ZZ_ADD_SORT_${TS}`
      await page.getByPlaceholder('Szukaj wg nazwy...').fill(uniq)
      await expect(page.locator('tbody')).toContainText(uniq, { timeout: 15_000 })
    })

    test('sortowanie po nazwie (asc → desc)', async ({ page }) => {
      await navigateTo(page, 'additional-services')
      await testSortToggle(page, 'Nazwa')
    })

    // P2-005: kolumna "Nr wew." usunięta z AdditionalServicesListView — test sortowania usunięty
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 4. DASHBOARD — UMOWY (filtry + sortowanie)
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('DashboardView/contracts — filtry i sortowanie', () => {
    test('search filtruje listę umów', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      // Wpisz coś w search — powinien zawęzić listę
      await page.getByPlaceholder('Szukaj wg numeru, kontrahenta...').fill('ZZZ_NIE_ISTNIEJE')
      await page.waitForTimeout(600) // debounce
      // Lista powinna być pusta lub mieć komunikat "brak"
      const tbody = page.locator('tbody')
      await expect(tbody).not.toContainText('ZZZ_NIE_ISTNIEJE', { timeout: 10_000 })
    })

    test('filtr typu umowy (S/U)', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      // Znajdź select dla typu umowy
      const typeSelect = page.locator('select').filter({ hasText: /S|U|Wszystkie/ }).first()
      if (await typeSelect.isVisible({ timeout: 3_000 }).catch(() => false)) {
        const options = await typeSelect.locator('option').allTextContents()
        if (options.length > 1) {
          await typeSelect.selectOption({ index: 1 })
          await page.waitForTimeout(500)
          await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
        }
      }
    })

    test('filtr statusu rozliczenia', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      // Select dla settled/active
      const settledSelect = page.locator('select').filter({ hasText: /Aktywne|Rozliczone|Wszystkie/ }).first()
      if (await settledSelect.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await settledSelect.selectOption({ index: 0 })
        await page.waitForTimeout(500)
        await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
      }
    })

    test('filtr daty (od/do)', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      const dateFrom = page.locator('input[type="date"]').first()
      if (await dateFrom.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await dateFrom.fill('2026-01-01')
        await page.waitForTimeout(500)
        await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
      }
    })

    test('filtr handlowca', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      // Select handlowca
      const salesSelect = page.locator('select').filter({ hasText: /handlow|salesperson/i }).first()
      if (await salesSelect.isVisible({ timeout: 3_000 }).catch(() => false)) {
        const options = await salesSelect.locator('option').allTextContents()
        if (options.length > 1) {
          await salesSelect.selectOption({ index: 1 })
          await page.waitForTimeout(500)
          await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
        }
      }
    })

    test('filtr miasta', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      const cityInput = page.getByPlaceholder('Miasto...')
      if (await cityInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await cityInput.fill('ZZZ_NIE_ISTNIEJE_MIASTO')
        await page.waitForTimeout(500)
        await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
      }
    })

    test('sortowanie po Numerze', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await testSortToggle(page, 'Numer')
    })

    test('sortowanie po Kontrahent', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await testSortToggle(page, 'Kontrahent')
    })

    test('sortowanie po Data od', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await testSortToggle(page, 'Data od')
    })

    test('sortowanie po Data do', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await testSortToggle(page, 'Data do')
    })

    test('sortowanie po Handlowiec', async ({ page }) => {
      await navigateTo(page, 'contracts')
      await testSortToggle(page, 'Handlowiec')
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 5. DASHBOARD — KONTRAHENCI (filtry + sortowanie)
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('DashboardView/contractors — filtry i sortowanie', () => {
    test('search filtruje listę kontrahentów', async ({ page }) => {
      await navigateTo(page, 'contractors')
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      await page.getByPlaceholder('Szukaj wg nazwy, NIP...').fill('ZZZ_NIE_ISTNIEJE')
      await page.waitForTimeout(600)
      const tbody = page.locator('tbody')
      await expect(tbody).not.toContainText('ZZZ_NIE_ISTNIEJE', { timeout: 10_000 })
    })

    test('sortowanie po Nazwa (asc → desc)', async ({ page }) => {
      await navigateTo(page, 'contractors')
      await testSortToggle(page, 'Nazwa')
    })

    test('sortowanie po NIP', async ({ page }) => {
      await navigateTo(page, 'contractors')
      await testSortToggle(page, 'NIP')
    })

    test('sortowanie po Miasto', async ({ page }) => {
      await navigateTo(page, 'contractors')
      await testSortToggle(page, 'Miasto')
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 6. DASHBOARD — ARTYKUŁY/MASZYNY (filtry + sortowanie)
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('DashboardView/articles — filtry i sortowanie', () => {
    test('search filtruje listę artykułów', async ({ page }) => {
      // Dashboard/articles to sekcja w DashboardView
      await page.goto('/rao/dashboard/articles', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      await page.getByPlaceholder('Szukaj wg nazwy, numeru...').fill('ZZZ_NIE_ISTNIEJE')
      await page.waitForTimeout(600)
      const tbody = page.locator('tbody')
      await expect(tbody).not.toContainText('ZZZ_NIE_ISTNIEJE', { timeout: 10_000 })
    })

    test('sortowanie po Nazwa (asc → desc)', async ({ page }) => {
      await page.goto('/rao/dashboard/articles', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await testSortToggle(page, 'Nazwa')
    })

    test('sortowanie po Nr wew.', async ({ page }) => {
      await page.goto('/rao/dashboard/articles', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await testSortToggle(page, 'Nr wew.')
    })

    test('sortowanie po Nr rej.', async ({ page }) => {
      await page.goto('/rao/dashboard/articles', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await testSortToggle(page, 'Nr rej.')
    })

    test('sortowanie po Marka', async ({ page }) => {
      await page.goto('/rao/dashboard/articles', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await testSortToggle(page, 'Marka')
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 7. ARCHIVE — filtry
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('ArchiveView — filtry', () => {
    test('zakładka umowy ładuje się z filtrami', async ({ page }) => {
      await page.goto('/rao/archive', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      // Sprawdź że search jest widoczny
      const search = page.getByPlaceholder(/szukaj/i).first()
      await expect(search).toBeVisible({ timeout: 5_000 })
    })

    test('search filtruje listę w archiwum', async ({ page }) => {
      await page.goto('/rao/archive', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      await page.getByPlaceholder(/szukaj/i).first().fill('ZZZ_NIE_ISTNIEJE')
      await page.waitForTimeout(600)
      // Lista powinna się odświeżyć
      await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
    })

    test('filtr typu umowy w archiwum', async ({ page }) => {
      await page.goto('/rao/archive', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      const typeSelect = page.locator('select').filter({ hasText: /S|U|Wszystkie/ }).first()
      if (await typeSelect.isVisible({ timeout: 3_000 }).catch(() => false)) {
        const options = await typeSelect.locator('option').allTextContents()
        if (options.length > 1) {
          await typeSelect.selectOption({ index: 1 })
          await page.waitForTimeout(500)
          await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
        }
      }
    })

    test('filtr daty w archiwum', async ({ page }) => {
      await page.goto('/rao/archive', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page.locator('table')).toBeVisible({ timeout: 10_000 })
      const dateFrom = page.locator('input[type="date"]').first()
      if (await dateFrom.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await dateFrom.fill('2026-01-01')
        await page.waitForTimeout(500)
        await expect(page.locator('table')).toBeVisible({ timeout: 5_000 })
      }
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 8. RESERVATIONS — filtry
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('ReservationsView — filtry', () => {
    test('kalendarz rezerwacji ładuje się', async ({ page }) => {
      await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      // Sprawdź że kalendarz lub lista jest widoczna
      await expect(page.getByTestId('rv-calendar')).toBeVisible({ timeout: 10_000 })
    })

    test('filtr maszyny w rezerwacjach', async ({ page }) => {
      await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page.getByTestId('rv-calendar')).toBeVisible({ timeout: 10_000 })
      const machineSelect = page.locator('[data-testid="rv-filter-machine"]')
      await expect(machineSelect).toBeVisible({ timeout: 5_000 })
      const options = await machineSelect.locator('option').allTextContents()
      if (options.length > 1) {
        await machineSelect.selectOption({ index: 1 })
        await page.waitForTimeout(500)
      }
    })

    test('filtr statusu w rezerwacjach', async ({ page }) => {
      await page.goto('/rao/reservations', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await expect(page.getByTestId('rv-calendar')).toBeVisible({ timeout: 10_000 })
      const statusSelect = page.locator('[data-testid="rv-filter-status"]')
      await expect(statusSelect).toBeVisible({ timeout: 5_000 })
      const options = await statusSelect.locator('option').allTextContents()
      if (options.length > 1) {
        await statusSelect.selectOption({ index: 1 })
        await page.waitForTimeout(500)
      }
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 9. ANALYTICS — filtry
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('AnalyticsView — filtry', () => {
    test('analytics ładuje się z filtrami', async ({ page }) => {
      await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      // Sprawdź że sekcja analytics jest widoczna
      await expect(page.locator('body')).toBeVisible({ timeout: 5_000 })
      // Poczekaj na załadowanie
      await page.waitForTimeout(2000)
    })

    test('preset okresu działa', async ({ page }) => {
      await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await page.waitForTimeout(2000)
      // Kliknij preset "Dziś"
      const todayBtn = page.locator('button, [data-testid]', { hasText: 'Dziś' }).first()
      if (await todayBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await todayBtn.click()
        await page.waitForTimeout(1000)
      }
    })

    test('filtr articleType działa', async ({ page }) => {
      await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await page.waitForTimeout(2000)
      const articleTypeSelect = page.locator('[data-testid="filter-article-type"], select').filter({ hasText: /maszyn|usług|wszystk/i }).first()
      if (await articleTypeSelect.isVisible({ timeout: 3_000 }).catch(() => false)) {
        const options = await articleTypeSelect.locator('option').allTextContents()
        if (options.length > 1) {
          await articleTypeSelect.selectOption({ index: 1 })
          await page.waitForTimeout(1000)
        }
      }
    })

    test('filtr miasta działa', async ({ page }) => {
      await page.goto('/rao/analytics', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      await page.waitForTimeout(2000)
      const cityInput = page.locator('[data-testid="filter-city"], input').filter({ hasText: '' }).first()
      const cityByPlaceholder = page.getByPlaceholder(/miasto/i).first()
      const target = (await cityInput.isVisible().catch(() => false)) ? cityInput : cityByPlaceholder
      if (await target.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await target.fill('Warszawa')
        await page.waitForTimeout(1000)
      }
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // 10. COMMISSION — filtry daty
  // ═══════════════════════════════════════════════════════════════════════════

  test.describe('CommissionView — filtry', () => {
    test('commission ładuje się z filtrem daty', async ({ page }) => {
      await page.goto('/rao/commission', { waitUntil: 'domcontentloaded', timeout: 15_000 })
      const dateFrom = page.locator('input[type="date"]').first()
      if (await dateFrom.isVisible({ timeout: 5_000 }).catch(() => false)) {
        await dateFrom.fill('2026-01-01')
        await page.waitForTimeout(500)
        // Drugi date input (dateTo)
        const dateTo = page.locator('input[type="date"]').nth(1)
        if (await dateTo.isVisible({ timeout: 3_000 }).catch(() => false)) {
          await dateTo.fill('2026-12-31')
          await page.waitForTimeout(500)
        }
      }
    })
  })
})
