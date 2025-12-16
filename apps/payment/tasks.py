# apps/subscription/tasks.py
from celery import shared_task
from django.utils import timezone
from apps.subscription.models import UserSubscription
from apps.subscription.models.subscription import SubscriptionStatus


@shared_task(bind=True, name="apps.subscription.tasks.check_expired_subscriptions")
def check_expired_subscriptions():
    """Check for and update expired subscriptions"""
    now = timezone.now()

    # Find subscriptions that have expired but still marked as active
    expired_subscriptions = UserSubscription.objects.filter(status=SubscriptionStatus.ACTIVE, end_date__lt=now)

    for subscription in expired_subscriptions:
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.save()

    return f"Updated {expired_subscriptions.count()} expired subscriptions"
