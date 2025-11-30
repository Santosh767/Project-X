<template>
  <div class="cover-container-wrapper">
    <div class="cover-container">
      <i class="bi bi-hospital hospital-icon"></i>
      
      <h1>Hospital Management System</h1>
      
      <p class="lead">
        A comprehensive solution for all your hospital management needs
      </p>
      
      <div class="features">
        <div class="feature">
          <i class="bi bi-person-badge"></i>
          <h5>Patient Care</h5>
        </div>
        <div class="feature">
          <i class="bi bi-calendar-check"></i>
          <h5>Appointments</h5>
        </div>
        <div class="feature">
          <i class="bi bi-file-medical"></i>
          <h5>Records</h5>
        </div>
      </div>
      
      <router-link to="/login" class="btn btn-custom">
        <i class="bi bi-box-arrow-in-right me-2"></i>
        Get Started
      </router-link>
      
      <p class="footer-text">
        <i class="bi bi-shield-check me-1"></i>
        Secure • Reliable • Efficient
      </p>
    </div>
  </div>
</template>

<style scoped>
.cover-container-wrapper {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.cover-container {
  text-align: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width: 90%;
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hospital-icon {
  font-size: 120px;
  color: #667eea;
  margin-bottom: 20px;
}

h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 15px;
}

.lead {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 30px;
}

.features {
  display: flex;
  justify-content: space-around;
  margin: 30px 0;
  flex-wrap: wrap;
}

.feature {
  flex: 1;
  min-width: 150px;
  padding: 15px;
  margin: 10px;
  background: #f8f9fa;
  border-radius: 10px;
  transition: transform 0.3s ease;
}

.feature:hover {
  transform: translateY(-5px);
  background: #e9ecef;
}

.feature i {
  font-size: 2.5rem;
  color: #667eea;
  margin-bottom: 10px;
}

.btn-custom {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 15px 50px;
  font-size: 1.2rem;
  font-weight: 600;
  border-radius: 50px;
  transition: all 0.3s ease;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
  text-decoration: none;
  display: inline-block;
}

.btn-custom:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
  color: white;
}

.footer-text {
  margin-top: 30px;
  color: #999;
  font-size: 0.9rem;
}
</style>