<template>
    <div class="sidebar">
      <div class="sidebar-header">
        <h4>Admin Panel</h4>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/admin" class="sidebar-link">Dashboard</router-link>
        <router-link to="/admin/patients" class="sidebar-link">Patients</router-link>
        <router-link to="/admin/doctors" class="sidebar-link">Doctors</router-link>
        <router-link to="/admin/appointments" class="sidebar-link">Appointments</router-link>
      </nav>
    </div>
  </template>
  
  <style scoped>
  .sidebar {
    width: 250px;
    background: #2c3e50;
    color: white;
    min-height: 100vh;
  }
  
  .sidebar-header {
    padding: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .sidebar-nav {
    padding: 1rem 0;
  }
  
  .sidebar-link {
    display: block;
    padding: 0.75rem 1.5rem;
    color: white;
    text-decoration: none;
    transition: background 0.2s;
  }
  
  .sidebar-link:hover,
  .sidebar-link.router-link-active {
    background: rgba(255, 255, 255, 0.1);
    color: white;
  }
  </style>