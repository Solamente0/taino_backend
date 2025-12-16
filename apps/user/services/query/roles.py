# apps/user/services/roles.py

from django.db.models import QuerySet

from apps.authentication.models import UserType
from base_utils.services import AbstractBaseQuery


class UserRoleService(AbstractBaseQuery):
    """
    Service for user roles
    """

    @staticmethod
    def get_available_roles() -> QuerySet:
        """
        Get all available user roles
        """

        return UserType.objects.filter(is_active=True)

    @staticmethod
    def get_user_roles(user) -> QuerySet:
        """
        Get roles for a specific user
        """

        roles = UserType.objects.filter(users=user, is_active=True)

        return roles
