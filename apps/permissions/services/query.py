from django.db.models import QuerySet

from apps.permissions.models import Permission, PermissionCategory, UserPermission, UserTypePermission
from base_utils.services import AbstractBaseQuery


class PermissionQuery(AbstractBaseQuery):
    """
    Query service for permission-related models
    """

    @staticmethod
    def get_active_permissions() -> QuerySet[Permission]:
        """
        Get all active permissions

        Returns:
            QuerySet: QuerySet of active Permission objects
        """
        return Permission.objects.filter(is_active=True)

    @staticmethod
    def get_active_permission_categories() -> QuerySet[PermissionCategory]:
        """
        Get all permission categories with active permissions

        Returns:
            QuerySet: QuerySet of PermissionCategory objects
        """
        categories_with_active_permissions = (
            Permission.objects.filter(is_active=True).values_list("category_id", flat=True).distinct()
        )

        return PermissionCategory.objects.filter(id__in=categories_with_active_permissions)

    @staticmethod
    def get_user_permissions(user_id: str) -> QuerySet[UserPermission]:
        """
        Get all custom permissions assigned to a user

        Args:
            user_id: The ID of the user

        Returns:
            QuerySet: QuerySet of UserPermission objects
        """
        return UserPermission.objects.filter(user__pid=user_id).select_related("permission", "permission__category")

    @staticmethod
    def get_user_type_permissions(user_type_id: str) -> QuerySet[UserTypePermission]:
        """
        Get all permissions assigned to a user type

        Args:
            user_type_id: The ID of the user type

        Returns:
            QuerySet: QuerySet of UserTypePermission objects
        """
        return UserTypePermission.objects.filter(user_type__pid=user_type_id).select_related(
            "permission", "permission__category"
        )

    @staticmethod
    def get_permissions_by_category() -> dict:
        """
        Get all permissions grouped by category

        Returns:
            dict: A dictionary with category names as keys and lists of permissions as values
        """
        permissions_by_category = {}

        for category in PermissionCategory.objects.all():
            permissions = Permission.objects.filter(category=category, is_active=True)

            if permissions.exists():
                permissions_by_category[category.name] = list(permissions)

        return permissions_by_category
