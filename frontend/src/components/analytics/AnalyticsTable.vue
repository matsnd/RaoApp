<script setup lang="ts">
import { computed } from 'vue'

export interface AnalyticsColumn {
  key: string
  label: string
  sortable?: boolean
  align?: 'left' | 'right' | 'center'
  width?: string
  clickable?: boolean
}

// Wiersze są generyczne — komponent tylko renderuje wartości po kluczu kolumny.
// `Record<string, unknown>` wymusza użycie indeksowania stringiem (kluczem kolumny).
export type AnalyticsRow = Record<string, unknown>

interface Props {
  columns: AnalyticsColumn[]
  rows: AnalyticsRow[]
  sortKey: string
  sortDir: 'asc' | 'desc'
  rowKey: string
  clickable?: boolean
  loading?: boolean
  skeletonRows?: number
}

const props = withDefaults(defineProps<Props>(), {
  clickable: false,
  loading: false,
  skeletonRows: 6,
})

const emit = defineEmits<{
  sort: [key: string]
  rowClick: [row: AnalyticsRow]
}>()

const skeletonCount = computed(() => Math.max(1, props.skeletonRows))

function onHeaderClick(col: AnalyticsColumn): void {
  if (!col.sortable) return
  emit('sort', col.key)
}

function onRowClick(row: AnalyticsRow): void {
  if (!props.clickable) return
  emit('rowClick', row)
}

function alignClass(col: AnalyticsColumn): string {
  return `col-${col.align ?? 'left'}`
}

function sortIcon(col: AnalyticsColumn): string {
  if (col.key !== props.sortKey) return ''
  return props.sortDir === 'asc' ? '▲' : '▼'
}
</script>

<template>
  <div class="analytics-table-wrap" data-testid="analytics-table">
    <!-- LOADING (skeleton) -->
    <div v-if="loading" class="at-skeleton" data-testid="analytics-table-loading">
      <slot name="loading">
        <div
          v-for="i in skeletonCount"
          :key="i"
          class="at-skel-row"
        ></div>
      </slot>
    </div>

    <!-- EMPTY -->
    <div v-else-if="!rows.length" class="at-empty" data-testid="analytics-table-empty">
      <slot name="empty">Brak danych</slot>
    </div>

    <!-- TABLE -->
    <div v-else class="at-scroll">
      <table class="analytics-table">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :data-testid="`th-${col.key}`"
              :class="[
                alignClass(col),
                { sortable: col.sortable, sorted: col.key === sortKey },
              ]"
              :style="col.width ? { width: col.width } : undefined"
              @click="onHeaderClick(col)"
            >
              <span class="th-label">{{ col.label }}</span>
              <span
                v-if="col.sortable && sortIcon(col)"
                class="sort-icon"
                :data-testid="`sort-icon-${col.key}`"
              >{{ sortIcon(col) }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="String(row[rowKey])"
            :class="{ 'row-clickable': clickable }"
            :data-testid="`row-${String(row[rowKey])}`"
            @click="clickable && onRowClick(row)"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[alignClass(col), { 'cell-clickable': col.clickable }]"
            >
              <slot
                :name="`cell-${col.key}`"
                :row="row"
                :value="row[col.key]"
              >
                {{ row[col.key] ?? '—' }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.analytics-table-wrap {
  width: 100%;
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  font-family: var(--font-family);
}

.at-scroll {
  overflow: auto;
  max-height: calc(100vh - 240px);
}

.analytics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.analytics-table thead th {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: sticky;
  top: 0;
  white-space: nowrap;
  user-select: none;
}

.analytics-table thead th.sortable {
  cursor: pointer;
}
.analytics-table thead th.sortable:hover {
  background: var(--color-primary-light);
}
.analytics-table thead th .sort-icon {
  margin-left: var(--spacing-xs);
  font-size: 12px;
  opacity: 0.6;
}
.analytics-table thead th.sorted .sort-icon {
  opacity: 1;
}

.analytics-table thead th.col-right,
.analytics-table tbody td.col-right {
  text-align: right;
}
.analytics-table thead th.col-center,
.analytics-table tbody td.col-center {
  text-align: center;
}

.analytics-table tbody tr {
  border-bottom: 1px solid var(--color-border);
  transition: background var(--transition-fast);
}
.analytics-table tbody tr:nth-child(even) {
  background: var(--color-row-even);
}
.analytics-table tbody tr.row-clickable {
  cursor: pointer;
}
.analytics-table tbody tr:hover {
  background: var(--color-bg-card-hover);
}

.analytics-table tbody td {
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text-body);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 240px;
}

/* Empty + skeleton */
.at-empty {
  text-align: center;
  padding: var(--spacing-2xl) var(--spacing-lg);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.at-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
}
.at-skel-row {
  height: 36px;
  background: var(--color-bg-light);
  border-radius: var(--border-radius-sm);
  animation: at-pulse 1.2s ease-in-out infinite;
}
@keyframes at-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
