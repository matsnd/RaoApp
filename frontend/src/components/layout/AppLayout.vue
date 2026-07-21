<template>
  <div class="app-shell">
    <AppSidebar :active-section="activeSection" @navigate="handleNavigate" />
    <div class="main-area">
      <router-view :key="route.fullPath" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppSidebar from './AppSidebar.vue'

const route = useRoute()
const router = useRouter()

const activeSection = computed(() => {
  const section = route.params.section
  if (section) return section
  if (route.path.startsWith('/contractors')) return 'contractors'
  if (route.path.startsWith('/contracts')) return 'contracts'
  if (route.path.startsWith('/machines')) return 'machines'
  if (route.path.startsWith('/services')) return 'services'
  if (route.path.startsWith('/additional-services')) return 'additional-services'
  if (route.path.startsWith('/articles')) return 'machines'  // backward compat
  if (route.path.startsWith('/reservations')) return 'reservations'
  if (route.path.startsWith('/deliveries')) return 'deliveries'
  if (route.path.startsWith('/worker')) return 'worker'
  if (route.path.startsWith('/analytics')) return 'analytics'
  if (route.path.startsWith('/commissions')) return 'commissions'
  if (route.path.startsWith('/archive')) return 'archive'
  if (route.path.startsWith('/settings')) return 'settings'
  if (route.path.startsWith('/password')) return 'password'
  if (route.path.startsWith('/admin')) return 'admin'
  if (route.path === '/home') return 'home'
  return 'contracts'
})

// Keyboard shortcuts: Ctrl+N → new item, Escape → back
function handleKeydown(e) {
  // Ignore when typing in inputs / textareas / selects
  const tag = document.activeElement?.tagName
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return
  // Ignore when a modal overlay is open
  if (document.querySelector('.modal-overlay')) return

  if (e.ctrlKey && e.key === 'n') {
    e.preventDefault()
    const section = activeSection.value
    if (section === 'contracts') router.push({ name: 'ContractNew' })
    else if (section === 'contractors') router.push({ name: 'ContractorNew' })
    else if (section === 'machines') router.push({ name: 'MachineNew' })
  }
  if (e.key === 'Escape') {
    // Go back if we are in a form view
    const path = route.path
    if (path.endsWith('/new') || path.includes('/edit')) {
      router.back()
    }
  }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

function handleNavigate(section) {
  if (section === 'home') {
    router.push('/home')
  } else if (section === 'settings') {
    router.push('/settings')
  } else if (section === 'admin') {
    router.push('/admin')
  } else if (section === 'password') {
    router.push('/password')
  } else if (section === 'worker') {
    router.push('/worker')
  } else if (section === 'stats') {
    router.push('/analytics')
  } else if (section === 'analytics') {
    router.push('/analytics')
  } else if (section === 'commissions') {
    router.push('/commissions')
  } else if (section === 'reservations') {
    router.push('/reservations')
  } else if (section === 'deliveries') {
    router.push('/deliveries')
  } else if (section === 'machines') {
    router.push('/machines')
  } else if (section === 'services') {
    router.push('/services')
  } else if (section === 'additional-services') {
    router.push('/additional-services')
  } else if (section === 'archive') {
    router.push('/archive')
  } else {
    router.push(`/dashboard/${section}`)
  }
}
</script>
