<template>
  <nav class="sidebar">
    <div class="sidebar-logo">
      <span class="sidebar-logo-text">TOOLSMART</span>
      <span class="sidebar-logo-sub">WYNAJEM MASZYN</span>
    </div>
    <button
      :class="['sidebar-btn', 'sidebar-btn-home', { active: activeSection === 'home' }]"
      @click="$emit('navigate', 'home')"
    >Start</button>
    <div class="sidebar-divider"></div>
    <button
      v-for="item in topItems"
      :key="item.section"
      :class="['sidebar-btn', { active: activeSection === item.section }]"
      @click="$emit('navigate', item.section)"
    >{{ item.label }}</button>
    <div class="sidebar-spacer"></div>
    <div class="sidebar-bottom">
      <button
        :class="['sidebar-btn', { active: activeSection === 'worker' }]"
        @click="$emit('navigate', 'worker')"
      >Pulpit</button>
      <button
        :class="['sidebar-btn', { active: activeSection === 'commissions' }]"
        @click="$emit('navigate', 'commissions')"
      >Prowizje</button>
      <button
        :class="['sidebar-btn', { active: activeSection === 'reports' }]"
        @click="$emit('navigate', 'reports')"
      >Raporty</button>
      <button
        :class="['sidebar-btn', { active: activeSection === 'settings' }]"
        @click="$emit('navigate', 'settings')"
      >Ustawienia</button>
      <button
        v-if="authStore.user?.role === 'admin'"
        :class="['sidebar-btn', { active: activeSection === 'admin' }]"
        @click="$emit('navigate', 'admin')"
      >Admin</button>
      <button class="sidebar-btn" style="opacity:0.8;font-size:12px;" @click="$emit('navigate', 'password')">Zmień hasło</button>
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

<style scoped>
.sidebar-divider {
  height: 1px;
  background: rgba(255,255,255,0.12);
  margin: 4px 12px;
}
.sidebar-btn-home {
  font-size: 13px;
}
</style>
