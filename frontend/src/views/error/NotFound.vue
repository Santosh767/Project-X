<template>
    <div class="not-found">
      <h1>404</h1>
      <p>Page Not Found</p>
      <router-link to="/" class="btn btn-primary">Go Home</router-link>
    </div>
  </template>
  
  <style scoped>
  .not-found {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
  }
  
  h1 {
    font-size: 6rem;
    color: #667eea;
  }
  </style>