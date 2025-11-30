import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue')
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/AdminDashboard.vue'),
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/doctor',
    name: 'DoctorDashboard',
    component: () => import('@/views/doctor/DoctorDashboard.vue'),
    meta: { requiresAuth: true, role: 'doctor' }
  },
  {
    path: '/patient',
    name: 'PatientDashboard',
    component: () => import('@/views/patient/PatientDashboard.vue'),
    meta: { requiresAuth: true, role: 'patient' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  userStore.initializeAuth()
  
  const requiresAuth = to.meta.requiresAuth
  const requiredRole = to.meta.role
  
  if (requiresAuth && !userStore.isAuthenticated) {
    next('/login')
  } else if (requiredRole && userStore.userRole !== requiredRole) {
    next('/login')
  } else {
    next()
  }
})

export default router