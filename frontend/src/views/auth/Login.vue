<template>
  <div class="auth-container">
    <div class="container">
      <div class="row justify-content-center mt-5">
        <div class="col-md-5">
          <div class="card shadow">
            <div class="card-body p-5">
              <h2 class="text-center mb-4">🏥 Hospital Management</h2>
              <h5 class="text-center text-muted mb-4">Login to your account</h5>

              <div v-if="error" class="alert alert-danger">{{ error }}</div>

              <form @submit.prevent="handleLogin">
                <div class="mb-3">
                  <label class="form-label">Username</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    v-model="credentials.username" 
                    required
                    placeholder="Enter username"
                  >
                </div>

                <div class="mb-3">
                  <label class="form-label">Password</label>
                  <input 
                    type="password" 
                    class="form-control" 
                    v-model="credentials.password" 
                    required
                    placeholder="Enter password"
                  >
                </div>

                <button 
                  type="submit" 
                  class="btn btn-primary w-100"
                  :disabled="loading"
                >
                  <span v-if="loading">Logging in...</span>
                  <span v-else>Login</span>
                </button>
              </form>

              <hr class="my-4">

              <div class="text-center">
                <p class="mb-0">Don't have an account?</p>
                <router-link to="/register" class="btn btn-link">Register as Patient</router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

const credentials = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref(null)

const handleLogin = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await axios.post('/api/auth/login', credentials.value)
    
    userStore.login(response.data.access_token, response.data.user)
    
    // Redirect based on role
    const role = response.data.user.role
    if (role === 'admin') {
      router.push('/admin')
    } else if (role === 'doctor') {
      router.push('/doctor')
    } else {
      router.push('/patient')
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Login failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background-color: #f8f9fa;
  padding: 20px;
}
</style>