import { test, expect } from '@playwright/test'
import { waitForBackend, login } from './helpers'
import path from 'path'

/**
 * RAO-P2-016: SPIKE - Playwright screenshot wszystkich widoków dla UX review
 * 
 * Ten test robi screenshoty wszystkich widoków aplikacji w różnych stanach:
 * - Empty state (brak danych)
 * - Loading state (jeśli dotyczy)
 * - Error state (jeśli dotyczy)
 * - Populated state (z danymi)
 * - Validation state (błędy walidacji)
 * 
 * Screenshoty są zapisywane w e2e/screenshots/ux-review/ i służą do weryfikacji
 * zgodności z design systemem Toolsmart przez UX Designera.
 */

test.describe('RAO-P2-016: UX Screenshots', () => {
  const SCREENSHOT_DIR = path.join(__dirname, '..', 'screenshots', 'ux-review')

  test.beforeAll(async () => {
    // Utwórz folder na screenshoty
    const fs = require('fs')
    if (!fs.existsSync(SCREENSHOT_DIR)) {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    }
  })

  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
  })

  test('LoginView - empty state', async ({ page }) => {
    await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-login-empty.png') })
  })

  test('LoginView - validation error', async ({ page }) => {
    await page.goto('/rao/login', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByPlaceholder('Podaj login').fill('bledny_user')
    await page.getByPlaceholder('Podaj hasło').fill('zle_haslo')
    await page.getByRole('button', { name: 'Zaloguj się' }).click()
    await page.waitForTimeout(500) // Czekaj na błąd
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02-login-validation-error.png') })
  })

  test('DashboardView - empty state', async ({ page }) => {
    await login(page)
    await page.goto('/rao/home', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(1000) // Czekaj na ładowanie
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03-dashboard-empty.png') })
  })

  test('HomeView - landing page', async ({ page }) => {
    await login(page)
    await page.goto('/rao/home', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(1000)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04-home-landing.png') })
  })

  test('ContractorFormView - new contractor (empty)', async ({ page }) => {
    await login(page)
    await page.goto('/rao/contractors/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05-contractor-form-new-empty.png') })
  })

  test('ContractorFormView - validation error', async ({ page }) => {
    await login(page)
    await page.goto('/rao/contractors/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    // Spróbuj zapisać pusty formularz
    await page.getByRole('button', { name: 'Zapisz' }).click()
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06-contractor-form-validation.png') })
  })

  test('ArticleFormView - new article (empty)', async ({ page }) => {
    // Backward compat — legacy /articles/new route (Faza 7: usuń po migracji)
    await login(page)
    await page.goto('/rao/articles/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07-article-form-new-empty.png') })
  })

  // Faza 5: nowe widoki maszyn / usług / usług dodatkowych
  test('MachineFormView - new machine (empty)', async ({ page }) => {
    await login(page)
    await page.goto('/rao/machines/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07a-machine-form-new-empty.png') })
  })

  test('ServiceFormView - new service (empty)', async ({ page }) => {
    await login(page)
    await page.goto('/rao/services/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07b-service-form-new-empty.png') })
  })

  test('AdditionalServiceFormView - new additional service (empty)', async ({ page }) => {
    await login(page)
    await page.goto('/rao/additional-services/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07c-additional-service-form-new-empty.png') })
  })

  test('ContractFormView - new contract (empty)', async ({ page }) => {
    await login(page)
    await page.goto('/rao/contracts/new', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08-contract-form-new-empty.png') })
  })

  test('SettingsView - company data', async ({ page }) => {
    await login(page)
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09-settings-company.png') })
  })

  test('SettingsView - salespeople', async ({ page }) => {
    await login(page)
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    // Kliknij zakładkę Handlowcy
    await page.getByRole('button', { name: 'Handlowcy' }).click()
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10-settings-salespeople.png') })
  })

  test('SettingsView - categories', async ({ page }) => {
    await login(page)
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: 'Kategorie' }).click()
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '11-settings-categories.png') })
  })

  test('SettingsView - fee presets', async ({ page }) => {
    await login(page)
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: 'Zestawy usług' }).click()
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '12-settings-fee-presets.png') })
  })

  test('SettingsView - Fakturownia', async ({ page }) => {
    await login(page)
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.getByRole('button', { name: 'Fakturownia' }).click()
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '13-settings-fakturownia.png') })
  })

  test('ChangePasswordView - empty form', async ({ page }) => {
    await login(page)
    await page.goto('/rao/change-password', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '14-change-password-empty.png') })
  })

  test('AdminView - admin panel', async ({ page }) => {
    await login(page)
    await page.goto('/rao/admin', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '15-admin-panel.png') })
  })

  test('WorkerView - worker view', async ({ page }) => {
    await login(page)
    await page.goto('/rao/worker', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '16-worker-view.png') })
  })

  test('CommissionView - commission view', async ({ page }) => {
    await login(page)
    await page.goto('/rao/commission', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '17-commission-view.png') })
  })
})