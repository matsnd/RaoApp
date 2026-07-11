<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useReservationsStore, type ReservationWithMachine } from '@/stores/reservations'
import KpiRow, { type KpiCard } from '@/components/analytics/KpiRow.vue'
import AnalyticsTable, {
  type AnalyticsColumn,
  type AnalyticsRow,
} from '@/components/analytics/AnalyticsTable.vue'
import ExportCsvButton, { type CsvColumn } from '@/components/analytics/ExportCsvButton.vue'
import StateMessage from '@/components/StateMessage.vue'
import { useSort } from '@/composables/useSort'
import { formatCurrency } from '@/utils/format'

const store = useReservationsStore()

const search = ref('')
const filter = ref<'all' | 'active' | 'expired'>('all')

const sort = useSort<AnalyticsRow>('reserved_from', 'desc')

const today = new Date().toISOString().slice(0, 10)

const columns: AnalyticsColumn[] = [
  { key: 'article_name', label: 'Maszyna', sortable: true },
  { key: 'internal_number', label: 'Nr wewnętrzny', sortable: true },
  { key: 'reserved_from', label: 'Od', sortable: true },
  { key: 'reserved_to', label: 'Do', sortable: true },
  { key: 'days', label: 'Dni', align: 'right', sortable: true },
  { key: 'status', label: 'Status', align: 'center' },
  { key: 'note', label: 'Notatka' },
]

const filteredData = computed<ReservationWithMachine[]>(() => {
  let items = store.allList
  if (filter.value === 'active') {
    items = items.filter((r) => r.reserved_to >= today)
  } else if (filter.value === 'expired') {
    items = items.filter((r) => r.reserved_to < today)
  }
  const q = search.value.trim().toLowerCase()
  if (q) {
    items = items.filter(
      (r) =>
        r.article_name?.toLowerCase().includes(q) ||
        r.internal_number?.toLowerCase().includes(q) ||
        r.note?.toLowerCase().includes(q),
    )
  }
  return items
})

const rows = computed<AnalyticsRow[]>(() =>
  filteredData.value.map((r) => {
    const from = new Date(r.reserved_from)
    const to = new Date(r.reserved_to)
    const days = Math.round((to.getTime() - from.getTime()) / 86400000) + 1
    const isActive = r.reserved_to >= today
    return {
      id: r.id,
      article_name: r.article_name ?? '—',
      internal_number: r.internal_number ?? '—',
      reserved_from: r.reserved_from,
      reserved_to: r.reserved_to,
      days,
      status: isActive ? 'Aktywna' : 'Wygasła',
      note: r.note ?? '',
    }
  }),
)

const sortedRows = computed(() => sort.sortedRows(rows.value))

const kpiCards = computed<KpiCard[]>(() => {
  if (!store.allList.length) return []
  const active = store.allList.filter((r) => r.reserved_to >= today).length
  const expired = store.allList.length - active
  const uniqueMachines = new Set(store.allList.map((r) => r.machine_id ?? r.article_id)).size
  return [
    {
      value: store.allList.length,
      label: 'Rezerwacji',
      sub: 'łącznie',
      icon: '📆' as never,
      testId: 'kpi-res-total',
    },
    {
      value: active,
      label: 'Aktywnych',
      sub: 'termin w przyszłości',
      variant: 'success',
      icon: '✅' as never,
      testId: 'kpi-res-active',
    },
    {
      value: expired,
      label: 'Wygasłych',
      sub: 'termin w przeszłości',
      variant: 'warn',
      icon: '⏰' as never,
      testId: 'kpi-res-expired',
    },
    {
      value: uniqueMachines,
      label: 'Maszyn',
      sub: 'z rezerwacjami',
      icon: '🏗️' as never,
      testId: 'kpi-res-machines',
    },
  ]
})

const csvColumns: CsvColumn[] = [
  { key: 'article_name', label: 'Maszyna' },
  { key: 'internal_number', label: 'Nr wewnętrzny' },
  { key: 'reserved_from', label: 'Od' },
  { key: 'reserved_to', label: 'Do' },
  { key: 'days', label: 'Dni' },
  { key: 'status', label: 'Status' },
  { key: 'note', label: 'Notatka' },
]

function formatDate(d: string | null | undefined): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('pl-PL')
}

onMounted(() => {
  store.fetchAllWithMachines()
})
</script>

<template>
  <div class="res-tab" data-testid="reservations-tab">
    <div v-if="store.loadingAll && !store.allList.length" class="res-loading">
      Ładowanie rezerwacji…
    </div>

    <template v-else-if="store.allList.length">
      <KpiRow :cards="kpiCards" />

      <div class="res-section">
        <div class="res-section-head">
          <span class="res-section-title">📆 Rezerwacje maszyn ({{ filteredData.length }})</span>
          <div class="res-actions">
            <div class="res-filter-toggle" role="group" aria-label="Filtr rezerwacji">
              <button
                :class="['res-toggle-btn', { active: filter === 'all' }]"
                data-testid="res-filter-all"
                @click="filter = 'all'"
              >Wszystkie</button>
              <button
                :class="['res-toggle-btn', { active: filter === 'active' }]"
                data-testid="res-filter-active"
                @click="filter = 'active'"
              >Aktywne</button>
              <button
                :class="['res-toggle-btn', { active: filter === 'expired' }]"
                data-testid="res-filter-expired"
                @click="filter = 'expired'"
              >Wygasłe</button>
            </div>
            <input
              v-model="search"
              type="text"
              class="res-search"
              placeholder="Szukaj: maszyna, nr, notatka…"
              data-testid="res-search"
            />
            <ExportCsvButton
              :columns="csvColumns"
              :rows="sortedRows"
              filename="rezerwacje.csv"
            />
          </div>
        </div>
        <AnalyticsTable
          :columns="columns"
          :rows="sortedRows"
          :sort-key="String(sort.sortKey.value)"
          :sort-dir="sort.sortDir.value"
          row-key="id"
          data-testid="res-table"
          @sort="sort.toggleSort"
        >
          <template #cell-reserved_from="{ value }">
            {{ formatDate(value as string) }}
          </template>
          <template #cell-reserved_to="{ value }">
            {{ formatDate(value as string) }}
          </template>
          <template #cell-status="{ value }">
            <span :class="['res-badge', value === 'Aktywna' ? 'res-badge-active' : 'res-badge-expired']">
              {{ value }}
            </span>
          </template>
          <template #empty>Brak rezerwacji pasujących do filtrów</template>
        </AnalyticsTable>
      </div>
    </template>

    <div v-else-if="store.error" class="res-error">
      <StateMessage type="error" :message="store.error" />
    </div>

    <div v-else class="res-empty" data-testid="res-empty">
      Brak rezerwacji w systemie.
      <span class="res-empty-hint">Rezerwacje można dodawać z poziomu karty artykułu.</span>
    </div>
  </div>
</template>

<style scoped>
.res-tab {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}
.res-loading {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.res-section {
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-lg);
}
.res-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}
.res-section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-heading);
}
.res-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}
.res-filter-toggle {
  display: flex;
  gap: var(--spacing-xs);
}
.res-toggle-btn {
  padding: 4px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-pill, 24px);
  background: var(--color-bg-card);
  color: var(--color-text-body);
  font-family: var(--font-family);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.res-toggle-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.res-toggle-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-on-primary, #fff);
}
.res-search {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  width: 250px;
  max-width: 100%;
}
.res-search:focus {
  outline: none;
  border-color: var(--color-primary);
}
.res-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--border-radius-pill, 24px);
  font-size: var(--font-size-xs);
  font-weight: 600;
}
.res-badge-active {
  background: var(--color-success-bg, rgba(34, 197, 94, 0.15));
  color: var(--color-success);
}
.res-badge-expired {
  background: var(--color-bg-light);
  color: var(--color-text-muted);
}
.res-empty {
  padding: var(--spacing-xl) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.res-empty-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  opacity: 0.8;
}
.res-error {
  padding: var(--spacing-lg) 0;
}
</style>
