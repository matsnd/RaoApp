<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'

interface Props {
  open: boolean
  title: string
  subtitle?: string
  loading?: boolean
  error?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

function onKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape' && props.open) {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})

// Watch open — gdy zamykamy, przywróć scroll body (bezpieczne nawet gdy nie był blokowany)
watch(
  () => props.open,
  (isOpen) => {
    if (typeof document === 'undefined') return
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
)

function onOverlayClick(): void {
  emit('close')
}

function onDrawerClick(e: MouseEvent): void {
  // nie zamykaj gdy klik wewnątrz drawera
  e.stopPropagation()
}

function close(): void {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drill-fade">
      <div
        v-if="open"
        class="drill-overlay"
        data-testid="drill-overlay"
        @click="onOverlayClick"
      >
        <div
          class="drill-drawer"
          data-testid="drill-drawer"
          @click="onDrawerClick"
        >
          <!-- Header -->
          <div class="drill-header">
            <div class="drill-title-block">
              <h3 class="drill-title">{{ title }}</h3>
              <p v-if="subtitle" class="drill-subtitle">{{ subtitle }}</p>
            </div>
            <button
              type="button"
              class="drill-close"
              data-testid="drill-close"
              title="Zamknij (Esc)"
              @click="close"
            >✕</button>
          </div>

          <!-- RAO-P2-065 #15: opcjonalny slot toolbar (np. pasek wyszukiwania w ArchiveView) -->
          <div v-if="$slots.toolbar" class="drill-toolbar" data-testid="drill-toolbar">
            <slot name="toolbar"></slot>
          </div>

          <!-- Body -->
          <div class="drill-body">
            <!-- Loading -->
            <div v-if="loading" class="drill-skeleton" data-testid="drill-loading">
              <div v-for="i in 5" :key="i" class="drill-skel-row"></div>
            </div>

            <!-- Error -->
            <div v-else-if="error" class="drill-error" data-testid="drill-error">
              <p>Nie udało się pobrać danych.</p>
              <p class="drill-error-detail">{{ error }}</p>
            </div>

            <!-- Content slot -->
            <slot v-else></slot>
          </div>

          <!-- Footer slot (np. paginacja) -->
          <div v-if="$slots.footer" class="drill-footer" data-testid="drill-footer">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<!-- NON-SCOPED style — bo <Teleport to="body"> traci atrybuty scoped.
     Prefiks klas: drill- (unikamy kolizji ze stylem ArchiveView.vue). -->
<style>
.drill-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.drill-drawer {
  width: 60%;
  min-width: 480px;
  max-width: 900px;
  height: 100%;
  background: var(--color-bg-white);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-modal);
  font-family: var(--font-family);
}

/* Transition: slide-in z prawej + fade overlay */
.drill-fade-enter-active,
.drill-fade-leave-active {
  transition: opacity 0.2s ease;
}
.drill-fade-enter-active .drill-drawer,
.drill-fade-leave-active .drill-drawer {
  transition: transform 0.25s ease;
}
.drill-fade-enter-from,
.drill-fade-leave-to {
  opacity: 0;
}
.drill-fade-enter-from .drill-drawer,
.drill-fade-leave-to .drill-drawer {
  transform: translateX(100%);
}

.drill-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-white);
  flex: 0 0 auto;
}
.drill-title-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.drill-title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  line-height: var(--line-height-tight);
}
.drill-subtitle {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}
.drill-close {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-md);
  color: var(--color-text-muted);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  line-height: 1;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.drill-close:hover {
  background: var(--color-bg-light);
  color: var(--color-text-heading);
}

.drill-body {
  flex: 1;
  overflow: auto;
  padding: var(--spacing-lg) var(--spacing-5);
}

/* RAO-P2-065 #15: toolbar (slot między header a body) */
.drill-toolbar {
  flex: 0 0 auto;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-light);
}

/* Skeleton */
.drill-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.drill-skel-row {
  height: 40px;
  background: var(--color-bg-light);
  border-radius: var(--border-radius-sm);
  animation: drill-pulse 1.2s ease-in-out infinite;
}
@keyframes drill-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Error */
.drill-error {
  text-align: center;
  padding: var(--spacing-2xl) var(--spacing-5);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
.drill-error p {
  margin: var(--spacing-sm) 0;
}
.drill-error-detail {
  color: var(--color-danger);
  font-size: var(--font-size-xs);
}

/* Footer */
.drill-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-5);
  border-top: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  background: var(--color-bg-white);
  flex: 0 0 auto;
}
</style>
