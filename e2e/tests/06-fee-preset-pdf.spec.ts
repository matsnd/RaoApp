import { test, expect } from '@playwright/test'
import { waitForBackend, login, API, apiLogin, authHeaders, safeDelete, newApiContext, genValidNip } from './helpers'

const createdPresetIds: number[] = []
const createdContractIds: number[] = []
const createdContractorIds: number[] = []

test.describe('TEST-06: Fee Preset + PDF Verification', () => {
  test.beforeEach(async ({ page }) => {
    await waitForBackend(page)
    await login(page)
  })

  test('tworzy preset z placeholderem, aplikuje do umowy i weryfikuje PDF', async ({ request }) => {
    const token = await apiLogin(request)
    const ts = Date.now()

    // 1. Utwórz zestaw usług (fee preset group)
    const presetRes = await request.post(`${API}/settings/fee-preset-groups`, {
      headers: authHeaders(token),
      data: { name: `TestPreset ${ts}`, description: 'Test preset for PDF verification', contract_type: 'S' },
    })
    expect([200, 201]).toContain(presetRes.status())
    const preset = await presetRes.json()
    createdPresetIds.push(preset.id)

    // 2. Dodaj szablon z placeholderem $1 do zestawu
    const templateRes = await request.post(`${API}/settings/fee-preset-groups/${preset.id}/templates`, {
      headers: authHeaders(token),
      data: {
        contract_type: 'S',
        name: 'Test Service',
        amount_from: 150.00,
        amount_to: 200.00,
        unit: 'km',
        description: '- Usługa testowa: $1 zł (plus koszt)',
        is_active: true,
      },
    })
    expect([200, 201]).toContain(templateRes.status())

    // 3. Utwórz kontrahenta
    const cr = await request.post(`${API}/contractors`, {
      headers: authHeaders(token),
      data: { name: `PDFTest ${ts}`, nip: genValidNip(ts) },
    })
    const contractor = await cr.json()
    createdContractorIds.push(contractor.id)

    // 4. Utwórz umowę
    const today = new Date().toISOString().slice(0, 10)
    const ctr = await request.post(`${API}/contracts`, {
      headers: authHeaders(token),
      data: { contractor_id: contractor.id, contract_type: 'S', date_from: today },
    })
    expect(ctr.status()).toBe(201)
    const contract = await ctr.json()
    createdContractIds.push(contract.id)

    // 5. Zastosuj zestaw do umowy
    const applyRes = await request.post(
      `${API}/contracts/${contract.id}/service-fees/apply-preset?preset_id=${preset.id}&replace=true`,
      { headers: authHeaders(token) }
    )
    expect(applyRes.status()).toBe(200)

    // 6. Wygeneruj PDF
    const pdfRes = await request.post(`${API}/reports/contract/${contract.id}?type=contract`, {
      headers: authHeaders(token),
      timeout: 30_000,
    })
    expect(pdfRes.status()).toBe(200)
    expect(pdfRes.headers()['content-type']).toContain('application/pdf')

    // 7. Zapisz PDF na dysk
    const pdfBuffer = await pdfRes.body()
    const fs = await import('fs')
    const path = await import('path')
    const pdfPath = path.join(process.cwd(), 'e2e', 'artifacts', 'pdfs', `test-fee-preset-${ts}.pdf`)
    await fs.promises.mkdir(path.dirname(pdfPath), { recursive: true })
    await fs.promises.writeFile(pdfPath, pdfBuffer)

    // 8. Weryfikacja tekstu w PDF przez skrypt Python
    const { execSync } = await import('child_process')
    const pythonPath = path.join(process.cwd(), '..', 'backend', '.venv', 'Scripts', 'python.exe')
    const scriptPath = path.join(process.cwd(), '..', 'backend', 'tests', 'unit', 'verify_pdf_fees.py')

    // Oczekiwany tekst po podmianie $1 → 150.00 zł
    const expectedText = 'Usługa testowa: 150.00 zł (plus koszt)'
    const result = execSync(
      `"${pythonPath}" "${scriptPath}" "${pdfPath}" "${expectedText}"`,
      { encoding: 'utf-8', cwd: process.cwd() }
    )
    expect(result.trim()).toContain('PASS')

    // Dodatkowo: sprawdź że NIE ma surowego placeholdera $1
    // Skrypt zwraca exit 1 gdy tekst nie znaleziony — użyj spawnSync żeby obsłużyć
    const { spawnSync } = await import('child_process')
    const result2 = spawnSync(pythonPath, [scriptPath, pdfPath, '$1 zł'], {
      encoding: 'utf-8',
      cwd: process.cwd(),
    })
    expect(result2.stdout).toContain('FAIL')
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
