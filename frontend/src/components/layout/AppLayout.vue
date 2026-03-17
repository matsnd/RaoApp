<template>
  <div class="app-shell">
    <AppSidebar :active-section="activeSection" @navigate="handleNavigate" />
    <div class="main-area">
      <router-view :key="route.fullPath" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppSidebar from './AppSidebar.vue'

const route = useRoute()
const router = useRouter()

const activeSection = computed(() => {
  const section = route.params.section
  if (section) return section
  if (route.path.startsWith('/contractors')) return 'contractors'
  if (route.path.startsWith('/contracts')) return 'contracts'
  if (route.path.startsWith('/articles')) return 'articles'
  if (route.path.startsWith('/worker')) return 'worker'
  if (route.path.startsWith('/commissions')) return 'commissions'
  if (route.path.startsWith('/settings')) return 'settings'
  if (route.path.startsWith('/admin')) return 'admin'
  return 'contracts'
})

function handleNavigate(section) {
  if (section === 'settings') {
    router.push('/settings')
  } else if (section === 'admin') {
    router.push('/admin')
  } else if (section === 'worker') {
    router.push('/worker')
  } else if (section === 'commissions') {
    router.push('/commissions')
  } else {
    router.push(`/dashboard/${section}`)
  }
}
</script>
