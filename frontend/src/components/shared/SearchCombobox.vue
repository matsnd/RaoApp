<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

interface Option {
  id: number
  name: string
  [key: string]: unknown
}

interface Props {
  modelValue: number | null
  options: Option[]
  placeholder?: string
  dataTestId?: string
  allowClear?: boolean
  clearLabel?: string
  emptyLabel?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Wpisz aby wyszukać...',
  dataTestId: 'search-combobox',
  allowClear: true,
  clearLabel: 'Brak',
  emptyLabel: 'Brak wyników',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const isOpen = ref(false)
const query = ref('')
const rootRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const highlightedIndex = ref(-1)

const selectedName = computed(() => {
  if (props.modelValue == null) return ''
  const c = props.options.find((x) => x.id === props.modelValue)
  return c ? c.name : ''
})

const displayValue = computed(() => (isOpen.value ? query.value : selectedName.value))

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.options.slice(0, 100)
  return props.options
    .filter((c) => c.name.toLowerCase().includes(q))
    .slice(0, 100)
})

function open() {
  if (props.disabled) return
  isOpen.value = true
  query.value = ''
  highlightedIndex.value = -1
  setTimeout(() => inputRef.value?.focus(), 0)
}

function close() {
  isOpen.value = false
  query.value = ''
  highlightedIndex.value = -1
}

function selectOption(c: Option | null) {
  emit('update:modelValue', c ? c.id : null)
  close()
}

function clearSelection() {
  emit('update:modelValue', null)
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
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, -1)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (highlightedIndex.value >= 0 && highlightedIndex.value < list.length) {
      selectOption(list[highlightedIndex.value])
    } else if (highlightedIndex.value === -1 && props.allowClear) {
      selectOption(null)
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

watch(filtered, () => {
  highlightedIndex.value = -1
})
</script>

<template>
  <div class="search-combobox" ref="rootRef" :data-testid="dataTestId">
    <div class="sc-input-wrap">
      <input
        ref="inputRef"
        type="text"
        class="af-input sc-input"
        :placeholder="placeholder"
        :value="displayValue"
        :data-testid="`${dataTestId}-input`"
        :disabled="disabled"
        @focus="open"
        @input="onInput"
        @keydown="onKeyDown"
      />
      <button
        v-if="modelValue != null && !isOpen && allowClear"
        type="button"
        class="sc-clear"
        :data-testid="`${dataTestId}-clear`"
        title="Wyczyść"
        @click="clearSelection"
      >✕</button>
      <button
        v-else
        type="button"
        class="sc-toggle"
        :data-testid="`${dataTestId}-toggle`"
        title="Pokaż listę"
        @click="isOpen ? close() : open()"
      >{{ isOpen ? '▲' : '▼' }}</button>
    </div>

    <div v-if="isOpen" class="sc-dropdown" :data-testid="`${dataTestId}-dropdown`">
      <button
        v-if="allowClear"
        type="button"
        class="sc-option sc-all"
        :class="{ 'sc-highlighted': highlightedIndex === -1 }"
        @click="selectOption(null)"
        @mouseenter="highlightedIndex = -1"
      >{{ clearLabel }}</button>
      <button
        v-for="(c, i) in filtered"
        :key="c.id"
        type="button"
        class="sc-option"
        :class="{ 'sc-highlighted': i === highlightedIndex }"
        @click="selectOption(c)"
        @mouseenter="highlightedIndex = i"
      >{{ c.name }}</button>
      <div v-if="filtered.length === 0" class="sc-empty">
        {{ emptyLabel }}{{ query ? ` — „${query}”` : '' }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-combobox {
  position: relative;
  display: inline-block;
  width: 100%;
}

.sc-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.sc-input {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  padding-right: 28px;
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-body);
  background: var(--color-bg-white);
  width: 100%;
  box-sizing: border-box;
  transition: border-color var(--transition-fast);
}
.sc-input:focus {
  outline: none;
  border-color: var(--color-border-focus);
}
.sc-input:disabled {
  background: var(--color-bg-light);
  cursor: not-allowed;
}

.sc-clear,
.sc-toggle {
  position: absolute;
  right: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 11px;
  padding: 2px 4px;
  line-height: 1;
}

.sc-clear:hover { color: var(--color-danger); }
.sc-toggle:hover { color: var(--color-text-body); }

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
  max-height: 280px;
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

.sc-all {
  font-weight: var(--font-weight-semibold);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-muted);
}

.sc-empty {
  padding: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-align: center;
}
</style>
