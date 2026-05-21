/**
 * useToast — prosty system powiadomień
 * Renderuje toast w App.vue
 * Singleton pattern - jeden ref toast dla całej aplikacji
 */
import { ref } from 'vue'

const toast = ref(null)

export function useToast() {
  function showToast(message, type = 'success', duration = 3000) {
    toast.value = { message, type, duration }
    setTimeout(() => {
      toast.value = null
    }, duration)
  }

  return { toast, showToast }
}
