from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import User, Appointment, Treatment, DoctorAvailability
from app.models.availability import DoctorAvailability
from app.utils.decorators import role_required, get_current_user
from app.utils.validators import validate_date, validate_time
from datetime import datetime, date, time, timedelta
from sqlalchemy import and_

bp = Blueprint('doctor', __name__, url_prefix='/api/doctor')

# ==================== DASHBOARD ====================

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required('doctor')
def dashboard():
    """Doctor's dashboard with upcoming appointments and statistics"""
    doctor = get_current_user()
    
    # Get today's date
    today = date.today()
    week_later = today + timedelta(days=7)
    
    # Upcoming appointments (next 7 days)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week_later,
        Appointment.status == 'booked'
    ).order_by(
        Appointment.appointment_date.asc(),
        Appointment.appointment_time.asc()
    ).all()
    
    # Today's appointments
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == today,
        Appointment.status.in_(['booked', 'completed'])
    ).order_by(Appointment.appointment_time.asc()).all()
    
    # Statistics
    total_appointments = Appointment.query.filter_by(doctor_id=doctor.id).count()
    completed = Appointment.query.filter_by(doctor_id=doctor.id, status='completed').count()
    pending = Appointment.query.filter_by(doctor_id=doctor.id, status='booked').count()
    
    # Get all patients assigned to this doctor
    patient_ids = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().all()
    total_patients = len(patient_ids)
    
    return jsonify({
        'doctor_info': doctor.to_dict(),
        'statistics': {
            'total_appointments': total_appointments,
            'completed_appointments': completed,
            'pending_appointments': pending,
            'total_patients': total_patients
        },
        'today_appointments': [apt.to_dict() for apt in today_appointments],
        'upcoming_appointments': [apt.to_dict() for apt in upcoming_appointments]
    }), 200


@bp.route('/statistics/performance', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_performance_statistics():
    """Get doctor's performance statistics"""
    doctor = get_current_user()
    
    # Get today's date
    today = date.today()
    week_start = today - timedelta(days=7)
    
    # This week statistics
    week_completed = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= week_start,
        Appointment.status == 'completed'
    ).count()
    
    week_cancelled = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= week_start,
        Appointment.status == 'cancelled'
    ).count()
    
    # Lifetime statistics
    lifetime_completed = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'completed'
    ).count()
    
    lifetime_cancelled = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'cancelled'
    ).count()
    
    return jsonify({
        'this_week': {
            'completed': week_completed,
            'cancelled': week_cancelled
        },
        'lifetime': {
            'completed': lifetime_completed,
            'cancelled': lifetime_cancelled
        }
    }), 200

# ==================== AVAILABILITY ====================

@bp.route('/doctor/availability', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_doctor_availability():   # ======== Dead Code ========
    doctor_id = get_jwt_identity()
    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
    output = {}
    for avail in availabilities:
        date = avail.date.isoformat()
        slot = f"{avail.starttime.strftime('%H:%M')}-{avail.endtime.strftime('%H:%M')}"
        if date not in output:
            output[date] = []
        output[date].append(slot)
    response = [{"date": d, "slots": s} for d, s in output.items()]
    return jsonify(response)

# ==================== APPOINTMENTS ====================

@bp.route('/appointments', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_appointments():
    """Get all appointments for the doctor with filters"""
    doctor = get_current_user()
    
    status = request.args.get('status')
    date_filter = request.args.get('date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Appointment.query.filter_by(doctor_id=doctor.id)
    
    if status:
        query = query.filter_by(status=status)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=filter_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
    
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


@bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_appointment(appointment_id):
    """Get specific appointment details"""
    doctor = get_current_user()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    apt_data = appointment.to_dict()
    
    # Include patient details
    apt_data['patient_details'] = appointment.patient.to_dict()
    
    # Include treatment if exists
    if appointment.treatment:
        apt_data['treatment'] = appointment.treatment.to_dict()
    
    return jsonify(apt_data), 200


@bp.route('/appointments/<int:appointment_id>/complete', methods=['POST'])
@jwt_required()
@role_required('doctor')
def complete_appointment(appointment_id):
    """Mark appointment as completed"""
    doctor = get_current_user()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    if appointment.status == 'completed':
        return jsonify({'error': 'Appointment already completed'}), 400
    
    if appointment.status == 'cancelled':
        return jsonify({'error': 'Cannot complete a cancelled appointment'}), 400
    
    appointment.status = 'completed'
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment marked as completed',
        'appointment': appointment.to_dict()
    }), 200


@bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@jwt_required()
@role_required('doctor')
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    doctor = get_current_user()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    if appointment.status == 'completed':
        return jsonify({'error': 'Cannot cancel a completed appointment'}), 400
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment cancelled',
        'appointment': appointment.to_dict()
    }), 200


# ==================== TREATMENTS ====================

@bp.route('/appointments/<int:appointment_id>/treatment', methods=['POST'])
@jwt_required()
@role_required('doctor')
def add_treatment(appointment_id):
    """Add or update treatment for an appointment"""
    doctor = get_current_user()
    data = request.get_json()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    if not data.get('diagnosis'):
        return jsonify({'error': 'Diagnosis is required'}), 400
    
    # Check and update 
    if appointment.treatment:
        treatment = appointment.treatment
        treatment.diagnosis = data['diagnosis']
        treatment.prescription = data.get('prescription', '')
        treatment.notes = data.get('notes', '')
        
        if data.get('next_visit_date'):
            try:
                treatment.next_visit_date = datetime.strptime(
                    data['next_visit_date'], '%Y-%m-%d'
                ).date()
            except ValueError:
                return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
        
        message = 'Treatment updated successfully'
    else:
        treatment = Treatment(
            appointment_id=appointment_id,
            diagnosis=data['diagnosis'],
            prescription=data.get('prescription', ''),
            notes=data.get('notes', '')
        )
        
        if data.get('next_visit_date'):
            try:
                treatment.next_visit_date = datetime.strptime(
                    data['next_visit_date'], '%Y-%m-%d'
                ).date()
            except ValueError:
                return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
        
        db.session.add(treatment)
        message = 'Treatment added successfully'
    
    if appointment.status != 'completed':
        appointment.status = 'completed'
    
    db.session.commit()
    
    return jsonify({
        'message': message,
        'treatment': treatment.to_dict()
    }), 201 if not appointment.treatment else 200


@bp.route('/appointments/<int:appointment_id>/treatment', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_treatment(appointment_id):
    """Get treatment for an appointment"""
    doctor = get_current_user()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    if not appointment.treatment:
        return jsonify({'error': 'No treatment found for this appointment'}), 404
    
    return jsonify(appointment.treatment.to_dict()), 200


# ==================== PATIENTS ====================

@bp.route('/patients', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_patients():
    """Get all patients assigned to this doctor"""
    doctor = get_current_user()
    
    patient_ids = db.session.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().all()
    
    patient_ids = [pid[0] for pid in patient_ids]
    patients = User.query.filter(User.id.in_(patient_ids)).all()
    
    patients_data = []
    for patient in patients:
        patient_info = patient.to_dict()
        
        apt_count = Appointment.query.filter_by(
            patient_id=patient.id,
            doctor_id=doctor.id
        ).count()
        
        patient_info['appointment_count'] = apt_count
        patients_data.append(patient_info)
    
    return jsonify({'patients': patients_data}), 200


@bp.route('/patients/<int:patient_id>/history', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_patient_history(patient_id):
    """Get patient's treatment history with this doctor"""
    doctor = get_current_user()
    
    patient = User.query.filter_by(id=patient_id, role='patient').first()
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=doctor.id,
        status='completed'
    ).order_by(Appointment.appointment_date.desc()).all()
    
    history = []
    for apt in appointments:
        apt_data = apt.to_dict()
        if apt.treatment:
            apt_data['treatment'] = apt.treatment.to_dict()
        history.append(apt_data)
    
    return jsonify({
        'patient': patient.to_dict(),
        'history': history
    }), 200


# ==================== AVAILABILITY ====================

@bp.route('/availability', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_availability():
    """Get doctor's availability for next 7 days"""
    doctor = get_current_user()
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= week_later
    ).order_by(DoctorAvailability.date.asc()).all()
    
    return jsonify({
        'availability': [avail.to_dict() for avail in availability]
    }), 200


@bp.route('/availability', methods=['POST'])
@jwt_required()
@role_required('doctor')
def set_availability():
    """Set availability for specific date (create or update) with lunch break support"""
    doctor = get_current_user()
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
    
    lunch_break_start = None
    lunch_break_end = None
    
    if data.get('lunch_break_start') and data.get('lunch_break_end'):
        if validate_time(data['lunch_break_start']) and validate_time(data['lunch_break_end']):
            lunch_break_start = datetime.strptime(data['lunch_break_start'], '%H:%M').time()
            lunch_break_end = datetime.strptime(data['lunch_break_end'], '%H:%M').time()
            
            if lunch_break_start < start_time or lunch_break_end > end_time:
                return jsonify({'error': 'Lunch break must be within working hours'}), 400
            
            if lunch_break_start >= lunch_break_end:
                return jsonify({'error': 'Lunch break start must be before end time'}), 400
    
    existing = DoctorAvailability.query.filter_by(
        doctor_id=doctor.id,
        date=avail_date
    ).first()
    
    if existing:
        existing.start_time = start_time
        existing.end_time = end_time
        existing.is_available = data.get('is_available', True)
        existing.lunch_break_start = lunch_break_start
        existing.lunch_break_end = lunch_break_end
        message = 'Availability updated successfully'
    else:
        availability = DoctorAvailability(
            doctor_id=doctor.id,
            date=avail_date,
            start_time=start_time,
            end_time=end_time,
            is_available=data.get('is_available', True),
            lunch_break_start=lunch_break_start,
            lunch_break_end=lunch_break_end
        )
        db.session.add(availability)
        message = 'Availability set successfully'
    
    db.session.commit()
    
    return jsonify({'message': message}), 201


@bp.route('/availability/bulk', methods=['POST'])
@jwt_required()
@role_required('doctor')
def set_bulk_availability():
    """Set availability for multiple dates (next 7 days)"""
    doctor = get_current_user()
    data = request.get_json()
    
    if not data.get('start_time') or not data.get('end_time'):
        return jsonify({'error': 'Start time and end time are required'}), 400
    
    if not validate_time(data['start_time']) or not validate_time(data['end_time']):
        return jsonify({'error': 'Invalid time format (use HH:MM)'}), 400
    
    start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    
    # Set for next 7 days
    today = date.today()
    created_count = 0
    
    for i in range(7):
        avail_date = today + timedelta(days=i)
        
        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            date=avail_date
        ).first()
        
        if not existing:
            availability = DoctorAvailability(
                doctor_id=doctor.id,
                date=avail_date,
                start_time=start_time,
                end_time=end_time,
                is_available=True
            )
            db.session.add(availability)
            created_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'Availability set for {created_count} days'
    }), 201


# ==================== Availability CRUD Operations ====================

@bp.route('/availability/<int:avail_id>', methods=['DELETE'])
@jwt_required()
@role_required('doctor')
def delete_availability(avail_id):
    """Delete specific availability slot"""
    doctor = get_current_user()
    
    availability = DoctorAvailability.query.filter_by(
        id=avail_id,
        doctor_id=doctor.id
    ).first()
    
    if not availability:
        return jsonify({'error': 'Availability not found'}), 404
    
    db.session.delete(availability)
    db.session.commit()
    
    return jsonify({'message': 'Availability deleted successfully'}), 200


@bp.route('/availability/<int:avail_id>', methods=['PUT'])
@jwt_required()
@role_required('doctor')
def update_availability(avail_id):
    """Update specific availability slot"""
    doctor = get_current_user()
    data = request.get_json()
    
    availability = DoctorAvailability.query.filter_by(
        id=avail_id,
        doctor_id=doctor.id
    ).first()
    
    if not availability:
        return jsonify({'error': 'Availability not found'}), 404
    
    if 'start_time' in data:
        if not validate_time(data['start_time']):
            return jsonify({'error': 'Invalid start time format (use HH:MM)'}), 400
        availability.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    
    if 'end_time' in data:
        if not validate_time(data['end_time']):
            return jsonify({'error': 'Invalid end time format (use HH:MM)'}), 400
        availability.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    
    if 'is_available' in data:
        availability.is_available = bool(data['is_available'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Availability updated successfully',
        'availability': availability.to_dict()
    }), 200

@bp.route('/availability/<int:avail_id>', methods=['GET'])
@jwt_required()
@role_required('doctor')
def get_availability_slot(avail_id):
    """Get specific availability slot details"""
    doctor = get_current_user()
    
    availability = DoctorAvailability.query.filter_by(
        id=avail_id,
        doctor_id=doctor.id
    ).first()
    
    if not availability:
        return jsonify({'error': 'Availability not found'}), 404
    
    return jsonify(availability.to_dict()), 200

# ==================== Add Patient History Without Appointment ====================

@bp.route('/patients/<int:patient_id>/history/add', methods=['POST'])
@jwt_required()
@role_required('doctor')
def add_patient_history(patient_id):
    """Add treatment history entry without requiring an appointment"""
    doctor = get_current_user()
    data = request.get_json()
    
    # Verify patient exists
    patient = User.query.filter_by(id=patient_id, role='patient').first()
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    if not data.get('diagnosis'):
        return jsonify({'error': 'Diagnosis is required'}), 400
    
    if not data.get('visit_date'):
        return jsonify({'error': 'Visit date is required'}), 400
    
    try:
        visit_date = datetime.strptime(data['visit_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
    
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor.id,
        appointment_date=visit_date,
        appointment_time=datetime.now().time(),
        status='completed',
        reason=data.get('notes', 'Follow-up consultation')[:50]
    )
    
    db.session.add(appointment)
    db.session.flush()  
    
    treatment = Treatment(
        appointment_id=appointment.id,
        diagnosis=data['diagnosis'],
        prescription=data.get('prescription', ''),
        notes=data.get('notes', '')
    )
    
    if data.get('tests'):
        treatment.notes += f"\n\nLab Tests: {data['tests']}"
    
    if data.get('next_visit'):
        try:
            treatment.next_visit_date = datetime.strptime(
                data['next_visit'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    db.session.add(treatment)
    db.session.commit()
    
    return jsonify({
        'message': 'Patient history updated successfully',
        'treatment': treatment.to_dict()
    }), 201
