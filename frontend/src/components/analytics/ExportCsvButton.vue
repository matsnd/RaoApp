<script setup lang="ts">
import { computed } from 'vue'

export interface CsvColumn {
  key: string
  label: string
  format?: (value: unknown) => string
}

interface Props {
  columns: CsvColumn[]
  rows: Record<string, unknown>[]
  filename?: string
  label?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: 'Eksport CSV',
  disabled: false,
})

function escapeCsv(value: string): string {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`
  }
  return value
}

function downloadCsv(): void {
  if (props.disabled || !props.rows.length) return

  const filename = props.filename || `export_${new Date().toISOString().slice(0, 10)}.csv`
  const header = props.columns.map((c) => escapeCsv(c.label)).join(',')
  const body = props.rows
    .map((row) =>
      props.columns
        .map((col) => {
          const raw = row[col.key]
          const val = col.format ? col.format(raw) : String(raw ?? '')
          return escapeCsv(val)
        })
        .join(','),
    )
    .join('\n')

  const csv = '\uFEFF' + header + '\n' + body
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <button
    class="export-csv-btn"
    :disabled="disabled || !rows.length"
    data-testid="export-csv-btn"
    @click="downloadCsv"
  >
    <span class="export-csv-icon">📥</span>
    {{ label }}
  </button>
</template>

<style scoped>
.export-csv-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-card);
  color: var(--color-text-body);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all 0.15s ease;
}
.export-csv-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-bg-light);
}
.export-csv-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.export-csv-icon {
  font-size: 14px;
}
</style>
