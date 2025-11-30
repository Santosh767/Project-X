export default [
    {
      path: '/patient/dashboard',
      name: 'PatientDashboard',
      component: () => import('@/views/patient/dashboard/PatientDashboard.vue'),
      meta: { requiresAuth: true, role: 'patient' }
    },
    {
      path: '/patient/appointments',
      name: 'PatientAppointments',
      component: () => import('@/views/patient/PatientAppointments.vue'),
      meta: { requiresAuth: true, role: 'patient' }
    }
  ]