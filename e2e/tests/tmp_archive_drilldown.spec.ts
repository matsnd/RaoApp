import { test, expect } from '@playwright/test'
import { waitForBackend, login } from './helpers'
import * as fs from 'fs'
import * as path from 'path'

const SHOTS_DIR = path.join(__dirname, '..', 'screenshots')

test.describe('TMP: Archive drill-down screenshots', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    if (!fs.existsSync(SHOTS_DIR)) fs.mkdirSync(SHOTS_DIR, { recursive: true })
  })

  test('archive stats + drill-down drawer (machine + city)', async ({ page }) => {
    // Przechwytuj błędy JS w konsoli
    const consoleErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })
    page.on('pageerror', (err) => consoleErrors.push(`PAGEERROR: ${err.message}`))

    // Viewport 1440x900 zgodnie z wymaganiami
    await page.setViewportSize({ width: 1440, height: 900 })

    await login(page)
    await page.goto('/rao/archive', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page).toHaveURL(/\/rao\/archive/, { timeout: 8_000 })

    const statsTab = page.locator('.archive-tab', { hasText: 'Statystyki' })
    await expect(statsTab).toBeVisible({ timeout: 8_000 })
    await statsTab.click()

    await expect(page.locator('.stats-card-header', { hasText: 'Top maszyny' })).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('.stats-card-header', { hasText: 'Miasta' })).toBeVisible({ timeout: 10_000 })
    await page.waitForTimeout(1500)

    // ===== SCREENSHOT 1: statystyki archiwum (pełna strona) =====
    await page.screenshot({ path: path.join(SHOTS_DIR, 'archive_stats.png'), fullPage: true })

    const observations: string[] = []

    // ===== Top maszyny =====
    const topMachinesCard = page.locator('.stats-card', { has: page.locator('.stats-card-header', { hasText: 'Top maszyny' }) })
    const machineRows = topMachinesCard.locator('tbody tr.drill-row')
    const machineRowCount = await machineRows.count()
    observations.push(`Top maszyny: ${machineRowCount} wierszy drill-row`)

    if (machineRowCount === 0) {
      observations.push('Top maszyny: BRAK DANYCH (pusty stan)')
      await topMachinesCard.screenshot({ path: path.join(SHOTS_DIR, 'archive_stats_top_machines_empty.png') })
    } else {
      await machineRows.first().click()
      await expect(page.locator('.drill-drawer')).toBeVisible({ timeout: 8_000 })
      await expect(page.locator('.drill-title')).toBeVisible({ timeout: 5_000 })
      await page.waitForTimeout(1500)

      // ===== SCREENSHOT 2: drill-down drawer (maszyna) =====
      await page.screenshot({ path: path.join(SHOTS_DIR, 'archive_drilldown_machine.png'), fullPage: true })

      const drawerTitle = (await page.locator('.drill-title').textContent())?.trim()
      const drawerSubtitle = (await page.locator('.drill-subtitle').textContent())?.trim()
      observations.push(`Drawer maszyna: title="${drawerTitle}", subtitle="${drawerSubtitle}"`)

      const drawerBody = page.locator('.drill-body')
      const hasTable = await drawerBody.locator('.drill-contract-row').count()
      const hasEmpty = await drawerBody.locator('.drill-empty').count()
      const hasError = await drawerBody.locator('.drill-error').count()
      const hasSkeleton = await drawerBody.locator('.drill-skeleton').count()
      observations.push(`Drawer maszyna: contractRows=${hasTable}, empty=${hasEmpty}, error=${hasError}, skeleton=${hasSkeleton}`)

      const footerVisible = await page.locator('.drill-footer').isVisible().catch(() => false)
      observations.push(`Drawer maszyna: footer(paginacja) visible=${footerVisible}`)

      // Zamknij drawer (Esc)
      await page.keyboard.press('Escape')
      await expect(page.locator('.drill-drawer')).not.toBeVisible({ timeout: 5_000 })
    }

    // ===== Miasta =====
    const citiesCard = page.locator('.stats-card', { has: page.locator('.stats-card-header', { hasText: 'Miasta' }) })
    const cityRows = citiesCard.locator('tbody tr.drill-row')
    const cityRowCount = await cityRows.count()
    observations.push(`Miasta: ${cityRowCount} wierszy drill-row`)

    if (cityRowCount === 0) {
      observations.push('Miasta: BRAK DANYCH (pusty stan)')
      await citiesCard.screenshot({ path: path.join(SHOTS_DIR, 'archive_stats_cities_empty.png') })
    } else {
      await cityRows.first().click()
      await expect(page.locator('.drill-drawer')).toBeVisible({ timeout: 8_000 })
      await expect(page.locator('.drill-title')).toBeVisible({ timeout: 5_000 })
      await page.waitForTimeout(1500)

      // ===== SCREENSHOT 3: drill-down drawer (miasto) =====
      await page.screenshot({ path: path.join(SHOTS_DIR, 'archive_drilldown_city.png'), fullPage: true })

      const drawerTitle = (await page.locator('.drill-title').textContent())?.trim()
      const drawerSubtitle = (await page.locator('.drill-subtitle').textContent())?.trim()
      observations.push(`Drawer miasto: title="${drawerTitle}", subtitle="${drawerSubtitle}"`)

      const drawerBody = page.locator('.drill-body')
      const hasTable = await drawerBody.locator('.drill-contract-row').count()
      const hasEmpty = await drawerBody.locator('.drill-empty').count()
      const hasError = await drawerBody.locator('.drill-error').count()
      observations.push(`Drawer miasto: contractRows=${hasTable}, empty=${hasEmpty}, error=${hasError}`)

      // Zamknij przez przycisk
      const closeBtn = page.locator('.drill-close')
      await expect(closeBtn).toBeVisible()
      await closeBtn.click()
      await expect(page.locator('.drill-drawer')).not.toBeVisible({ timeout: 5_000 })
    }

    console.log('=== ARCHIVE DRILL-DOWN OBSERVATIONS ===')
    for (const o of observations) console.log(' - ' + o)
    console.log(`=== Console JS errors (${consoleErrors.length}): ===`)
    for (const e of consoleErrors) console.log(' ! ' + e)
    console.log('=== END OBSERVATIONS ===')

    // Sanity assert (nie failujemy na brak danych — to wizualna weryfikacja)
    expect(observations.length).toBeGreaterThan(0)
  })
})
