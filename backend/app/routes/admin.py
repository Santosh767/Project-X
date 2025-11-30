from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app import cache
from app.models import User, Department, Appointment, DoctorAvailability
from app.utils.decorators import role_required, get_current_user
from app.utils.validators import validate_date, validate_time, validate_email, validate_phone
from datetime import datetime, date, timedelta
from sqlalchemy import or_, func

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ==================== DASHBOARD ====================

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required('admin')
@cache.cached(timeout=60, key_prefix='admin_dashboard')
def dashboard():
    """Admin dashboard statistics"""
    total_doctors = User.query.filter_by(role='doctor', is_active=True).count()
    total_patients = User.query.filter_by(role='patient', is_active=True).count()
    total_appointments = Appointment.query.count()
    
    # Appointments by status
    booked = Appointment.query.filter_by(status='booked').count()
    completed = Appointment.query.filter_by(status='completed').count()
    cancelled = Appointment.query.filter_by(status='cancelled').count()
    
    # Recent appointments (last 10)
    recent_appointments = Appointment.query.order_by(
        Appointment.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'statistics': {
            'total_doctors': total_doctors,
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'booked_appointments': booked,
            'completed_appointments': completed,
            'cancelled_appointments': cancelled
        },
        'recent_appointments': [apt.to_dict() for apt in recent_appointments],
        'cached': True
    }), 200


# ==================== DEPARTMENT/SPECIALIZATION MANAGEMENT ✓ ENHANCED ====================

@bp.route('/departments', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_departments():
    """Get all departments"""
    departments = Department.query.all()
    return jsonify({
        'departments': [dept.to_dict() for dept in departments]
    }), 200


@bp.route('/departments', methods=['POST'])
@jwt_required()
@role_required('admin')
def add_department():
    """Add new department"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Department name is required'}), 400
    
    # Check if department exists
    if Department.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Department already exists'}), 400
    
    department = Department(
        name=data['name'],
        description=data.get('description', '')
    )
    
    db.session.add(department)
    db.session.commit()
    
    # Clear cache
    cache.delete('all_departments')
    
    return jsonify({
        'message': 'Department added successfully',
        'department': department.to_dict()
    }), 201


@bp.route('/departments/<int:dept_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_department(dept_id):
    """Update department"""
    department = Department.query.get(dept_id)
    
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        # Check if new name conflicts with existing
        existing = Department.query.filter_by(name=data['name']).first()
        if existing and existing.id != dept_id:
            return jsonify({'error': 'Department name already exists'}), 400
        department.name = data['name']
    
    if 'description' in data:
        department.description = data['description']
    
    db.session.commit()
    
    # Clear cache
    cache.delete('all_departments')
    
    return jsonify({
        'message': 'Department updated successfully',
        'department': department.to_dict()
    }), 200


@bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_department(dept_id):
    """Delete department"""
    department = Department.query.get(dept_id)
    
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    # Check if any doctors are assigned to this department
    doctors_count = User.query.filter_by(role='doctor', specialization_id=dept_id).count()
    if doctors_count > 0:
        return jsonify({
            'error': f'Cannot delete department. {doctors_count} doctor(s) are assigned to this department.'
        }), 400
    
    db.session.delete(department)
    db.session.commit()
    
    # Clear cache
    cache.delete('all_departments')
    
    return jsonify({'message': 'Department deleted successfully'}), 200


# ==================== DOCTOR MANAGEMENT ====================

@bp.route('/doctors', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_doctors():
    """Get all doctors with optional search"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = User.query.filter_by(role='doctor')
    
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    doctors = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'doctors': [doctor.to_dict() for doctor in doctors.items],
        'total': doctors.total,
        'pages': doctors.pages,
        'current_page': page
    }), 200


@bp.route('/doctors/<int:doctor_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_doctor(doctor_id):
    """Get specific doctor details"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Get doctor's appointment statistics
    total_appointments = doctor.doctor_appointments.count()
    completed_appointments = doctor.doctor_appointments.filter_by(status='completed').count()
    
    doctor_data = doctor.to_dict()
    doctor_data['appointment_stats'] = {
        'total': total_appointments,
        'completed': completed_appointments
    }
    
    return jsonify(doctor_data), 200


@bp.route('/doctors', methods=['POST'])
@jwt_required()
@role_required('admin')
def add_doctor():
    """Add new doctor"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'full_name', 'phone', 'specialization_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate email and phone
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if not validate_phone(data['phone']):
        return jsonify({'error': 'Invalid phone number'}), 400
    
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Check if username/email exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Check if department exists
    department = Department.query.get(data['specialization_id'])
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    # Create doctor
    doctor = User(
        username=data['username'],
        email=data['email'],
        role='doctor',
        full_name=data['full_name'],
        phone=data['phone'],
        address=data.get('address'),
        gender=data.get('gender'),
        specialization_id=data['specialization_id'],
        qualification=data.get('qualification'),
        experience_years=data.get('experience_years', 0),
        consultation_fee=data.get('consultation_fee', 0.0)
    )
    doctor.set_password(data['password'])
    
    db.session.add(doctor)
    db.session.commit()
    
    # Clear cache
    cache.delete('admin_dashboard')
    
    return jsonify({
        'message': 'Doctor added successfully',
        'doctor': doctor.to_dict()
    }), 201


@bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_doctor(doctor_id):
    """Admin can update all doctor details including username and password"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    data = request.get_json()
    
    # Update username (with uniqueness check)
    if 'username' in data and data['username'] != doctor.username:
        existing = User.query.filter_by(username=data['username']).first()
        if existing:
            return jsonify({'error': 'Username already exists'}), 400
        doctor.username = data['username']
    
    # Update email (with uniqueness check)
    if 'email' in data and data['email'] != doctor.email:
        existing = User.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({'error': 'Email already exists'}), 400
        doctor.email = data['email']
    
    # Update password if provided
    if 'password' in data and data['password']:
        doctor.set_password(data['password'])
    
    # Update other fields
    if 'full_name' in data:
        doctor.full_name = data['full_name']
    if 'phone' in data:
        doctor.phone = data['phone']
    if 'specialization_id' in data:
        doctor.specialization_id = data['specialization_id']
    if 'qualification' in data:
        doctor.qualification = data['qualification']
    if 'experience_years' in data:
        doctor.experience_years = data['experience_years']
    if 'consultation_fee' in data:
        doctor.consultation_fee = data['consultation_fee']
    if 'is_active' in data:
        doctor.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Doctor updated successfully',
        'doctor': doctor.to_dict()
    }), 200


@bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_doctor(doctor_id):
    """Delete/Blacklist doctor"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Soft delete - just deactivate
    doctor.is_active = False
    db.session.commit()
    
    # Clear cache
    cache.delete('admin_dashboard')
    
    return jsonify({'message': 'Doctor deactivated successfully'}), 200


# ==================== PATIENT MANAGEMENT ====================

@bp.route('/patients', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_patients():
    """Get all patients with optional search"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = User.query.filter_by(role='patient')
    
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.phone.ilike(f'%{search}%')
            )
        )
    
    patients = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'patients': [patient.to_dict() for patient in patients.items],
        'total': patients.total,
        'pages': patients.pages,
        'current_page': page
    }), 200


@bp.route('/patients/<int:patient_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_patient(patient_id):
    """Get specific patient details"""
    patient = User.query.filter_by(id=patient_id, role='patient').first()
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get patient's appointments
    appointments = patient.patient_appointments.order_by(
        Appointment.appointment_date.desc()
    ).limit(10).all()
    
    patient_data = patient.to_dict()
    patient_data['recent_appointments'] = [apt.to_dict() for apt in appointments]
    
    return jsonify(patient_data), 200


@bp.route('/patients/<int:patient_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_patient(patient_id):
    """Admin can update all patient details including username and password"""
    patient = User.query.filter_by(id=patient_id, role='patient').first()
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.get_json()
    
    # Update username (with uniqueness check)
    if 'username' in data and data['username'] != patient.username:
        existing = User.query.filter_by(username=data['username']).first()
        if existing:
            return jsonify({'error': 'Username already exists'}), 400
        patient.username = data['username']
    
    # Update email (with uniqueness check)
    if 'email' in data and data['email'] != patient.email:
        existing = User.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({'error': 'Email already exists'}), 400
        patient.email = data['email']
    
    # Update password if provided
    if 'password' in data and data['password']:
        patient.set_password(data['password'])
    
    # Update other fields
    if 'full_name' in data:
        patient.full_name = data['full_name']
    if 'phone' in data:
        patient.phone = data['phone']
    if 'is_active' in data:
        patient.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Patient updated successfully',
        'patient': patient.to_dict()
    }), 200


@bp.route('/patients/<int:patient_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_patient(patient_id):
    """Delete/Blacklist patient"""
    patient = User.query.filter_by(id=patient_id, role='patient').first()
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Soft delete
    patient.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Patient deactivated successfully'}), 200


# ==================== APPOINTMENT MANAGEMENT ====================

@bp.route('/appointments', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_all_appointments():
    """Get all appointments with filters"""
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Appointment.query
    
    if status:
        query = query.filter_by(status=status)
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'appointments': [apt.to_dict() for apt in appointments.items],
        'total': appointments.total,
        'pages': appointments.pages,
        'current_page': page
    }), 200


# ==================== SEARCH FUNCTIONALITY ====================

@bp.route('/search', methods=['GET'])
@jwt_required()
@role_required('admin')
def search():
    """Global search for doctors, patients, and appointments"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    results = {}
    
    if search_type in ['all', 'doctor']:
        doctors = User.query.filter(
            User.role == 'doctor',
            or_(
                User.full_name.ilike(f'%{query}%'),
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(10).all()
        results['doctors'] = [doc.to_dict() for doc in doctors]
    
    if search_type in ['all', 'patient']:
        patients = User.query.filter(
            User.role == 'patient',
            or_(
                User.full_name.ilike(f'%{query}%'),
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.phone.ilike(f'%{query}%')
            )
        ).limit(10).all()
        results['patients'] = [pat.to_dict() for pat in patients]
    
    return jsonify(results), 200

# ==================== APPOINTMENT MANAGEMENT ====================

@bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_appointment(appointment_id):
    """Admin can update appointment details"""
    data = request.get_json()
    
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Update fields
    if 'appointment_date' in data:
        try:
            appointment.appointment_date = datetime.strptime(
                data['appointment_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    if 'appointment_time' in data:
        try:
            time_str = str(data['appointment_time'])
            # Handle both HH:MM and HH:MM:SS formats
            if len(time_str) <= 5:  # HH:MM
                appointment.appointment_time = datetime.strptime(time_str, '%H:%M').time()
            else:  # HH:MM:SS
                appointment.appointment_time = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
    
    if 'status' in data:
        if data['status'] not in ['booked', 'completed', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400
        appointment.status = data['status']
    
    if 'reason' in data:
        appointment.reason = data['reason']
    
    # Update timestamp
    appointment.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Clear cache
    cache.delete('admin_dashboard')
    
    return jsonify({
        'message': 'Appointment updated successfully',
        'appointment': appointment.to_dict()
    }), 200

# ==================== DOCTOR AVAILABILITY MANAGEMENT (ADMIN) ====================

@bp.route('/doctors/<int:doctor_id>/availability', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_doctor_availability_admin(doctor_id):
    """Admin can view doctor's availability"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= week_later
    ).order_by(DoctorAvailability.date.asc()).all()
    
    return jsonify({
        'doctor': doctor.to_dict(),
        'availability': [avail.to_dict() for avail in availability]
    }), 200


@bp.route('/doctors/<int:doctor_id>/availability', methods=['POST'])
@jwt_required()
@role_required('admin')
def set_doctor_availability_admin(doctor_id):
    """Admin can set/update doctor's availability"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    data = request.get_json()
    
    if not data.get('date'):
        return jsonify({'error': 'Date is required'}), 400
    
    if not validate_date(data['date']):
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
    
    if not data.get('start_time') or not data.get('end_time'):
        return jsonify({'error': 'Start time and end time are required'}), 400
    
    if not validate_time(data['start_time']) or not validate_time(data['end_time']):
        return jsonify({'error': 'Invalid time format (use HH:MM)'}), 400
    
    avail_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    
    # Check if availability already exists
    existing = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        date=avail_date
    ).first()
    
    if existing:
        # Update existing
        existing.start_time = start_time
        existing.end_time = end_time
        existing.is_available = data.get('is_available', True)
        message = 'Availability updated successfully'
    else:
        # Create new
        availability = DoctorAvailability(
            doctor_id=doctor_id,
            date=avail_date,
            start_time=start_time,
            end_time=end_time,
            is_available=data.get('is_available', True)
        )
        db.session.add(availability)
        message = 'Availability set successfully'
    
    db.session.commit()
    
    return jsonify({'message': message}), 201


@bp.route('/doctors/<int:doctor_id>/availability/<int:avail_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_doctor_availability_admin(doctor_id, avail_id):
    """Admin can delete doctor's availability slot"""
    availability = DoctorAvailability.query.filter_by(
        id=avail_id,
        doctor_id=doctor_id
    ).first()
    
    if not availability:
        return jsonify({'error': 'Availability not found'}), 404
    
    db.session.delete(availability)
    db.session.commit()
    
    return jsonify({'message': 'Availability deleted successfully'}), 200

# ==================== PERMANENT DELETE WITH CASCADE ====================

@bp.route('/doctors/<int:doctor_id>/permanent', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def permanent_delete_doctor(doctor_id):
    """Permanently delete doctor from database with cascading"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    try:
        # Delete all appointments for this doctor (CASCADE will handle treatments)
        Appointment.query.filter_by(doctor_id=doctor_id).delete()
        
        # Delete doctor availability
        DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()
        
        # Delete the doctor
        db.session.delete(doctor)
        db.session.commit()
        
        cache.delete('admin_dashboard')
        
        return jsonify({'message': 'Doctor and all related data permanently deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete: {str(e)}'}), 500


@bp.route('/patients/<int:patient_id>/permanent', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def permanent_delete_patient(patient_id):
    """Permanently delete patient from database with cascading"""
    patient = User.query.filter_by(id=patient_id, role='patient').first()
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    try:
        # Delete all appointments for this patient (CASCADE will handle treatments)
        Appointment.query.filter_by(patient_id=patient_id).delete()
        
        # Delete the patient
        db.session.delete(patient)
        db.session.commit()
        
        cache.delete('admin_dashboard')
        
        return jsonify({'message': 'Patient and all related data permanently deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete: {str(e)}'}), 500


@bp.route('/departments/<int:dept_id>/permanent', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def permanent_delete_department(dept_id):
    """Permanently delete department with cascading delete of doctors and their data"""
    department = Department.query.get(dept_id)
    
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    try:
        # Get all doctors in this department
        doctors = User.query.filter_by(role='doctor', specialization_id=dept_id).all()
        
        # Delete all related data for each doctor
        for doctor in doctors:
            # Delete appointments (CASCADE will handle treatments)
            Appointment.query.filter_by(doctor_id=doctor.id).delete()
            # Delete availability
            DoctorAvailability.query.filter_by(doctor_id=doctor.id).delete()
            # Delete doctor
            db.session.delete(doctor)
        
        # Delete the department
        db.session.delete(department)
        db.session.commit()
        
        cache.delete('admin_dashboard')
        cache.delete('all_departments')
        
        return jsonify({'message': 'Department and all related data permanently deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete: {str(e)}'}), 500