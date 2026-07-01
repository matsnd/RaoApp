import { ref } from 'vue'

export type SortDir = 'asc' | 'desc'

/**
 * Composable do client-side sortowania tabel.
 *
 * `toggleSort(key)`:
 *  - klik na aktywną kolumnę → odwróć kierunek
 *  - klik na nową kolumnę → ustaw key + dir='desc'
 *
 * `sortedRows(rows)`:
 *  - zwraca NOWĄ posortowaną tablicę (nie mutuje oryginału)
 *  - null/undefined lądują zawsze na końcu (niezależnie od dir)
 *  - string → localeCompare('pl')
 *  - number → porównanie numeryczne
 */
export function useSort<T extends Record<string, unknown>>(
  initialKey: keyof T,
  initialDir: SortDir = 'desc',
) {
  const sortKey = ref<keyof T>(initialKey)
  const sortDir = ref<SortDir>(initialDir)

  function toggleSort(key: keyof T): void {
    if (sortKey.value === key) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortKey.value = key
      sortDir.value = 'desc'
    }
  }

  /**
   * Zwraca posortowaną kopię `rows`. Typ U domyślnie = T, ale pozwala
   * na szerszy typ (np. wiersze z dodatkowymi polami wyliczanymi).
   */
  function sortedRows<U extends Record<string, unknown>>(rows: U[]): U[] {
    const key = sortKey.value as string
    const dir = sortDir.value
    const factor = dir === 'asc' ? 1 : -1

    return [...rows].sort((a, b) => {
      const av = a[key]
      const bv = b[key]

      // null / undefined → zawsze na końcu
      const aNil = av == null
      const bNil = bv == null
      if (aNil && bNil) return 0
      if (aNil) return 1
      if (bNil) return -1

      // number
      if (typeof av === 'number' && typeof bv === 'number') {
        if (Number.isNaN(av)) return 1
        if (Number.isNaN(bv)) return -1
        return (av - bv) * factor
      }

      // string
      if (typeof av === 'string' && typeof bv === 'string') {
        return av.localeCompare(bv, 'pl') * factor
      }

      // boolean
      if (typeof av === 'boolean' && typeof bv === 'boolean') {
        return (Number(av) - Number(bv)) * factor
      }

      // Date
      if (av instanceof Date && bv instanceof Date) {
        return (av.getTime() - bv.getTime()) * factor
      }

      // fallback — toString + localeCompare
      const as = String(av)
      const bs = String(bv)
      return as.localeCompare(bs, 'pl') * factor
    })
  }

  return { sortKey, sortDir, toggleSort, sortedRows }
}
