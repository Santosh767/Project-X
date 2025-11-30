<template>
  <footer class="footer mt-auto py-3 bg-light">
    <div class="container text-center">
      <span class="text-muted">
        <i class="bi bi-hospital me-2"></i>
        Hospital Management System © {{ currentYear }}
      </span>
      <div class="mt-2">
        <small class="text-secondary">
          <i class="bi bi-shield-check me-1"></i>
          Secure • Reliable • Efficient
        </small>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped>
.footer {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid #dee2e6;
  margin-top: 2rem;
}
</style>