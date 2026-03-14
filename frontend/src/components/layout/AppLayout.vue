<template>
  <div class="app-shell">
    <AppSidebar :active-section="activeSection" @navigate="handleNavigate" />
    <div class="main-area">
      <router-view />
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
  if (route.path.startsWith('/settings')) return 'settings'
  return 'contracts'
})

function handleNavigate(section) {
  if (section === 'settings') {
    router.push('/settings')
  } else {
    router.push(`/dashboard/${section}`)
  }
}
</script>
