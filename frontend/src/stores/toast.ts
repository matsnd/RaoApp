import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastItem {
  id: number
  message: string
  type: ToastType
  duration: number
}

let nextId = 1

/**
 * RAO-P2-070: Centralny store toastów.
 * Stackuje wiele toastów, auto-dismiss po `duration` (ms), manual close przez dismiss(id).
 * Pozycja renderowania: top-right (komponent AppToast.vue).
 */
export const useToastStore = defineStore('toast', () => {
  const items = ref<ToastItem[]>([])

  function push(message: string, type: ToastType = 'info', duration = 4000): number {
    const id = nextId++
    items.value.push({ id, message, type, duration })
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
    return id
  }

  function dismiss(id: number): void {
    const idx = items.value.findIndex((t) => t.id === id)
    if (idx >= 0) items.value.splice(idx, 1)
  }

  function clear(): void {
    items.value = []
  }

  // Wygodne akcje semantyczne (B6/B7)
  function success(message: string, duration = 4000): number {
    return push(message, 'success', duration)
  }

  function error(message: string, duration = 6000): number {
    return push(message, 'error', duration)
  }

  function info(message: string, duration = 4000): number {
    return push(message, 'info', duration)
  }

  function warning(message: string, duration = 5000): number {
    return push(message, 'warning', duration)
  }

  // Backward-compat: stara API showToast(message, type, duration)
  function showToast(message: string, type: ToastType = 'success', duration = 4000): number {
    return push(message, type, duration)
  }

  return { items, push, dismiss, clear, success, error, info, warning, showToast }
})
