<script setup lang="ts">
/**
 * RAO-P3-071 Faza 5: TableSkeleton — blok skeleton-rows dla tabel ladowanych asynchronicznie.
 *
 * Renderuje siatke `rows` x `cols` animowanych placeholderow (shimmer via `.skeleton`
 * z assets/styles/animations.css). Uzywany zamiast tekstu "Ladowanie..." w widokach
 * (SettingsView, ArchiveView, AdminView) dla lepszej percepcji wydajnosci.
 *
 * Dwa tryby renderu (prop `layout`):
 *  - 'block'  (default): standalone blok — nadaje sie do zastapienia `<div class="empty-state">Ladowanie...</div>`
 *  - 'inline': pojedynczy wiersz do wstawienia w `<td colspan="N">` (kompatybilne z <table>)
 *
 * @example standalone
 *   <TableSkeleton v-if="store.loading" :rows="5" :cols="4" />
 * @example wewnatrz tabeli
 *   <tr v-if="store.loading"><td colspan="8"><TableSkeleton :rows="5" :cols="8" layout="inline" /></td></tr>
 *
 * Accessibility: role="status" + aria-label informuje screen readery o trwajacym ladowaniu.
 */
interface Props {
  /** Liczba wierszy-skeletonow */
  rows?: number
  /** Liczba kolumn-skeletonow w wierszu */
  cols?: number
  /** Etykieta dla screen readerow */
  label?: string
  /** Tryb renderu: 'block' (standalone) | 'inline' (pojedynczy wiersz w <td>) */
  layout?: 'block' | 'inline'
}

const props = withDefaults(defineProps<Props>(), {
  rows: 5,
  cols: 4,
  label: 'Ladowanie danych',
  layout: 'block',
})

/** Zroznicowane szerokosci komorek dla naturalnego wygladu (jak SkeletonRow) */
function cellClass(idx: number): string {
  const cycle = idx % 3
  if (cycle === 0) return 'ts-cell short'
  if (cycle === 1) return 'ts-cell medium'
  return 'ts-cell long'
}
</script>

<template>
  <div
    class="table-skeleton"
    :class="{ 'table-skeleton--inline': props.layout === 'inline' }"
    role="status"
    aria-live="polite"
    :aria-label="props.label"
  >
    <div v-for="r in props.rows" :key="r" class="ts-row">
      <span
        v-for="c in props.cols"
        :key="c"
        :class="cellClass(c - 1)"
        aria-hidden="true"
      ></span>
    </div>
    <span class="sr-only">{{ props.label }}</span>
  </div>
</template>

<style scoped>
.table-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-2);
  width: 100%;
}
.table-skeleton--inline {
  padding: 0;
}

.ts-row {
  display: flex;
  gap: var(--spacing-2);
  width: 100%;
  height: 18px;
}

/* Placeholder komorki — korzysta z animacji `pulse` z animations.css
   oraz zmiennych CSS design systemu (zgodne z `.skeleton`). */
.ts-cell {
  flex: 1 1 0;
  height: 100%;
  background: var(--color-bg-light);
  border-radius: var(--border-radius-sm);
  animation: pulse 1.5s ease-in-out infinite;
}
.ts-cell.short  { flex: 0 0 18%; }
.ts-cell.medium { flex: 0 0 32%; }
.ts-cell.long   { flex: 1 1 0; }

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

@media (prefers-reduced-motion: reduce) {
  .ts-cell { animation: none; }
}
</style>
