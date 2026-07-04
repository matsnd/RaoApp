<script setup lang="ts">
/**
 * RAO-P3-071 Faza 5: Skeleton loader dla tabel ladowanych asynchronicznie.
 *
 * Renderuje animowany placeholder wiersza tabeli (shimmer effect).
 * Uzywany w DashboardView / AnalyticsView zamiast "Ladowanie..." tekstu
 * dla lepszej percepcji wydajnosci (perceived performance).
 *
 * @example
 *   <tr v-if="contractStore.loading">
 *     <td colspan="10"><SkeletonRow :cols="6" /></td>
 *   </tr>
 *
 * Accessibility: role="status" + aria-label informuje screen readery
 * o trwajacym ladowaniu. Respektuje prefers-reduced-motion (CSS).
 */
interface Props {
  /** Liczba kolumn-skeletonow w wierszu */
  cols?: number
  /** Etykieta dla screen readerow (domyslnie "Ladowanie danych") */
  label?: string
  /** Rozmiar komorek: 'mix' (rozne szerokosci) | 'even' (rowne) */
  variant?: 'mix' | 'even'
}
const props = withDefaults(defineProps<Props>(), {
  cols: 5,
  label: 'Ladowanie danych',
  variant: 'mix',
})

function cellClass(idx: number): string {
  if (props.variant === 'even') return 'skeleton-cell'
  const cycle = idx % 3
  if (cycle === 0) return 'skeleton-cell short'
  if (cycle === 1) return 'skeleton-cell medium'
  return 'skeleton-cell long'
}
</script>

<template>
  <div
    class="skeleton-row"
    role="status"
    aria-live="polite"
    :aria-label="label"
  >
    <span
      v-for="i in cols"
      :key="i"
      :class="cellClass(i - 1)"
      aria-hidden="true"
    ></span>
    <span class="sr-only">{{ label }}</span>
  </div>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
