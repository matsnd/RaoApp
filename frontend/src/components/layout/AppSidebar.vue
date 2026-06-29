<template>
  <nav class="sidebar">
    <!-- RAO-P3-003: Logo firmy (jeśli wgrane) lub domyślna nazwa -->
    <div class="sidebar-logo">
      <img
        src="/logo.svg"
        alt="TOOLSMART"
        class="sidebar-company-logo"
      />
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
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'

defineProps({ activeSection: String })
defineEmits(['navigate'])

const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const topItems = [
  { section: 'contracts', label: 'Umowy' },
  { section: 'contractors', label: 'Kontrahenci' },
  { section: 'articles', label: 'Artykuły' },
]

function handleLogout() {
  authStore.logout()
  // RAO-P1-042: hard redirect czyści wszystkie Pinia stores (memory safety)
  // router.push zostawia cached data w stores (contracts, contractors, etc.)
  window.location.href = '/login'
}

// RAO-P3-003: załaduj dane firmy (logo) jeśli nie są dostępne
onMounted(async () => {
  if (!settingsStore.company) {
    await settingsStore.fetchCompany()
  }
})
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
/* RAO-P3-003: logo firmy w sidebarze */
.sidebar-company-logo {
  max-height: 22px;
  width: auto;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}
</style>
