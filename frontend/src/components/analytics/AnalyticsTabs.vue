<script setup lang="ts">
export interface AnalyticsTab {
  key: string
  label: string
  icon?: string
}

interface Props {
  tabs: AnalyticsTab[]
  active: string
}

defineProps<Props>()

const emit = defineEmits<{
  change: [key: string]
}>()

function select(key: string): void {
  emit('change', key)
}
</script>

<template>
  <div class="analytics-tabs" data-testid="analytics-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      :class="['at-tab', { 'at-tab-active': active === tab.key }]"
      :data-testid="`tab-${tab.key}`"
      @click="select(tab.key)"
    >
      <span v-if="tab.icon" class="at-tab-icon">{{ tab.icon }}</span>
      <span class="at-tab-label">{{ tab.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.analytics-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  font-family: var(--font-family);
}

.at-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-body);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius-pill);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
}
.at-tab:hover {
  background: var(--color-bg-light);
}
.at-tab-active {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  border-color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}
.at-tab-active:hover {
  background: var(--color-primary);
}

.at-tab-icon {
  font-size: var(--font-size-base);
  line-height: 1;
}
</style>
