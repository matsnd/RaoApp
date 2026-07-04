<script setup lang="ts">
import { computed } from 'vue'
import { useToastStore, type ToastType } from '@/stores/toast'

const toastStore = useToastStore()

const iconFor: Record<ToastType, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
  warning: '⚠',
}

const toasts = computed(() => toastStore.items)

function close(id: number): void {
  toastStore.dismiss(id)
}
</script>

<template>
  <div class="app-toast-stack" role="region" aria-label="Powiadomienia" aria-live="polite">
    <transition-group name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        :class="['app-toast', `app-toast--${t.type}`]"
        role="alert"
      >
        <span class="app-toast__icon" aria-hidden="true">{{ iconFor[t.type] }}</span>
        <span class="app-toast__msg">{{ t.message }}</span>
        <button
          type="button"
          class="app-toast__close"
          aria-label="Zamknij powiadomienie"
          @click="close(t.id)"
        >×</button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.app-toast-stack {
  position: fixed;
  top: var(--spacing-4);
  right: var(--spacing-4);
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  pointer-events: none;
  max-width: 380px;
}

.app-toast {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-bg-white);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-modal);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text-body);
  border-left: 4px solid var(--color-primary);
  min-width: 280px;
}

.app-toast--success { border-left-color: var(--color-success); }
.app-toast--error   { border-left-color: var(--color-error); }
.app-toast--info    { border-left-color: var(--color-info); }
.app-toast--warning { border-left-color: var(--color-warning); }

.app-toast__icon {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
  font-weight: var(--font-weight-bold);
  color: var(--color-bg-white);
  margin-top: 1px;
}
.app-toast--success .app-toast__icon { background: var(--color-success); }
.app-toast--error   .app-toast__icon { background: var(--color-error); }
.app-toast--info    .app-toast__icon { background: var(--color-info); }
.app-toast--warning .app-toast__icon { background: var(--color-warning); }

.app-toast__msg {
  flex: 1 1 auto;
  line-height: var(--line-height-normal);
  word-break: break-word;
}

.app-toast__close {
  flex: 0 0 auto;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  color: var(--color-text-muted);
  padding: 0 2px;
  margin-top: -2px;
  border-radius: var(--border-radius-sm);
}
.app-toast__close:hover {
  color: var(--color-text-heading);
  background: var(--color-bg-light);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
.toast-move {
  transition: transform 0.25s ease;
}
</style>
