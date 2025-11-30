<template>
  <div class="container-fluid py-4">
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-orange mb-4 rounded shadow-sm px-3 sticky-top">
      <span class="navbar-brand mb-0 h1 fw-bold">🏥 HMS Admin Dashboard</span>
      <button 
        class="btn ms-auto" 
        style="border: 2px solid #fff; color: #fff; background-color: transparent;" 
        @click="logout"
      >
        Logout
      </button>
    </nav>

    <!-- Statistics Cards -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-primary text-white">
        <span>📊 Dashboard Statistics</span>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-2" v-for="(value, key) in stats" :key="key">
            <div class="card text-center shadow stat-card">
              <div class="card-body">
                <h6 class="card-title text-uppercase text-secondary small">{{ statTitles[key] }}</h6>
                <h2 class="mb-0 text-primary">{{ value }}</h2>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Departments Management Section -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
        <span>🏢 Hospital Departments/Specializations</span>
        <button class="btn btn-light btn-sm" @click="openAddDepartmentModal">+ Add Department</button>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-3" v-for="dept in activeDepartments" :key="dept.id">
            <div class="card mb-3 border-success shadow">
              <div class="card-body border border-primary rounded">
                <h6 class="card-title">{{ dept.name }}</h6>
                <p class="card-text small text-muted">{{ dept.description || 'No description' }}</p>
                <button class="btn btn-sm btn-outline-primary me-1" @click="editDepartment(dept)">Edit</button>
                <button class="btn btn-sm btn-outline-danger" @click="softDeleteDepartment(dept)">Delete</button>
              </div>
            </div>
          </div>
          <div v-if="activeDepartments.length === 0" class="col-12 text-center text-muted py-5">
            <p>No departments added yet</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Doctors Table with Search -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <span>👨‍⚕️ Registered Doctors</span>
        <div class="d-flex gap-2">
          <input 
            type="text" 
            v-model="doctorSearchQuery" 
            class="form-control form-control-sm search-input" 
            placeholder="Search doctors..."
          >
          <button class="btn btn-light btn-sm" @click="openAddDoctorModal">Add Doctor</button>
        </div>
      </div>
      <div class="card-body p-0">
        <div class="table-scroll-container">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Department</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredDoctors.length === 0">
                <td colspan="7" class="text-center text-muted py-3">No doctors found</td>
              </tr>
              <tr v-for="doc in filteredDoctors" :key="doc.id">
                <td>{{ doc.id }}</td>
                <td>{{ doc.full_name }}</td>
                <td><span class="badge bg-info">{{ doc.specialization || 'N/A' }}</span></td>
                <td>{{ doc.email }}</td>
                <td>{{ doc.phone }}</td>
                <td>
                  <button 
                    class="btn btn-sm" 
                    :class="doc.is_active ? 'btn-success' : 'btn-danger'"
                    @click="toggleDoctorStatus(doc)"
                  >
                    {{ doc.is_active ? '✓' : '🚫' }}
                  </button>
                </td>
                <td>
                  <button class="btn btn-primary btn-sm me-1" @click="viewDoctor(doc)" title="View">👁️</button>
                  <button class="btn btn-warning btn-sm me-1" @click="manageDoctorAvailability(doc)" title="Availability">📅</button>
                  <button class="btn btn-danger btn-sm" @click="softDeleteDoctor(doc)" title="Delete">🗑️</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Patients Table with Search -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
        <span>🧑‍🤝‍🧑 Registered Patients</span>
        <input 
          type="text" 
          v-model="patientSearchQuery" 
          class="form-control form-control-sm search-input" 
          placeholder="Search patients..."
        >
      </div>
      <div class="card-body p-0">
        <div class="table-scroll-container">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredPatients.length === 0">
                <td colspan="6" class="text-center text-muted py-3">No patients found</td>
              </tr>
              <tr v-for="pat in filteredPatients" :key="pat.id">
                <td>{{ pat.id }}</td>
                <td>{{ pat.full_name }}</td>
                <td>{{ pat.email }}</td>
                <td>{{ pat.phone }}</td>
                <td>
                  <span class="badge" :class="pat.is_active ? 'bg-success' : 'bg-secondary'">
                    {{ pat.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>
                  <button class="btn btn-primary btn-sm me-1" @click="viewPatient(pat)" title="View">👁️</button>
                  <button 
                    class="btn btn-sm me-1" 
                    :class="pat.is_active ? 'btn-success' : 'btn-danger'"
                    @click="togglePatientStatus(pat)"
                    :title="pat.is_active ? 'Deactivate' : 'Activate'"
                  >
                    {{ pat.is_active ? '✓' : '🚫' }}
                  </button>
                  <button class="btn btn-danger btn-sm" @click="softDeletePatient(pat)" title="Delete">🗑️</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add Department Modal -->
    <div v-if="showDepartmentModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog">
        <form class="modal-content" @submit.prevent="submitDepartment">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">{{ departmentForm.id ? 'Edit' : 'Add' }} Department</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeDepartmentModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Department Name *</label>
              <input 
                v-model="departmentForm.name" 
                required 
                class="form-control" 
                placeholder="e.g., Cardiology, Orthopedics"
              >
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea 
                v-model="departmentForm.description" 
                class="form-control" 
                rows="3" 
                placeholder="Brief description"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-success">
              {{ departmentForm.id ? 'Update' : 'Add' }}
            </button>
            <button type="button" class="btn btn-secondary" @click="closeDepartmentModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add Doctor Modal -->
    <div v-if="showDoctorModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <form class="modal-content" @submit.prevent="submitDoctor">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">Add New Doctor</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeDoctorModal"></button>
          </div>
          <div class="modal-body">
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Full Name *</label>
                <input v-model="doctorForm.full_name" required class="form-control">
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Department *</label>
                <select v-model="doctorForm.department_id" class="form-select" required>
                  <option value="">Select Department</option>
                  <option v-for="dept in activeDepartments" :key="dept.id" :value="dept.id">
                    {{ dept.name }}
                  </option>
                </select>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Username *</label>
                <input v-model="doctorForm.username" required class="form-control">
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Email *</label>
                <input v-model="doctorForm.email" type="email" required class="form-control">
              </div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Phone *</label>
                <input v-model="doctorForm.phone" required class="form-control">
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Password *</label>
                <input v-model="doctorForm.password" type="password" required class="form-control">
              </div>
            </div>
            <div class="row">
              <div class="col-md-4 mb-3">
                <label class="form-label">Qualification</label>
                <input v-model="doctorForm.qualification" class="form-control">
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Experience</label>
                <input v-model.number="doctorForm.experience_years" type="number" class="form-control">
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Fee (₹)</label>
                <input v-model.number="doctorForm.consultation_fee" type="number" class="form-control">
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-success">Add Doctor</button>
            <button type="button" class="btn btn-secondary" @click="closeDoctorModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- View/Edit Doctor Modal -->
    <div v-if="showDoctorViewModal" class="modal show" style="display:block;" tabindex="-1">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">
              {{ doctorViewMode === 'view' ? '👁️ Doctor Details' : '✏️ Edit Doctor' }}
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeDoctorViewModal"></button>
          </div>
          <form @submit.prevent="submitDoctorFromView">
            <div class="modal-body">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Full Name</label>
                  <input v-model="viewedDoctor.full_name" class="form-control" :readonly="doctorViewMode === 'view'">
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Username</label>
                  <input v-model="viewedDoctor.username" class="form-control" :readonly="doctorViewMode === 'view'">
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Email</label>
                  <input v-model="viewedDoctor.email" type="email" class="form-control" :readonly="doctorViewMode === 'view'">
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Phone</label>
                  <input v-model="viewedDoctor.phone" class="form-control" :readonly="doctorViewMode === 'view'">
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Department</label>
                  <select v-model="viewedDoctor.department_id" class="form-select" :disabled="doctorViewMode === 'view'">
                    <option v-for="dept in activeDepartments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                  </select>
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Qualification</label>
                  <input v-model="viewedDoctor.qualification" class="form-control" :readonly="doctorViewMode === 'view'">
                </div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label fw-bold">Experience (years)</label>
                  <input v-model.number="viewedDoctor.experience_years" type="number" class="form-control" :readonly="doctorViewMode === 'view'">
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label fw-bold">Consultation Fee (₹)</label>
                  <input v-model.number="viewedDoctor.consultation_fee" type="number" class="form-control" :readonly="doctorViewMode === 'view'">
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label fw-bold">Status</label>
                  <select v-model="viewedDoctor.is_active" class="form-select" :disabled="doctorViewMode === 'view'">
                    <option :value="true">Active</option>
                    <option :value="false">Inactive</option>
                  </select>
                </div>
              </div>
              <div v-if="doctorViewMode === 'edit'" class="row">
                <div class="col-md-12 mb-3">
                  <label class="form-label fw-bold">New Password (leave empty to keep current)</label>
                  <input v-model="viewedDoctor.password" type="password" class="form-control" placeholder="Enter new password">
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button v-if="doctorViewMode === 'view'" type="button" class="btn btn-warning" @dblclick="switchToEditMode('doctor')">
                ✏️ Double-click to Edit
              </button>
              <button v-if="doctorViewMode === 'edit'" type="submit" class="btn btn-success">
                💾 Save Changes
              </button>
              <button type="button" class="btn btn-secondary" @click="closeDoctorViewModal">Close</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- View/Edit Patient Modal -->
    <div v-if="showPatientViewModal" class="modal show" style="display:block;" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-secondary text-white">
            <h5 class="modal-title">
              {{ patientViewMode === 'view' ? '👁️ Patient Details' : '✏️ Edit Patient' }}
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closePatientViewModal"></button>
          </div>
          <form @submit.prevent="submitPatientFromView">
            <div class="modal-body">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Full Name</label>
                  <input v-model="viewedPatient.full_name" class="form-control" :readonly="patientViewMode === 'view'">
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Username</label>
                  <input v-model="viewedPatient.username" class="form-control" :readonly="patientViewMode === 'view'">
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Email</label>
                  <input v-model="viewedPatient.email" type="email" class="form-control" :readonly="patientViewMode === 'view'">
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Phone</label>
                  <input v-model="viewedPatient.phone" class="form-control" :readonly="patientViewMode === 'view'">
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Status</label>
                  <select v-model="viewedPatient.is_active" class="form-select" :disabled="patientViewMode === 'view'">
                    <option :value="true">Active</option>
                    <option :value="false">Inactive</option>
                  </select>
                </div>
                <div class="col-md-6 mb-3" v-if="patientViewMode === 'edit'">
                  <label class="form-label fw-bold">New Password (optional)</label>
                  <input v-model="viewedPatient.password" type="password" class="form-control" placeholder="Enter new password">
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button v-if="patientViewMode === 'view'" type="button" class="btn btn-warning" @dblclick="switchToEditMode('patient')">
                ✏️ Double-click to Edit
              </button>
              <button v-if="patientViewMode === 'edit'" type="submit" class="btn btn-success">
                💾 Save Changes
              </button>
              <button type="button" class="btn btn-secondary" @click="closePatientViewModal">Close</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Recent Appointments with Filter -->
    <div class="card shadow mb-4">
      <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
        <span>📅 All Appointments</span>
        <select v-model="appointmentStatusFilter" class="form-select form-select-sm" style="max-width: 150px;">
          <option value="">All Status</option>
          <option value="booked">Booked</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
      <div class="card-body p-0">
        <div class="table-scroll-container" style="max-height: 500px;">
          <table class="table table-bordered align-middle mb-0">
            <thead class="table-light sticky-top">
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Time</th>
                <th>Doctor</th>
                <th>Patient</th>
                <th>Status</th>
                <!-- Remove Actions column header -->
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredAppointments.length === 0">
                <td colspan="6" class="text-center text-muted py-3">No appointments found</td>
              </tr>
              <tr v-for="apt in filteredAppointments" :key="apt.id">
                <td>
                  <!-- Make ID clickable with a link -->
                  <a 
                    href="#" 
                    @click.prevent="editAppointment(apt)" 
                    class="appointment-id-link"
                    title="Click to edit appointment"
                  >
                    {{ apt.id }}
                  </a>
                </td>
                <td>{{ apt.appointment_date }}</td>
                <td>{{ apt.appointment_time }}</td>
                <td>{{ apt.doctor_name }}</td>
                <td>{{ apt.patient_name }}</td>
                <td>
                  <span 
                    class="badge" 
                    :class="{
                      'bg-warning text-dark': apt.status === 'booked',
                      'bg-success': apt.status === 'completed',
                      'bg-danger': apt.status === 'cancelled'
                    }"
                  >
                    {{ apt.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Doctor Availability Management Modal -->
    <div v-if="showAvailabilityModal" class="modal show" style="display:block;" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-warning">
            <h5 class="modal-title">📅 Manage Availability - Dr. {{ selectedDoctorForAvailability?.full_name }}</h5>
            <button type="button" class="btn-close" @click="closeAvailabilityModal"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted">Set availability for the next 7 days</p>
            <div class="row">
              <div class="col-md-6 mb-3" v-for="day in next7Days" :key="day.date">
                <div class="card">
                  <div class="card-body">
                    <h6>{{ day.dayName }} - {{ day.date }}</h6>
                    <div class="row">
                      <div class="col-6">
                        <label class="form-label small">Start</label>
                        <input type="time" v-model="availabilityData[day.date].start_time" class="form-control form-control-sm">
                      </div>
                      <div class="col-6">
                        <label class="form-label small">End</label>
                        <input type="time" v-model="availabilityData[day.date].end_time" class="form-control form-control-sm">
                      </div>
                    </div>
                    <div class="form-check mt-2">
                      <input type="checkbox" v-model="availabilityData[day.date].is_available" class="form-check-input">
                      <label class="form-check-label small">Available</label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-success" @click="saveAvailability">Save Availability</button>
            <button type="button" class="btn btn-secondary" @click="closeAvailabilityModal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Appointment Modal -->
    <div v-if="showAppointmentEditModal" class="modal show" style="display:block;" tabindex="-1">
      <div class="modal-dialog">
        <form class="modal-content" @submit.prevent="submitAppointmentEdit">
          <div class="modal-header bg-info text-white">
            <h5 class="modal-title">✏️ Edit Appointment #{{ editedAppointment.id }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeAppointmentEditModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Date</label>
              <input v-model="editedAppointment.appointment_date" type="date" class="form-control">
            </div>
            <div class="mb-3">
              <label class="form-label">Time</label>
              <input v-model="editedAppointment.appointment_time" type="time" class="form-control">
            </div>
            <div class="mb-3">
              <label class="form-label">Status</label>
              <select v-model="editedAppointment.status" class="form-select">
                <option value="booked">Booked</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">Reason</label>
              <textarea v-model="editedAppointment.reason" class="form-control" rows="2"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-success">Save Changes</button>
            <button type="button" class="btn btn-secondary" @click="closeAppointmentEditModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- DELETED ITEMS Section (Hidden by default) -->
    <div v-if="showDeletedItems" class="card deleted-section shadow mb-4">
      <div class="card-header bg-danger text-white">
        <h5 class="mb-0">🗑️ Deleted Items</h5>
      </div>
      <div class="card-body">
        <!-- Deleted Departments -->
        <div v-if="deletedDepartments.length > 0" class="mb-4">
          <h6 class="text-danger">Deleted Departments</h6>
          <div class="row">
            <div class="col-md-3" v-for="dept in deletedDepartments" :key="dept.id">
              <div class="card mb-2 border-danger">
                <div class="card-body py-2">
                  <small class="text-muted d-block">{{ dept.name }}</small>
                  <button class="btn btn-sm btn-outline-success me-1" @click="restoreDepartment(dept)">↺ Restore</button>
                  <button class="btn btn-sm btn-outline-danger" @click="permanentDeleteDepartment(dept)">❌ Delete</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Deleted Doctors -->
        <div v-if="deletedDoctors.length > 0" class="mb-4">
          <h6 class="text-danger">Deleted Doctors</h6>
          <table class="table table-sm">
            <thead>
              <tr><th>Name</th><th>Department</th><th>Actions</th></tr>
            </thead>
            <tbody>
              <tr v-for="doc in deletedDoctors" :key="doc.id">
                <td>{{ doc.full_name }}</td>
                <td>{{ doc.specialization }}</td>
                <td>
                  <button class="btn btn-sm btn-outline-success me-1" @click="restoreDoctor(doc)">↺ Restore</button>
                  <button class="btn btn-sm btn-outline-danger" @click="permanentDeleteDoctor(doc)">❌ Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Deleted Patients -->
        <div v-if="deletedPatients.length > 0" class="mb-4">
          <h6 class="text-danger">Deleted Patients</h6>
          <table class="table table-sm">
            <thead>
              <tr><th>Name</th><th>Email</th><th>Actions</th></tr>
            </thead>
            <tbody>
              <tr v-for="pat in deletedPatients" :key="pat.id">
                <td>{{ pat.full_name }}</td>
                <td>{{ pat.email }}</td>
                <td>
                  <button class="btn btn-sm btn-outline-success me-1" @click="restorePatient(pat)">↺ Restore</button>
                  <button class="btn btn-sm btn-outline-danger" @click="permanentDeletePatient(pat)">❌ Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="deletedDepartments.length === 0 && deletedDoctors.length === 0 && deletedPatients.length === 0" 
          class="text-center text-muted py-3">
          No deleted items
        </div>
      </div>
    </div>

    <!-- Toggle Deleted Items Button at Bottom -->
    <div class="text-center mb-4">
      <button class="btn btn-outline-danger" @click="showDeletedItems = !showDeletedItems">
        🗑️ {{ showDeletedItems ? 'Hide' : 'Show' }} Deleted Items
      </button>
    </div>

    <!-- Modal Backdrop -->
    <div 
      v-if="showDoctorModal || showPatientViewModal || showDepartmentModal || showDoctorViewModal || showAppointmentEditModal || showAvailabilityModal"
      class="modal-backdrop fade show"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import apiClient from '@/utils/api'

const router = useRouter()
const userStore = useUserStore()

// Data
const stats = ref({})
const statTitles = {
  total_doctors: "Doctors",
  total_patients: "Patients",
  total_appointments: "Appointments",
  booked_appointments: "Booked",
  completed_appointments: "Completed",
  cancelled_appointments: "Cancelled"
}

const doctors = ref([])
const patients = ref([])
const appointments = ref([])
const departments = ref([])

// Search & Filter
const doctorSearchQuery = ref('')
const patientSearchQuery = ref('')
const appointmentStatusFilter = ref('')

// Modals
const showDepartmentModal = ref(false)
const showDoctorModal = ref(false)

// Forms
const departmentForm = ref({
  id: null,
  name: '',
  description: ''
})

const doctorForm = ref({
  id: null,
  username: '',
  full_name: '',
  department_id: '',
  email: '',
  phone: '',
  password: '',
  qualification: '',
  experience_years: 0,
  consultation_fee: 0
})

// Computed Properties
const activeDepartments = computed(() => {
  return departments.value.filter(d => !d.name?.startsWith('[DELETED]'))
})

const activeDoctors = computed(() => {
  return doctors.value.filter(d => !d.full_name?.startsWith('[DELETED]'))
})

const activePatients = computed(() => {
  return patients.value.filter(p => !p.full_name?.startsWith('[DELETED]'))
})

const filteredDoctors = computed(() => {
  if (!doctorSearchQuery.value) return activeDoctors.value
  
  const query = doctorSearchQuery.value.toLowerCase()
  return activeDoctors.value.filter(doc => 
    doc.full_name?.toLowerCase().includes(query) ||
    doc.email?.toLowerCase().includes(query) ||
    doc.phone?.includes(query) ||
    doc.specialization?.toLowerCase().includes(query)
  )
})

const filteredPatients = computed(() => {
  if (!patientSearchQuery.value) return activePatients.value
  
  const query = patientSearchQuery.value.toLowerCase()
  return activePatients.value.filter(pat => 
    pat.full_name?.toLowerCase().includes(query) ||
    pat.email?.toLowerCase().includes(query) ||
    pat.phone?.includes(query)
  )
})

// Methods
const fetchDashboard = async () => {
  try {
    const response = await apiClient.get('/api/admin/dashboard')
    stats.value = response.data.statistics
    appointments.value = response.data.recent_appointments || []
  } catch (error) {
    console.error('Error fetching dashboard:', error)
    alert('Failed to load dashboard')
  }
}

const fetchDoctors = async () => {
  try {
    const response = await apiClient.get('/api/admin/doctors')
    doctors.value = response.data.doctors || []
  } catch (error) {
    console.error('Error fetching doctors:', error)
  }
}

const fetchPatients = async () => {
  try {
    const response = await apiClient.get('/api/admin/patients')
    patients.value = response.data.patients || []
  } catch (error) {
    console.error('Error fetching patients:', error)
  }
}

const fetchDepartments = async () => {
  try {
    const response = await apiClient.get('/api/admin/departments')
    departments.value = response.data.departments || []
  } catch (error) {
    console.error('Error fetching departments:', error)
  }
}

// Department Management
const openAddDepartmentModal = () => {
  departmentForm.value = { id: null, name: '', description: '' }
  showDepartmentModal.value = true
}

const editDepartment = (dept) => {
  departmentForm.value = { ...dept }
  showDepartmentModal.value = true
}

const closeDepartmentModal = () => {
  showDepartmentModal.value = false
  departmentForm.value = { id: null, name: '', description: '' }
}

const submitDepartment = async () => {
  const isEdit = !!departmentForm.value.id
  const url = isEdit 
    ? `/api/admin/departments/${departmentForm.value.id}`
    : '/api/admin/departments'
  const method = isEdit ? 'put' : 'post'
  
  try {
    await apiClient[method](url, departmentForm.value)
    alert(isEdit ? 'Department updated!' : 'Department added!')
    await fetchDepartments()
    closeDepartmentModal()
  } catch (error) {
    alert(error.response?.data?.error || 'Operation failed')
  }
}

const softDeleteDepartment = async (dept) => {
  if (!confirm(`Delete ${dept.name}?`)) return
  
  try {
    await apiClient.put(`/api/admin/departments/${dept.id}`, {
      name: `[DELETED] ${dept.name}`,
      description: dept.description
    })
    alert('Department moved to deleted items')
    await fetchDepartments()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to delete')
  }
}

// Doctor Management
const openAddDoctorModal = () => {
  if (activeDepartments.value.length === 0) {
    alert('Please add at least one department first!')
    return
  }
  doctorForm.value = {
    id: null,
    username: '',
    full_name: '',
    department_id: '',
    email: '',
    phone: '',
    password: '',
    qualification: '',
    experience_years: 0,
    consultation_fee: 0
  }
  showDoctorModal.value = true
}

const closeDoctorModal = () => {
  showDoctorModal.value = false
}

const submitDoctor = async () => {
  try {
    await apiClient.post('/api/admin/doctors', {
      username: doctorForm.value.username,
      full_name: doctorForm.value.full_name,
      specialization_id: doctorForm.value.department_id,
      email: doctorForm.value.email,
      phone: doctorForm.value.phone,
      password: doctorForm.value.password,
      qualification: doctorForm.value.qualification,
      experience_years: doctorForm.value.experience_years,
      consultation_fee: doctorForm.value.consultation_fee
    })
    alert('Doctor added successfully!')
    await fetchDoctors()
    closeDoctorModal()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to add doctor')
  }
}

const showDoctorViewModal = ref(false)
const viewedDoctor = ref({})
const doctorViewMode = ref('view') // 'view' or 'edit'

const viewDoctor = async (doc) => {
  try {
    const response = await apiClient.get(`/api/admin/doctors/${doc.id}`)
    viewedDoctor.value = {
      ...response.data,
      department_id: response.data.specialization_id,
      password: '' // empty for security
    }
    doctorViewMode.value = 'view'
    showDoctorViewModal.value = true
  } catch (error) {
    alert('Failed to load doctor details')
  }
}

const closeDoctorViewModal = () => {
  showDoctorViewModal.value = false
  viewedDoctor.value = {}
}

const switchToEditMode = (type) => {
  if (type === 'doctor') {
    doctorViewMode.value = 'edit'
  } else if (type === 'patient') {
    patientViewMode.value = 'edit'
  }
}

const submitDoctorFromView = async () => {
  try {
    const payload = {
      full_name: viewedDoctor.value.full_name,
      username: viewedDoctor.value.username,
      email: viewedDoctor.value.email,
      phone: viewedDoctor.value.phone,
      specialization_id: viewedDoctor.value.department_id,
      qualification: viewedDoctor.value.qualification,
      experience_years: viewedDoctor.value.experience_years,
      consultation_fee: viewedDoctor.value.consultation_fee,
      is_active: viewedDoctor.value.is_active
    }
    
    if (viewedDoctor.value.password) {
      payload.password = viewedDoctor.value.password
    }
    
    await apiClient.put(`/api/admin/doctors/${viewedDoctor.value.id}`, payload)
    alert('Doctor updated successfully!')
    await fetchDoctors()
    closeDoctorViewModal()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to update doctor')
  }
}

const showAvailabilityModal = ref(false)
const selectedDoctorForAvailability = ref(null)
const availabilityData = ref({})

const next7Days = computed(() => {
  const days = []
  const today = new Date()
  for (let i = 0; i < 7; i++) {
    const date = new Date(today)
    date.setDate(today.getDate() + i)
    const dateStr = date.toISOString().split('T')[0]
    days.push({
      date: dateStr,
      dayName: date.toLocaleDateString('en-US', { weekday: 'short' })
    })
  }
  return days
})

const manageDoctorAvailability = async (doc) => {
  selectedDoctorForAvailability.value = doc
  
  // Initialize availability data for next 7 days
  availabilityData.value = {}
  next7Days.value.forEach(day => {
    availabilityData.value[day.date] = {
      start_time: '09:00',
      end_time: '17:00',
      is_available: true
    }
  })
  
  // Fetch existing availability
  try {
    const response = await apiClient.get(`/api/admin/doctors/${doc.id}/availability`)
    if (response.data.availability) {
      response.data.availability.forEach(avail => {
        if (availabilityData.value[avail.date]) {
          availabilityData.value[avail.date] = {
            start_time: avail.start_time,
            end_time: avail.end_time,
            is_available: avail.is_available
          }
        }
      })
    }
  } catch (error) {
    console.error('Failed to fetch availability')
  }
  
  showAvailabilityModal.value = true
}

const closeAvailabilityModal = () => {
  showAvailabilityModal.value = false
  selectedDoctorForAvailability.value = null
}

const saveAvailability = async () => {
  if (!selectedDoctorForAvailability.value) return
  
  try {
    const promises = Object.entries(availabilityData.value).map(([date, data]) => {
      return apiClient.post(`/api/admin/doctors/${selectedDoctorForAvailability.value.id}/availability`, {
        date,
        start_time: data.start_time,
        end_time: data.end_time,
        is_available: data.is_available
      })
    })
    
    await Promise.all(promises)
    alert('Availability updated successfully!')
    closeAvailabilityModal()
  } catch (error) {
    alert('Failed to save availability')
  }
}

const toggleDoctorStatus = async (doc) => {
  const newStatus = !doc.is_active
  const action = newStatus ? 'activate' : 'deactivate'
  
  if (!confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} ${doc.full_name}?`)) return
  
  try {
    await apiClient.put(`/api/admin/doctors/${doc.id}`, {
      ...doc,
      specialization_id: doc.department_id || doc.specialization_id,
      is_active: newStatus
    })
    alert(`Doctor ${action}d successfully!`)
    await fetchDoctors()
  } catch (error) {
    alert('Failed to update status')
  }
}

const softDeleteDoctor = async (doc) => {
  if (!confirm(`Delete Dr. ${doc.full_name}?`)) return
  
  try {
    await apiClient.put(`/api/admin/doctors/${doc.id}`, {
      ...doc,
      full_name: `[DELETED] ${doc.full_name}`,
      specialization_id: doc.department_id || doc.specialization_id,
      is_active: false
    })
    alert('Doctor moved to deleted items')
    await fetchDoctors()
  } catch (error) {
    alert('Failed to delete doctor')
  }
}

// Patient Management
const showPatientViewModal = ref(false)
const viewedPatient = ref({})
const patientViewMode = ref('view')

const viewPatient = async (pat) => {
  try {
    const response = await apiClient.get(`/api/admin/patients/${pat.id}`)
    viewedPatient.value = {
      ...response.data,
      password: ''
    }
    patientViewMode.value = 'view'
    showPatientViewModal.value = true
  } catch (error) {
    alert('Failed to load patient details')
  }
}

const closePatientViewModal = () => {
  showPatientViewModal.value = false
  viewedPatient.value = {}
}

const submitPatientFromView = async () => {
  try {
    const payload = {
      full_name: viewedPatient.value.full_name,
      username: viewedPatient.value.username,
      email: viewedPatient.value.email,
      phone: viewedPatient.value.phone,
      is_active: viewedPatient.value.is_active
    }
    
    if (viewedPatient.value.password) {
      payload.password = viewedPatient.value.password
    }
    
    await apiClient.put(`/api/admin/patients/${viewedPatient.value.id}`, payload)
    alert('Patient updated successfully!')
    await fetchPatients()
    closePatientViewModal()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to update patient')
  }
}

const togglePatientStatus = async (pat) => {
  const newStatus = !pat.is_active
  const action = newStatus ? 'activate' : 'deactivate'
  
  if (!confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} ${pat.full_name}?`)) return
  
  try {
    await apiClient.put(`/api/admin/patients/${pat.id}`, {
      ...pat,
      is_active: newStatus
    })
    alert(`Patient ${action}d successfully!`)
    await fetchPatients()
  } catch (error) {
    alert('Failed to update status')
  }
}

const softDeletePatient = async (pat) => {
  if (!confirm(`Delete ${pat.full_name}?`)) return
  
  try {
    await apiClient.put(`/api/admin/patients/${pat.id}`, {
      ...pat,
      full_name: `[DELETED] ${pat.full_name}`,
      is_active: false
    })
    alert('Patient moved to deleted items')
    await fetchPatients()
  } catch (error) {
    alert('Failed to delete patient')
  }
}

const showDeletedItems = ref(false)

const deletedDepartments = computed(() => {
  return departments.value.filter(d => d.name?.startsWith('[DELETED]'))
})

const deletedDoctors = computed(() => {
  return doctors.value.filter(d => d.full_name?.startsWith('[DELETED]'))
})

const deletedPatients = computed(() => {
  return patients.value.filter(p => p.full_name?.startsWith('[DELETED]'))
})

// Restore methods
const restoreDepartment = async (dept) => {
  if (!confirm(`Restore ${dept.name}?`)) return
  
  try {
    const originalName = dept.name.replace('[DELETED] ', '')
    await apiClient.put(`/api/admin/departments/${dept.id}`, {
      name: originalName,
      description: dept.description
    })
    alert('Department restored!')
    await fetchDepartments()
  } catch (error) {
    alert('Failed to restore department')
  }
}

const restoreDoctor = async (doc) => {
  if (!confirm(`Restore ${doc.full_name}?`)) return
  
  try {
    const originalName = doc.full_name.replace('[DELETED] ', '')
    await apiClient.put(`/api/admin/doctors/${doc.id}`, {
      ...doc,
      full_name: originalName,
      specialization_id: doc.department_id || doc.specialization_id,
      is_active: true
    })
    alert('Doctor restored!')
    await fetchDoctors()
  } catch (error) {
    alert('Failed to restore doctor')
  }
}

const restorePatient = async (pat) => {
  if (!confirm(`Restore ${pat.full_name}?`)) return
  
  try {
    const originalName = pat.full_name.replace('[DELETED] ', '')
    await apiClient.put(`/api/admin/patients/${pat.id}`, {
      ...pat,
      full_name: originalName,
      is_active: true
    })
    alert('Patient restored!')
    await fetchPatients()
  } catch (error) {
    alert('Failed to restore patient')
  }
}

// Permanent delete methods
const permanentDeleteDepartment = async (dept) => {
  if (!confirm(`PERMANENTLY delete ${dept.name}? This cannot be undone!`)) return
  
  try {
    await apiClient.delete(`/api/admin/departments/${dept.id}/permanent`)
    alert('Department permanently deleted!')
    await fetchDepartments()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to delete')
  }
}

const permanentDeleteDoctor = async (doc) => {
  if (!confirm(`PERMANENTLY delete ${doc.full_name}? This cannot be undone!`)) return
  
  try {
    await apiClient.delete(`/api/admin/doctors/${doc.id}/permanent`)
    alert('Doctor permanently deleted!')
    await fetchDoctors()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to delete')
  }
}

const permanentDeletePatient = async (pat) => {
  if (!confirm(`PERMANENTLY delete ${pat.full_name}? This cannot be undone!`)) return
  
  try {
    await apiClient.delete(`/api/admin/patients/${pat.id}/permanent`)
    alert('Patient permanently deleted!')
    await fetchPatients()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to delete')
  }
}

const logout = () => {
  userStore.logout()
  router.push('/login')
}

// Add a new ref for all appointments
const allAppointments = ref([])

// Update the filteredAppointments computed property
const filteredAppointments = computed(() => {
  if (!appointmentStatusFilter.value) return allAppointments.value
  return allAppointments.value.filter(apt => apt.status === appointmentStatusFilter.value)
})

// Add a new method to fetch all appointments
const fetchAllAppointments = async () => {
  try {
    const response = await apiClient.get('/api/admin/appointments')
    allAppointments.value = response.data.appointments || []
  } catch (error) {
    console.error('Error fetching appointments:', error)
  }
}

// Update the onMounted hook
onMounted(() => {
  fetchDepartments()
  fetchDashboard()
  fetchDoctors()
  fetchPatients()
  fetchAllAppointments()  
})

// Add these new refs for appointment editing
const showAppointmentEditModal = ref(false)
const editedAppointment = ref({})

// Add this method to open the edit modal (call this when user clicks edit button)
const editAppointment = (apt) => {
  editedAppointment.value = { ...apt }
  showAppointmentEditModal.value = true
}

// Add this method to close the modal
const closeAppointmentEditModal = () => {
  showAppointmentEditModal.value = false
  editedAppointment.value = {}
}

// Add this method to submit the edited appointment
const submitAppointmentEdit = async () => {
  try {
    await apiClient.put(`/api/admin/appointments/${editedAppointment.value.id}`, {
      appointment_date: editedAppointment.value.appointment_date,
      appointment_time: editedAppointment.value.appointment_time,
      status: editedAppointment.value.status,
      reason: editedAppointment.value.reason
    })
    alert('Appointment updated successfully!')
    await fetchAllAppointments()
    await fetchDashboard()
    closeAppointmentEditModal()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to update appointment')
  }
}
</script>

<style scoped>
.navbar-orange {
  background: linear-gradient(90deg, #ff9800 0%, #ffa726 100%);
  color: #fff;
}

.stat-card {
  border-left: 4px solid #28a745;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-left-width: 8px;
}

.table-scroll-container {
  max-height: 450px;
  overflow-y: auto;
  overflow-x: auto;
}

.search-input {
  max-width: 250px;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

.table-scroll-container {
  max-height: 450px;
  overflow-y: auto;
  overflow-x: auto;
}

/* Make table header sticky when scrolling */
.sticky-top {
  position: sticky;
  top: 0;
  background-color: #f8f9fa;
  z-index: 10;
}

/* Add scrollbar styling for better UX */
.table-scroll-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-scroll-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.table-scroll-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.table-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Style for clickable appointment ID */
.appointment-id-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.appointment-id-link:hover {
  color: #0056b3;
  text-decoration: underline;
  transform: scale(1.05);
}

.appointment-id-link:active {
  color: #004085;
}
</style>