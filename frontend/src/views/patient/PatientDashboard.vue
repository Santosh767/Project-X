<template>
  <div class="container-fluid py-4">
    <!-- Navbar -->
    <nav class="navbar navbar-green mb-3 rounded shadow-sm sticky-top">
      <span class="navbar-brand fw-bold">Welcome {{ patient.full_name }}</span>
      <div class="d-flex gap-2">
        <button class="btn btn-light btn-sm" @click="openProfileModal">
          <i class="bi bi-person-circle"></i> Profile
        </button>
        <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
      </div>
    </nav>

    <!-- Upcoming Appointments -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-primary text-white">Upcoming Appointments</div>
      <div class="table-scroll-container">
        <table class="table table-borderless align-middle mb-0">
          <thead class="table-light sticky-top">
            <tr>
              <th>Date</th>
              <th>Time</th>
              <th>Doctor</th>
              <th>Status</th>
              <th>Amount</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="appointments.length === 0">
              <td colspan="6" class="text-center text-muted py-3">No upcoming appointments</td>
            </tr>
            <tr v-for="apt in appointments" :key="apt.id">
              <td>{{ apt.appointment_date }}</td>
              <td>{{ apt.appointment_time }}</td>
              <td>{{ apt.doctor_name }}</td>
              <td>
                <span class="badge" :class="{
                  'bg-warning text-dark': apt.status === 'booked',
                  'bg-success': apt.status === 'completed',
                  'bg-danger': apt.status === 'cancelled'
                }">{{ apt.status }}</span>
              </td>
              <td>₹{{ apt.consultation_fee || 0 }}</td>
              <td>
                <button v-if="apt.status === 'booked'" class="btn btn-warning btn-sm me-1" @click="openRescheduleModal(apt)">
                  Reschedule
                </button>
                <button v-if="apt.status === 'booked'" class="btn btn-danger btn-sm" @click="openCancelModal(apt)">
                  Cancel
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Departments & Doctors -->
    <div class="row">
      <div class="col-md-4">
        <div class="card mb-4 shadow">
          <div class="card-header bg-secondary text-white">Departments</div>
          <div class="table-scroll-container">
            <ul class="list-group list-group-flush">
              <li class="list-group-item" v-for="dept in departments" :key="dept.id">
                {{ dept.name }}
                <button class="btn btn-info btn-sm float-end" @click="viewDepartment(dept)">
                  View Doctors
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="col-md-8">
        <div class="card mb-4 shadow">
          <div class="card-header bg-info text-black d-flex justify-content-between align-items-center">
            <span>Doctors</span>
            <div class="input-group" style="width: 300px;">
              <input 
                type="text" 
                v-model="doctorSearch" 
                class="form-control form-control-sm" 
                placeholder="Search by doctor name..."
                @input="filterDoctors"
              >
              <button class="btn btn-light btn-sm" type="button">
                <i class="bi bi-search"></i>
              </button>
            </div>
          </div>
          <div class="table-scroll-container">
            <div class="p-3">
              <div v-if="filteredDoctors.length === 0" class="text-center text-muted py-4">
                {{ doctorSearch ? 'No doctors found' : 'Select a department' }}
              </div>

              <div v-for="doc in filteredDoctors" :key="doc.id" class="doctor-card">
                <div class="row align-items-center">
                  <div class="col-md-6">
                    <h5 class="mb-1">
                      <i class="bi bi-person-badge text-primary"></i>
                      Dr. {{ doc.full_name }}
                    </h5>
                    <p class="text-muted mb-2">
                      <i class="bi bi-hospital"></i> {{ doc.specialization }}
                    </p>
                    <div>
                      <span class="badge bg-primary doctor-info-badge">
                        {{ doc.qualification || 'MBBS' }}
                      </span>
                      <span class="badge bg-success doctor-info-badge">
                        {{ doc.experience_years || 0 }} years
                      </span>
                      <span class="badge bg-warning text-dark doctor-info-badge">
                        ₹{{ doc.consultation_fee || 500 }}
                      </span>
                    </div>
                  </div>
                  <div class="col-md-6 text-end">
                    <button class="btn btn-outline-info btn-sm me-1" @click="checkAvailability(doc)">
                      Availability
                    </button>
                    <button class="btn btn-success btn-sm" @click="bookAppointment(doc)">
                      Book
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Treatment History -->
    <div class="card mb-4 shadow">
      <div class="card-header bg-warning d-flex justify-content-between align-items-center">
        <span>Treatment History</span>
        <button class="btn btn-outline-dark btn-sm" @click="exportHistorySync">
          <i class="bi bi-download"></i> Export CSV
        </button>
      </div>
      <div class="table-scroll-container">
        <table class="table align-middle mb-0">
          <thead class="table-light sticky-top">
            <tr>
              <th>Date</th>
              <th>Doctor</th>
              <th>Diagnosis</th>
              <th>Prescription</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="history.length === 0">
              <td colspan="4" class="text-center text-muted py-3">No treatment history yet</td>
            </tr>
            <tr v-for="h in history" :key="h.id">
              <td>{{ h.appointment_date }}</td>
              <td>{{ h.doctor_details?.name || 'N/A' }}</td>
              <td>{{ h.treatment?.diagnosis || 'N/A' }}</td>
              <td>{{ h.treatment?.prescription || 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Check Availability Modal -->
<div v-if="showAvailabilityModal" class="modal show" style="display:block;" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header bg-info text-white">
        <h5 class="modal-title">
          <i class="bi bi-calendar-check"></i> Doctor's Availability - Dr. {{ selectedDoctor?.full_name }}
        </h5>
        <button type="button" class="btn-close btn-close-white" @click="closeAvailabilityModal"></button>
      </div>
      <div class="modal-body">
        <div v-if="selectedDoctor" class="alert alert-info">
          <strong>Specialization:</strong> {{ selectedDoctor.specialization }}<br>
          <strong>Consultation Fee:</strong> ₹{{ selectedDoctor.consultation_fee || 500 }}<br>
          <strong>Experience:</strong> {{ selectedDoctor.experience_years || 0 }} years
        </div>

        <h6 class="mb-3">Available Time Slots (Next 7 Days)</h6>

        <div v-if="selectedDoctor?.availability && selectedDoctor.availability.length > 0">
          <div v-for="avail in selectedDoctor.availability" :key="avail.id" class="card availability-card mb-2">
            <div class="card-body py-2">
              <div class="row align-items-center">
                <div class="col-md-4">
                  <strong>{{ formatDate(avail.date) }}</strong>
                  <br>
                  <small class="text-muted">{{ getDayName(avail.date) }}</small>
                </div>
                <div class="col-md-8">
                  <span class="badge bg-success time-badge">
                    {{ avail.start_time }} - {{ avail.end_time }}
                  </span>
                  <span v-if="avail.lunch_break_start" class="badge bg-danger time-badge">
                    🍽️ Break: {{ avail.lunch_break_start }} - {{ avail.lunch_break_end }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-4">
          <i class="bi bi-calendar-x text-muted" style="font-size: 3rem;"></i>
          <p class="mt-2 text-muted">No availability set for the next 7 days</p>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-success" @click="bookFromAvailability">Book Appointment</button>
        <button type="button" class="btn btn-secondary" @click="closeAvailabilityModal">Close</button>
      </div>
    </div>
  </div>
</div>
    <!-- Book Appointment Modal -->
    <div v-if="showBookModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <form class="modal-content" @submit.prevent="proceedToPayment">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">Book Appointment with Dr. {{ selectedDoctor?.full_name }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeBookModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Appointment Date *</label>
              <input 
                type="date" 
                v-model="bookForm.appointment_date" 
                class="form-control" 
                required 
                :min="minDate" 
                @change="loadAvailableSlots"
              >
            </div>

            <div class="mb-3" v-if="bookForm.appointment_date">
              <label class="form-label">Select Time Slot (10-min intervals) *</label>
              <div v-if="loadingSlots" class="text-center py-3">
                <div class="spinner-border text-primary"></div>
              </div>
              <div v-else-if="availableTimeSlots.length === 0" class="alert alert-warning">
                No available slots for this date. Doctor may not be available.
              </div>
              <div v-else class="d-flex flex-wrap">
                <button 
                  v-for="slot in availableTimeSlots" 
                  :key="slot.time"
                  type="button"
                  class="time-slot-btn"
                  :class="{ 
                    'selected': bookForm.appointment_time === slot.time,
                    'lunch-break': slot.isLunchBreak 
                  }"
                  :disabled="!slot.available"
                  @click="selectTimeSlot(slot.time)"
                  :title="slot.reason || 'Available'"
                >
                  {{ slot.time }}
                  <small v-if="slot.isLunchBreak" class="d-block">🍽️ Lunch</small>
                  <small v-else-if="!slot.available" class="d-block">Booked</small>
                </button>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Purpose/Reason</label>
              <textarea v-model="bookForm.reason" class="form-control" rows="2"></textarea>
            </div>

            <div class="alert alert-success">
              <strong>Consultation Fee:</strong> ₹{{ selectedDoctor?.consultation_fee || 500 }}
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-success" :disabled="!bookForm.appointment_time">
              Proceed to Payment
            </button>
            <button type="button" class="btn btn-secondary" @click="closeBookModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Payment Modal -->
    <div v-if="showPaymentModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <form class="modal-content" @submit.prevent="processPayment">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">Payment Details</h5>
            <button type="button" class="btn-close btn-close-white" @click="closePaymentModal"></button>
          </div>
          <div class="modal-body">
            <div class="payment-card-preview">
              <h6>Appointment Summary</h6>
              <div class="row mt-3">
                <div class="col-6">
                  <small>Doctor:</small><br>
                  <strong>Dr. {{ selectedDoctor?.full_name }}</strong>
                </div>
                <div class="col-6 text-end">
                  <small>Date & Time:</small><br>
                  <strong>{{ bookForm.appointment_date }} {{ bookForm.appointment_time }}</strong>
                </div>
              </div>
              <hr class="bg-white">
              <div class="d-flex justify-content-between">
                <h5>Total:</h5>
                <h5>₹{{ selectedDoctor?.consultation_fee || 500 }}</h5>
              </div>
            </div>

            <div class="row">
              <div class="col-md-12 mb-3">
                <label class="form-label">Cardholder Name *</label>
                <input type="text" v-model="paymentForm.cardName" class="form-control" required>
              </div>
            </div>

            <div class="row">
              <div class="col-md-12 mb-3">
                <label class="form-label">Card Number *</label>
                <input 
                  type="text" 
                  v-model="paymentForm.cardNumber" 
                  class="form-control" 
                  required 
                  maxlength="19" 
                  @input="formatCardNumber"
                >
              </div>
            </div>

            <div class="row">
              <div class="col-md-4 mb-3">
                <label class="form-label">Month *</label>
                <select v-model="paymentForm.expiryMonth" class="form-select" required>
                  <option value="">MM</option>
                  <option v-for="m in 12" :key="m" :value="String(m).padStart(2, '0')">
                    {{ String(m).padStart(2, '0') }}
                  </option>
                </select>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Year *</label>
                <select v-model="paymentForm.expiryYear" class="form-select" required>
                  <option value="">YYYY</option>
                  <option v-for="y in 10" :key="y" :value="2024 + y">{{ 2024 + y }}</option>
                </select>
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">CVV *</label>
                <input 
                  type="password" 
                  v-model="paymentForm.cvv" 
                  class="form-control" 
                  required 
                  maxlength="3"
                >
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-primary" :disabled="processingPayment">
              <span v-if="processingPayment">Processing...</span>
              <span v-else>Pay ₹{{ selectedDoctor?.consultation_fee || 500 }}</span>
            </button>
            <button type="button" class="btn btn-secondary" @click="closePaymentModal">Back</button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Profile Edit Modal with Password Change -->
    <div v-if="showProfileModal" class="modal show" style="display:block;" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <form class="modal-content" @submit.prevent="submitProfileUpdate">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">
              <i class="bi bi-person-circle"></i> Edit Profile
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeProfileModal"></button>
          </div>
          <div class="modal-body">
            <ul class="nav nav-tabs mb-3" role="tablist">
              <li class="nav-item">
                <button class="nav-link" :class="{ active: profileTab === 'info' }" type="button" 
                  @click="profileTab = 'info'">Profile Info</button>
              </li>
              <li class="nav-item">
                <button class="nav-link" :class="{ active: profileTab === 'password' }" type="button" 
                  @click="profileTab = 'password'">Change Password</button>
              </li>
            </ul>

            <!-- Profile Info Tab -->
            <div v-show="profileTab === 'info'">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">Full Name *</label>
                  <input type="text" v-model="profileForm.full_name" class="form-control" required>
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">Email *</label>
                  <input type="email" v-model="profileForm.email" class="form-control" required>
                </div>
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">Phone Number *</label>
                  <input type="tel" v-model="profileForm.phone" class="form-control" required 
                    placeholder="+91 9876543210">
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">Date of Birth</label>
                  <input type="date" v-model="profileForm.date_of_birth" class="form-control" :max="maxBirthDate">
                </div>
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">Gender</label>
                  <select v-model="profileForm.gender" class="form-select">
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">Username (Read-only)</label>
                  <input type="text" :value="patient.username" class="form-control" disabled>
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Address</label>
                <textarea v-model="profileForm.address" class="form-control" rows="2" 
                  placeholder="Enter your full address"></textarea>
              </div>
            </div>

            <!-- Change Password Tab -->
            <div v-show="profileTab === 'password'">
              <div class="alert alert-info">
                <i class="bi bi-shield-lock"></i> 
                <strong>Security:</strong> Choose a strong password with at least 8 characters.
              </div>

              <div class="mb-3">
                <label class="form-label">Current Password *</label>
                <input type="password" v-model="passwordForm.current_password" class="form-control" 
                  :required="profileTab === 'password'" placeholder="Enter current password">
              </div>

              <div class="mb-3">
                <label class="form-label">New Password *</label>
                <input type="password" v-model="passwordForm.new_password" class="form-control" 
                  :required="profileTab === 'password'" minlength="8" placeholder="Enter new password">
                <small class="text-muted">Minimum 8 characters</small>
              </div>

              <div class="mb-3">
                <label class="form-label">Confirm New Password *</label>
                <input type="password" v-model="passwordForm.confirm_password" class="form-control" 
                  :required="profileTab === 'password'" minlength="8" placeholder="Confirm new password">
              </div>

              <div v-if="passwordError" class="alert alert-danger">
                {{ passwordError }}
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button v-if="profileTab === 'info'" type="submit" class="btn btn-success">Save Profile Changes</button>
            <button v-if="profileTab === 'password'" type="button" class="btn btn-primary" @click="changePassword">
              Update Password
            </button>
            <button type="button" class="btn btn-secondary" @click="closeProfileModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Cancel Modal -->
    <div v-if="showCancelModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog">
        <form class="modal-content" @submit.prevent="submitCancel">
          <div class="modal-header bg-danger text-white">
            <h5 class="modal-title">Cancel Appointment</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeCancelModal"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-warning">
              Full refund of ₹{{ currentCancelAppointment?.consultation_fee || 0 }} will be initiated
            </div>
            <div class="mb-3">
              <label class="form-label">Cancellation Reason *</label>
              <textarea v-model="cancelReason" class="form-control" rows="3" required></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-danger">Confirm Cancellation</button>
            <button type="button" class="btn btn-secondary" @click="closeCancelModal">Back</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Reschedule Modal -->
    <div v-if="showRescheduleModal" class="modal show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <form class="modal-content" @submit.prevent="submitReschedule">
          <div class="modal-header bg-warning">
            <h5 class="modal-title">Reschedule Appointment</h5>
            <button type="button" class="btn-close" @click="closeRescheduleModal"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-info">
              <strong>Current:</strong> {{ currentRescheduleAppointment?.appointment_date }} at {{ currentRescheduleAppointment?.appointment_time }}<br>
              <strong>Doctor:</strong> {{ currentRescheduleAppointment?.doctor_name }}
            </div>
            
            <div class="mb-3">
              <label class="form-label">New Date *</label>
              <input 
                type="date" 
                v-model="rescheduleForm.appointment_date" 
                class="form-control" 
                required 
                :min="minDate"
                @change="loadRescheduleSlotsForDate"
              >
            </div>

            <div class="mb-3" v-if="rescheduleForm.appointment_date">
              <label class="form-label">Select New Time Slot *</label>
              <div v-if="loadingRescheduleSlots" class="text-center py-3">
                <div class="spinner-border text-primary"></div>
              </div>
              <div v-else-if="rescheduleAvailableSlots.length === 0" class="alert alert-warning">
                No available slots for this date
              </div>
              <div v-else class="d-flex flex-wrap">
                <button 
                  v-for="slot in rescheduleAvailableSlots" 
                  :key="slot.time"
                  type="button"
                  class="time-slot-btn"
                  :class="{ 'selected': rescheduleForm.appointment_time === slot.time }"
                  :disabled="!slot.available"
                  @click="selectRescheduleTimeSlot(slot.time)"
                >
                  {{ slot.time }}
                  <small v-if="!slot.available" class="d-block">Booked</small>
                </button>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-warning" :disabled="!rescheduleForm.appointment_time">
              Reschedule Appointment
            </button>
            <button type="button" class="btn btn-secondary" @click="closeRescheduleModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Backdrop -->
    <div 
      v-if="showBookModal || showPaymentModal || showCancelModal || showProfileModal || showAvailabilityModal || showRescheduleModal"
      class="modal-backdrop fade show"></div>
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
const patient = ref({})
const appointments = ref([])
const departments = ref([])
const doctors = ref([])
const filteredDoctors = ref([])
const doctorSearch = ref('')
const history = ref([])

// Modals
const showBookModal = ref(false)
const showPaymentModal = ref(false)
const showCancelModal = ref(false)

// Current selections
const selectedDoctor = ref(null)
const currentCancelAppointment = ref(null)

// Time slots
const availableTimeSlots = ref([])
const loadingSlots = ref(false)

// Forms
const bookForm = ref({
  doctor_id: null,
  appointment_date: '',
  appointment_time: '',
  reason: ''
})

const paymentForm = ref({
  cardName: '',
  cardNumber: '',
  expiryMonth: '',
  expiryYear: '',
  cvv: ''
})

const cancelReason = ref('')
const processingPayment = ref(false)

// Computed
const minDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

// Methods
const fetchPatient = async () => {
  try {
    const response = await apiClient.get('/api/auth/me')
    patient.value = response.data
  } catch (error) {
    console.error('Error:', error)
  }
}

const fetchDashboard = async () => {
  try {
    const response = await apiClient.get('/api/patient/dashboard')
    appointments.value = response.data.upcoming_appointments || []
    departments.value = response.data.departments || []
  } catch (error) {
    console.error('Error:', error)
  }
}

const fetchHistory = async () => {
  try {
    const response = await apiClient.get('/api/patient/history')
    history.value = response.data.history || []
  } catch (error) {
    console.error('Error:', error)
  }
}

const viewDepartment = async (dept) => {
  try {
    const response = await apiClient.get(`/api/patient/doctors?specialization_id=${dept.id}`)
    doctors.value = response.data.doctors || []
    filteredDoctors.value = doctors.value
    doctorSearch.value = ''
  } catch (error) {
    console.error('Error:', error)
  }
}

const filterDoctors = () => {
  if (!doctorSearch.value) {
    filteredDoctors.value = doctors.value
    return
  }
  
  const query = doctorSearch.value.toLowerCase()
  filteredDoctors.value = doctors.value.filter(doc => 
    doc.full_name.toLowerCase().includes(query)
  )
}

// Add these refs if not already present
const showAvailabilityModal = ref(false)

// Replace checkAvailability
const checkAvailability = async (doc) => {
  try {
    // Fetch full doctor details with availability
    const response = await apiClient.get(`/api/patient/doctors/${doc.id}`)
    selectedDoctor.value = response.data
    showAvailabilityModal.value = true
  } catch (error) {
    alert('Failed to load availability')
  }
}

const closeAvailabilityModal = () => {
  showAvailabilityModal.value = false
}

const bookFromAvailability = () => {
  closeAvailabilityModal()
  bookAppointment(selectedDoctor.value)
}

// Add these helper methods for the availability modal
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  })
}

const getDayName = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { weekday: 'long' })
}

const bookAppointment = (doc) => {
  selectedDoctor.value = doc
  bookForm.value = {
    doctor_id: doc.id,
    appointment_date: '',
    appointment_time: '',
    reason: ''
  }
  availableTimeSlots.value = []
  showBookModal.value = true
}

const loadAvailableSlots = async () => {
  if (!bookForm.value.appointment_date || !selectedDoctor.value) return
  
  loadingSlots.value = true
  availableTimeSlots.value = []
  
  try {
    // Fetch doctor's availability for the selected date
    const availabilityResponse = await apiClient.get(
      `/api/patient/doctors/${selectedDoctor.value.id}`
    )
    
    // Find availability for the selected date
    const selectedDateAvailability = availabilityResponse.data.availability?.find(
      avail => avail.date === bookForm.value.appointment_date
    )
    
    // Fetch booked slots
    const bookedResponse = await apiClient.get(
      `/api/patient/booked-slots?doctor_id=${selectedDoctor.value.id}&date=${bookForm.value.appointment_date}`
    )
    const bookedTimes = bookedResponse.data.booked_slots || []
    
    // If no availability set for this date, show alert
    if (!selectedDateAvailability || !selectedDateAvailability.is_available) {
      availableTimeSlots.value = []
      alert('Doctor is not available on this date. Please select another date.')
      loadingSlots.value = false
      return
    }
    
    // Parse doctor's working hours
    const startHour = parseInt(selectedDateAvailability.start_time.split(':')[0])
    const startMin = parseInt(selectedDateAvailability.start_time.split(':')[1])
    const endHour = parseInt(selectedDateAvailability.end_time.split(':')[0])
    const endMin = parseInt(selectedDateAvailability.end_time.split(':')[1])
    
    // Parse lunch break if exists
    let lunchStartHour = null, lunchStartMin = null, lunchEndHour = null, lunchEndMin = null
    if (selectedDateAvailability.lunch_break_start && selectedDateAvailability.lunch_break_end) {
      lunchStartHour = parseInt(selectedDateAvailability.lunch_break_start.split(':')[0])
      lunchStartMin = parseInt(selectedDateAvailability.lunch_break_start.split(':')[1])
      lunchEndHour = parseInt(selectedDateAvailability.lunch_break_end.split(':')[0])
      lunchEndMin = parseInt(selectedDateAvailability.lunch_break_end.split(':')[1])
    }
    
    // Generate 10-minute slots within working hours
    const slots = []
    let currentHour = startHour
    let currentMin = startMin
    
    while (currentHour < endHour || (currentHour === endHour && currentMin < endMin)) {
      const timeStr = `${String(currentHour).padStart(2, '0')}:${String(currentMin).padStart(2, '0')}`
      
      // Check if time is during lunch break
      let isDuringLunch = false
      if (lunchStartHour !== null) {
        const currentTimeInMin = currentHour * 60 + currentMin
        const lunchStartInMin = lunchStartHour * 60 + lunchStartMin
        const lunchEndInMin = lunchEndHour * 60 + lunchEndMin
        
        if (currentTimeInMin >= lunchStartInMin && currentTimeInMin < lunchEndInMin) {
          isDuringLunch = true
        }
      }
      
      slots.push({
        time: timeStr,
        available: !bookedTimes.includes(timeStr) && !isDuringLunch,
        isLunchBreak: isDuringLunch,
        reason: isDuringLunch ? 'Lunch Break' : (bookedTimes.includes(timeStr) ? 'Booked' : '')
      })
      
      // Increment by 10 minutes
      currentMin += 10
      if (currentMin >= 60) {
        currentMin = 0
        currentHour += 1
      }
    }
    
    availableTimeSlots.value = slots
  } catch (error) {
    console.error('Error loading slots:', error)
    alert('Failed to load available time slots')
  } finally {
    loadingSlots.value = false
  }
}

// Also update the selectTimeSlot to prevent selecting unavailable slots
const selectTimeSlot = (time) => {
  const slot = availableTimeSlots.value.find(s => s.time === time)
  if (slot && slot.available) {
    bookForm.value.appointment_time = time
  }
}

const proceedToPayment = () => {
  if (!bookForm.value.appointment_time) {
    alert('Please select a time slot')
    return
  }
  
  paymentForm.value = {
    cardName: '',
    cardNumber: '',
    expiryMonth: '',
    expiryYear: '',
    cvv: ''
  }
  
  showBookModal.value = false
  showPaymentModal.value = true
}

const formatCardNumber = () => {
  let value = paymentForm.value.cardNumber.replace(/\s/g, '')
  let formatted = value.match(/.{1,4}/g)
  paymentForm.value.cardNumber = formatted ? formatted.join(' ') : value
}

const processPayment = async () => {
  processingPayment.value = true
  
  try {
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    await apiClient.post('/api/patient/appointments', {
      doctor_id: bookForm.value.doctor_id,
      appointment_date: bookForm.value.appointment_date,
      appointment_time: bookForm.value.appointment_time,
      reason: bookForm.value.reason || 'General consultation',
      consultation_fee: selectedDoctor.value.consultation_fee || 500,
      payment_status: 'paid',
      payment_method: 'card'
    })
    
    alert('Payment Successful! Appointment booked!')
    closePaymentModal()
    closeBookModal()
    await fetchDashboard()
  } catch (error) {
    alert('Payment failed: ' + (error.response?.data?.error || 'Unknown error'))
  } finally {
    processingPayment.value = false
  }
}

const closeBookModal = () => {
  showBookModal.value = false
  selectedDoctor.value = null
}

const closePaymentModal = () => {
  showPaymentModal.value = false
}

const openCancelModal = (apt) => {
  currentCancelAppointment.value = apt
  cancelReason.value = ''
  showCancelModal.value = true
}

const closeCancelModal = () => {
  showCancelModal.value = false
  currentCancelAppointment.value = null
}

const submitCancel = async () => {
  if (!cancelReason.value.trim()) {
    alert('Cancellation reason is required')
    return
  }
  
  try {
    await apiClient.post(`/api/patient/appointments/${currentCancelAppointment.value.id}/cancel`, {
      reason: cancelReason.value
    })
    alert('Appointment cancelled! Refund initiated.')
    closeCancelModal()
    await fetchDashboard()
  } catch (error) {
    alert('Failed to cancel appointment')
  }
}

// Add these refs
const showRescheduleModal = ref(false)
const currentRescheduleAppointment = ref(null)
const rescheduleForm = ref({
  appointment_date: '',
  appointment_time: ''
})
const rescheduleAvailableSlots = ref([])
const loadingRescheduleSlots = ref(false)

// Replace openRescheduleModal
const openRescheduleModal = (apt) => {
  currentRescheduleAppointment.value = apt
  rescheduleForm.value = {
    appointment_date: apt.appointment_date,
    appointment_time: apt.appointment_time
  }
  rescheduleAvailableSlots.value = []
  showRescheduleModal.value = true
  
  // Load slots for current date
  loadRescheduleSlotsForDate()
}

const closeRescheduleModal = () => {
  showRescheduleModal.value = false
  currentRescheduleAppointment.value = null
  rescheduleAvailableSlots.value = []
}

const loadRescheduleSlotsForDate = async () => {
  if (!rescheduleForm.value.appointment_date || !currentRescheduleAppointment.value) return
  
  loadingRescheduleSlots.value = true
  rescheduleAvailableSlots.value = []
  
  try {
    // Fetch doctor's availability
    const availabilityResponse = await apiClient.get(
      `/api/patient/doctors/${currentRescheduleAppointment.value.doctor_id}`
    )
    
    const selectedDateAvailability = availabilityResponse.data.availability?.find(
      avail => avail.date === rescheduleForm.value.appointment_date
    )
    
    // Fetch booked slots
    const bookedResponse = await apiClient.get(
      `/api/patient/booked-slots?doctor_id=${currentRescheduleAppointment.value.doctor_id}&date=${rescheduleForm.value.appointment_date}`
    )
    const bookedTimes = bookedResponse.data.booked_slots || []
    
    if (!selectedDateAvailability || !selectedDateAvailability.is_available) {
      rescheduleAvailableSlots.value = []
      alert('Doctor is not available on this date.')
      loadingRescheduleSlots.value = false
      return
    }
    
    // Parse working hours and lunch break (same logic as above)
    const startHour = parseInt(selectedDateAvailability.start_time.split(':')[0])
    const startMin = parseInt(selectedDateAvailability.start_time.split(':')[1])
    const endHour = parseInt(selectedDateAvailability.end_time.split(':')[0])
    const endMin = parseInt(selectedDateAvailability.end_time.split(':')[1])
    
    let lunchStartHour = null, lunchStartMin = null, lunchEndHour = null, lunchEndMin = null
    if (selectedDateAvailability.lunch_break_start && selectedDateAvailability.lunch_break_end) {
      lunchStartHour = parseInt(selectedDateAvailability.lunch_break_start.split(':')[0])
      lunchStartMin = parseInt(selectedDateAvailability.lunch_break_start.split(':')[1])
      lunchEndHour = parseInt(selectedDateAvailability.lunch_break_end.split(':')[0])
      lunchEndMin = parseInt(selectedDateAvailability.lunch_break_end.split(':')[1])
    }
    
    // Generate slots
    const slots = []
    let currentHour = startHour
    let currentMin = startMin
    
    while (currentHour < endHour || (currentHour === endHour && currentMin < endMin)) {
      const timeStr = `${String(currentHour).padStart(2, '0')}:${String(currentMin).padStart(2, '0')}`
      
      let isDuringLunch = false
      if (lunchStartHour !== null) {
        const currentTimeInMin = currentHour * 60 + currentMin
        const lunchStartInMin = lunchStartHour * 60 + lunchStartMin
        const lunchEndInMin = lunchEndHour * 60 + lunchEndMin
        
        if (currentTimeInMin >= lunchStartInMin && currentTimeInMin < lunchEndInMin) {
          isDuringLunch = true
        }
      }
      
      // Allow current appointment time to be selectable even if booked
      const isCurrentTime = timeStr === currentRescheduleAppointment.value.appointment_time
      
      slots.push({
        time: timeStr,
        available: (isCurrentTime || !bookedTimes.includes(timeStr)) && !isDuringLunch,
        isLunchBreak: isDuringLunch,
        reason: isDuringLunch ? 'Lunch Break' : (bookedTimes.includes(timeStr) ? 'Booked' : '')
      })
      
      currentMin += 10
      if (currentMin >= 60) {
        currentMin = 0
        currentHour += 1
      }
    }
    
    rescheduleAvailableSlots.value = slots
  } catch (error) {
    console.error('Error loading slots:', error)
  } finally {
    loadingRescheduleSlots.value = false
  }
}

const selectRescheduleTimeSlot = (time) => {
  rescheduleForm.value.appointment_time = time
}

const submitReschedule = async () => {
  if (!rescheduleForm.value.appointment_time) {
    alert('Please select a time slot')
    return
  }
  
  try {
    await apiClient.put(
      `/api/patient/appointments/${currentRescheduleAppointment.value.id}/reschedule`,
      rescheduleForm.value
    )
    alert('Appointment rescheduled successfully!')
    closeRescheduleModal()
    await fetchDashboard()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to reschedule appointment')
  }
}

// Add these refs after line 150 (with other modal refs)
const showProfileModal = ref(false)
const profileTab = ref('info') // 'info' or 'password'
const profileForm = ref({
  full_name: '',
  email: '',
  phone: '',
  address: '',
  gender: '',
  date_of_birth: ''
})
const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})
const passwordError = ref('')

// Add this computed property
const maxBirthDate = computed(() => {
  const today = new Date()
  today.setFullYear(today.getFullYear() - 18) // Minimum 18 years old
  return today.toISOString().split('T')[0]
})

// Replace the openProfileModal method (around line 380)
const openProfileModal = () => {
  profileForm.value = {
    full_name: patient.value.full_name || '',
    email: patient.value.email || '',
    phone: patient.value.phone || '',
    address: patient.value.address || '',
    gender: patient.value.gender || '',
    date_of_birth: patient.value.date_of_birth || ''
  }
  passwordForm.value = {
    current_password: '',
    new_password: '',
    confirm_password: ''
  }
  passwordError.value = ''
  profileTab.value = 'info'
  showProfileModal.value = true
}

const closeProfileModal = () => {
  showProfileModal.value = false
  profileTab.value = 'info'
  passwordError.value = ''
}

const submitProfileUpdate = async () => {
  try {
    await apiClient.put('/api/patient/profile', profileForm.value)
    alert('Profile updated successfully!')
    await fetchPatient()
    closeProfileModal()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to update profile')
  }
}

const changePassword = async () => {
  passwordError.value = ''
  
  // Validate passwords match
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    passwordError.value = 'New passwords do not match'
    return
  }
  
  if (passwordForm.value.new_password.length < 8) {
    passwordError.value = 'Password must be at least 8 characters'
    return
  }
  
  try {
    await apiClient.post('/api/patient/change-password', {
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password
    })
    alert('Password changed successfully!')
    closeProfileModal()
  } catch (error) {
    passwordError.value = error.response?.data?.error || 'Failed to change password'
  }
}

const exportHistorySync = async () => {
  if (history.value.length === 0) {
    alert('No history to export')
    return
  }
  
  try {
    const response = await apiClient.get('/api/patient/export-history', {
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `treatment_history_${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    alert('History exported successfully!')
  } catch (error) {
    alert('Export failed')
  }
}

const logout = () => {
  userStore.logout()
  router.push('/login')
}

// Initialize
onMounted(() => {
  fetchPatient()
  fetchDashboard()
  fetchHistory()
})
</script>

<style scoped>
.navbar-green {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
}

.doctor-card {
  border: 1px solid #dee2e6;
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.3s ease;
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.doctor-card:hover {
  box-shadow: 0 5px 20px rgba(0,0,0,0.15);
  transform: translateY(-3px);
}

.doctor-info-badge {
  font-size: 0.85rem;
  padding: 0.25rem 0.5rem;
  margin: 0.2rem;
}

.time-slot-btn {
  margin: 0.2rem;
  padding: 0.5rem 1rem;
  border-radius: 10px;
  border: 2px solid #28a745;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 80px;
}

.time-slot-btn:hover:not(:disabled) {
  background: #28a745;
  color: white;
  transform: scale(1.05);
}

.time-slot-btn.selected {
  background: #28a745;
  color: white;
  font-weight: bold;
}

.time-slot-btn:disabled {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
  cursor: not-allowed;
  opacity: 0.6;
}

.payment-card-preview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 1rem;
  margin-bottom: 1rem;
}

.table-scroll-container {
  max-height: 450px;
  overflow-y: auto;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

.availability-card {
  border: 1px solid #dee2e6;
  transition: all 0.2s ease;
}

.availability-card:hover {
  border-color: #28a745;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
}

.time-badge {
  font-size: 0.9rem;
  padding: 0.4rem 0.8rem;
  margin: 0.2rem;
}

.nav-tabs .nav-link {
  color: #495057;
  cursor: pointer;
}

.nav-tabs .nav-link.active {
  background-color: #28a745;
  color: white;
  border-color: #28a745;
}

.time-slot-btn.lunch-break {
  background: #ffc107;
  color: #000;
  border-color: #ffc107;
  cursor: not-allowed;
  opacity: 0.7;
}

.time-slot-btn.lunch-break:hover {
  background: #ffc107;
  color: #000;
  transform: none;
}
</style>