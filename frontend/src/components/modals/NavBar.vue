<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
      <router-link class="navbar-brand" to="/">
        <i class="bi bi-hospital me-2"></i>
        HMS
      </router-link>
      <button 
        class="navbar-toggler" 
        type="button" 
        data-bs-toggle="collapse" 
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item" v-if="!userStore.isAuthenticated">
            <router-link class="nav-link" to="/login">Login</router-link>
          </li>
          <li class="nav-item" v-if="!userStore.isAuthenticated">
            <router-link class="nav-link" to="/register">Sign Up</router-link>
          </li>
          <li class="nav-item" v-if="userStore.isAuthenticated">
            <span class="nav-link">{{ userStore.user?.full_name || userStore.user?.username }}</span>
          </li>
          <li class="nav-item" v-if="userStore.isAuthenticated">
            <button class="btn btn-link nav-link" @click="logout">Logout</button>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useUserStore } from '@/store/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const logout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  font-weight: 600;
  font-size: 1.5rem;
}

.btn-link {
  text-decoration: none;
  color: rgba(255, 255, 255, 0.85);
}

.btn-link:hover {
  color: white;
}
</style>