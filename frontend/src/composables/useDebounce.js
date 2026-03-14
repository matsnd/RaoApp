import { ref, watch } from 'vue'

export function useDebounce(value, delay = 400) {
  const debounced = ref(value.value)
  let timer = null

  watch(value, (newVal) => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      debounced.value = newVal
    }, delay)
  })

  return debounced
}
