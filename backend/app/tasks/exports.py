from celery import shared_task
from app import db
from app.models import Appointment, Treatment, User
import csv
import os
from datetime import datetime

@shared_task(name='app.tasks.export_patient_treatments')
def export_patient_treatments(patient_id):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        patient = User.query.get(patient_id)
        
        if not patient:
            return {'error': 'Patient not found'}
        
        # Get all completed appointments with treatments
        appointments = Appointment.query.filter_by(
            patient_id=patient_id,
            status='completed'
        ).order_by(Appointment.appointment_date.desc()).all()
        
        # Create CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"patient_{patient_id}_treatments_{timestamp}.csv"
        filepath = os.path.join('exports', filename)
        
        # Create exports directory if not exists
        os.makedirs('exports', exist_ok=True)
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Patient ID',
                'Patient Name',
                'Doctor Name',
                'Appointment Date',
                'Appointment Time',
                'Diagnosis',
                'Prescription',
                'Treatment Notes',
                'Next Visit Date'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for apt in appointments:
                if apt.treatment:
                    writer.writerow({
                        'Patient ID': patient.id,
                        'Patient Name': patient.full_name,
                        'Doctor Name': apt.doctor.full_name,
                        'Appointment Date': apt.appointment_date.strftime('%Y-%m-%d'),
                        'Appointment Time': apt.appointment_time.strftime('%H:%M'),
                        'Diagnosis': apt.treatment.diagnosis,
                        'Prescription': apt.treatment.prescription or 'N/A',
                        'Treatment Notes': apt.treatment.notes or 'N/A',
                        'Next Visit Date': apt.treatment.next_visit_date.strftime('%Y-%m-%d') if apt.treatment.next_visit_date else 'N/A'
                    })
        
        print(f"CSV export completed: {filepath}")
        return {
            'status': 'success',
            'filename': filename,
            'filepath': filepath,
            'records': len(appointments)
        }