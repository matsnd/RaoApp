import { test, expect, type Page, type Request } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'
import { login, waitForBackend, BASE } from './helpers'

// ============================================================================
// QA AUDIT: Analytics — wszystkie filtry x wszystkie taby
// Zbiera wartości UI (KPI + tabele) + przechwycone requesty API do JSON.
// NIE modyfikuje kodu aplikacji — tylko test.
// ============================================================================

interface ApiCall {
  method: string
  url: string
  params: Record<string, string>
  ts: string
}

interface KpiSnapshot {
  testId: string
  value: string
  label: string
  sub: string
}

interface TableSnapshot {
  section: string
  columns: string[]
  rows: string[][]
  rowCount: number
  empty?: string
}

interface TabSnapshot {
  tab: string
  kpi: KpiSnapshot[]
  tables: TableSnapshot[]
  extraText: Record<string, string>
  visible: boolean
  error?: string
}

interface ScenarioResult {
  scenario: string
  description: string
  filters: {
    preset: string
    articleType: string
    contractorId: string
    contractorName: string
    city: string
    dateFrom: string
    dateTo: string
  }
  apiCalls: ApiCall[]
  tabs: TabSnapshot[]
  filtersPanelVisible: boolean
  notes: string[]
}

const OUT_FILE = path.join(__dirname, '..', 'analytics_filters_audit_results.json')
const results: ScenarioResult[] = []

// ── Helpers ekstrakcji UI ────────────────────────────────────────────────────

async function captureApiCalls(page: Page, fn: () => Promise<void>): Promise<ApiCall[]> {
  const calls: ApiCall[] = []
  const handler = (req: Request) => {
    const u = req.url()
    if (!u.includes('/rao/api/')) return
    if (req.method() !== 'GET') return
    // pomijamy health/auth/contractors list (noise)
    if (u.includes('/auth/') || u.includes('/health') || u.includes('/contractors?')) return
    const url = new URL(u)
    const params: Record<string, string> = {}
    url.searchParams.forEach((v, k) => { params[k] = v })
    calls.push({
      method: req.method(),
      url: url.pathname,
      params,
      ts: new Date().toISOString(),
    })
  }
  page.on('request', handler)
  try {
    await fn()
    await page.waitForTimeout(2500)
  } finally {
    page.off('request', handler)
  }
  return calls
}

async function readKpi(page: Page): Promise<KpiSnapshot[]> {
  const cards = page.locator('[data-testid="kpi-row"] .kpi-card')
  const count = await cards.count()
  const out: KpiSnapshot[] = []
  for (let i = 0; i < count; i++) {
    const c = cards.nth(i)
    const testId = (await c.getAttribute('data-testid')) || `kpi-card-${i}`
    const value = (await c.locator('.kpi-value').textContent())?.trim() || ''
    const label = (await c.locator('.kpi-label').textContent())?.trim() || ''
    let sub = ''
    const subLoc = c.locator('.kpi-sub')
    if (await subLoc.count() > 0) sub = (await subLoc.textContent())?.trim() || ''
    out.push({ testId, value, label, sub })
  }
  return out
}

async function readTable(page: Page, section: string, tableLoc: import('@playwright/test').Locator): Promise<TableSnapshot> {
  const empty = tableLoc.locator('[data-testid="analytics-table-empty"]')
  if (await empty.count() > 0) {
    return { section, columns: [], rows: [], rowCount: 0, empty: (await empty.textContent())?.trim() || '' }
  }
  const loading = tableLoc.locator('[data-testid="analytics-table-loading"]')
  if (await loading.count() > 0) {
    return { section, columns: [], rows: [], rowCount: 0, empty: 'LOADING' }
  }
  const ths = tableLoc.locator('thead th')
  const thCount = await ths.count()
  const columns: string[] = []
  for (let i = 0; i < thCount; i++) {
    const labelEl = ths.nth(i).locator('.th-label')
    let txt = ''
    if (await labelEl.count() > 0) txt = (await labelEl.textContent())?.trim() || ''
    if (!txt) txt = (await ths.nth(i).textContent())?.trim() || ''
    columns.push(txt.replace(/\s+/g, ' '))
  }
  const trs = tableLoc.locator('tbody tr')
  const trCount = await trs.count()
  const rows: string[][] = []
  for (let i = 0; i < Math.min(trCount, 50); i++) {
    const tds = trs.nth(i).locator('td')
    const tdCount = await tds.count()
    const row: string[] = []
    for (let j = 0; j < tdCount; j++) {
      row.push(((await tds.nth(j).textContent())?.trim() || '').replace(/\s+/g, ' '))
    }
    rows.push(row)
  }
  return { section, columns, rows, rowCount: trCount }
}

async function snapshotTab(page: Page, tab: 'live' | 'period' | 'locations' | 'explorer'): Promise<TabSnapshot> {
  const result: TabSnapshot = { tab, kpi: [], tables: [], extraText: {}, visible: false }
  try {
    await page.locator(`[data-testid="tab-${tab}"]`).click()
    await page.waitForTimeout(1500)

    const filtersVisible = await page.locator('[data-testid="analytics-filters"]').count()
    result.visible = filtersVisible > 0

    result.kpi = await readKpi(page)

    if (tab === 'period') {
      const periodRoot = page.locator('[data-testid="period-rental-tab"]')
      const sections = periodRoot.locator('.pr-section')
      const sCount = await sections.count()
      for (let i = 0; i < sCount; i++) {
        const sec = sections.nth(i)
        const titleEl = sec.locator('.pr-section-title')
        const title = ((await titleEl.textContent())?.trim() || '').replace(/\s+/g, ' ')
        const tbl = sec.locator('[data-testid="analytics-table"]')
        if (await tbl.count() > 0) {
          result.tables.push(await readTable(page, title, tbl.first()))
        }
      }
      const rb = page.locator('[data-testid="revenue-breakdown"]')
      if (await rb.count() > 0) {
        result.extraText['revenue-breakdown'] = ((await rb.textContent())?.trim() || '').replace(/\s+/g, ' ')
      }
    } else if (tab === 'live') {
      const liveRoot = page.locator('[data-testid="live-fleet-tab"]')
      const sec = liveRoot.locator('.lf-section [data-testid="analytics-table"]')
      if (await sec.count() > 0) {
        result.tables.push(await readTable(page, 'Maszyny aktualnie wynajęte', sec.first()))
      }
      const utilBar = liveRoot.locator('[data-testid="live-util-bar"]')
      if (await utilBar.count() > 0) {
        result.extraText['util-bar'] = ((await utilBar.textContent())?.trim() || '').replace(/\s+/g, ' ')
      }
    } else if (tab === 'locations') {
      const locRoot = page.locator('[data-testid="locations-tab"]')
      const tbl = locRoot.locator('[data-testid="analytics-table"]')
      if (await tbl.count() > 0) {
        result.tables.push(await readTable(page, 'Ranking lokalizacji', tbl.first()))
      }
      const chart = locRoot.locator('[data-testid="loc-chart"]')
      if (await chart.count() > 0) {
        const bars = chart.locator('.loc-bar-row')
        const bCount = await bars.count()
        const barTexts: string[] = []
        for (let i = 0; i < Math.min(bCount, 10); i++) {
          barTexts.push(((await bars.nth(i).textContent())?.trim() || '').replace(/\s+/g, ' '))
        }
        result.extraText['chart-bars'] = barTexts.join(' | ')
      }
    } else if (tab === 'explorer') {
      const exRoot = page.locator('[data-testid="explorer-tab"]')
      const summary = exRoot.locator('[data-testid="explorer-summary"]')
      if (await summary.count() > 0) {
        result.extraText['summary'] = ((await summary.textContent())?.trim() || '').replace(/\s+/g, ' ')
      }
      const tbl = exRoot.locator('[data-testid="analytics-table"]')
      if (await tbl.count() > 0) {
        result.tables.push(await readTable(page, 'Wyniki wyszukiwania', tbl.first()))
      }
    }
  } catch (e: any) {
    result.error = e?.message || String(e)
  }
  return result
}

async function readFiltersState(page: Page): Promise<ScenarioResult['filters']> {
  let preset = ''
  for (const p of ['today', 'week', 'month', 'quarter', 'year', 'all', 'custom']) {
    const btn = page.locator(`[data-testid="preset-${p}"]`)
    if (await btn.count() > 0) {
      const cls = (await btn.getAttribute('class')) || ''
      if (cls.includes('active')) { preset = p; break }
    }
  }
  const sel = page.locator('[data-testid="filter-article-type"]')
  const articleType = (await sel.count()) > 0 ? (await sel.inputValue()) : 'n/a'
  const cityInput = page.locator('[data-testid="filter-city"]')
  const city = (await cityInput.count()) > 0 ? (await cityInput.inputValue()) : ''
  const contractorInput = page.locator('[data-testid="filter-contractor-input"]')
  const contractorName = (await contractorInput.count()) > 0 ? (await contractorInput.inputValue()) : ''
  const df = page.locator('[data-testid="filter-date-from"]')
  const dt = page.locator('[data-testid="filter-date-to"]')
  const dateFrom = (await df.count()) > 0 ? (await df.inputValue()) : ''
  const dateTo = (await dt.count()) > 0 ? (await dt.inputValue()) : ''
  return {
    preset,
    articleType,
    contractorId: contractorName ? `(name=${contractorName})` : '',
    contractorName,
    city,
    dateFrom,
    dateTo,
  }
}

// ── Akcje filtra ─────────────────────────────────────────────────────────────

async function clickPreset(page: Page, key: string) {
  await page.locator(`[data-testid="preset-${key}"]`).click()
  await page.waitForTimeout(1800)
}

async function setArticleType(page: Page, value: 'all' | 'machine' | 'service') {
  await page.locator('[data-testid="filter-article-type"]').selectOption(value)
  await page.waitForTimeout(1800)
}

async function setCity(page: Page, value: string) {
  const inp = page.locator('[data-testid="filter-city"]')
  await inp.fill('')
  if (value) await inp.fill(value)
  await page.waitForTimeout(1800)
}

async function pickFirstContractor(page: Page): Promise<string> {
  const toggle = page.locator('[data-testid="filter-contractor-toggle"]')
  await toggle.click()
  await page.waitForTimeout(500)
  const opts = page.locator('[data-testid="filter-contractor-dropdown"] .cc-option')
  const cnt = await opts.count()
  if (cnt < 2) { await page.keyboard.press('Escape'); return '' }
  const first = opts.nth(1)
  const name = ((await first.textContent())?.trim()) || ''
  await first.click()
  await page.waitForTimeout(1800)
  return name
}

async function setCustomRange(page: Page, from: string, to: string) {
  await page.locator('[data-testid="preset-custom"]').click()
  await page.waitForTimeout(500)
  await page.locator('[data-testid="filter-date-from"]').fill(from)
  await page.locator('[data-testid="filter-date-to"]').fill(to)
  await page.waitForTimeout(2000)
}

async function clearFilters(page: Page) {
  await page.locator('[data-testid="filter-clear"]').click()
  await page.waitForTimeout(2000)
}

// ── Setup ────────────────────────────────────────────────────────────────────

test.describe.configure({ mode: 'serial' })

test.describe('Analytics — audit filtrów x taby', () => {
  let page: Page

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
    await waitForBackend(page)
    await login(page)
    await page.goto(`${BASE}/analytics`, { waitUntil: 'domcontentloaded' })
    await page.waitForSelector('[data-testid="analytics-view"]', { timeout: 15_000 })
    await page.waitForTimeout(3000)
  })

  test.afterAll(async () => {
    try { await page.close() } catch { /* page może być już zamknięta po timeout */ }
    // MERGE z istniejącym plikiem (dedupe po scenario) — żeby retry nie tracił danych
    let existing: ScenarioResult[] = []
    try {
      if (fs.existsSync(OUT_FILE)) {
        existing = JSON.parse(fs.readFileSync(OUT_FILE, 'utf-8')) as ScenarioResult[]
      }
    } catch { /* ignore */ }
    const byKey = new Map<string, ScenarioResult>()
    for (const s of existing) byKey.set(s.scenario, s)
    for (const s of results) byKey.set(s.scenario, s) // nowe nadpisują stare
    const merged = Array.from(byKey.values())
    fs.writeFileSync(OUT_FILE, JSON.stringify(merged, null, 2), 'utf-8')
    console.log(`\n[AUDIT] Zapisano ${merged.length} scenariuszy do ${OUT_FILE}`)
  })

  // ── A. Baseline ─────────────────────────────────────────────────────────────
  test('A. baseline month/all/null/empty', async () => {
    const apiCalls = await captureApiCalls(page, async () => {
      if (await page.locator('[data-testid="filter-clear"]').count() > 0) {
        await clearFilters(page)
      }
    })
    const filters = await readFiltersState(page)
    const tabs: TabSnapshot[] = []
    for (const t of ['live', 'period', 'locations', 'explorer'] as const) {
      tabs.push(await snapshotTab(page, t))
    }
    results.push({
      scenario: 'A-baseline',
      description: 'preset=month, type=all, contractor=null, city=""',
      filters,
      apiCalls,
      tabs,
      filtersPanelVisible: filters.preset !== '',
      notes: ['Baseline — domyślny stan po wejściu na /analytics'],
    })
    expect(tabs.find(t => t.tab === 'period')?.kpi.length || 0).toBeGreaterThan(0)
  })

  // ── B. Zmiana preseta ───────────────────────────────────────────────────────
  for (const preset of ['today', 'week', 'quarter', 'year', 'all'] as const) {
    test(`B. preset=${preset} (period tab)`, async () => {
      const apiCalls = await captureApiCalls(page, async () => {
        await clickPreset(page, preset)
      })
      const periodTab = await snapshotTab(page, 'period')
      const filters = await readFiltersState(page)
      results.push({
        scenario: `B-preset-${preset}`,
        description: `preset=${preset}, type=all, contractor=null, city=""`,
        filters,
        apiCalls,
        tabs: [periodTab],
        filtersPanelVisible: true,
        notes: [`Zmiana tylko preseta — sprawdzamy czy KPI/Top maszyny reagują`],
      })
      expect(periodTab.kpi.length).toBeGreaterThan(0)
    })
  }

  // ── C. Zmiana typu ──────────────────────────────────────────────────────────
  for (const t of ['machine', 'service'] as const) {
    test(`C. articleType=${t} (period tab)`, async () => {
      await clickPreset(page, 'month')
      const apiCalls = await captureApiCalls(page, async () => {
        await setArticleType(page, t)
      })
      const periodTab = await snapshotTab(page, 'period')
      const filters = await readFiltersState(page)
      results.push({
        scenario: `C-type-${t}`,
        description: `preset=month, type=${t}, contractor=null, city=""`,
        filters,
        apiCalls,
        tabs: [periodTab],
        filtersPanelVisible: true,
        notes: [
          `PODEJRZANY BUG: fetchSummary ignoruje articleType — KPI powinno być takie same dla machine vs service`,
          `PODEJRZANY BUG: fetchPositions dostaje hardcoded type='all' (nie z filtra) — tabela Pozycje powinna być identyczna`,
          `PODEJRZANY BUG: fetchByCategory — czy articleType trafia do API? (store wysyła)`,
        ],
      })
      expect(periodTab.kpi.length).toBeGreaterThan(0)
    })
  }

  // ── D. Kontrahent ───────────────────────────────────────────────────────────
  test('D. contractor=pierwszy z listy (period tab)', async () => {
    await clickPreset(page, 'month')
    await setArticleType(page, 'all')
    let contractorName = ''
    const apiCalls = await captureApiCalls(page, async () => {
      contractorName = await pickFirstContractor(page)
    })
    const periodTab = await snapshotTab(page, 'period')
    const filters = await readFiltersState(page)
    results.push({
      scenario: 'D-contractor',
      description: `preset=month, type=all, contractor="${contractorName}", city=""`,
      filters,
      apiCalls,
      tabs: [periodTab],
      filtersPanelVisible: true,
      notes: [
        `PODEJRZANY BUG: fetchSummary ignoruje contractorId — KPI powinno być takie same jak baseline`,
        `PODEJRZANY BUG: fetchByCategory ignoruje contractorId — tabela Kategorie powinna być identyczna`,
        `fetchTopMachines / fetchAdditionalFees / fetchLocations / fetchPositions — czy wysyłają contractor_id?`,
      ],
    })
    expect(periodTab.kpi.length).toBeGreaterThan(0)
  })

  // ── E. Miasto ───────────────────────────────────────────────────────────────
  test('E. city="Warszawa" (period tab)', async () => {
    await clickPreset(page, 'month')
    await setArticleType(page, 'all')
    const clearC = page.locator('[data-testid="filter-contractor-clear"]')
    if (await clearC.count() > 0) { await clearC.click(); await page.waitForTimeout(1500) }
    const apiCalls = await captureApiCalls(page, async () => {
      await setCity(page, 'Warszawa')
    })
    const periodTab = await snapshotTab(page, 'period')
    const filters = await readFiltersState(page)
    results.push({
      scenario: 'E-city-warszawa',
      description: `preset=month, type=all, contractor=null, city="Warszawa"`,
      filters,
      apiCalls,
      tabs: [periodTab],
      filtersPanelVisible: true,
      notes: [
        `PODEJRZANY BUG: fetchSummary ignoruje city — KPI powinno być identyczne jak baseline`,
        `PODEJRZANY BUG: fetchByCategory ignoruje city — Kategorie identyczne`,
        `PODEJRZANY BUG: fetchLocations ignoruje city (store nie wysyła city do /stats/locations)`,
        `fetchTopMachines / fetchPositions — wysyłają city`,
      ],
    })
    expect(periodTab.kpi.length).toBeGreaterThan(0)
  })

  // ── F. Kombinacja ───────────────────────────────────────────────────────────
  test('F. kombinacja year+machine+contractor', async () => {
    await clearFilters(page)
    let contractorName = ''
    const apiCalls = await captureApiCalls(page, async () => {
      await clickPreset(page, 'year')
      await setArticleType(page, 'machine')
      contractorName = await pickFirstContractor(page)
    })
    const periodTab = await snapshotTab(page, 'period')
    const filters = await readFiltersState(page)
    results.push({
      scenario: 'F-combo-year-machine-contractor',
      description: `preset=year, type=machine, contractor="${contractorName}", city=""`,
      filters,
      apiCalls,
      tabs: [periodTab],
      filtersPanelVisible: true,
      notes: [`Kombinacja 3 filtrów — cross-check czy wszystkie parametry trafiają do API`],
    })
    expect(periodTab.kpi.length).toBeGreaterThan(0)
  })

  // ── G. Custom range ─────────────────────────────────────────────────────────
  test('G. custom range 2025-01-01..2025-12-31', async () => {
    await clearFilters(page)
    const apiCalls = await captureApiCalls(page, async () => {
      await setCustomRange(page, '2025-01-01', '2025-12-31')
    })
    const periodTab = await snapshotTab(page, 'period')
    const filters = await readFiltersState(page)
    results.push({
      scenario: 'G-custom-range',
      description: `preset=custom, dateFrom=2025-01-01, dateTo=2025-12-31, type=all`,
      filters,
      apiCalls,
      tabs: [periodTab],
      filtersPanelVisible: true,
      notes: [`Custom range — czy date_from/date_to trafiają do WSZYSTKICH endpointów?`],
    })
    expect(filters.preset).toBe('custom')
    expect(periodTab.kpi.length).toBeGreaterThan(0)
  })

  // ── H. Clear → baseline ─────────────────────────────────────────────────────
  test('H. clear → baseline month/all/null/empty', async () => {
    await setArticleType(page, 'service')
    await setCity(page, 'Kraków')
    const apiCalls = await captureApiCalls(page, async () => {
      await clearFilters(page)
    })
    const filters = await readFiltersState(page)
    const periodTab = await snapshotTab(page, 'period')
    results.push({
      scenario: 'H-clear',
      description: `Po kliknięciu "Wyczyść" — powinno wrócić do month/all/null/''`,
      filters,
      apiCalls,
      tabs: [periodTab],
      filtersPanelVisible: true,
      notes: [
        `Weryfikacja: preset=month, articleType=all, contractor=null, city=''`,
        `Czy clearFilters() emituje poprawny stan? czy watcher w PeriodRentalTab reaguje?`,
      ],
    })
    expect(filters.preset).toBe('month')
    expect(filters.articleType).toBe('all')
    expect(filters.city).toBe('')
    expect(filters.contractorName).toBe('')
  })

  // ── I. Cross-tab: czy filtry wpływają na locations/explorer? ────────────────
  test('I. cross-tab — locations/explorer ignorują contractor/city/type', async () => {
    await clearFilters(page)
    await setArticleType(page, 'machine')
    await setCity(page, 'Warszawa')
    let contractorName = ''
    const apiCalls = await captureApiCalls(page, async () => {
      contractorName = await pickFirstContractor(page)
      await snapshotTab(page, 'locations')
      await snapshotTab(page, 'explorer')
    })
    const filters = await readFiltersState(page)
    const locTab = await snapshotTab(page, 'locations')
    // przejdź na explorer i wpisz frazę
    await page.locator('[data-testid="tab-explorer"]').click()
    await page.waitForTimeout(1000)
    await page.locator('[data-testid="explorer-query"]').fill('Warszawa')
    await page.locator('[data-testid="explorer-search-btn"]').click()
    await page.waitForTimeout(2500)
    const exTab = await snapshotTab(page, 'explorer')
    results.push({
      scenario: 'I-cross-tab-filters-ignored',
      description: `Filtry ustawione (machine/Warszawa/${contractorName}) — sprawdzamy locations + explorer`,
      filters,
      apiCalls,
      tabs: [locTab, exTab],
      filtersPanelVisible: true,
      notes: [
        `PODEJRZANY BUG (potwierdzony w kodzie): LocationsTab i ExplorerTab dostają TYLKO dateFrom/dateTo — ignorują contractorId/city/articleType`,
        `Sprawdzić w apiCalls: czy /explorer/locations lub /explorer/search dostały contractor_id/city/article_type? (NIE powinny — bo store ich nie wysyła)`,
        `To oznacza że użytkownik ustawi filtr kontrahenta, przełączy na "Lokalizacje" i zobaczy dane dla WSZYSTKICH kontrahentów — mylące UX`,
      ],
    })
  })
})
