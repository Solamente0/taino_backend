# apps/subscription/tasks.py

import logging
from celery import shared_task
from django.utils import timezone
from apps.subscription.models import UserSubscription
from apps.subscription.models.subscription import SubscriptionStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="apps.subscription.tasks.check_expired_subscriptions")
def check_expired_subscriptions():
    """Check for and update expired subscriptions"""
    now = timezone.now()

    # Find subscriptions that have expired but still marked as active
    expired_subscriptions = UserSubscription.objects.filter(status=SubscriptionStatus.ACTIVE, end_date__lt=now)
    count = 0

    for subscription in expired_subscriptions:
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.save()

        # Also update user's premium status
        from apps.subscription.services.subscription import SubscriptionService

        SubscriptionService.sync_premium_status_with_subscription(subscription.user)
        count += 1

    return f"Updated {count} expired subscriptions"


@shared_task(bind=True, name="apps.subscription.tasks.sync_premium_status")
def sync_premium_status():
    """Sync premium status for all users based on their subscription status"""
    from apps.subscription.services.subscription import SubscriptionService

    updated_count, error_count = SubscriptionService.sync_all_users_premium_status()

    return f"Premium status synced for {updated_count} users with {error_count} errors"
