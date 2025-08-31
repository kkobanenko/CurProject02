from __future__ import annotations
import logging
from datetime import datetime, timedelta
from celery.schedules import crontab
from app.tasks.celery_tasks import celery_app, cleanup_old_data
from app.settings import settings

logger = logging.getLogger(__name__)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-data-daily': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
        'args': (settings.cleanup_ttl_days,),
        'options': {'queue': 'default'}
    },
    'cleanup-old-data-weekly': {
        'task': 'cleanup_old_data',
        'schedule': crontab(day_of_week=1, hour=3, minute=0),  # Weekly on Monday at 3:00 AM
        'args': (settings.cleanup_ttl_days * 2,),  # Clean older data
        'options': {'queue': 'default'}
    },
}

def schedule_cleanup_task(days: int = None) -> str:
    """
    Schedule a one-time cleanup task.
    
    Args:
        days: Number of days to keep data
    
    Returns:
        Task ID
    """
    days = days or settings.cleanup_ttl_days
    logger.info(f"Scheduling cleanup task for data older than {days} days")
    
    result = cleanup_old_data.apply_async(
        args=[days],
        countdown=60,  # Run after 1 minute
        queue='default'
    )
    
    logger.info(f"Cleanup task scheduled: {result.id}")
    return result.id

def get_scheduled_tasks() -> dict:
    """Get information about scheduled tasks."""
    return {
        'beat_schedule': celery_app.conf.beat_schedule,
        'cleanup_ttl_days': settings.cleanup_ttl_days,
        'next_cleanup': datetime.now().replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1)
    }
