<script setup lang="ts">
interface Props {
  title: string
  icon?: string
  loading?: boolean
  empty?: boolean
  emptyMessage?: string
  height?: number
  testId?: string
}
withDefaults(defineProps<Props>(), {
  loading: false,
  empty: false,
  emptyMessage: 'Brak danych do wykresu',
  height: 300,
  testId: 'chart-card',
})
</script>

<template>
  <div class="chart-card" :data-testid="testId">
    <div class="chart-card-head">
      <span class="chart-card-title">
        <span v-if="icon" class="chart-card-icon">{{ icon }}</span>
        {{ title }}
      </span>
      <slot name="actions" />
    </div>
    <div class="chart-card-body">
      <div v-if="loading" class="chart-card-loading">Ładowanie wykresu…</div>
      <div v-else-if="empty" class="chart-card-empty">{{ emptyMessage }}</div>
      <div v-else class="chart-card-canvas" :style="{ height: height + 'px' }">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}
.chart-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}
.chart-card-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-heading);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}
.chart-card-icon {
  font-size: var(--font-size-lg);
}
.chart-card-loading,
.chart-card-empty {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.chart-card-canvas {
  position: relative;
  width: 100%;
}
</style>
