<template>
  <div class="container-fluid py-4">
    <!-- Navbar -->
    <nav class="navbar navbar-violet mb-3 rounded shadow-sm sticky-top">
      <span class="navbar-brand fw-bold">
        <i class="bi bi-person-badge me-2"></i>
        Welcome Dr. {{ doctor.full_name }}
      </span>
      <span class="navbar-text mx-auto">
        <span class="badge bg-light text-dark fs-6">
          <i class="bi bi-hospital me-1"></i>
          {{ doctor.specialization || 'General Medicine' }}
        </span>
      </span>
      <button class="btn btn-outline-light" @click="logout">
        <i class="bi bi-box-arrow-right me-1"></i>
        Logout
      </button>
    </nav>

    <!-- Stats Cards -->
    <div class="row mb-4">
      <div class="col-md-3">
        <div class="card text-center shadow stat-card">
          <div class="card-body">
            <i class="bi bi-calendar-check text-primary" style="font-size: 2rem;"></i>
            <h3 class="mt-2 mb-0 text-primary">{{ appointments.length }}</h3>
            <p class="text-muted mb-0">Upcoming</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card text-center shadow stat-card">
          <div class="card-body">
            <i class="bi bi-people text-info" style="font-size: 2rem;"></i>
            <h3 class="mt-2 mb-0 text-info">{{ patients.length }}</h3>
            <p class="text-muted mb-0">Patients</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card text-center shadow stat-card">
          <div class="card-body">
            <i class="bi bi-check-circle text-success" style="font-size: 2rem;"></i>
            <h3 class="mt-2 mb-0 text-success">{{ completedToday }}</h3>
            <p class="text-muted mb-0">Completed Today</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card text-center shadow stat-card">
          <div class="card-body">
            <i class="bi bi-clock text-warning" style="font-size: 2rem;"></i>
            <h3 class="mt-2 mb-0 text-warning">{{ pendingCount }}</h3>
            <p class="text-muted mb-0">Pending</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Upcoming Appointments -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <span>
          <i class="bi bi-calendar-event me-2"></i>
          Upcoming Appointments
        </span>
        <span class="badge bg-light text-dark">{{ appointments.length }} appointments</span>
      </div>
      <div class="card-body">
        <div class="table-scroll-container">
          <table class="table table-hover">
            <thead class="table-light">
              <tr>
                <th><i class="bi bi-calendar3 me-1"></i>Date</th>
                <th><i class="bi bi-clock me-1"></i>Time</th>
                <th><i class="bi bi-person me-1"></i>Patient</th>
                <th><i class="bi bi-chat-left-text me-1"></i>Reason</th>
                <th><i class="bi bi-gear me-1"></i>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="appointments.length === 0">
                <td colspan="5" class="text-center text-muted py-4">
                  <i class="bi bi-calendar-x" style="font-size: 3rem; opacity: 0.3;"></i>
                  <p class="mt-2 mb-0">No upcoming appointments</p>
                </td>
              </tr>
              <tr v-for="apt in appointments" :key="apt.id">
                <td>
                  <strong>{{ formatDate(apt.appointment_date) }}</strong>
                </td>
                <td>
                  <span class="badge bg-info">{{ apt.appointment_time }}</span>
                </td>
                <td>
                  <i class="bi bi-person-circle me-1"></i>
                  {{ apt.patient_name }}
                </td>
                <td>{{ apt.reason || 'General consultation' }}</td>
                <td>
                  <button 
                    class="btn btn-success btn-sm me-1" 
                    @click="completeAppointment(apt)"
                    title="Complete & Add Treatment"
                  >
                    <i class="bi bi-check-circle me-1"></i>
                    Complete
                  </button>
                  <button 
                    class="btn btn-danger btn-sm" 
                    @click="cancelAppointment(apt)"
                    title="Cancel Appointment"
                  >
                    <i class="bi bi-x-circle"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Availability Schedule -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-warning text-dark d-flex justify-content-between align-items-center">
        <span>
          <i class="bi bi-calendar-week me-2"></i>
          Availability Schedule
        </span>
        <button class="btn btn-sm btn-primary" @click="openBulkAvailabilityModal">
          <i class="bi bi-calendar-plus me-1"></i>
          Set 7-Day Availability
        </button>
      </div>
      <div class="card-body">
        <div class="table-scroll-container">
          <table class="table table-striped table-hover">
            <thead class="table-light">
              <tr>
                <th>Date</th>
                <th>Day</th>
                <th>Time Slot</th>
                <th>Lunch Break</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="availability.length === 0">
                <td colspan="6" class="text-center text-muted py-4">
                  <i class="bi bi-calendar-x" style="font-size: 3rem; opacity: 0.3;"></i>
                  <p class="mt-2 mb-0">No availability set. Click "Set 7-Day Availability" to configure your schedule.</p>
                </td>
              </tr>
              <tr v-for="avail in availability" :key="avail.id">
                <td><strong>{{ avail.date }}</strong></td>
                <td>
                  <span class="badge bg-secondary">{{ getDayName(avail.date) }}</span>
                </td>
                <td>
                  <i class="bi bi-clock me-1"></i>
                  {{ avail.start_time }} - {{ avail.end_time }}
                </td>
                <td>
                  <span v-if="avail.lunch_break_start" class="badge bg-warning text-dark">
                    🍽️ {{ avail.lunch_break_start }} - {{ avail.lunch_break_end }}
                  </span>
                  <span v-else class="text-muted">No break</span>
                </td>
                <td>
                  <span :class="avail.is_available ? 'badge bg-success' : 'badge bg-danger'">
                    {{ avail.is_available ? 'Available' : 'Unavailable' }}
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm btn-warning me-1" @click="editAvailability(avail)">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-sm btn-danger" @click="deleteAvailability(avail)">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Assigned Patients -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
        <span>
          <i class="bi bi-people me-2"></i>
          Assigned Patients
        </span>
        <input 
          type="text" 
          v-model="patientSearch" 
          class="form-control form-control-sm" 
          style="max-width: 250px;"
          placeholder="Search patients..."
        >
      </div>
      <div class="card-body">
        <div class="table-scroll-container">
          <table class="table table-striped">
            <thead class="table-light">
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Phone</th>
                <th>Update</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredPatients.length === 0">
                <td colspan="5" class="text-center text-muted py-3">
                  {{ patientSearch ? 'No patients found' : 'No patients assigned yet' }}
                </td>
              </tr>
              <tr v-for="pat in filteredPatients" :key="pat.id">
                <td>{{ pat.id }}</td>
                <td>
                  <i class="bi bi-person-fill me-1 text-primary"></i>
                  {{ pat.full_name }}
                </td>
                <td>
                  <i class="bi bi-telephone me-1"></i>
                  {{ pat.phone }}
                </td>
                <td>
                  <button 
                    class="btn btn-sm btn-primary me-1" 
                    @click="openUpdateHistoryModal(pat)"
                    title="Add Follow-up Record"
                  >
                    <i class="bi bi-journal-plus me-1"></i>
                    Update History
                  </button>
                  <button 
                    class="btn btn-sm btn-info" 
                    @click="viewPatientHistory(pat)"
                    title="View Treatment History"
                  >
                    <i class="bi bi-file-medical me-1"></i>
                    History
                  </button>
                </td>
                <td>
                  <button 
                    class="btn btn-sm btn-info" 
                    @click="viewPatientHistory(pat)"
                    title="View Treatment History"
                  >
                    <i class="bi bi-file-medical me-1"></i>
                    History
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Update Patient History Modal -->
    <div v-if="showUpdateHistoryModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <form class="modal-content" @submit.prevent="submitUpdateHistory">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">
              <i class="bi bi-journal-plus me-2"></i>
              Update Treatment History - {{ currentPatient?.full_name }}
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeUpdateHistoryModal"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-info">
              <strong>ℹ️ Note:</strong> Use this for follow-ups, medication adjustments, or routine check-ins without a scheduled appointment.
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-calendar3 me-1"></i>
                Visit Date *
              </label>
              <input 
                type="date" 
                v-model="updateHistoryForm.visit_date" 
                class="form-control" 
                required 
                :max="maxDate"
              >
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-clipboard-heart me-1"></i>
                Diagnosis/Condition *
              </label>
              <textarea 
                v-model="updateHistoryForm.diagnosis" 
                class="form-control" 
                rows="3" 
                required 
                placeholder="Current diagnosis, medical condition, or health status update..."
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-capsule me-1"></i>
                Prescription/Medication
              </label>
              <textarea 
                v-model="updateHistoryForm.prescription" 
                class="form-control" 
                rows="2" 
                placeholder="Prescribed medications, dosage, and frequency..."
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-journal-text me-1"></i>
                Clinical Notes
              </label>
              <textarea 
                v-model="updateHistoryForm.notes" 
                class="form-control" 
                rows="3" 
                placeholder="Lab results, patient progress, observations, recommendations..."
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-calendar-plus me-1"></i>
                Next Follow-up Date
              </label>
              <input 
                type="date" 
                v-model="updateHistoryForm.next_visit" 
                class="form-control" 
                :min="minDate"
              >
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-primary">
              <i class="bi bi-check-circle me-1"></i>
              Add to History
            </button>
            <button type="button" class="btn btn-secondary" @click="closeUpdateHistoryModal">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Bulk Availability Modal -->
    <div v-if="showBulkAvailabilityModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog">
        <form class="modal-content" @submit.prevent="submitBulkAvailability">
          <div class="modal-header bg-info text-white">
            <h5 class="modal-title">
              <i class="bi bi-calendar-check me-2"></i>
              Set 7-Day Availability
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeBulkAvailabilityModal"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-warning">
              <strong>⚠️ Note:</strong> This will set the same time slot for the next 7 days.
              You can edit individual days later.
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">Start Time *</label>
              <select v-model="bulkAvailabilityForm.start_time" class="form-select" required>
                <option value="">Select start time</option>
                <option v-for="time in timeSlots" :key="time" :value="time">{{ time }}</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">End Time *</label>
              <select v-model="bulkAvailabilityForm.end_time" class="form-select" required>
                <option value="">Select end time</option>
                <option v-for="time in timeSlots" :key="time" :value="time">{{ time }}</option>
              </select>
            </div>

            <div v-if="bulkAvailabilityForm.start_time && bulkAvailabilityForm.end_time" class="alert alert-success">
              <strong>✓ Preview:</strong> You'll be available from {{ bulkAvailabilityForm.start_time }} to {{ bulkAvailabilityForm.end_time }} for the next 7 days.
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-success">Set Availability</button>
            <button type="button" class="btn btn-secondary" @click="closeBulkAvailabilityModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Day Availability Modal -->
    <div v-if="showEditDayModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog">
        <form class="modal-content" @submit.prevent="submitDayAvailability">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">
              <i class="bi bi-calendar-edit me-2"></i>
              Edit Availability - {{ editDayForm.date }}
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeEditDayModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label fw-bold">Start Time *</label>
              <select v-model="editDayForm.start_time" class="form-select" required>
                <option value="">Select start time</option>
                <option v-for="time in timeSlots" :key="time" :value="time">{{ time }}</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">End Time *</label>
              <select v-model="editDayForm.end_time" class="form-select" required>
                <option value="">Select end time</option>
                <option v-for="time in timeSlots" :key="time" :value="time">{{ time }}</option>
              </select>
            </div>

            <!-- Lunch Break Section -->
            <div class="border-top pt-3 mb-3">
              <div class="form-check mb-2">
                <input 
                  type="checkbox" 
                  v-model="editDayForm.has_lunch_break" 
                  class="form-check-input" 
                  id="hasLunchBreak"
                >
                <label class="form-check-label" for="hasLunchBreak">
                  🍽️ Add Lunch Break
                </label>
              </div>

              <div v-if="editDayForm.has_lunch_break">
                <div class="row">
                  <div class="col-md-6 mb-2">
                    <label class="form-label">Lunch Start</label>
                    <select v-model="editDayForm.lunch_break_start" class="form-select">
                      <option value="">Select time</option>
                      <option v-for="time in timeSlots" :key="time" :value="time">{{ time }}</option>
                    </select>
                  </div>
                  <div class="col-md-6 mb-2">
                    <label class="form-label">Lunch End</label>
                    <select v-model="editDayForm.lunch_break_end" class="form-select">
                      <option value="">Select time</option>
                      <option v-for="time in timeSlots" :key="time" :value="time">{{ time }}</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-check">
              <input 
                type="checkbox" 
                v-model="editDayForm.is_available" 
                class="form-check-input" 
                id="available"
              >
              <label class="form-check-label" for="available">
                Mark as available (uncheck to block this day)
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-success">Save Changes</button>
            <button type="button" class="btn btn-secondary" @click="closeEditDayModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Complete Appointment Modal -->
    <div v-if="showTreatmentModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <form class="modal-content" @submit.prevent="submitTreatment">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">
              <i class="bi bi-clipboard-plus me-2"></i>
              Complete Appointment & Add Treatment
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeTreatmentModal"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-info">
              <strong>Patient:</strong> {{ currentAppointment?.patient_name }}<br>
              <strong>Date:</strong> {{ currentAppointment?.appointment_date }}<br>
              <strong>Time:</strong> {{ currentAppointment?.appointment_time }}
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-clipboard-heart me-1"></i>
                Diagnosis *
              </label>
              <textarea 
                v-model="treatmentForm.diagnosis" 
                class="form-control" 
                rows="3" 
                required 
                placeholder="Enter diagnosis..."
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-capsule me-1"></i>
                Prescription
              </label>
              <textarea 
                v-model="treatmentForm.prescription" 
                class="form-control" 
                rows="2" 
                placeholder="Enter prescription details..."
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-journal-text me-1"></i>
                Clinical Notes
              </label>
              <textarea 
                v-model="treatmentForm.notes" 
                class="form-control" 
                rows="2" 
                placeholder="Additional notes..."
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold">
                <i class="bi bi-calendar-plus me-1"></i>
                Next Visit Date
              </label>
              <input 
                type="date" 
                v-model="treatmentForm.next_visit_date" 
                class="form-control"
                :min="minDate"
              >
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-success">
              <i class="bi bi-check-circle me-1"></i>
              Save & Complete
            </button>
            <button type="button" class="btn btn-secondary" @click="closeTreatmentModal">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Patient History Modal -->
    <div v-if="showHistoryModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header bg-info text-white">
            <h5 class="modal-title">
              <i class="bi bi-file-medical-fill me-2"></i>
              Complete Treatment History - {{ selectedPatient?.full_name }}
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeHistoryModal"></button>
          </div>
          <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
            <div v-if="patientHistory.length === 0" class="text-center py-5">
              <i class="bi bi-inbox" style="font-size: 4rem; opacity: 0.3;"></i>
              <p class="text-muted mt-3">No treatment history available</p>
            </div>

            <div v-for="(record, index) in patientHistory" :key="record.id" class="card mb-3">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                  <div>
                    <h6 class="card-title mb-1">
                      <span class="badge bg-secondary">Visit #{{ index + 1 }}</span>
                      {{ formatDate(record.appointment_date) }}
                    </h6>
                    <small class="text-muted">
                      <strong>Time:</strong> {{ record.appointment_time }} | 
                      <strong>Reason:</strong> {{ record.reason || 'General consultation' }}
                    </small>
                  </div>
                  <span class="badge bg-success">Completed</span>
                </div>

                <div v-if="record.treatment">
                  <div class="row">
                    <div class="col-md-6">
                      <div class="mb-3">
                        <strong class="text-primary">
                          <i class="bi bi-clipboard-heart me-1"></i>
                          Diagnosis:
                        </strong>
                        <p class="mb-0">{{ record.treatment.diagnosis }}</p>
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="mb-3">
                        <strong class="text-success">
                          <i class="bi bi-capsule me-1"></i>
                          Prescription:
                        </strong>
                        <p class="mb-0">{{ record.treatment.prescription || 'None' }}</p>
                      </div>
                    </div>
                  </div>

                  <div v-if="record.treatment.notes">
                    <strong class="text-info">
                      <i class="bi bi-journal-text me-1"></i>
                      Notes:
                    </strong>
                    <p class="mb-0">{{ record.treatment.notes }}</p>
                  </div>

                  <div v-if="record.treatment.next_visit_date" class="alert alert-info mt-3 mb-0">
                    <strong>
                      <i class="bi bi-calendar-plus me-1"></i>
                      Next Follow-up:
                    </strong> 
                    {{ formatDate(record.treatment.next_visit_date) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeHistoryModal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Backdrop -->
    <div 
  v-if="showTreatmentModal || showHistoryModal || showUpdateHistoryModal || showBulkAvailabilityModal || showEditDayModal" 
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
const doctor = ref({})
const appointments = ref([])
const patients = ref([])
const patientSearch = ref('')
const patientHistory = ref([])
const selectedPatient = ref(null)

// Modals
const showTreatmentModal = ref(false)
const showHistoryModal = ref(false)

// Current items
const currentAppointment = ref(null)

// Forms
const treatmentForm = ref({
  diagnosis: '',
  prescription: '',
  notes: '',
  next_visit_date: ''
})

// Computed
const minDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

const completedToday = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return appointments.value.filter(apt => 
    apt.appointment_date === today && apt.status === 'completed'
  ).length
})

const pendingCount = computed(() => {
  return appointments.value.filter(apt => apt.status === 'booked').length
})

const filteredPatients = computed(() => {
  if (!patientSearch.value) return patients.value
  
  const query = patientSearch.value.toLowerCase()
  return patients.value.filter(pat => 
    pat.full_name?.toLowerCase().includes(query) ||
    pat.phone?.includes(query)
  )
})

// Methods
const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

const fetchDashboard = async () => {
  try {
    const response = await apiClient.get('/api/doctor/dashboard')
    doctor.value = response.data.doctor_info || {}
    appointments.value = response.data.upcoming_appointments?.filter(apt => apt.status === 'booked') || []
  } catch (error) {
    console.error('Error fetching dashboard:', error)
    alert('Failed to load dashboard data')
  }
}

const fetchPatients = async () => {
  try {
    const response = await apiClient.get('/api/doctor/patients')
    patients.value = response.data.patients || []
  } catch (error) {
    console.error('Error fetching patients:', error)
  }
}

const completeAppointment = (apt) => {
  currentAppointment.value = apt
  treatmentForm.value = {
    diagnosis: '',
    prescription: '',
    notes: '',
    next_visit_date: ''
  }
  showTreatmentModal.value = true
}

const submitTreatment = async () => {
  if (!treatmentForm.value.diagnosis.trim()) {
    alert('Diagnosis is required')
    return
  }
  
  try {
    await apiClient.post(
      `/api/doctor/appointments/${currentAppointment.value.id}/treatment`, 
      treatmentForm.value
    )
    alert('Treatment added and appointment completed!')
    closeTreatmentModal()
    await fetchDashboard()
  } catch (error) {
    alert('Failed to complete appointment: ' + (error.response?.data?.error || 'Unknown error'))
  }
}

const closeTreatmentModal = () => {
  showTreatmentModal.value = false
  currentAppointment.value = null
}

const cancelAppointment = async (apt) => {
  const reason = prompt('Enter cancellation reason:')
  if (!reason) return
  
  try {
    await apiClient.post(`/api/doctor/appointments/${apt.id}/cancel`, { reason })
    alert('Appointment cancelled successfully')
    await fetchDashboard()
  } catch (error) {
    alert('Failed to cancel appointment')
  }
}

const viewPatientHistory = async (pat) => {
  selectedPatient.value = pat
  
  try {
    const response = await apiClient.get(`/api/doctor/patients/${pat.id}/history`)
    patientHistory.value = response.data.history || []
    showHistoryModal.value = true
  } catch (error) {
    console.error('Error fetching patient history:', error)
    alert('Failed to load patient history')
  }
}

const closeHistoryModal = () => {
  showHistoryModal.value = false
  selectedPatient.value = null
  patientHistory.value = []
}

const logout = () => {
  userStore.logout()
  router.push('/login')
}

// Initialize
onMounted(() => {
  fetchDashboard()
  fetchPatients()
  fetchAvailability()
})

// Add these refs after the existing ones (around line 295)
const showUpdateHistoryModal = ref(false)
const showBulkAvailabilityModal = ref(false)
const showEditDayModal = ref(false)
const currentPatient = ref(null)
const availability = ref([])

// Forms
const updateHistoryForm = ref({
  visit_date: '',
  diagnosis: '',
  prescription: '',
  notes: '',
  next_visit: ''
})

const bulkAvailabilityForm = ref({
  start_time: '',
  end_time: ''
})

const editDayForm = ref({
  id: null,
  date: '',
  start_time: '',
  end_time: '',
  has_lunch_break: false,
  lunch_break_start: '',
  lunch_break_end: '',
  is_available: true
})

// Add computed property for maxDate
const maxDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

// Time slots for availability
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 0; hour < 24; hour++) {
    for (let min = 0; min < 60; min += 30) {
      const time = `${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}`
      slots.push(time)
    }
  }
  return slots
})

// Add getDayName helper
const getDayName = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { weekday: 'long' })
}

// Update History Methods
const openUpdateHistoryModal = (patient) => {
  currentPatient.value = patient
  updateHistoryForm.value = {
    visit_date: new Date().toISOString().split('T')[0],
    diagnosis: '',
    prescription: '',
    notes: '',
    next_visit: ''
  }
  showUpdateHistoryModal.value = true
}

const closeUpdateHistoryModal = () => {
  showUpdateHistoryModal.value = false
  currentPatient.value = null
}

const submitUpdateHistory = async () => {
  if (!updateHistoryForm.value.diagnosis.trim()) {
    alert('Diagnosis is required')
    return
  }
  
  try {
    await apiClient.post(
      `/api/doctor/patients/${currentPatient.value.id}/history/add`,
      updateHistoryForm.value
    )
    alert('Patient history updated successfully!')
    closeUpdateHistoryModal()
    await fetchPatients()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to update history')
  }
}

// Availability Methods
const fetchAvailability = async () => {
  try {
    const response = await apiClient.get('/api/doctor/availability')
    availability.value = response.data.availability || []
  } catch (error) {
    console.error('Error fetching availability:', error)
  }
}

const openBulkAvailabilityModal = () => {
  bulkAvailabilityForm.value = {
    start_time: '09:00',
    end_time: '17:00'
  }
  showBulkAvailabilityModal.value = true
}

const closeBulkAvailabilityModal = () => {
  showBulkAvailabilityModal.value = false
}

const submitBulkAvailability = async () => {
  try {
    await apiClient.post('/api/doctor/availability/bulk', bulkAvailabilityForm.value)
    alert('7-day availability set successfully!')
    closeBulkAvailabilityModal()
    await fetchAvailability()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to set availability')
  }
}

const editAvailability = (avail) => {
  editDayForm.value = {
    id: avail.id,
    date: avail.date,
    start_time: avail.start_time,
    end_time: avail.end_time,
    has_lunch_break: !!avail.lunch_break_start,
    lunch_break_start: avail.lunch_break_start || '',
    lunch_break_end: avail.lunch_break_end || '',
    is_available: avail.is_available
  }
  showEditDayModal.value = true
}

const closeEditDayModal = () => {
  showEditDayModal.value = false
}

const submitDayAvailability = async () => {
  try {
    const payload = {
      date: editDayForm.value.date,
      start_time: editDayForm.value.start_time,
      end_time: editDayForm.value.end_time,
      is_available: editDayForm.value.is_available
    }
    
    if (editDayForm.value.has_lunch_break) {
      payload.lunch_break_start = editDayForm.value.lunch_break_start
      payload.lunch_break_end = editDayForm.value.lunch_break_end
    }
    
    await apiClient.post('/api/doctor/availability', payload)
    alert('Availability updated successfully!')
    closeEditDayModal()
    await fetchAvailability()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to update availability')
  }
}

const deleteAvailability = async (avail) => {
  if (!confirm(`Delete availability for ${avail.date}?`)) return
  
  try {
    await apiClient.delete(`/api/doctor/availability/${avail.id}`)
    alert('Availability deleted successfully!')
    await fetchAvailability()
  } catch (error) {
    alert('Failed to delete availability')
  }
}
</script>

<style scoped>
.navbar-violet {
  background: linear-gradient(90deg, #7c4dff 0%, #512da8 100%);
  color: #fff;
}

.stat-card {
  border-left: 4px solid #28a745;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-left-width: 8px;
  transform: translateY(-2px);
}

.table-scroll-container {
  max-height: 450px;
  overflow-y: auto;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}
</style>