from app import db, celery
from app.models.availability import DoctorAvailability
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

@celery.task(name='app.tasks.cleanup.cleanup_old_availability')
def cleanup_old_availability():
    try:
        cutoff_date = date.today() - timedelta(days=30)
        
        # Delete old availability records
        deleted_count = DoctorAvailability.query.filter(
            DoctorAvailability.date < cutoff_date
        ).delete()
        
        db.session.commit()
        
        logger.info(f"Cleaned up {deleted_count} old availability records older than {cutoff_date}")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during cleanup: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }