from celery import shared_task
from app import db
from app.models.appointment import Appointment
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='app.tasks.auto_cancel.cancel_missed_appointments')
def cancel_missed_appointments():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            yesterday = date.today() - timedelta(days=1)
            
            logger.info(f"Checking for missed appointments on {yesterday}")
            
            missed_appointments = Appointment.query.filter(
                Appointment.appointment_date == yesterday,
                Appointment.status == 'booked'
            ).all()
            
            if not missed_appointments:
                logger.info(f"No missed appointments found for {yesterday}")
                return {
                    'status': 'success',
                    'cancelled_count': 0,
                    'date': yesterday.isoformat(),
                    'message': 'No missed appointments to cancel'
                }
            
            cancelled_count = 0
            cancelled_details = []
            
            for appointment in missed_appointments:
                try:
                    # Update appointment status
                    appointment.status = 'cancelled'
                    appointment.reason = "Auto-cancelled: Patient didn't show up"
                    
                    # Optional: Initiate refund if payment was made
                    if appointment.payment_status == 'paid':
                        appointment.refund_status = 'approved'
                        appointment.refund_date = date.today()
                    
                    cancelled_details.append({
                        'appointment_id': appointment.id,
                        'patient_name': appointment.patient.full_name,
                        'doctor_name': appointment.doctor.full_name,
                        'appointment_time': appointment.appointment_time.strftime('%H:%M'),
                        'consultation_fee': float(appointment.consultation_fee) if appointment.consultation_fee else 0
                    })
                    
                    cancelled_count += 1
                    
                except Exception as e:
                    logger.error(f" Error cancelling appointment {appointment.id}: {str(e)}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Auto-cancelled {cancelled_count} missed appointments from {yesterday}")
            
            # Optional: Send notification to admin
            if cancelled_count > 0:
                try:
                    send_admin_notification(cancelled_count, yesterday, cancelled_details)
                except Exception as e:
                    logger.warning(f"Failed to send admin notification: {str(e)}")
            
            return {
                'status': 'success',
                'cancelled_count': cancelled_count,
                'date': yesterday.isoformat(),
                'cancelled_appointments': cancelled_details,
                'total_refund_amount': sum(apt['consultation_fee'] for apt in cancelled_details)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during auto-cancel task: {str(e)}")
            
            return {
                'status': 'error',
                'error': str(e),
                'date': yesterday.isoformat() if 'yesterday' in locals() else None
            }


def send_admin_notification(cancelled_count, date, details):
    from flask import current_app
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Get admin email from config or use default
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@hospital.com')
    
    if not current_app.config.get('MAIL_USERNAME'):
        logger.info(f"Admin notification (email not configured):")
        logger.info(f"{cancelled_count} appointments auto-cancelled for {date}")
        return
    
    subject = f"Auto-Cancel Report - {cancelled_count} Missed Appointments on {date}"
    
    # Build detailed HTML email
    appointments_html = ""
    for apt in details:
        appointments_html += f"""
        <tr>
            <td>{apt['appointment_id']}</td>
            <td>{apt['patient_name']}</td>
            <td>{apt['doctor_name']}</td>
            <td>{apt['appointment_time']}</td>
            <td>₹{apt['consultation_fee']}</td>
        </tr>
        """
    
    total_refund = sum(apt['consultation_fee'] for apt in details)
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #dc3545; color: white; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h2>Auto-Cancel Report</h2>
        <div class="summary">
            <h3>Summary</h3>
            <ul>
                <li><strong>Date:</strong> {date}</li>
                <li><strong>Appointments Cancelled:</strong> {cancelled_count}</li>
                <li><strong>Total Refund Amount:</strong> ₹{total_refund}</li>
            </ul>
        </div>
        
        <h3>Cancelled Appointments</h3>
        <table>
            <tr>
                <th>ID</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Time</th>
                <th>Fee</th>
            </tr>
            {appointments_html}
        </table>
        
        <p><em>This is an automated report from the Hospital Management System.</em></p>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = admin_email
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(
            current_app.config['MAIL_USERNAME'],
            current_app.config['MAIL_PASSWORD']
        )
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Admin notification sent to {admin_email}")
        
    except Exception as e:
        logger.error(f"Failed to send admin email: {str(e)}")
        raise


@shared_task(name='app.tasks.auto_cancel.cancel_specific_appointment')
def cancel_specific_appointment(appointment_id, reason="Auto-cancelled"):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            appointment = Appointment.query.get(appointment_id)
            
            if not appointment:
                return {
                    'status': 'error',
                    'error': 'Appointment not found'
                }
            
            if appointment.status == 'cancelled':
                return {
                    'status': 'error',
                    'error': 'Appointment already cancelled'
                }
            
            appointment.status = 'cancelled'
            appointment.reason = reason
            
            # Initiate refund if paid
            if appointment.payment_status == 'paid':
                appointment.refund_status = 'approved'
                appointment.refund_date = date.today()
            
            db.session.commit()
            
            return {
                'status': 'success',
                'appointment_id': appointment_id,
                'message': f'Appointment {appointment_id} cancelled successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling appointment {appointment_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }