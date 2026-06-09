import { test, expect } from '@playwright/test'
import { waitForBackend, login, API, apiLogin, authHeaders, safeDelete, newApiContext, genValidNip } from './helpers'

const createdPresetIds: number[] = []
const createdContractIds: number[] = []
const createdContractorIds: number[] = []

test.describe('TEST-12: Fee Presets UI E2E', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('tworzy preset, edytuje go, dodaje szablon oplaty, edytuje go, aplikuje do umowy i weryfikuje PDF', async ({ page, request }) => {
    const ts = Date.now()
    const presetName = `UI Preset ${ts}`
    const updatedPresetName = `UI Preset Ed ${ts}`
    const presetDesc = `Opis zestawu UI ${ts}`
    const itemName = `UI Test Service ${ts}`

    // ----------------------------------------------------
    // KROK 1: Dodanie nowego zestawu w konfiguracji (Ustawienia)
    // ----------------------------------------------------
    await page.goto('/rao/settings', { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.getByRole('button', { name: 'Dane firmy' })).toBeVisible({ timeout: 8_000 })

    // Kliknij zakładkę "Zestawy usług" / "Zestawy usług dodatkowych"
    const feePresetsTab = page.getByRole('button', { name: 'Zestawy usług' })
    await expect(feePresetsTab).toBeVisible({ timeout: 5_000 })
    await feePresetsTab.click()
    await expect(page.locator('.panel-header').last()).toContainText('Zestawy usług', { timeout: 5_000 })

    // Wypełnij formularz nowego zestawu
    await page.locator('select').nth(0).selectOption('S') // Najem (S)
    await page.locator('input[placeholder="np. Standardowy, Premium…"]').fill(presetName)
    await page.locator('input[placeholder="Krótki opis zestawu"]').fill(presetDesc)

    // Oczekuj na odpowiedź z zapisu przed kliknięciem
    const presetResponsePromise = page.waitForResponse(response => 
      response.url().includes('/settings/fee-preset-groups') && response.request().method() === 'POST'
    )
    await page.getByRole('button', { name: '+ Nowy zestaw' }).click()
    
    const presetResponse = await presetResponsePromise
    expect(presetResponse.status()).toBe(201)
    const presetJson = await presetResponse.json()
    createdPresetIds.push(presetJson.id)

    // Zweryfikuj, że karta zestawu się pojawiła
    const card = page.locator('.preset-card', { hasText: presetName })
    await expect(card).toBeVisible({ timeout: 5_000 })

    // ----------------------------------------------------
    // KROK 2: Edycja nazwy zestawu
    // ----------------------------------------------------
    await card.locator('button[title="Zmień nazwę"]').click()
    
    // Używamy globalnego selektora dla aktywnego inputu edycji, ponieważ nazwa w card ulega unmounted
    const editInput = page.locator('.preset-card input.form-control-xs')
    await editInput.fill(updatedPresetName)

    const presetUpdatePromise = page.waitForResponse(response =>
      response.url().includes(`/settings/fee-preset-groups/${presetJson.id}`) && response.request().method() === 'PUT'
    )
    await page.locator('.preset-card button[title="Zapisz"]').click()
    await presetUpdatePromise

    // Potwierdź zmianę nazwy na karcie
    const updatedCard = page.locator('.preset-card', { hasText: updatedPresetName })
    await expect(updatedCard).toBeVisible({ timeout: 5_000 })

    // ----------------------------------------------------
    // KROK 3: Dodanie nowego szablonu (pozycji) do zestawu
    // ----------------------------------------------------
    // Rozwiń zestaw
    await updatedCard.locator('button[title="Pokaż/ukryj pozycje"]').click()
    const itemsPanel = updatedCard.locator('.preset-items')
    await expect(itemsPanel).toBeVisible({ timeout: 5_000 })

    // Kliknij "+ Dodaj pozycję"
    await itemsPanel.getByRole('button', { name: '+ Dodaj pozycję' }).click()

    // Wypełnij pola nowej pozycji w wierszu formularza
    const formRow = itemsPanel.locator('tbody tr').last()
    await formRow.locator('input[placeholder*="Nazwa"]').fill(itemName)
    await formRow.locator('input[placeholder="Cena domyślna"]').fill('150.00')
    await formRow.locator('input').nth(2).fill('200.00') // Kwota od
    await formRow.locator('input').nth(3).fill('300.00') // Kwota do
    await formRow.locator('input[placeholder="h, km…"]').fill('km')
    await formRow.locator('input').nth(5).fill('- Usługa testowa: $1 zł (plus koszt)') // Opis

    const templateResponsePromise = page.waitForResponse(response =>
      response.url().includes(`/settings/fee-preset-groups/${presetJson.id}/templates`) && response.request().method() === 'POST'
    )
    await formRow.locator('button[title="Dodaj (Enter)"]').click()
    await templateResponsePromise

    // Potwierdź, że pozycja jest widoczna na liście
    const itemRow = itemsPanel.locator('tr', { hasText: itemName })
    await expect(itemRow).toBeVisible({ timeout: 5_000 })

    // ----------------------------------------------------
    // KROK 4: Edycja nowej pozycji szablonu
    // ----------------------------------------------------
    await itemRow.locator('button[title="Edytuj"]').click()
    
    // Używamy selektora wewnątrz panelu, ponieważ tekst rzędu (itemName) w input-v-model nie jest widoczny jako .textContent
    await itemsPanel.locator('input[placeholder="h, km…"]').fill('h') // Zmiana j.m. z km na h

    const itemUpdatePromise = page.waitForResponse(response =>
      response.url().includes(`/settings/fee-preset-groups/${presetJson.id}/templates`) && response.request().method() === 'PUT'
    )
    await itemsPanel.locator('button[title="Zapisz"]').click()
    await itemUpdatePromise

    // Zweryfikuj zmianę j.m. na liście (teraz znowu filtrujemy po itemRow bo wyszedł z trybu edycji)
    await expect(itemRow.getByText('h')).toBeVisible({ timeout: 3_000 })

    // ----------------------------------------------------
    // KROK 5: Utworzenie umowy przez API i przejście do edycji w UI
    // ----------------------------------------------------
    const token = await apiLogin(request)
    
    // Utwórz kontrahenta
    const contractorRes = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `UI PDF Contractor ${ts}`, nip: genValidNip(ts) },
    })
    expect(contractorRes.status()).toBe(201)
    const contractor = await contractorRes.json()
    createdContractorIds.push(contractor.id)

    // Utwórz umowę
    const today = new Date().toISOString().slice(0, 10)
    const contractRes = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: contractor.id, contract_type: 'S', date_from: today },
    })
    expect(contractRes.status()).toBe(201)
    const contract = await contractRes.json()
    createdContractIds.push(contract.id)

    // Przejdź do formularza umowy w UI
    await page.goto(`/rao/contracts/${contract.id}/edit`, { waitUntil: 'domcontentloaded', timeout: 15_000 })
    await expect(page.locator('.toolbar-info')).toContainText(`Umowa: ${contract.number}`, { timeout: 10_000 })

    // ----------------------------------------------------
    // KROK 6: Aplikowanie nowego zestawu do umowy
    // ----------------------------------------------------
    // Obsłuż potwierdzenie dialogowe (confirm prompt)
    page.once('dialog', async dialog => {
      expect(dialog.message()).toContain(updatedPresetName)
      await dialog.accept()
    })

    // Kliknij "Wybierz zestaw"
    await page.locator('button[title="Wybierz zestaw usług"]').click()

    // Oczekuj na pokazanie modal-a i kliknij w nasz zestaw
    const presetCardInPicker = page.locator('.preset-picker-card', { hasText: updatedPresetName })
    await expect(presetCardInPicker).toBeVisible({ timeout: 5_000 })
    
    const applyResponsePromise = page.waitForResponse(response =>
      response.url().includes(`/contracts/${contract.id}/service-fees/apply-preset`) && response.request().method() === 'POST'
    )
    await presetCardInPicker.click()
    await applyResponsePromise

    // Zweryfikuj, czy usługa pojawiła się na liście usług dodatkowych umowy
    const feeRowInContract = page.locator('.data-grid tbody tr', { hasText: itemName })
    await expect(feeRowInContract).toBeVisible({ timeout: 5_000 })
    await expect(feeRowInContract).toContainText('200.00 zł')
    await expect(feeRowInContract).toContainText('300.00 zł')
    await expect(feeRowInContract).toContainText('h')

    // ----------------------------------------------------
    // KROK 7: Generowanie wydruku PDF i weryfikacja zawartości
    // ----------------------------------------------------
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('button[title="Drukuj PDF"]').click()
    ])

    const pdfPath = await download.path()
    expect(pdfPath).toBeTruthy()

    // Zweryfikuj tekst w PDF przez skrypt Python (podmiana $1 -> 200.00 zł)
    const { execSync } = await import('child_process')
    const path = await import('path')
    const workspaceRoot = process.cwd().endsWith('e2e') ? path.join(process.cwd(), '..') : process.cwd()
    const pythonPath = path.join(workspaceRoot, 'backend', '.venv', 'Scripts', 'python.exe')
    const scriptPath = path.join(workspaceRoot, 'backend', 'tests', 'unit', 'verify_pdf_fees.py')

    const expectedText = 'Usługa testowa: 200.00 zł (plus koszt)'
    const result = execSync(
      `"${pythonPath}" "${scriptPath}" "${pdfPath}" "${expectedText}"`,
      { encoding: 'utf-8', cwd: workspaceRoot }
    )
    expect(result.trim()).toContain('PASS')
  })

  test.afterAll(async () => {
    const ctx = await newApiContext()
    try {
      const token = await apiLogin(ctx)
      for (const id of createdContractIds) {
        await safeDelete(ctx, `${API}/contracts/${id}`, token)
      }
      for (const id of createdContractorIds) {
        await safeDelete(ctx, `${API}/contractors/${id}`, token)
      }
      for (const id of createdPresetIds) {
        await safeDelete(ctx, `${API}/settings/fee-preset-groups/${id}`, token)
      }
    } catch {
      /* ignore */
    } finally {
      await ctx.dispose()
    }
  })
})
