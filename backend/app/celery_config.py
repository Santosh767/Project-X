from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

def make_celery(app):
    """
    Create and configure Celery instance with Flask app context
    """
    celery = Celery(
        app.import_name,
        broker=app.config['BROKER_URL'],
        backend=app.config['RESULT_BACKEND']
    )
    
    # Update celery config with lowercase keys for Celery 5.x+
    celery.conf.update(
        broker_url=app.config['BROKER_URL'],
        result_backend=app.config['RESULT_BACKEND'],
        timezone='Asia/Kolkata',
        enable_utc=True,
        
        # BEAT SCHEDULE
        beat_schedule={
            # 1 Daily Reminders - Every day at 8:00 AM
            'send-daily-reminders': {
                'task': 'app.tasks.send_daily_reminders',
                'schedule': crontab(hour=8, minute=0),  # 8:00 AM daily
                'options': {
                    'expires': 3600,  # Task expires after 1 hour
                }
            },
            
            # 2 Monthly Reports - 1st of every month at 9:00 AM
            'send-monthly-reports': {
                'task': 'app.tasks.send_monthly_reports',
                'schedule': crontab(day_of_month=1, hour=9, minute=0),  # 1st @ 9 AM
                'options': {
                    'expires': 7200,  # Task expires after 2 hours
                }
            },
            
            # 3 Cleanup Old Availability - Daily at midnight
            'cleanup-old-availability': {
                'task': 'app.tasks.cleanup.cleanup_old_availability',
                'schedule': crontab(hour=0, minute=0),  # 12:00 AM daily
                'options': {
                    'expires': 1800,  # Task expires after 30 minutes
                }
            },
            
            # 4 Auto-cancel Missed Appointments - Daily at 1:00 AM
            'auto-cancel-missed-appointments': {
                'task': 'app.tasks.auto_cancel.cancel_missed_appointments',
                'schedule': crontab(hour=1, minute=0),  # 1:00 AM daily
                'options': {
                    'expires': 1800,  # Task expires after 30 minutes
                }
            },
            
            # Uncomment to test if beat scheduler is working
            'test-beat-schedule': {
                'task': 'app.tasks.cleanup.cleanup_old_availability',
                'schedule': crontab(minute='*/5'),  # Every 5 minutes
                },
        },
        
        # Task result settings
        result_expires=3600,  # Results expire after 1 hour
        result_persistent=True,  # Persist results in Redis
        
        # Worker settings
        worker_prefetch_multiplier=1,  # One task at a time
        worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
        task_acks_late=True,  # Acknowledge task after completion
        task_reject_on_worker_lost=True,  # Reject task if worker dies
        
        # Task routing (optional - for multiple queues)
        task_routes={
            'app.tasks.send_daily_reminders': {'queue': 'high_priority'},
            'app.tasks.send_monthly_reports': {'queue': 'low_priority'},
            'app.tasks.export_patient_treatments': {'queue': 'medium_priority'},
        },
        
        # Task time limits
        task_soft_time_limit=300,  # 5 minutes soft limit
        task_time_limit=600,  # 10 minutes hard limit
        
        # Serialization
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        
        # Beat scheduler database (optional - SQLAlchemy)
         beat_scheduler='celery.beat.PersistentScheduler',
         beat_schedule_filename='celerybeat-schedule',
    )
    
    # Create context task that runs within Flask app context
    class ContextTask(celery.Task):
        """
        Custom task class that ensures all tasks run within Flask app context
        """
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery