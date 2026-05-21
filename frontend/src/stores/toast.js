import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toast = ref(null)

  function showToast(message, type = 'success', duration = 3000) {
    toast.value = { message, type, duration }
    setTimeout(() => {
      toast.value = null
    }, duration)
  }

  return { toast, showToast }
})
