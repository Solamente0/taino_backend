# apps/subscription/services/subscription.py
import logging
from django.utils import timezone
from datetime import timedelta
from apps.subscription.models import UserSubscription
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service class for subscription-related operations"""

    @staticmethod
    def has_premium_access(user):
        """
        Check if user has access to premium features

        This checks if the user has an active subscription or has premium access enabled
        directly on their user account (for special cases).

        Args:
            user: The user to check

        Returns:
            bool: True if user has premium access, False otherwise
        """
        print(f"Checking premium access for user: {user}", flush=True)

        # First check if user has premium access granted directly
        if hasattr(user, "has_premium_account") and user.has_premium_account:
            print(f"User {user} has direct premium account access", flush=True)
            return True
        print(f"User {user} does not have direct premium account access", flush=True)

        is_secretary = (
            hasattr(user, "profile")
            and user.profile
            and getattr(user.profile, "is_secretary", False)
            and user.profile.lawyer is not None
        )
        print(f"User {user} is_secretary: {is_secretary}", flush=True)

        if is_secretary:
            lawyer = user.profile.lawyer
            print(f"Secretary {user} checking lawyer {lawyer} premium status", flush=True)

            # Check if lawyer has premium account or active subscription
            if hasattr(lawyer, "has_premium_account") and lawyer.has_premium_account:
                print(f"Lawyer {lawyer} has direct premium account, granting access to secretary", flush=True)
                return True
            print(f"Lawyer {lawyer} does not have direct premium account, checking subscription", flush=True)

            lawyer_has_subscription = SubscriptionService.has_active_subscription(lawyer)
            print(f"Lawyer {lawyer} has active subscription: {lawyer_has_subscription}", flush=True)
            return lawyer_has_subscription

        # Then check if user has an active subscription
        user_has_subscription = SubscriptionService.has_active_subscription(user)
        print(f"User {user} has active subscription: {user_has_subscription}", flush=True)
        return user_has_subscription

    @staticmethod
    def get_active_subscription(user):
        """
        Get the user's active subscription

        Args:
            user: The user to check

        Returns:
            UserSubscription: The active subscription or None if not found
        """
        # Check if user is a secretary and use lawyer's subscription if so
        is_secretary = (
            hasattr(user, "profile")
            and user.profile
            and getattr(user.profile, "is_secretary", False)
            and user.profile.lawyer is not None
        )

        if is_secretary:
            user = user.profile.lawyer

        now = timezone.now()

        # Get the most recent active subscription that's not expired
        subscription = (
            UserSubscription.objects.filter(user=user, status="active", start_date__lte=now, end_date__gte=now)
            .order_by("-created_at")
            .first()
        )

        return subscription

    @staticmethod
    def has_active_subscription(user):
        """
        Check if the user has an active subscription

        Args:
            user: The user to check

        Returns:
            bool: True if user has an active subscription, False otherwise
        """
        return SubscriptionService.get_active_subscription(user) is not None

    @staticmethod
    def is_subscription_expiring_soon(subscription, days=7):
        """
        Check if a subscription is expiring soon

        Args:
            subscription: The subscription to check
            days: Number of days to consider as "soon" (default: 7)

        Returns:
            bool: True if the subscription is expiring within the specified days
        """
        if not subscription or subscription.status != "active" or not subscription.end_date:
            return False

        now = timezone.now()
        return now < subscription.end_date <= (now + timedelta(days=days))

    @staticmethod
    def get_days_remaining(subscription):
        """
        Get the number of days remaining in a subscription

        Args:
            subscription: The subscription to check

        Returns:
            int: Number of days remaining, 0 if expired, or None if not applicable
        """
        if not subscription or subscription.status != "active" or not subscription.end_date:
            return None

        now = timezone.now()
        if now < subscription.end_date:
            delta = subscription.end_date - now
            return delta.days
        return 0

    @staticmethod
    def update_user_premium_status(user, is_premium=True):
        """
        Update user's premium status based on subscription status

        Args:
            user: The user to update
            is_premium: Whether the user should have premium status

        Returns:
            bool: True if user was updated, False otherwise
        """
        try:
            if user.has_premium_account != is_premium:
                user.has_premium_account = is_premium
                user.save(update_fields=["has_premium_account"])
                logger.info(f"Updated premium status for user {user.pid} to {is_premium}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating premium status for user {user.pid}: {str(e)}")
            return False

    @staticmethod
    def sync_premium_status_with_subscription(user):
        """
        Sync user's premium status with their subscription status

        Args:
            user: The user to update

        Returns:
            bool: True if user was updated, False if no change needed
        """
        has_active = SubscriptionService.has_active_subscription(user)
        return SubscriptionService.update_user_premium_status(user, has_active)

    @staticmethod
    def sync_all_users_premium_status():
        """
        Sync premium status for all users based on their subscription status

        Returns:
            tuple: (updated_count, error_count) - Number of users updated and errors encountered
        """

        updated_count = 0
        error_count = 0

        # Get all users with premium account
        users_with_premium = User.objects.filter(has_premium_account=True)

        for user in users_with_premium:
            try:
                # Check if user has active subscription
                has_active = SubscriptionService.has_active_subscription(user)

                # If not active, update premium status to False
                if not has_active:
                    SubscriptionService.update_user_premium_status(user, False)
                    updated_count += 1

            except Exception as e:
                logger.error(f"Error syncing premium status for user {user.pid}: {str(e)}")
                error_count += 1

        logger.info(f"Premium status sync completed: {updated_count} users updated, {error_count} errors")
        return updated_count, error_count
