from rest_framework import permissions
from apps.subscription.services.subscription import SubscriptionService


class HasActiveSubscriptionPermission(permissions.BasePermission):
    """
    Permission class to check if user has an active subscription
    """

    message = "This feature requires an active subscription."

    def has_permission(self, request, view):
        # Allow access to subscription-related views (to let users subscribe)
        if view.__class__.__name__ == "UserSubscriptionViewSet":
            return True

        # Allow authenticated users with an active subscription
        return request.user and request.user.is_authenticated and SubscriptionService.has_active_subscription(request.user)


class HasPremiumAccessPermission(permissions.BasePermission):
    """
    Permission class to check if user has premium access
    (either via subscription or has_premium_account flag)
    """

    message = "This feature requires premium access."

    def has_permission(self, request, view):
        # Allow access to subscription-related views (to let users subscribe)
        if view.__class__.__name__ == "UserSubscriptionViewSet":
            return True

        # Allow authenticated users with premium access
        return request.user and request.user.is_authenticated and SubscriptionService.has_premium_access(request.user)


class HasLawyerOrSecretarySubscriptionPermission(permissions.BasePermission):
    """
    Permission class to check if user has an active subscription or is a secretary of a lawyer with an active subscription
    """

    message = "This feature requires an active subscription. Please contact your lawyer."

    def has_permission(self, request, view):
        # Allow access to subscription-related views (to let users subscribe)
        if view.__class__.__name__ == "UserSubscriptionViewSet":
            return True

        # Check if the user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # If user is a lawyer, check their own subscription
        is_lawyer = hasattr(request.user, "role") and request.user.role and request.user.role.static_name == "lawyer"
        if is_lawyer:
            from apps.subscription.services.subscription import SubscriptionService

            return SubscriptionService.has_active_subscription(request.user)

        # If user is a secretary, check their lawyer's subscription
        is_secretary = (
            hasattr(request.user, "profile")
            and request.user.profile
            and getattr(request.user.profile, "is_secretary", False)
            and request.user.profile.lawyer
        )

        if is_secretary:
            from apps.subscription.services.subscription import SubscriptionService

            return SubscriptionService.has_active_subscription(request.user.profile.lawyer)

        # If neither lawyer nor secretary, deny access
        return False
