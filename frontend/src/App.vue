<template>
  <router-view />
  <Toast v-if="toastStore.toast" :message="toastStore.toast.message" :type="toastStore.toast.type" :duration="toastStore.toast.duration" />
</template>

<script setup>
import { useToastStore } from '@/stores/toast'
import Toast from '@/components/shared/Toast.vue'

const toastStore = useToastStore()
</script>
