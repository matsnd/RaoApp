import { ref, computed } from 'vue'

export function usePagination(perPage = 50) {
  const page = ref(1)
  const total = ref(0)
  const itemsPerPage = ref(perPage)

  const totalPages = computed(() => Math.ceil(total.value / itemsPerPage.value) || 1)
  const hasPrev = computed(() => page.value > 1)
  const hasNext = computed(() => page.value < totalPages.value)

  function setTotal(n) { total.value = n }
  function goToPage(n) { page.value = Math.max(1, Math.min(n, totalPages.value)) }
  function prev() { if (hasPrev.value) page.value-- }
  function next() { if (hasNext.value) page.value++ }
  function reset() { page.value = 1 }

  return { page, total, itemsPerPage, totalPages, hasPrev, hasNext, setTotal, goToPage, prev, next, reset }
}
