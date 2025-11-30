from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app import cache
from app.models import User, Department, Appointment, DoctorAvailability
from app.utils.decorators import role_required, get_current_user
from app.utils.validators import validate_date, validate_time
from datetime import datetime, date, time, timedelta
from sqlalchemy import and_, or_
from app.tasks.booking_notifications import send_booking_confirmation, send_pre_appointment_reminder
import logging
logger = logging.getLogger(__name__)

bp = Blueprint('patient', __name__, url_prefix='/api/patient')

# ==================== DASHBOARD ====================

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required('patient')
def dashboard():
    """Patient's dashboard with appointments and departments"""
    patient = get_current_user()
    
    # Get all departments
    departments = Department.query.all()
    
    # Get upcoming appointments
    today = date.today()
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= today,
        Appointment.status == 'booked'
    ).order_by(
        Appointment.appointment_date.asc(),
        Appointment.appointment_time.asc()
    ).limit(5).all()
    
    # Get recent completed appointments
    recent_completed = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.status == 'completed'
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()
    
    return jsonify({
        'patient_info': patient.to_dict(),
        'departments': [dept.to_dict() for dept in departments],
        'upcoming_appointments': [apt.to_dict() for apt in upcoming_appointments],
        'recent_completed': [apt.to_dict() for apt in recent_completed]
    }), 200


# ==================== PROFILE ====================

@bp.route('/profile', methods=['GET'])
@jwt_required()
@role_required('patient')
def get_profile():
    """Get patient profile"""
    patient = get_current_user()
    return jsonify(patient.to_dict()), 200


@bp.route('/profile', methods=['PUT'])
@jwt_required()
@role_required('patient')
def update_profile():
    """Update patient profile"""
    patient = get_current_user()
    data = request.get_json()
    
    from app.utils.validators import validate_email, validate_phone
    
    # Update allowed fields
    if 'full_name' in data:
        patient.full_name = data['full_name']
    
    if 'email' in data:
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        # Check if email is taken
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != patient.id:
            return jsonify({'error': 'Email already exists'}), 400
        patient.email = data['email']
    
    if 'phone' in data:
        if not validate_phone(data['phone']):
            return jsonify({'error': 'Invalid phone number'}), 400
        patient.phone = data['phone']
    
    if 'address' in data:
        patient.address = data['address']
    
    if 'gender' in data:
        patient.gender = data['gender']
    
    if 'date_of_birth' in data:
        try:
            patient.date_of_birth = datetime.strptime(
                data['date_of_birth'], '%Y-%m-%d'
            ).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'patient': patient.to_dict()
    }), 200

# Change password
@bp.route('/change-password', methods=['POST'])
@jwt_required()
@role_required('patient')
def change_password():
    """Change patient password"""
    patient = get_current_user()
    data = request.get_json()
    
    if not data.get('current_password'):
        return jsonify({'error': 'Current password is required'}), 400
    
    if not data.get('new_password'):
        return jsonify({'error': 'New password is required'}), 400
    
    # Verify current password
    if not patient.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    # Validate new password
    if len(data['new_password']) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    if data['current_password'] == data['new_password']:
        return jsonify({'error': 'New password must be different from current password'}), 400
    
    # Update password
    patient.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200

# ==================== DEPARTMENTS ====================

@bp.route('/departments', methods=['GET'])
@jwt_required()
@role_required('patient')
@cache.cached(timeout=300, key_prefix='all_departments')  # Cache for 5 minutes
def get_departments():
    """Get all departments/specializations"""
    departments = Department.query.all()
    
    dept_data = []
    for dept in departments:
        dept_info = dept.to_dict()
        dept_info['available_doctors'] = User.query.filter_by(
            specialization_id=dept.id,
            role='doctor',
            is_active=True
        ).count()
        dept_data.append(dept_info)
    
    return jsonify({'departments': dept_data, 'cached': True}), 200


# ==================== DOCTORS ====================

@bp.route('/doctors', methods=['GET'])
@jwt_required()
@role_required('patient')
def search_doctors():
    """Search doctors by specialization or name"""
    specialization_id = request.args.get('specialization_id', type=int)
    search = request.args.get('search', '')
    
    query = User.query.filter_by(role='doctor', is_active=True)
    
    if specialization_id:
        query = query.filter_by(specialization_id=specialization_id)
    
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%')
            )
        )
    
    doctors = query.all()
    
    # availability info
    today = date.today()
    week_later = today + timedelta(days=7)
    
    doctors_data = []
    for doctor in doctors:
        doctor_info = doctor.to_dict()
        
        availability = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date >= today,
            DoctorAvailability.date <= week_later,
            DoctorAvailability.is_available == True
        ).order_by(DoctorAvailability.date.asc()).all()
        
        doctor_info['availability'] = [avail.to_dict() for avail in availability]
        doctors_data.append(doctor_info)
    
    return jsonify({'doctors': doctors_data}), 200


@bp.route('/doctors/<int:doctor_id>', methods=['GET'])
@jwt_required()
@role_required('patient')
def get_doctor_details(doctor_id):
    """Get doctor details and availability"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor', is_active=True).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    doctor_info = doctor.to_dict()
    
    today = date.today()
    week_later = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date >= today,
        DoctorAvailability.date <= week_later,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.date.asc()).all()
    
    doctor_info['availability'] = [avail.to_dict() for avail in availability]
    
    # booked slots for conflict checking
    booked_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week_later,
        Appointment.status == 'booked'
    ).all()
    
    doctor_info['booked_slots'] = [
        {
            'date': apt.appointment_date.isoformat(),
            'time': apt.appointment_time.strftime('%H:%M')
        }
        for apt in booked_appointments
    ]
    
    return jsonify(doctor_info), 200

# Get booked slots for time slot availability check
@bp.route('/booked-slots', methods=['GET'])
@jwt_required()
@role_required('patient')
def get_booked_slots():
    """Get booked time slots for a specific doctor and date"""
    doctor_id = request.args.get('doctor_id', type=int)
    date_str = request.args.get('date')
    
    if not doctor_id or not date_str:
        return jsonify({'error': 'doctor_id and date are required'}), 400
    
    try:
        from datetime import datetime
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all booked appointments for this doctor and date
        booked_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            status='booked'
        ).all()
        
        # Extract just the time strings
        booked_slots = [apt.appointment_time.strftime('%H:%M') for apt in booked_appointments]
        
        return jsonify({
            'booked_slots': booked_slots,
            'total_booked': len(booked_slots)
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
# ==================== APPOINTMENTS ====================

@bp.route('/appointments', methods=['GET'])
@jwt_required()
@role_required('patient')
def get_appointments():
    """Get all patient's appointments"""
    patient = get_current_user()
    
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Appointment.query.filter_by(patient_id=patient.id)
    
    if status:
        query = query.filter_by(status=status)
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Include treatment details for completed appointments
    appointments_data = []
    for apt in appointments.items:
        apt_data = apt.to_dict()
        if apt.treatment:
            apt_data['treatment'] = apt.treatment.to_dict()
        appointments_data.append(apt_data)
    
    return jsonify({
        'appointments': appointments_data,
        'total': appointments.total,
        'pages': appointments.pages,
        'current_page': page
    }), 200


# Book appointment with payment details
@bp.route('/appointments', methods=['POST'])
@jwt_required()
@role_required('patient')
def book_appointment():
    patient = get_current_user()
    data = request.get_json()
    
    # required fields
    if not data.get('doctor_id'):
        return jsonify({'error': 'Doctor ID is required'}), 400
    
    if not data.get('appointment_date'):
        return jsonify({'error': 'Appointment date is required'}), 400
    
    if not data.get('appointment_time'):
        return jsonify({'error': 'Appointment time is required'}), 400
    
    # formats
    if not validate_date(data['appointment_date']):
        return jsonify({'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
    
    if not validate_time(data['appointment_time']):
        return jsonify({'error': 'Invalid time format (use HH:MM)'}), 400
    
    # Parse date and time
    apt_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    apt_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    
    # date is in the past
    if apt_date < date.today():
        return jsonify({'error': 'Cannot book appointment in the past'}), 400
    
    # doctor exists and is active
    doctor = User.query.filter_by(
        id=data['doctor_id'],
        role='doctor',
        is_active=True
    ).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found or inactive'}), 404
    
    # doctor is available on that date
    availability = DoctorAvailability.query.filter_by(
        doctor_id=data['doctor_id'],
        date=apt_date,
        is_available=True
    ).first()
    
    if not availability:
        return jsonify({'error': 'Doctor is not available on this date'}), 400
    
    # time is within doctor's availability
    if apt_time < availability.start_time or apt_time >= availability.end_time:
        return jsonify({
            'error': f'Time must be between {availability.start_time.strftime("%H:%M")} and {availability.end_time.strftime("%H:%M")}'
        }), 400
    
    # time is during lunch break
    if availability.lunch_break_start and availability.lunch_break_end:
        if apt_time >= availability.lunch_break_start and apt_time < availability.lunch_break_end:
            return jsonify({
                'error': f'This time is during lunch break ({availability.lunch_break_start.strftime("%H:%M")} - {availability.lunch_break_end.strftime("%H:%M")})'
            }), 400
    
    # appointment conflicts (same doctor, date, time)
    conflict = Appointment.query.filter_by(
        doctor_id=data['doctor_id'],
        appointment_date=apt_date,
        appointment_time=apt_time,
        status='booked'
    ).first()
    
    if conflict:
        return jsonify({
            'error': 'This time slot is already booked. Please choose another time.'
        }), 409
    
    # 10-minute slot limit 6 per hour
    # Get the hour of the appointment
    apt_hour = apt_time.hour
    
    # Count existing appointments in this hour
    hour_start = datetime.combine(apt_date, datetime.min.time().replace(hour=apt_hour))
    hour_end = datetime.combine(apt_date, datetime.min.time().replace(hour=apt_hour, minute=59, second=59))
    
    hour_appointments = Appointment.query.filter(
        Appointment.doctor_id == data['doctor_id'],
        Appointment.appointment_date == apt_date,
        Appointment.appointment_time >= hour_start.time(),
        Appointment.appointment_time <= hour_end.time(),
        Appointment.status == 'booked'
    ).count()
    
    if hour_appointments >= 6:
        return jsonify({
            'error': 'Maximum appointments per hour (6) reached. Please select a different time.'
        }), 400
    
    # Create appointment with payment info
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=data['doctor_id'],
        appointment_date=apt_date,
        appointment_time=apt_time,
        reason=data.get('reason', ''),
        status='booked',
        consultation_fee=data.get('consultation_fee', doctor.consultation_fee or 500),
        payment_status=data.get('payment_status', 'paid'),
        payment_method=data.get('payment_method', 'card'),
        transaction_id=f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{patient.id}"
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    # Send immediate booking confirmation
    try:
        send_booking_confirmation(appointment)
        logger.info(f"Booking confirmation sent for appointment #{appointment.id}")
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {str(e)}")
        # Don't fail the booking if notification fails
    
    # Schedule 30-minute reminder
    try:
        # Calculate reminder time (30 minutes before appointment)
        appointment_datetime = datetime.combine(apt_date, apt_time)
        reminder_time = appointment_datetime - timedelta(minutes=30)
        
        # Only schedule if appointment is in the future
        if reminder_time > datetime.now():
            send_pre_appointment_reminder.apply_async(
                args=[appointment.id],
                eta=reminder_time
            )
            logger.info(f"Scheduled reminder for appointment #{appointment.id} at {reminder_time}")
    except Exception as e:
        logger.error(f"Failed to schedule reminder: {str(e)}")
    
    return jsonify({
        'message': 'Appointment booked successfully',
        'appointment': appointment.to_dict(),
        'payment_confirmed': True,
        'notifications': {
            'confirmation_sent': True,
            'reminder_scheduled': True
        }
    }), 201


@bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
@role_required('patient')
def get_appointment(appointment_id):
    """Get specific appointment details"""
    patient = get_current_user()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    apt_data = appointment.to_dict()
    apt_data['doctor_details'] = appointment.doctor.to_dict()
    
    if appointment.treatment:
        apt_data['treatment'] = appointment.treatment.to_dict()
    
    return jsonify(apt_data), 200


@bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@jwt_required()
@role_required('patient')
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    patient = get_current_user()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    if appointment.status == 'completed':
        return jsonify({'error': 'Cannot cancel a completed appointment'}), 400
    
    if appointment.status == 'cancelled':
        return jsonify({'error': 'Appointment is already cancelled'}), 400
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment cancelled successfully',
        'appointment': appointment.to_dict()
    }), 200


@bp.route('/appointments/<int:appointment_id>/reschedule', methods=['PUT'])
@jwt_required()
@role_required('patient')
def reschedule_appointment(appointment_id):
    """Reschedule an appointment"""
    patient = get_current_user()
    data = request.get_json()
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    if appointment.status != 'booked':
        return jsonify({'error': 'Can only reschedule booked appointments'}), 400
    
    if not data.get('appointment_date') or not data.get('appointment_time'):
        return jsonify({'error': 'New date and time are required'}), 400
    
    # Validate formats
    if not validate_date(data['appointment_date']) or not validate_time(data['appointment_time']):
        return jsonify({'error': 'Invalid date or time format'}), 400
    
    new_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    new_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    
    # Check if date is in the past
    if new_date < date.today():
        return jsonify({'error': 'Cannot reschedule to a past date'}), 400
    
    # Check availability
    availability = DoctorAvailability.query.filter_by(
        doctor_id=appointment.doctor_id,
        date=new_date,
        is_available=True
    ).first()
    
    if not availability:
        return jsonify({'error': 'Doctor is not available on this date'}), 400
    
    # Check for conflicts
    conflict = Appointment.query.filter(
        Appointment.id != appointment_id,
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == new_date,
        Appointment.appointment_time == new_time,
        Appointment.status == 'booked'
    ).first()
    
    if conflict:
        return jsonify({'error': 'This time slot is already booked'}), 409
    
    # Update appointment
    appointment.appointment_date = new_date
    appointment.appointment_time = new_time
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment rescheduled successfully',
        'appointment': appointment.to_dict()
    }), 200


# ==================== TREATMENT HISTORY ====================

@bp.route('/history', methods=['GET'])
@jwt_required()
@role_required('patient')
def get_treatment_history():
    """Get patient's complete treatment history"""
    patient = get_current_user()
    
    # Get all completed appointments with treatments
    appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='completed'
    ).order_by(Appointment.appointment_date.desc()).all()
    
    history = []
    for apt in appointments:
        apt_data = apt.to_dict()
        apt_data['doctor_details'] = {
            'name': apt.doctor.full_name,
            'specialization': apt.doctor.specialization.name if apt.doctor.specialization else None
        }
        
        if apt.treatment:
            apt_data['treatment'] = apt.treatment.to_dict()
        
        history.append(apt_data)
    
    return jsonify({
        'total_visits': len(history),
        'history': history
    }), 200

# ==================== CSV EXPORT ====================

@bp.route('/export-history', methods=['GET'])
@jwt_required()
@role_required('patient')
def export_history_sync():
    """Synchronous CSV export (no Celery required)"""
    patient = get_current_user()
    
    try:
        # Get completed appointments with treatments
        appointments = Appointment.query.filter_by(
            patient_id=patient.id,
            status='completed'
        ).order_by(Appointment.appointment_date.desc()).all()
        
        if not appointments:
            return jsonify({'error': 'No treatment history to export'}), 404
        
        # Create CSV in memory
        import io
        import csv
        
        output = io.StringIO()
        fieldnames = [
            'Appointment Date',
            'Appointment Time', 
            'Doctor Name',
            'Specialization',
            'Diagnosis',
            'Prescription',
            'Treatment Notes',
            'Next Visit Date'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for apt in appointments:
            if apt.treatment:
                writer.writerow({
                    'Appointment Date': apt.appointment_date.strftime('%Y-%m-%d'),
                    'Appointment Time': apt.appointment_time.strftime('%H:%M'),
                    'Doctor Name': apt.doctor.full_name,
                    'Specialization': apt.doctor.specialization.name if apt.doctor.specialization else 'General',
                    'Diagnosis': apt.treatment.diagnosis or 'N/A',
                    'Prescription': apt.treatment.prescription or 'N/A',
                    'Treatment Notes': apt.treatment.notes or 'N/A',
                    'Next Visit Date': apt.treatment.next_visit_date.strftime('%Y-%m-%d') if apt.treatment.next_visit_date else 'N/A'
                })
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=treatment_history_{patient.id}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        logger.info(f"CSV exported for patient {patient.id}")
        return response
        
    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


@bp.route('/export-status/<task_id>', methods=['GET'])
@jwt_required()
@role_required('patient')
def get_export_status(task_id):
    from celery.result import AsyncResult
    from app.celery_config import make_celery
    from flask import current_app
    
    try:
        celery = make_celery(current_app._get_current_object())
        task = AsyncResult(task_id, app=celery)
        
        if task.ready():
            if task.successful():
                result = task.result
                return jsonify({
                    'status': 'completed',
                    'result': result,
                    'download_url': f'/exports/{result.get("filename")}' if result else None
                }), 200
            else:
                return jsonify({
                    'status': 'failed',
                    'error': str(task.info)
                }), 200
        else:
            return jsonify({
                'status': 'processing',
                'progress': getattr(task.info, 'get', lambda x, y: 0)('progress', 0)
            }), 200
            
    except Exception as e:
        logger.error(f"Error checking export status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@bp.route('/download-export/<filename>', methods=['GET'])
@jwt_required()
@role_required('patient')
def download_export(filename):
    import os
    from flask import send_file
    
    patient = get_current_user()
    
    # Security: Verify filename belongs to this patient
    if not filename.startswith(f'patient_{patient.id}_'):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    filepath = os.path.join('exports', filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found or expired'}), 404
    
    return send_file(
        filepath,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
