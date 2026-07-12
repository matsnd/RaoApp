/**
 * useFeeDescription — wspólna logika podmiany $1/$2 w opisach opłat dodatkowych.
 *
 * $1 → amount_from (sformatowane jako waluta)
 * $2 → amount_to (sformatowane jako waluta)
 *
 * Używane w:
 * - ContractFormView.vue (grid opłat + podgląd PDF)
 * - SettingsView.vue (zestawy usług dodatkowych — szablony)
 * - AdditionalServiceFormView.vue (opis usługi dodatkowej)
 */

export function formatFeeDescription(
  description: string | null | undefined,
  amountFrom: number | string | null | undefined,
  amountTo: number | string | null | undefined,
  name: string = ''
): string {
  if (!description) {
    const from = amountFrom !== null && amountFrom !== undefined && amountFrom !== ''
    const to = amountTo !== null && amountTo !== undefined && amountTo !== ''
    if (from) {
      const formattedFrom = formatFeeAmount(amountFrom)
      if (to) {
        const formattedTo = formatFeeAmount(amountTo)
        const prefix = name ? `${name}: ` : ''
        return `${prefix}${formattedFrom} - ${formattedTo}`
      }
      const prefix = name ? `${name}: ` : ''
      return `${prefix}${formattedFrom}`
    }
    return name ? `${name}: wycena indywidualna` : '—'
  }

  // Replace $1/$2 placeholders with formatted amounts
  let result = description
    .replace(/\$1/g, formatFeeAmount(amountFrom))
    .replace(/\$2/g, formatFeeAmount(amountTo))
  const prefix = name ? `${name}: ` : ''
  return `${prefix}${result}`
}

function formatFeeAmount(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '0,00 zł'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0,00 zł'
  return num.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł'
}

/**
 * Placeholder hint text for description inputs.
 */
export const FEE_DESCRIPTION_HINT = 'Użyj $1 = kwota od, $2 = kwota do (np. "$1 dostawa / $2 odbiór")'

/**
 * Check if description contains $1 or $2 placeholders.
 */
export function hasFeePlaceholders(description: string | null | undefined): boolean {
  if (!description) return false
  return /\$[12]/.test(description)
}
