export default [
    {
      path: '/admin',
      name: 'AdminDashboard',
      component: () => import('@/views/admin/AdminDashboard.vue'),
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/patients',
      name: 'AdminPatients',
      component: () => import('@/views/admin/AdminPatients.vue'),
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/doctors',
      name: 'AdminDoctors',
      component: () => import('@/views/admin/AdminDoctors.vue'),
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/appointments',
      name: 'AdminAppointments',
      component: () => import('@/views/admin/AdminAppointments.vue'),
      meta: { requiresAuth: true, role: 'admin' }
    }
  ]