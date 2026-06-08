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

  // Scroll to conditions section
  await page.evaluate(() => window.scrollTo(0, 1500));
  await page.waitForTimeout(1000);

  // Take screenshot
  await page.screenshot({ path: 'C:/projects/repos/RaoApp/temp/conditions_help_test.png', fullPage: true });

  await browser.close();
})();
