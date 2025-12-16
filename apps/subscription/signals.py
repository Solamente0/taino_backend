# apps/subscription/signals.py
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.subscription.models import UserSubscription

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserSubscription)
def update_user_premium_status(sender, instance, created, **kwargs):
    """
    Update user's premium status when subscription status changes
    """
    # Only process for active or expired/canceled subscriptions
    if instance.status in ["active", "expired", "canceled"]:
        from apps.subscription.services.subscription import SubscriptionService

        # Set premium status to True for active subscriptions, False otherwise
        is_premium = instance.status == "active"

        # Check if user has other active subscriptions before setting to False
        if not is_premium:
            has_active = SubscriptionService.has_active_subscription(instance.user)
            if has_active:
                # User has other active subscriptions, so don't change premium status
                return

        # Update user's premium status
        SubscriptionService.update_user_premium_status(instance.user, is_premium)
