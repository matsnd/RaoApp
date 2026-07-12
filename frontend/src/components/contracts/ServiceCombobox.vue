<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface ServiceOption {
  id: number
  name: string
  display_name?: string | null
  default_amount?: number | string | null
}

interface Props {
  modelValue: number | null
  services: ServiceOption[]
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Wpisz aby wyszukać...',
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
  'select': [service: ServiceOption | null]
}>()

const isOpen = ref(false)
const query = ref('')
const rootRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const highlightedIndex = ref(-1)

const selectedName = computed(() => {
  if (props.modelValue == null) return ''
  const s = props.services.find((x) => x.id === props.modelValue)
  return s ? (s.display_name || s.name) : ''
})

const displayValue = computed(() => (isOpen.value ? query.value : selectedName.value))

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.services
  return props.services.filter((s) =>
    (s.display_name || s.name).toLowerCase().includes(q)
  )
})

function open() {
  isOpen.value = true
  query.value = ''
  highlightedIndex.value = filtered.value.length > 0 ? 0 : -1
  setTimeout(() => inputRef.value?.focus(), 0)
}

function close() {
  isOpen.value = false
  query.value = ''
  highlightedIndex.value = -1
}

function selectService(s: ServiceOption) {
  emit('update:modelValue', s.id)
  emit('select', s)
  close()
}

function onInput(e: Event) {
  query.value = (e.target as HTMLInputElement).value
  if (!isOpen.value) isOpen.value = true
  highlightedIndex.value = filtered.value.length > 0 ? 0 : -1
}

function onKeyDown(e: KeyboardEvent) {
  if (!isOpen.value) {
    if (e.key === 'ArrowDown' || e.key === 'Enter') {
      open()
      e.preventDefault()
    }
    return
  }
  const list = filtered.value
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    highlightedIndex.value = Math.min(highlightedIndex.value + 1, list.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (highlightedIndex.value >= 0 && highlightedIndex.value < list.length) {
      selectService(list[highlightedIndex.value])
    }
  } else if (e.key === 'Escape') {
    close()
  }
}

function onClickOutside(e: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(e.target as Node)) {
    close()
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<template>
  <div class="service-combobox" ref="rootRef">
    <input
      ref="inputRef"
      type="text"
      class="form-control form-control-xs sc-input"
      :placeholder="placeholder"
      :value="displayValue"
      @focus="open"
      @input="onInput"
      @keydown="onKeyDown"
    />
    <div v-if="isOpen" class="sc-dropdown">
      <button
        v-for="(s, i) in filtered"
        :key="s.id"
        type="button"
        class="sc-option"
        :class="{ 'sc-highlighted': i === highlightedIndex }"
        @mousedown.prevent="selectService(s)"
        @mouseenter="highlightedIndex = i"
      >{{ s.display_name || s.name }}</button>
      <div v-if="filtered.length === 0" class="sc-empty">
        Brak usług pasujących do „{{ query }}”
      </div>
    </div>
  </div>
</template>

<style scoped>
.service-combobox {
  position: relative;
}

.sc-input {
  width: 100%;
}

.sc-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  box-shadow: var(--shadow-card);
  max-height: 240px;
  overflow-y: auto;
  margin-top: 2px;
}

.sc-option {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: var(--spacing-xs) var(--spacing-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.sc-option:hover,
.sc-option.sc-highlighted {
  background: var(--color-bg-light);
}

.sc-empty {
  padding: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-align: center;
}
</style>
