"""
apps/activity_log/tasks.py
Celery tasks for activity log maintenance
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.activity_log.tasks.delete_old_activity_logs")
def delete_old_activity_logs():
    """
    Delete activity logs older than 10 days.
    Runs daily via Celery Beat.
    """
    try:
        from apps.activity_log.models import ActivityLog
        
        # Calculate the cutoff date (10 days ago)
        cutoff_date = timezone.now() - timedelta(days=10)
        
        # Get count before deletion
        old_logs = ActivityLog.objects.filter(created_at__lt=cutoff_date)
        count = old_logs.count()
        
        if count > 0:
            # Delete old logs
            deleted_count, _ = old_logs.delete()
            logger.info(f"Deleted {deleted_count} activity logs older than 10 days")
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} old activity logs"
            }
        else:
            logger.info("No old activity logs to delete")
            return {
                "success": True,
                "deleted_count": 0,
                "message": "No old activity logs found"
            }
            
    except Exception as e:
        logger.error(f"Error deleting old activity logs: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete old activity logs"
        }


@shared_task(name="apps.activity_log.tasks.generate_activity_report")
def generate_activity_report(user_pid: str = None, days: int = 7):
    """
    Generate activity report for a user or all users.
    
    Args:
        user_pid: User PID (optional, if None generates for all users)
        days: Number of days to include in report
    """
    try:
        from apps.activity_log.models import ActivityLog
        from django.contrib.auth import get_user_model
        from django.db.models import Count
        
        User = get_user_model()
        cutoff_date = timezone.now() - timedelta(days=days)
        
        queryset = ActivityLog.objects.filter(created_at__gte=cutoff_date)
        
        if user_pid:
            user = User.objects.get(pid=user_pid)
            queryset = queryset.filter(user=user)
        
        # Generate statistics
        total_activities = queryset.count()
        successful_activities = queryset.filter(is_successful=True).count()
        failed_activities = queryset.filter(is_successful=False).count()
        
        # Activity breakdown by action
        action_breakdown = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Activity breakdown by level
        level_breakdown = queryset.values('level').annotate(
            count=Count('id')
        ).order_by('-count')
        
        report = {
            "success": True,
            "period_days": days,
            "total_activities": total_activities,
            "successful_activities": successful_activities,
            "failed_activities": failed_activities,
            "success_rate": (successful_activities / total_activities * 100) if total_activities > 0 else 0,
            "action_breakdown": list(action_breakdown),
            "level_breakdown": list(level_breakdown),
        }
        
        logger.info(f"Generated activity report: {total_activities} activities in {days} days")
        return report
        
    except Exception as e:
        logger.error(f"Error generating activity report: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@shared_task(name="apps.activity_log.tasks.cleanup_anonymous_logs")
def cleanup_anonymous_logs(days: int = 3):
    """
    Delete anonymous user logs older than specified days.
    Anonymous logs are less important and can be deleted sooner.
    
    Args:
        days: Number of days to keep anonymous logs (default 3)
    """
    try:
        from apps.activity_log.models import ActivityLog
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete anonymous logs
        old_anonymous_logs = ActivityLog.objects.filter(
            user__isnull=True,
            created_at__lt=cutoff_date
        )
        
        count = old_anonymous_logs.count()
        if count > 0:
            deleted_count, _ = old_anonymous_logs.delete()
            logger.info(f"Deleted {deleted_count} anonymous activity logs older than {days} days")
            return {
                "success": True,
                "deleted_count": deleted_count
            }
        else:
            return {
                "success": True,
                "deleted_count": 0,
                "message": "No old anonymous logs found"
            }
            
    except Exception as e:
        logger.error(f"Error deleting anonymous activity logs: {e}")
        return {
            "success": False,
            "error": str(e)
        }
