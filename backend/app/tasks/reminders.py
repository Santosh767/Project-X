from celery import shared_task
from app import db
from app.models import Appointment, User
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import requests
import logging

logger = logging.getLogger(__name__)


@shared_task(name='app.tasks.send_daily_reminders')
def send_daily_reminders():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        today = date.today()
        
        logger.info(f"🔔 Starting daily reminders for {today}")
        
        # Get all appointments for today with status 'booked'
        appointments = Appointment.query.filter_by(
            appointment_date=today,
            status='booked'
        ).all()
        
        if not appointments:
            logger.info(f"ℹ️ No appointments scheduled for {today}")
            return {
                'status': 'success',
                'reminders_sent': 0,
                'total_appointments': 0,
                'date': today.isoformat(),
                'message': 'No appointments today'
            }
        
        logger.info(f"📋 Found {len(appointments)} appointments for today")
        
        reminders_sent = 0
        failed_reminders = []
        reminder_details = []
        
        for appointment in appointments:
            patient = appointment.patient
            doctor = appointment.doctor
            
            reminder_data = {
                'appointment_id': appointment.id,
                'patient_email': patient.email,
                'patient_name': patient.full_name,
                'patient_phone': patient.phone,
                'doctor_name': doctor.full_name,
                'doctor_specialization': doctor.specialization.name if doctor.specialization else 'General',
                'appointment_time': appointment.appointment_time.strftime('%H:%M'),
                'appointment_date': appointment.appointment_date.strftime('%B %d, %Y'),
                'hospital_address': 'Hospital Management System, Main Branch'
            }
            
            success = False
            channels_used = []
            
            # Try Email (Primary Channel)
            if patient.email:
                try:
                    send_reminder_email(**reminder_data)
                    success = True
                    channels_used.append('email')
                    logger.info(f"Email sent to {patient.email}")
                except Exception as e:
                    logger.error(f"Email failed for {patient.email}: {str(e)}")
            
            # Try Google Chat (Optional)
            if app.config.get('GOOGLE_CHAT_WEBHOOK'):
                try:
                    send_google_chat_reminder(**reminder_data)
                    success = True
                    channels_used.append('google_chat')
                    logger.info(f"Google Chat notification sent for {patient.full_name}")
                except Exception as e:
                    logger.error(f"Google Chat failed: {str(e)}")
            
            if success:
                reminders_sent += 1
                reminder_details.append({
                    'patient_name': patient.full_name,
                    'channels': channels_used,
                    'appointment_time': reminder_data['appointment_time']
                })
            else:
                failed_reminders.append({
                    'patient_name': patient.full_name,
                    'patient_email': patient.email,
                    'reason': 'All channels failed'
                })
        
        result = {
            'status': 'success',
            'date': today.isoformat(),
            'total_appointments': len(appointments),
            'reminders_sent': reminders_sent,
            'failed': len(failed_reminders),
            'failed_patients': failed_reminders,
            'reminder_details': reminder_details
        }
        
        logger.info(f"Daily reminders completed: {reminders_sent}/{len(appointments)} sent")
        
        return result


def send_reminder_email(patient_email, patient_name, doctor_name, doctor_specialization,
                       appointment_time, appointment_date, hospital_address, **kwargs):
    """
    Send reminder email to patient with professional HTML template
    
    Args:
        patient_email (str): Patient's email address
        patient_name (str): Patient's full name
        doctor_name (str): Doctor's full name
        doctor_specialization (str): Doctor's specialization
        appointment_time (str): Appointment time (HH:MM format)
        appointment_date (str): Appointment date (formatted)
        hospital_address (str): Hospital address
        **kwargs: Additional optional parameters
    """
    
    subject = f"🏥 Appointment Reminder - {appointment_date}"
    
    # Professional HTML email template
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f6f9;
                padding: 20px;
                margin: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 18px;
                color: #333;
                margin-bottom: 20px;
            }}
            .appointment-card {{
                background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
                border-left: 4px solid #667eea;
                padding: 25px;
                border-radius: 10px;
                margin: 25px 0;
            }}
            .appointment-card h3 {{
                margin: 0 0 20px 0;
                color: #667eea;
                font-size: 20px;
            }}
            .detail-row {{
                display: flex;
                margin: 12px 0;
                align-items: center;
            }}
            .detail-label {{
                font-weight: 600;
                color: #555;
                min-width: 140px;
                display: flex;
                align-items: center;
            }}
            .detail-label::before {{
                content: "•";
                color: #667eea;
                font-size: 20px;
                margin-right: 10px;
            }}
            .detail-value {{
                color: #333;
                font-size: 16px;
            }}
            .important-note {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                padding: 15px;
                border-radius: 8px;
                margin: 25px 0;
                display: flex;
                align-items: center;
            }}
            .important-note::before {{
                content: "⚠️";
                font-size: 24px;
                margin-right: 15px;
            }}
            .important-note strong {{
                color: #856404;
            }}
            .instructions {{
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .instructions h4 {{
                margin: 0 0 15px 0;
                color: #004085;
            }}
            .instructions ul {{
                margin: 0;
                padding-left: 20px;
            }}
            .instructions li {{
                margin: 8px 0;
                color: #004085;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            .footer p {{
                margin: 5px 0;
            }}
            .footer a {{
                color: #667eea;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🏥 Appointment Reminder</h1>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Dear <strong>{patient_name}</strong>,
                </div>
                
                <p style="color: #666; line-height: 1.6;">
                    This is a friendly reminder about your upcoming appointment at our hospital.
                </p>
                
                <div class="appointment-card">
                    <h3>📅 Appointment Details</h3>
                    
                    <div class="detail-row">
                        <div class="detail-label">Doctor</div>
                        <div class="detail-value">Dr. {doctor_name}</div>
                    </div>
                    
                    <div class="detail-row">
                        <div class="detail-label">Specialization</div>
                        <div class="detail-value">{doctor_specialization}</div>
                    </div>
                    
                    <div class="detail-row">
                        <div class="detail-label">Date</div>
                        <div class="detail-value">{appointment_date}</div>
                    </div>
                    
                    <div class="detail-row">
                        <div class="detail-label">Time</div>
                        <div class="detail-value">{appointment_time}</div>
                    </div>
                    
                    <div class="detail-row">
                        <div class="detail-label">Location</div>
                        <div class="detail-value">{hospital_address}</div>
                    </div>
                </div>
                
                <div class="important-note">
                    <strong>Please arrive 10-15 minutes early for registration and check-in.</strong>
                </div>
                
                <div class="instructions">
                    <h4>📋 Please Remember to Bring:</h4>
                    <ul>
                        <li>Valid ID proof</li>
                        <li>Previous medical records (if any)</li>
                        <li>Insurance card (if applicable)</li>
                        <li>List of current medications</li>
                    </ul>
                </div>
                
                <p style="color: #666; margin-top: 25px; line-height: 1.6;">
                    If you need to reschedule or cancel your appointment, please contact us immediately 
                    through our patient portal or call our helpline.
                </p>
                
                <p style="color: #666; margin-top: 20px;">
                    We look forward to seeing you!
                </p>
            </div>
            
            <div class="footer">
                <p><strong>Hospital Management System</strong></p>
                <p>{hospital_address}</p>
                <p style="margin-top: 15px; font-size: 12px;">
                    <em>This is an automated message. Please do not reply to this email.</em>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        from flask import current_app
        
        # Check if email is configured
        if not current_app.config.get('MAIL_USERNAME'):
            logger.warning("⚠️ Email not configured - printing to console instead")
            print(f"\n{'='*70}")
            print(f"📧 REMINDER EMAIL (Email not configured)")
            print(f"{'='*70}")
            print(f"To: {patient_email}")
            print(f"Subject: {subject}")
            print(f"Patient: {patient_name}")
            print(f"Doctor: Dr. {doctor_name} ({doctor_specialization})")
            print(f"Time: {appointment_date} at {appointment_time}")
            print(f"{'='*70}\n")
            return True
        
        # Send actual email via SMTP
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = patient_email
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(
            current_app.config['MAIL_SERVER'],
            current_app.config['MAIL_PORT']
        )
        server.starttls()
        server.login(
            current_app.config['MAIL_USERNAME'],
            current_app.config['MAIL_PASSWORD']
        )
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {patient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        raise

def send_google_chat_reminder(patient_name, doctor_name, doctor_specialization,
                              appointment_time, appointment_date, **kwargs):
    from flask import current_app
    
    webhook_url = current_app.config.get('GOOGLE_CHAT_WEBHOOK')
    
    if not webhook_url:
        logger.warning("Google Chat webhook not configured")
        return False
    
    # Google Chat Card format (v2)
    message = {
        "cards": [{
            "header": {
                "title": "🏥 Appointment Reminder",
                "subtitle": f"Today's Schedule - {appointment_date}",
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
                            "topLabel": "Specialization",
                            "content": doctor_specialization,
                            "icon": "BOOKMARK"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Appointment Time",
                            "content": f"{appointment_date} at {appointment_time}",
                            "icon": "CLOCK"
                        }
                    },
                    {
                        "textParagraph": {
                            "text": "⏰ <b>Please arrive 10-15 minutes early for check-in</b>"
                        }
                    },
                    {
                        "buttons": [
                            {
                                "textButton": {
                                    "text": "View Appointments",
                                    "onClick": {
                                        "openLink": {
                                            "url": "http://127.0.0.1:5000/html/patient-dashboard.html"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }]
        }]
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=message,
            timeout=10,
            headers={'Content-Type': 'application/json; charset=UTF-8'}
        )
        response.raise_for_status()
        
        logger.info(f"Google Chat notification sent successfully")
        logger.debug(f"Response: {response.status_code} - {response.text}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Google Chat webhook failed: {str(e)}")
        raise