from celery import shared_task


@shared_task
def delete_old_notifications_task():
    """
    Delete notifications older than the retention period set in GeneralSettings.
    This task should run daily to clean up old notifications.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.notification.models import UserSentNotification
    from apps.setting.services.query import GeneralSettingsQuery

    # Get retention period from settings (default to 30 days)
    retention_days = GeneralSettingsQuery.get_notification_retention_days()

    # Calculate the cutoff date
    cutoff_date = timezone.now() - timedelta(days=retention_days)

    # Delete notifications older than the cutoff date
    deleted_count = UserSentNotification.objects.filter(created_at__lt=cutoff_date).delete()

    print(f"Notification cleanup: Deleted {deleted_count} notifications older than {retention_days} days")
    return deleted_count
