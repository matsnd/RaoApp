<template>
  <router-view v-slot="{ Component }">
    <Transition name="fade" mode="out-in">
      <component :is="Component" />
    </Transition>
  </router-view>
  <AppToast />
</template>

<script setup lang="ts">
import AppToast from '@/components/AppToast.vue'
</script>
