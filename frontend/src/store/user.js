import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: false
  }),
  
  getters: {
    userRole: (state) => state.user?.role || null
  },
  
  actions: {
    login(token, user) {
      this.token = token
      this.user = user
      this.isAuthenticated = true
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    
    logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
    
    initializeAuth() {
      const token = localStorage.getItem('token')
      const userStr = localStorage.getItem('user')
      
      if (token && userStr) {
        this.token = token
        this.user = JSON.parse(userStr)
        this.isAuthenticated = true
      }
    }
  }
})