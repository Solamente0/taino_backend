"""
apps/crm_hub/signals.py
Signals for automatic engagement tracking
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.activity_log.models import ActivityLog

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=ActivityLog)
def update_engagement_on_activity(sender, instance, created, **kwargs):
    """
    Update user engagement when new activity is logged
    """
    if created and instance.user:
        try:
            # Import here to avoid circular imports
            from apps.crm_hub.tasks import update_user_engagement_task
            
            # Update engagement asynchronously
            update_user_engagement_task.apply_async(
                kwargs={'user_pid': instance.user.pid},
                countdown=60  # Wait 1 minute to batch multiple activities
            )
        except Exception as e:
            logger.error(f"Error triggering engagement update: {e}")


@receiver(post_save, sender=User)
def create_engagement_on_user_creation(sender, instance, created, **kwargs):
    """
    Create engagement record when new user is created
    """
    if created:
        try:
            from apps.crm_hub.models import CRMUserEngagement
            
            CRMUserEngagement.objects.get_or_create(user=instance)
            logger.info(f"Created engagement record for user {instance.pid}")
        except Exception as e:
            logger.error(f"Error creating engagement record: {e}")
