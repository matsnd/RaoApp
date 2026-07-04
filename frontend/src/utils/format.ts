/**
 * RAO-P3-071 Faza 2: Unifikacja formatowania dat i walut.
 *
 * Wzorzec (zgodny z audytem UX):
 *  - Data: "04.07.2026" (pl-PL, leading zero, dd.MM.yyyy)
 *  - Waluta: "10 150,00 zł" (spacja jako separator tysiecy, przecinek dziesietny, suffix " zł")
 *  - Liczba: "1 234" (spacja jako separator tysiecy, bez cyfr po przecinku)
 *
 * Uzywane w: DashboardView, AnalyticsView, ArchiveView, ContractFormView,
 * HomeView, WorkerView, ConditionPanel, CommissionView, analytics tabs.
 *
 * Nie uzywa zewnetrznych bibliotek (date-fns, etc.) - wlasna implementacja
 * oparta o Intl.NumberFormat / Intl.DateTimeFormat z locale 'pl-PL'.
 */

/** Pusty / null / undefined -> placeholder "—" */
const EMPTY_PLACEHOLDER = '—'

/**
 * Formatuje date ISO (lub null) do postaci "04.07.2026" (pl-PL, dd.MM.yyyy).
 * Akceptuje rowniez obiekt Date.
 *
 * @example formatDate('2026-07-04')        // "04.07.2026"
 * @example formatDate(null)                 // "—"
 * @example formatDate('not-a-date')         // "—" (fallback)
 */
export function formatDate(input: string | Date | null | undefined): string {
  if (input === null || input === undefined || input === '') return EMPTY_PLACEHOLDER
  const d = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(d.getTime())) return EMPTY_PLACEHOLDER
  // dd.MM.yyyy - leading zero wymuszony przez 2-digit
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}.${month}.${year}`
}

/**
 * Formatuje liczbe dziesietna jako walute PLN: "10 150,00 zł".
 * Spacja nierozdzielajaca (U+00A0) jako separator tysiecy - zgodne z pl-PL.
 * Przecinek jako separator dziesietny. Suffix " zł" (z nelamliwa spacja).
 *
 * @example formatCurrency(10150)            // "10 150,00 zł"
 * @example formatCurrency('1234.5')         // "1 234,50 zł"
 * @example formatCurrency(null)             // "0,00 zł"
 */
export function formatCurrency(
  value: number | string | null | undefined,
): string {
  if (value === null || value === undefined || value === '') return '0,00 zł'
  const n = typeof value === 'string' ? parseFloat(value) : value
  if (!Number.isFinite(n)) return '0,00 zł'
  // pl-PL: spacja (nierozdzielajaca) jako separator grup, przecinek dziesietny
  const formatted = new Intl.NumberFormat('pl-PL', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    useGrouping: true,
  }).format(n)
  return `${formatted}` + '\u00A0' + 'zł'
}

/**
 * Formatuje liczbe calkowita z separatorem tysiecy: "1 234".
 * Bez cyfr po przecinku. Spacja nierozdzielajaca jako separator grup.
 *
 * @example formatNumber(1234)               // "1 234"
 * @example formatNumber('12345')            // "12 345"
 * @example formatNumber(null)               // "0"
 */
export function formatNumber(
  value: number | string | null | undefined,
): string {
  if (value === null || value === undefined || value === '') return '0'
  const n = typeof value === 'string' ? parseInt(value, 10) : value
  if (!Number.isFinite(n)) return '0'
  return new Intl.NumberFormat('pl-PL', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true,
  }).format(n)
}
