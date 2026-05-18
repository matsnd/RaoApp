/**
 * RAO-P2-012 QA: Unit tests for frontend/src/stores/fakturownia.ts
 *
 * Mocks the api module to avoid real HTTP calls.
 *
 * NOTE: The store imports from '../utils/api' which does NOT exist in this codebase.
 * All other stores import from '@/composables/useApi'. Tests stub both paths via vi.mock
 * so that whichever one is in effect is intercepted.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// vi.mock factories are hoisted — use vi.hoisted for shared mock instance.
const { apiMock } = vi.hoisted(() => ({
  apiMock: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))
// Store imports '../utils/api' which doesn't exist (BUG #1).
// vitest.config.ts aliases that path to __mocks__/api-stub.ts — we mock the stub.
vi.mock('./__mocks__/api-stub', () => ({ default: apiMock }))
vi.mock('@/composables/useApi', () => ({ default: apiMock }))

import { useFakturowniaStore } from '../fakturownia'

describe('useFakturowniaStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    apiMock.get.mockReset()
    apiMock.put.mockReset()
  })

  // ── fetchSettings ──────────────────────────────────────────────────────────

  it('fetchSettings: GET /settings and updates state', async () => {
    const payload = {
      id: 1,
      enabled: true,
      api_token_preview: 'tk_s****7890',
      domain_subdomain: 'toolsmart',
      api_token_updated_at: '2025-05-20T10:00:00',
      api_token_updated_by: 1,
    }
    apiMock.get.mockResolvedValueOnce({ data: payload })

    const store = useFakturowniaStore()
    await store.fetchSettings()

    expect(apiMock.get).toHaveBeenCalledWith('/integrations/fakturownia/settings')
    expect(store.settings).toEqual(payload)
    expect(store.error).toBeNull()
  })

  it('fetchSettings: sets error message on failure (does not throw)', async () => {
    apiMock.get.mockRejectedValueOnce(new Error('Network'))

    const store = useFakturowniaStore()
    await store.fetchSettings()  // must NOT throw

    expect(store.settings).toBeNull()
    expect(store.error).toBe('Błąd pobierania ustawień Fakturownia')
  })

  // ── updateSettings ─────────────────────────────────────────────────────────

  it('updateSettings: PUT with payload and updates state', async () => {
    const updated = {
      id: 1,
      enabled: true,
      api_token_preview: 'tk_n****0000',
      domain_subdomain: 'toolsmart',
      api_token_updated_at: '2025-05-20T11:00:00',
      api_token_updated_by: 1,
    }
    apiMock.put.mockResolvedValueOnce({ data: updated })

    const store = useFakturowniaStore()
    const sent = { enabled: true, api_token: 'tk_new0000', domain_subdomain: 'toolsmart' }
    await store.updateSettings(sent)

    expect(apiMock.put).toHaveBeenCalledWith(
      '/integrations/fakturownia/settings',
      sent,
    )
    expect(store.settings).toEqual(updated)
  })

  it('updateSettings: re-throws on failure (so component can show toast)', async () => {
    const err = Object.assign(new Error('Forbidden'), {
      response: { status: 403, data: { detail: 'brak uprawnień' } },
    })
    apiMock.put.mockRejectedValueOnce(err)

    const store = useFakturowniaStore()
    await expect(
      store.updateSettings({ enabled: true })
    ).rejects.toBe(err)
    expect(store.error).toBe('Błąd aktualizacji ustawień Fakturownia')
  })

  // ── fetchInvoicesByContractId ──────────────────────────────────────────────

  it('fetchInvoicesByContractId: passes contract_id and stores invoices', async () => {
    const invoices = [{
      invoice_number: 'FV/1/2025',
      lines: [],
      total_net: 1000,
      mapped_total_net: 1000,
      unmapped_count: 0,
    }]
    apiMock.get.mockResolvedValueOnce({ data: invoices })

    const store = useFakturowniaStore()
    await store.fetchInvoicesByContractId(42)

    expect(apiMock.get).toHaveBeenCalledWith(
      '/integrations/fakturownia/invoices?contract_id=42'
    )
    expect(store.invoices).toEqual(invoices)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchInvoicesByContractId: toggles loading flag', async () => {
    let resolveIt: (v: any) => void
    apiMock.get.mockReturnValueOnce(new Promise(r => { resolveIt = r }))

    const store = useFakturowniaStore()
    const p = store.fetchInvoicesByContractId(1)
    expect(store.loading).toBe(true)
    resolveIt!({ data: [] })
    await p
    expect(store.loading).toBe(false)
  })

  it('fetchInvoicesByContractId: sets error and resets loading on failure', async () => {
    apiMock.get.mockRejectedValueOnce(new Error('boom'))

    const store = useFakturowniaStore()
    await store.fetchInvoicesByContractId(1)  // does NOT throw

    expect(store.error).toBe('Błąd pobierania faktur z Fakturownia')
    expect(store.loading).toBe(false)
    expect(store.invoices).toEqual([])
  })

  // ── Edge: contract_id values (integer expected by backend Query(ge=1)) ──────

  it('fetchInvoicesByContractId: stringifies contract_id in URL (would send 0 / negative as-is — backend rejects)', async () => {
    apiMock.get.mockResolvedValueOnce({ data: [] })
    const store = useFakturowniaStore()
    await store.fetchInvoicesByContractId(0)
    // Frontend currently does not validate — backend Query(ge=1) returns 422
    expect(apiMock.get).toHaveBeenCalledWith(
      '/integrations/fakturownia/invoices?contract_id=0'
    )
  })
})
