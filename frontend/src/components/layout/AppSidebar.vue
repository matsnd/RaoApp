<template>
  <nav class="sidebar">
    <div class="sidebar-logo">RAO</div>
    <button
      v-for="item in topItems"
      :key="item.section"
      :class="['sidebar-btn', { active: activeSection === item.section }]"
      @click="$emit('navigate', item.section)"
    >{{ item.label }}</button>
    <div class="sidebar-spacer"></div>
    <div class="sidebar-bottom">
      <button
        :class="['sidebar-btn', { active: activeSection === 'reports' }]"
        @click="$emit('navigate', 'reports')"
      >Raporty</button>
      <button
        :class="['sidebar-btn', { active: activeSection === 'settings' }]"
        @click="$emit('navigate', 'settings')"
      >Ustawienia</button>
      <button class="sidebar-btn" style="opacity:0.6;font-size:12px;" @click="handleLogout">Wyloguj</button>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineProps({ activeSection: String })
defineEmits(['navigate'])

const router = useRouter()
const authStore = useAuthStore()

const topItems = [
  { section: 'contracts', label: 'Umowy' },
  { section: 'contractors', label: 'Kontrahenci' },
  { section: 'articles', label: 'Artykuły' },
]

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
