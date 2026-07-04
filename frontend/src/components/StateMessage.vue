<script setup lang="ts">
/**
 * StateMessage - reuzywalny komponent stanow loading / error / empty.
 * RAO-P2-049: spojne stany we wszystkich widokach listowych.
 *
 * Props:
 *  - type: 'loading' | 'error' | 'empty'
 *  - message: tekst komunikatu
 *  - actionLabel: etykieta przycisku (opcjonalnie)
 *  - retryLabel: alias dla actionLabel (kompatybilnosc)
 *  - compact: tryb kompaktowy (mniejsze paddingi, np. wewnatrz komorki tabeli)
 *
 * Emits:
 *  - action: klik przycisku (np. "Sprobuj ponownie" / "Dodaj")
 *
 * Style wylacznie przez zmienne CSS z style.css (brak inline hardcoded colors).
 */
interface Props {
  type: 'loading' | 'error' | 'empty'
  message?: string
  actionLabel?: string
  retryLabel?: string
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  message: '',
  actionLabel: '',
  retryLabel: '',
  compact: false,
})

const emit = defineEmits<{ action: [] }>()

function defaultLabel(): string {
  if (props.type === 'loading') return ''
  if (props.type === 'error') return 'Sprobuj ponownie'
  return ''
}

const buttonLabel = (): string => props.actionLabel || props.retryLabel || defaultLabel()
const hasAction = (): boolean => !!(props.actionLabel || props.retryLabel || props.type === 'error')

function onAction(): void {
  emit('action')
}
</script>

<template>
  <div
    class="state-message"
    :class="[`state-${type}`, { 'state-compact': compact }]"
    :data-testid="`state-${type}`"
    role="status"
    :aria-live="type === 'error' ? 'assertive' : 'polite'"
  >
    <span v-if="type === 'loading'" class="state-spinner" aria-hidden="true"></span>
    <span v-else-if="type === 'error'" class="state-icon" aria-hidden="true">⚠️</span>
    <span v-else class="state-icon" aria-hidden="true">📭</span>

    <span class="state-text">
      {{ message || (type === 'loading' ? 'Ladowanie...' : type === 'error' ? 'Wystapil blad' : 'Brak danych') }}
    </span>

    <button
      v-if="hasAction()"
      type="button"
      class="btn btn-primary btn-sm state-action"
      :data-testid="`state-${type}-action`"
      @click="onAction"
    >
      {{ buttonLabel() }}
    </button>
  </div>
</template>

<style scoped>
.state-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  padding: var(--spacing-8) var(--spacing-4);
  font-family: var(--font-family);
  color: var(--color-text-body);
  text-align: center;
  min-height: 120px;
}

.state-compact {
  padding: var(--spacing-4);
  min-height: 80px;
}

.state-icon {
  font-size: 28px;
  line-height: 1;
}

.state-text {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  max-width: 480px;
}

.state-error .state-text {
  color: var(--color-error);
}

.state-empty .state-text {
  color: var(--color-text-muted);
}

.state-action {
  margin-top: var(--spacing-1);
}

/* Spinner - uzywa koloru primary z design systemu */
.state-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: state-spin 0.8s linear infinite;
}

@keyframes state-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .state-spinner {
    animation-duration: 1.6s;
  }
}
</style>