from celery import shared_task
from app import db
from app.models import Appointment, User
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import requests
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation(appointment):
    """Send immediate booking confirmation to patient"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            patient = appointment.patient
            doctor = appointment.doctor
            
            # Email confirmation
            if patient.email:
                send_confirmation_email(
                    patient_email=patient.email,
                    patient_name=patient.full_name,
                    doctor_name=doctor.full_name,
                    doctor_specialization=doctor.specialization.name if doctor.specialization else 'General',
                    appointment_date=appointment.appointment_date.strftime('%B %d, %Y'),
                    appointment_time=appointment.appointment_time.strftime('%H:%M'),
                    consultation_fee=float(appointment.consultation_fee) if appointment.consultation_fee else 500,
                    appointment_id=appointment.id
                )
                logger.info(f"✅ Booking confirmation email sent to {patient.email}")
            
            # Google Chat notification (if configured)
            if app.config.get('GOOGLE_CHAT_WEBHOOK'):
                send_google_chat_booking(
                    patient_name=patient.full_name,
                    doctor_name=doctor.full_name,
                    appointment_date=appointment.appointment_date.strftime('%B %d, %Y'),
                    appointment_time=appointment.appointment_time.strftime('%H:%M'),
                    consultation_fee=float(appointment.consultation_fee) if appointment.consultation_fee else 500
                )
                logger.info("✅ Google Chat booking notification sent")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send booking confirmation: {str(e)}")
            return False


def send_confirmation_email(patient_email, patient_name, doctor_name, doctor_specialization,
                           appointment_date, appointment_time, consultation_fee, appointment_id):
    """Send booking confirmation email"""
    from flask import current_app
    
    subject = f"✅ Appointment Confirmed - {appointment_date}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f9;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .success-icon {{
                font-size: 48px;
                color: #28a745;
                text-align: center;
                margin-bottom: 20px;
            }}
            .appointment-card {{
                background: #f8f9fa;
                border-left: 4px solid #28a745;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e0e0e0;
            }}
            .detail-label {{
                font-weight: 600;
                color: #555;
            }}
            .detail-value {{
                color: #333;
            }}
            .amount {{
                background: #28a745;
                color: white;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
                margin: 20px 0;
                font-size: 20px;
                font-weight: bold;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
            }}
            .button {{
                display: inline-block;
                background-color: #28a745;
                color: white !important;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Appointment Confirmed!</h1>
                <p>Your booking has been successfully confirmed</p>
            </div>
            
            <div class="content">
                <div class="success-icon">✓</div>
                
                <p>Dear <strong>{patient_name}</strong>,</p>
                
                <p>Thank you for booking your appointment. Your consultation has been confirmed and payment has been received.</p>
                
                <div class="appointment-card">
                    <h3 style="margin-top: 0; color: #28a745;">Appointment Details</h3>
                    
                    <div class="detail-row">
                        <span class="detail-label">Appointment ID:</span>
                        <span class="detail-value">#{appointment_id}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Doctor:</span>
                        <span class="detail-value">Dr. {doctor_name}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Specialization:</span>
                        <span class="detail-value">{doctor_specialization}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{appointment_date}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{appointment_time}</span>
                    </div>
                </div>
                
                <div class="amount">
                    💳 Amount Paid: ₹{consultation_fee}
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>⏰ Important Reminder:</strong><br>
                    Please arrive 10-15 minutes early for registration.
                    You will receive a reminder notification 30 minutes before your appointment.
                </div>
                
                <div style="background-color: #d1ecf1; border: 1px solid #0dcaf0; padding: 15px; border-radius: 5px;">
                    <strong>📋 What to Bring:</strong>
                    <ul style="margin: 10px 0;">
                        <li>Valid ID proof</li>
                        <li>Previous medical records (if any)</li>
                        <li>List of current medications</li>
                    </ul>
                </div>
                
                <p style="margin-top: 30px; color: #666;">
                    If you need to cancel or reschedule, please do so through your patient dashboard at least 2 hours before the appointment.
                </p>
            </div>
            
            <div class="footer">
                <p><strong>Hospital Management System</strong></p>
                <p style="font-size: 12px; margin-top: 10px;">
                    <em>This is an automated confirmation. Please do not reply to this email.</em>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        if not current_app.config.get('MAIL_USERNAME'):
            logger.warning("📧 Email not configured - printing confirmation to console")
            print(f"\n{'='*70}")
            print(f"📧 BOOKING CONFIRMATION (Email not configured)")
            print(f"{'='*70}")
            print(f"To: {patient_email}")
            print(f"Subject: {subject}")
            print(f"Appointment ID: {appointment_id}")
            print(f"Patient: {patient_name}")
            print(f"Doctor: Dr. {doctor_name}")
            print(f"Date & Time: {appointment_date} at {appointment_time}")
            print(f"Amount: ₹{consultation_fee}")
            print(f"{'='*70}\n")
            return True
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = patient_email
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        raise


def send_google_chat_booking(patient_name, doctor_name, appointment_date, appointment_time, consultation_fee):
    """Send Google Chat booking notification"""
    from flask import current_app
    
    webhook_url = current_app.config.get('GOOGLE_CHAT_WEBHOOK')
    if not webhook_url:
        return False
    
    message = {
        "cards": [{
            "header": {
                "title": "✅ New Appointment Booked",
                "subtitle": f"Booking Confirmed - {appointment_date}",
                "imageUrl": "https://cdn-icons-png.flaticon.com/512/2913/2913133.png"
            },
            "sections": [{
                "widgets": [
                    {
                        "keyValue": {
                            "topLabel": "Patient",
                            "content": patient_name,
                            "icon": "PERSON"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Doctor",
                            "content": f"Dr. {doctor_name}",
                            "icon": "STAR"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Date & Time",
                            "content": f"{appointment_date} at {appointment_time}",
                            "icon": "CLOCK"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Amount Paid",
                            "content": f"₹{consultation_fee}",
                            "icon": "DESCRIPTION"
                        }
                    }
                ]
            }]
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Google Chat webhook failed: {str(e)}")
        raise


@shared_task(name='app.tasks.booking_notifications.send_pre_appointment_reminder')
def send_pre_appointment_reminder(appointment_id):
    """Send reminder 30 minutes before appointment"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            appointment = Appointment.query.get(appointment_id)
            if not appointment or appointment.status != 'booked':
                return {'status': 'skipped', 'reason': 'Appointment not found or not booked'}
            
            patient = appointment.patient
            doctor = appointment.doctor
            
            # Send reminder email
            send_reminder_email(
                patient_email=patient.email,
                patient_name=patient.full_name,
                doctor_name=doctor.full_name,
                appointment_date=appointment.appointment_date.strftime('%B %d, %Y'),
                appointment_time=appointment.appointment_time.strftime('%H:%M')
            )
            
            return {
                'status': 'success',
                'appointment_id': appointment_id,
                'patient': patient.full_name
            }
        except Exception as e:
            logger.error(f"Failed to send pre-appointment reminder: {str(e)}")
            return {'status': 'error', 'error': str(e)}


def send_reminder_email(patient_email, patient_name, doctor_name, appointment_date, appointment_time):
    """Send 30-minute reminder email"""
    from flask import current_app
    
    subject = f"⏰ Reminder: Appointment in 30 Minutes"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f9;
                padding: 20px;
            }}
            .container {{
                max-width: 500px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .reminder-header {{
                background: #ffc107;
                color: #333;
                padding: 20px;
                border-radius: 5px;
                text-align: center;
                margin-bottom: 20px;
            }}
            .urgent {{
                font-size: 48px;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="reminder-header">
                <div class="urgent">⏰</div>
                <h2 style="margin: 0;">Appointment Reminder</h2>
                <p style="margin: 10px 0 0 0;">Your appointment is in 30 minutes!</p>
            </div>
            
            <p>Dear <strong>{patient_name}</strong>,</p>
            
            <p>This is a friendly reminder that your appointment is scheduled in 30 minutes.</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Doctor:</strong> Dr. {doctor_name}</p>
                <p><strong>Date:</strong> {appointment_date}</p>
                <p><strong>Time:</strong> {appointment_time}</p>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>📍 Please ensure you arrive on time!</strong>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        if not current_app.config.get('MAIL_USERNAME'):
            print(f"\n⏰ REMINDER: {patient_name} has appointment with Dr. {doctor_name} at {appointment_time}\n")
            return True
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = patient_email
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Reminder email failed: {str(e)}")
        raise