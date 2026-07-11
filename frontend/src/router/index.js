import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NProgress from 'nprogress'

NProgress.configure({ showSpinner: false, speed: 300, minimum: 0.2 })

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPasswordView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/home' },
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/HomeView.vue'),
      },
      {
        path: 'dashboard/:section',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        props: true,
      },
      {
        path: 'contractors/new',
        name: 'ContractorNew',
        component: () => import('@/views/ContractorFormView.vue'),
      },
      {
        path: 'contractors/:id/edit',
        name: 'ContractorEdit',
        component: () => import('@/views/ContractorFormView.vue'),
        props: true,
      },
      {
        path: 'articles/new',
        name: 'ArticleNew',
        component: () => import('@/views/ArticleFormView.vue'),
      },
      {
        path: 'articles/:id/edit',
        name: 'ArticleEdit',
        component: () => import('@/views/ArticleFormView.vue'),
        props: true,
      },
      {
        path: 'reservations',
        name: 'Reservations',
        component: () => import('@/views/ReservationsView.vue'),
      },
      {
        path: 'contracts/new',
        name: 'ContractNew',
        component: () => import('@/views/ContractFormView.vue'),
      },
      {
        path: 'contracts/:id/edit',
        name: 'ContractEdit',
        component: () => import('@/views/ContractFormView.vue'),
        props: true,
      },
      {
        path: 'worker',
        name: 'Worker',
        component: () => import('@/views/WorkerView.vue'),
      },
      {
        path: 'commissions',
        name: 'Commissions',
        component: () => import('@/views/CommissionView.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
      },
      {
        path: 'password',
        name: 'ChangePassword',
        component: () => import('@/views/ChangePasswordView.vue'),
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/AdminView.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'archive',
        name: 'Archive',
        component: () => import('@/views/ArchiveView.vue'),
      },
      {
        path: 'stats',
        redirect: '/analytics',
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/AnalyticsView.vue'),
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory('/rao'),
  routes,
})

router.beforeEach((to, from, next) => {
  NProgress.start()
  const auth = useAuthStore()
  if (to.meta.requiresAuth !== false && !auth.isAuthenticated) {
    NProgress.done()
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  if (to.name === 'Login' && auth.isAuthenticated) {
    NProgress.done()
    return next('/')
  }
  if (to.meta.requiresAdmin && auth.user?.role !== 'admin') {
    NProgress.done()
    return next('/home')
  }
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
