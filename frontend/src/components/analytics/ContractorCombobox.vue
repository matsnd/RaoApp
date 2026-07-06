<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

interface ContractorOption {
  id: number
  name: string
}

interface Props {
  modelValue: number | null
  contractors: ContractorOption[]
  placeholder?: string
  dataTestId?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Wszyscy',
  dataTestId: 'filter-contractor',
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const isOpen = ref(false)
const query = ref('')
const rootRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const highlightedIndex = ref(-1)

// Wybrany kontrahent (nazwa wyświetlana w inpucie gdy zamknięty)
const selectedName = computed(() => {
  if (props.modelValue == null) return ''
  const c = props.contractors.find((x) => x.id === props.modelValue)
  return c ? c.name : ''
})

// Display value: query gdy otwarty, selectedName gdy zamknięty
const displayValue = computed(() => (isOpen.value ? query.value : selectedName.value))

// Filtrowana lista (case-insensitive substring)
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.contractors.slice(0, 100) // limit 100 dla wydajności
  return props.contractors
    .filter((c) => c.name.toLowerCase().includes(q))
    .slice(0, 100)
})

function open() {
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

function selectContractor(c: ContractorOption | null) {
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
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (highlightedIndex.value >= 0 && highlightedIndex.value < list.length) {
      selectContractor(list[highlightedIndex.value])
    }
  } else if (e.key === 'Escape') {
    close()
  }
}

// Click outside → close
function onClickOutside(e: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(e.target as Node)) {
    close()
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))

// Reset highlight gdy lista się zmienia
watch(filtered, () => {
  highlightedIndex.value = -1
})
</script>

<template>
  <div class="contractor-combobox" ref="rootRef" :data-testid="dataTestId">
    <div class="cc-input-wrap">
      <input
        ref="inputRef"
        type="text"
        class="af-input cc-input"
        :placeholder="placeholder"
        :value="displayValue"
        :data-testid="`${dataTestId}-input`"
        @focus="open"
        @input="onInput"
        @keydown="onKeyDown"
      />
      <button
        v-if="modelValue != null && !isOpen"
        type="button"
        class="cc-clear"
        :data-testid="`${dataTestId}-clear`"
        title="Wyczyść"
        @click="clearSelection"
      >✕</button>
      <button
        v-else
        type="button"
        class="cc-toggle"
        :data-testid="`${dataTestId}-toggle`"
        title="Pokaż listę"
        @click="isOpen ? close() : open()"
      >{{ isOpen ? '▲' : '▼' }}</button>
    </div>

    <div v-if="isOpen" class="cc-dropdown" :data-testid="`${dataTestId}-dropdown`">
      <button
        type="button"
        class="cc-option cc-all"
        :class="{ 'cc-highlighted': highlightedIndex === -1 }"
        @click="selectContractor(null)"
        @mouseenter="highlightedIndex = -1"
      >Wszyscy</button>
      <button
        v-for="(c, i) in filtered"
        :key="c.id"
        type="button"
        class="cc-option"
        :class="{ 'cc-highlighted': i === highlightedIndex }"
        @click="selectContractor(c)"
        @mouseenter="highlightedIndex = i"
      >{{ c.name }}</button>
      <div v-if="filtered.length === 0" class="cc-empty">
        Brak kontrahentów pasujących do „{{ query }}”
      </div>
    </div>
  </div>
</template>

<style scoped>
.contractor-combobox {
  position: relative;
  display: inline-block;
}

.cc-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.cc-input {
  padding-right: 28px;
  width: 240px;
}

.cc-clear,
.cc-toggle {
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

.cc-clear:hover { color: var(--color-danger); }
.cc-toggle:hover { color: var(--color-text-body); }

.cc-dropdown {
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

.cc-option {
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

.cc-option:hover,
.cc-option.cc-highlighted {
  background: var(--color-bg-light);
}

.cc-all {
  font-weight: var(--font-weight-semibold);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-muted);
}

.cc-empty {
  padding: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-align: center;
}
</style>
