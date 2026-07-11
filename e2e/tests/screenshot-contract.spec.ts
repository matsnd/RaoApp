import { test } from '@playwright/test'

test('Screenshot contract edit page', async ({ page }) => {
  // Login
  await page.goto('http://localhost:5173/rao/login')
  await page.fill('input[placeholder="Podaj login"]', 'admin')
  await page.fill('input[placeholder="Podaj hasło"]', 'admin123')
  await page.click('button:has-text("Zaloguj się")')
  await page.waitForURL('**/home')

  // Navigate to contract edit
  await page.goto('http://localhost:5173/rao/contracts/15/edit')
  await page.waitForLoadState('networkidle')

  // Screenshot
  await page.screenshot({ path: 'e2e/artifacts/condition_panel_screenshot.png', fullPage: true })
})
