<template>
  <div class="toolbar">
    <button v-if="showViewButton" class="toolbar-btn" title="Podgląd / Drukuj" @click="$emit('view')">⎙</button>
    <span class="toolbar-info">{{ infoText }}</span>
    <button v-if="showHelpButton" class="toolbar-btn" title="Szczegóły" @click="$emit('help')">?</button>
    <button class="toolbar-btn danger" title="Usuń" @click="$emit('remove')">−</button>
    <button class="toolbar-btn success" title="Dodaj nowy" @click="$emit('add')">+</button>
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
