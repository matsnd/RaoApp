<template>
  <div class="toolbar">
    <button v-if="showViewButton" class="toolbar-btn" title="Podgląd / Drukuj" aria-label="Podgląd i drukuj umowę" @click="$emit('view')">⎙</button>
    <span class="toolbar-info">{{ infoText }}</span>
    <button v-if="showHelpButton" class="toolbar-btn" title="Szczegóły" aria-label="Pokaż szczegóły umowy" @click="$emit('help')">?</button>
    <button class="toolbar-btn danger" title="Usuń" aria-label="Usuń wybraną pozycję" @click="$emit('remove')">−</button>
    <button class="toolbar-btn success" title="Dodaj nowy" aria-label="Dodaj nową pozycję" @click="$emit('add')">+</button>
  </div>
</template>

<script setup>
defineProps({
  infoText: { type: String, default: '' },
  showViewButton: { type: Boolean, default: false },
  showHelpButton: { type: Boolean, default: false },
})
defineEmits(['view', 'help', 'remove', 'add'])
</script>
