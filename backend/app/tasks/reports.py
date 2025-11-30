from celery import shared_task
from app import db
from app.models import Appointment, User, Treatment
from datetime import datetime, timedelta
from calendar import monthrange
import logging

logger = logging.getLogger(__name__)


@shared_task(name='app.tasks.send_monthly_reports')
def send_monthly_reports():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Get last month's data
        today = datetime.now()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        logger.info(f"Generating monthly reports for {last_day_last_month.strftime('%B %Y')}")
        
        # Get all active doctors
        doctors = User.query.filter_by(role='doctor', is_active=True).all()
        
        if not doctors:
            logger.warning("No active doctors found")
            return {
                'status': 'success',
                'reports_sent': 0,
                'message': 'No active doctors'
            }
        
        reports_sent = 0
        failed_reports = []
        
        for doctor in doctors:
            try:
                # Generate comprehensive report
                report_data = generate_doctor_report_data(
                    doctor=doctor,
                    start_date=first_day_last_month,
                    end_date=last_day_last_month
                )
                
                # Generate HTML report
                report_html = generate_professional_html_report(doctor, report_data)
                
                # Send report via email
                send_report_email(
                    doctor_email=doctor.email,
                    doctor_name=doctor.full_name,
                    report_html=report_html,
                    month=last_day_last_month.strftime('%B %Y'),
                    report_data=report_data
                )
                
                reports_sent += 1
                logger.info(f"Report sent to Dr. {doctor.full_name}")
                
            except Exception as e:
                logger.error(f"Failed to send report to Dr. {doctor.full_name}: {str(e)}")
                failed_reports.append({
                    'doctor_name': doctor.full_name,
                    'error': str(e)
                })
        
        result = {
            'status': 'success',
            'month': last_day_last_month.strftime('%B %Y'),
            'total_doctors': len(doctors),
            'reports_sent': reports_sent,
            'failed': len(failed_reports),
            'failed_reports': failed_reports
        }
        
        logger.info(f"Monthly reports completed: {reports_sent}/{len(doctors)} sent")
        return result


def generate_doctor_report_data(doctor, start_date, end_date):
    # Get appointments for the month
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= start_date.date(),
        Appointment.appointment_date <= end_date.date()
    ).all()
    
    # Calculate statistics
    total_appointments = len(appointments)
    completed = len([a for a in appointments if a.status == 'completed'])
    cancelled = len([a for a in appointments if a.status == 'cancelled'])
    booked = len([a for a in appointments if a.status == 'booked'])
    
    # Calculate revenue
    total_revenue = sum(
        float(a.consultation_fee) if a.consultation_fee and a.payment_status == 'paid' 
        else 0 
        for a in appointments
    )
    
    # Get treatments provided
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= start_date.date(),
        Appointment.appointment_date <= end_date.date()
    ).all()
    
    # Appointments by day of week
    day_distribution = {}
    for apt in appointments:
        day_name = apt.appointment_date.strftime('%A')
        day_distribution[day_name] = day_distribution.get(day_name, 0) + 1
    
    # Most common diagnoses
    diagnosis_counts = {}
    for treatment in treatments:
        if treatment.diagnosis:
            diagnosis_counts[treatment.diagnosis] = diagnosis_counts.get(treatment.diagnosis, 0) + 1
    
    top_diagnoses = sorted(diagnosis_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Appointment time distribution
    morning = len([a for a in appointments if a.appointment_time.hour < 12])
    afternoon = len([a for a in appointments if 12 <= a.appointment_time.hour < 17])
    evening = len([a for a in appointments if a.appointment_time.hour >= 17])
    
    # Patient demographics (unique patients)
    unique_patients = set(a.patient_id for a in appointments)
    
    return {
        'period': {
            'start': start_date.strftime('%B %d, %Y'),
            'end': end_date.strftime('%B %d, %Y'),
            'month': start_date.strftime('%B %Y')
        },
        'summary': {
            'total_appointments': total_appointments,
            'completed': completed,
            'cancelled': cancelled,
            'booked': booked,
            'completion_rate': round((completed / total_appointments * 100) if total_appointments > 0 else 0, 1),
            'total_revenue': total_revenue,
            'unique_patients': len(unique_patients)
        },
        'distributions': {
            'by_day': day_distribution,
            'by_time': {
                'Morning (6AM-12PM)': morning,
                'Afternoon (12PM-5PM)': afternoon,
                'Evening (5PM-9PM)': evening
            }
        },
        'treatments': {
            'total': len(treatments),
            'top_diagnoses': top_diagnoses
        },
        'appointments': appointments,
        'treatments_list': treatments
    }


def generate_professional_html_report(doctor, report_data):
    summary = report_data['summary']
    period = report_data['period']
    distributions = report_data['distributions']
    treatments = report_data['treatments']
    
    # Generate chart data for day distribution
    day_chart = generate_bar_chart_html(
        distributions['by_day'],
        "Appointments by Day of Week",
        color="#667eea"
    )
    
    # Generate chart data for time distribution
    time_chart = generate_bar_chart_html(
        distributions['by_time'],
        "Appointments by Time of Day",
        color="#764ba2"
    )
    
    # Generate status pie chart
    status_data = {
        'Completed': summary['completed'],
        'Cancelled': summary['cancelled'],
        'Booked': summary['booked']
    }
    status_chart = generate_pie_chart_html(status_data)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Monthly Activity Report - {period['month']}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                line-height: 1.6;
            }}
            
            .report-container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
                font-weight: 600;
            }}
            
            .header .subtitle {{
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            
            .content {{
                padding: 40px;
            }}
            
            .doctor-info {{
                background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 30px;
                border-left: 5px solid #667eea;
            }}
            
            .doctor-info h2 {{
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.8rem;
            }}
            
            .doctor-info p {{
                color: #555;
                font-size: 1.1rem;
                margin: 5px 0;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            
            .stat-card {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                transition: transform 0.3s ease;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            
            .stat-card:hover {{
                transform: translateY(-5px);
            }}
            
            .stat-value {{
                font-size: 2.5rem;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }}
            
            .stat-label {{
                color: #666;
                font-size: 0.95rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .section {{
                margin: 40px 0;
            }}
            
            .section-title {{
                font-size: 1.8rem;
                color: #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #667eea;
            }}
            
            .chart-container {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 15px;
                margin: 20px 0;
            }}
            
            .chart-title {{
                font-size: 1.3rem;
                color: #555;
                margin-bottom: 20px;
                text-align: center;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            
            th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            
            td {{
                padding: 12px 15px;
                border-bottom: 1px solid #eee;
                color: #555;
            }}
            
            tr:hover {{
                background-color: #f5f7fa;
            }}
            
            .badge {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
            }}
            
            .badge-completed {{
                background: #d4edda;
                color: #155724;
            }}
            
            .badge-cancelled {{
                background: #f8d7da;
                color: #721c24;
            }}
            
            .badge-booked {{
                background: #fff3cd;
                color: #856404;
            }}
            
            .footer {{
                background: #f8f9fa;
                padding: 30px;
                text-align: center;
                color: #666;
            }}
            
            .footer p {{
                margin: 10px 0;
            }}
            
            .highlight {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }}
            
            .highlight h3 {{
                margin-bottom: 10px;
            }}
            
            @media print {{
                body {{
                    background: white;
                    padding: 0;
                }}
                
                .report-container {{
                    box-shadow: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="report-container">
            <!-- Header -->
            <div class="header">
                <h1>📊 Monthly Activity Report</h1>
                <div class="subtitle">{period['month']}</div>
            </div>
            
            <!-- Content -->
            <div class="content">
                <!-- Doctor Information -->
                <div class="doctor-info">
                    <h2>Dr. {doctor.full_name}</h2>
                    <p><strong>Specialization:</strong> {doctor.specialization.name if doctor.specialization else 'General Practice'}</p>
                    <p><strong>Qualification:</strong> {doctor.qualification or 'MBBS'}</p>
                    <p><strong>Experience:</strong> {doctor.experience_years or 0} years</p>
                    <p><strong>Report Period:</strong> {period['start']} - {period['end']}</p>
                </div>
                
                <!-- Summary Statistics -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Appointments</div>
                        <div class="stat-value">{summary['total_appointments']}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Completed</div>
                        <div class="stat-value" style="color: #28a745;">{summary['completed']}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Completion Rate</div>
                        <div class="stat-value" style="color: #17a2b8;">{summary['completion_rate']}%</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Revenue Generated</div>
                        <div class="stat-value" style="color: #ffc107;">₹{summary['total_revenue']:,.0f}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Unique Patients</div>
                        <div class="stat-value">{summary['unique_patients']}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Treatments Given</div>
                        <div class="stat-value">{treatments['total']}</div>
                    </div>
                </div>
                
                <!-- Performance Highlight -->
                {generate_performance_highlight(summary)}
                
                <!-- Charts Section -->
                <div class="section">
                    <h3 class="section-title">📈 Distribution Analysis</h3>
                    
                    <div class="chart-container">
                        {day_chart}
                    </div>
                    
                    <div class="chart-container">
                        {time_chart}
                    </div>
                    
                    <div class="chart-container">
                        <div class="chart-title">Appointment Status Distribution</div>
                        {status_chart}
                    </div>
                </div>
                
                <!-- Top Diagnoses -->
                {generate_top_diagnoses_section(treatments['top_diagnoses'])}
                
                <!-- Recent Appointments Table -->
                {generate_appointments_table(report_data['appointments'][:10])}
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p><strong>Hospital Management System</strong></p>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                <p style="margin-top: 15px; font-size: 0.9rem;">
                    <em>This is an automated report. For questions, contact admin@hospital.com</em>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_bar_chart_html(data, title, color="#667eea"):
    """Generate HTML/CSS bar chart"""
    if not data:
        return "<p>No data available</p>"
    
    max_value = max(data.values()) if data else 1
    
    chart_html = f'<div class="chart-title">{title}</div>'
    chart_html += '<div style="padding: 20px;">'
    
    for label, value in data.items():
        percentage = (value / max_value * 100) if max_value > 0 else 0
        chart_html += f'''
        <div style="margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-weight: 600; color: #555;">{label}</span>
                <span style="color: {color}; font-weight: bold;">{value}</span>
            </div>
            <div style="background: #e0e0e0; height: 30px; border-radius: 15px; overflow: hidden;">
                <div style="background: {color}; height: 100%; width: {percentage}%; 
                            transition: width 0.5s ease; display: flex; align-items: center;
                            padding-left: 10px; color: white; font-weight: bold;">
                </div>
            </div>
        </div>
        '''
    
    chart_html += '</div>'
    return chart_html


def generate_pie_chart_html(data):
    """Generate HTML/CSS pie chart representation"""
    if not data:
        return "<p>No data available</p>"
    
    total = sum(data.values())
    colors = {
        'Completed': '#28a745',
        'Cancelled': '#dc3545',
        'Booked': '#ffc107'
    }
    
    html = '<div style="display: flex; justify-content: space-around; align-items: center;">'
    
    for label, value in data.items():
        percentage = (value / total * 100) if total > 0 else 0
        color = colors.get(label, '#667eea')
        
        html += f'''
        <div style="text-align: center; margin: 20px;">
            <div style="width: 120px; height: 120px; border-radius: 50%; 
                        background: conic-gradient({color} 0% {percentage}%, #e0e0e0 {percentage}% 100%);
                        display: flex; align-items: center; justify-content: center;
                        position: relative; margin: 0 auto 15px;">
                <div style="width: 80px; height: 80px; background: white; border-radius: 50%;
                            display: flex; align-items: center; justify-content: center;
                            font-size: 1.5rem; font-weight: bold; color: {color};">
                    {percentage:.0f}%
                </div>
            </div>
            <div style="font-weight: 600; color: #555; margin-bottom: 5px;">{label}</div>
            <div style="color: {color}; font-weight: bold; font-size: 1.2rem;">{value}</div>
        </div>
        '''
    
    html += '</div>'
    return html


def generate_performance_highlight(summary):
    """Generate performance highlight section"""
    if summary['completion_rate'] >= 80:
        emoji = "🌟"
        message = "Excellent performance! Maintaining high completion rate."
        color = "#28a745"
    elif summary['completion_rate'] >= 60:
        emoji = "👍"
        message = "Good performance! Keep up the consistent work."
        color = "#17a2b8"
    else:
        emoji = "📈"
        message = "Room for improvement. Focus on reducing cancellations."
        color = "#ffc107"
    
    return f'''
    <div class="highlight" style="background: {color};">
        <h3>{emoji} Performance Highlight</h3>
        <p style="font-size: 1.1rem;">{message}</p>
        <p>You've successfully completed {summary['completed']} out of {summary['total_appointments']} appointments this month.</p>
    </div>
    '''


def generate_top_diagnoses_section(top_diagnoses):
    """Generate top diagnoses section"""
    if not top_diagnoses:
        return ""
    
    html = '''
    <div class="section">
        <h3 class="section-title">🏥 Most Common Diagnoses</h3>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Diagnosis</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for idx, (diagnosis, count) in enumerate(top_diagnoses, 1):
        html += f'''
        <tr>
            <td><strong>#{idx}</strong></td>
            <td>{diagnosis}</td>
            <td><strong>{count}</strong></td>
        </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </div>
    '''
    
    return html


def generate_appointments_table(appointments):
    """Generate appointments table"""
    if not appointments:
        return ""
    
    html = '''
    <div class="section">
        <h3 class="section-title">📅 Recent Appointments</h3>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Patient</th>
                    <th>Status</th>
                    <th>Diagnosis</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for apt in appointments:
        diagnosis = apt.treatment.diagnosis if apt.treatment else 'N/A'
        status_class = f"badge-{apt.status}"
        
        html += f'''
        <tr>
            <td>{apt.appointment_date.strftime('%Y-%m-%d')}</td>
            <td>{apt.appointment_time.strftime('%H:%M')}</td>
            <td>{apt.patient.full_name}</td>
            <td><span class="badge {status_class}">{apt.status.upper()}</span></td>
            <td>{diagnosis}</td>
        </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </div>
    '''
    
    return html


def send_report_email(doctor_email, doctor_name, report_html, month, report_data):
    """Send monthly report email to doctor"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from flask import current_app
    
    subject = f"📊 Monthly Activity Report - {month}"
    
    # Check if email is configured
    if not current_app.config.get('MAIL_USERNAME'):
        # Save to file for testing
        filename = f"report_{doctor_name.replace(' ', '_')}_{month.replace(' ', '_')}.html"
        import os
        os.makedirs('reports', exist_ok=True)
        filepath = os.path.join('reports', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📧 MONTHLY REPORT (Email not configured)")
        logger.info(f"{'='*70}")
        logger.info(f"To: {doctor_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Report saved to: {filepath}")
        logger.info(f"{'='*70}\n")
        return
    
    # Send actual email
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = doctor_email
        
        html_part = MIMEText(report_html, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(
            current_app.config['MAIL_USERNAME'],
            current_app.config['MAIL_PASSWORD']
        )
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Monthly report email sent to {doctor_email}")
        
    except Exception as e:
        logger.error(f"Failed to send report email: {str(e)}")
        raise