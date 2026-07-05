<template>
  <Transition name="modal">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('cancel')">
      <div class="modal-box" style="min-width:320px;max-width:440px;" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
        <div class="modal-title" id="confirm-dialog-title">{{ title }}</div>
        <p style="color:var(--color-text-body);font-size:14px;line-height:1.6;">{{ message }}</p>
        <div class="modal-actions">
          <button class="btn btn-secondary btn-sm" @click="$emit('cancel')">{{ cancelLabel }}</button>
          <button class="btn btn-danger btn-sm" @click="$emit('confirm')">{{ confirmLabel }}</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  visible: Boolean,
  title: { type: String, default: 'Potwierdzenie' },
  message: { type: String, default: 'Czy na pewno chcesz wykonać tę operację?' },
  confirmLabel: { type: String, default: 'Tak, usuń' },
  cancelLabel: { type: String, default: 'Anuluj' },
})
defineEmits(['confirm', 'cancel'])
</script>
