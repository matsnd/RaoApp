const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Login
  await page.goto('http://localhost:5173/rao/login');
  await page.getByPlaceholder('Podaj login').fill('admin');
  await page.getByPlaceholder('Podaj hasło').fill('admin123');
  await page.getByRole('button', { name: 'Zaloguj się' }).click();
  await page.waitForURL('**/home');

  // Navigate to contract form
  await page.goto('http://localhost:5173/rao/contracts/new');
  await page.waitForLoadState('networkidle');

  // Click "Wybierz" button to open contractor picker
  await page.getByRole('button', { name: 'Wybierz' }).click();
  await page.waitForTimeout(2000);

  // Clear search field first
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(500);

  // Type non-existent contractor in search
  await page.keyboard.type('NieistniejącyKontrahentTest123XYZ');
  await page.waitForTimeout(4000);

  // Take screenshot
  await page.screenshot({ path: 'C:/projects/repos/RaoApp/temp/inline_contractor_test.png', fullPage: true });

  await browser.close();
})();
