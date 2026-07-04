<script setup lang="ts">
import AppIcon, { type AppIconName } from '@/components/shared/AppIcon.vue'

export type KpiVariant = 'default' | 'success' | 'accent' | 'danger' | 'warn'

export interface KpiCard {
  value: string | number
  label: string
  sub?: string
  variant?: KpiVariant
  // RAO-P2-065 #16: ikona jako nazwa AppIcon (zamiast emoji string).
  icon?: AppIconName
  /** Opcjonalny data-testid dla testów E2E */
  testId?: string
}

interface Props {
  cards: KpiCard[]
}

defineProps<Props>()
</script>

<template>
  <div class="kpi-row" data-testid="kpi-row">
    <div
      v-for="(card, idx) in cards"
      :key="card.label + '-' + idx"
      class="kpi-card"
      :class="`kpi-${card.variant ?? 'default'}`"
      :data-testid="card.testId ?? `kpi-card-${idx}`"
    >
      <div v-if="card.icon" class="kpi-icon">
        <AppIcon :name="card.icon" :size="22" />
      </div>
      <div class="kpi-body">
        <div class="kpi-value">{{ card.value }}</div>
        <div class="kpi-label">{{ card.label }}</div>
        <div v-if="card.sub" class="kpi-sub">{{ card.sub }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--spacing-md);
  font-family: var(--font-family);
}

.kpi-card {
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-5);
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}
.kpi-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-1px);
}

.kpi-icon {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  color: var(--color-primary);
}

.kpi-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.kpi-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
  color: var(--color-text-heading);
}

.kpi-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  font-weight: var(--font-weight-medium);
}

.kpi-sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Varianty koloru wartości */
.kpi-success .kpi-value { color: var(--color-success); }
.kpi-accent  .kpi-value { color: var(--color-info); }
.kpi-danger  .kpi-value { color: var(--color-danger); }
.kpi-warn    .kpi-value { color: var(--color-warning); }
.kpi-default .kpi-value { color: var(--color-primary); }
</style>
