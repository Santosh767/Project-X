<template>
    <div class="auth-container">
      <div class="container">
        <div class="row justify-content-center mt-5">
          <div class="col-md-6">
            <div class="card shadow">
              <div class="card-body p-4">
                <h2 class="text-center mb-4">Patient Registration</h2>
  
                <div v-if="error" class="alert alert-danger">{{ error }}</div>
                <div v-if="success" class="alert alert-success">{{ success }}</div>
  
                <form @submit.prevent="handleRegister">
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Username *</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        v-model="formData.username" 
                        required
                      >
                    </div>
  
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Full Name *</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        v-model="formData.full_name" 
                        required
                      >
                    </div>
                  </div>
  
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Email *</label>
                      <input 
                        type="email" 
                        class="form-control" 
                        v-model="formData.email" 
                        required
                      >
                    </div>
  
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Phone (10 digits) *</label>
                      <input 
                        type="tel" 
                        class="form-control" 
                        v-model="formData.phone" 
                        pattern="[0-9]{10}"
                        required
                      >
                    </div>
                  </div>
  
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Password *</label>
                      <input 
                        type="password" 
                        class="form-control" 
                        v-model="formData.password" 
                        minlength="6"
                        required
                      >
                      <small class="text-muted">Minimum 6 characters</small>
                    </div>
  
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Gender</label>
                      <select class="form-select" v-model="formData.gender">
                        <option value="">Select Gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
  
                  <div class="mb-3">
                    <label class="form-label">Address</label>
                    <textarea 
                      class="form-control" 
                      v-model="formData.address" 
                      rows="2"
                    ></textarea>
                  </div>
  
                  <button 
                    type="submit" 
                    class="btn btn-primary w-100"
                    :disabled="loading"
                  >
                    <span v-if="loading">Registering...</span>
                    <span v-else>Register</span>
                  </button>
                </form>
  
                <hr class="my-4">
  
                <div class="text-center">
                  <p class="mb-0">Already have an account?</p>
                  <router-link to="/login" class="btn btn-link">Login Here</router-link>
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
  import apiClient from '@/utils/api'
  
  const router = useRouter()
  
  const formData = ref({
    username: '',
    email: '',
    password: '',
    full_name: '',
    phone: '',
    gender: '',
    address: ''
  })
  
  const loading = ref(false)
  const error = ref(null)
  const success = ref(null)
  
  const handleRegister = async () => {
    loading.value = true
    error.value = null
    success.value = null
  
    try {
      await apiClient.post('/api/auth/register', formData.value)
      
      success.value = 'Registration successful! Redirecting to login...'
      
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } catch (err) {
      error.value = err.response?.data?.error || 'Registration failed. Please try again.'
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