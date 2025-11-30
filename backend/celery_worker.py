from app import create_app
from app.celery_config import make_celery

app = create_app()
celery = make_celery(app)

from app.tasks import send_daily_reminders, send_monthly_reports, export_patient_treatments

from app.tasks.reminders import send_daily_reminders
from app.tasks.reports import send_monthly_reports
from app.tasks.exports import export_patient_treatments
from app.tasks.cleanup import cleanup_old_availability
from app.tasks.auto_cancel import cancel_missed_appointments  

print("Registered Celery Tasks:")
print(f"  - send_daily_reminders: {send_daily_reminders}")
print(f"  - send_monthly_reports: {send_monthly_reports}")
print(f"  - export_patient_treatments: {export_patient_treatments}")
print(f"  - cleanup_old_availability: {cleanup_old_availability}")
print(f"  - cancel_missed_appointments: {cancel_missed_appointments}")