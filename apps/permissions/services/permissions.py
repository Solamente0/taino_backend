from typing import List, Optional
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.permissions.models import Permission, UserPermission, UserTypePermission
from base_utils.services import AbstractBaseService

User = get_user_model()


class PermissionService(AbstractBaseService):
    """
    Service for handling permission-related operations
    """

    @staticmethod
    def has_permission(user: User, permission_code: str) -> bool:
        """
        Check if a user has a specific permission

        Args:
            user: The user to check permissions for
            permission_code: The code name of the permission

        Returns:
            bool: True if the user has permission, False otherwise
        """
        if user.is_superuser:
            return True

        try:
            # Check for explicit user permission denial first
            user_permission = UserPermission.objects.filter(user=user, permission__code_name=permission_code).first()

            if user_permission:
                return user_permission.is_granted

            # Get all permissions the user should have (including secretary-lawyer relationship)
            all_permissions = PermissionService.get_user_permissions(user)

            # Check if the specific permission is in the user's permissions
            return all_permissions.filter(code_name=permission_code).exists()

        except Exception:
            return False

    @staticmethod
    def get_user_permissions(user: User) -> List[Permission]:
        """
        Get all permissions assigned to a user (both direct and via user type)
        Including lawyer permissions for secretary users

        Args:
            user: The user to get permissions for

        Returns:
            List[Permission]: A list of Permission objects
        """
        if user.is_superuser:
            return Permission.objects.filter(is_active=True)

        # Get user's role
        user_role = user.role

        # Get explicitly granted user permissions
        granted_permissions = UserPermission.objects.filter(user=user, is_granted=True).values_list(
            "permission_id", flat=True
        )

        # Get explicitly denied user permissions
        denied_permissions = UserPermission.objects.filter(user=user, is_granted=False).values_list(
            "permission_id", flat=True
        )

        # Initialize permission IDs set
        permission_ids = set(granted_permissions)

        if user_role:
            # Get permissions from user type (role)
            type_permissions = UserTypePermission.objects.filter(user_type=user_role, permission__is_active=True).values_list(
                "permission_id", flat=True
            )

            permission_ids.update(type_permissions)

            # If user is a secretary, add the lawyer permissions
            if user_role.static_name == "secretary":
                try:
                    # Get lawyer permissions using a safer approach
                    from apps.authentication.models import UserType, UserProfile

                    # First check if the user has a profile with an assigned lawyer
                    profile = UserProfile.objects.filter(user=user).first()

                    if profile and profile.lawyer:
                        # Find lawyer role
                        lawyer_role = UserType.objects.filter(static_name="lawyer").first()

                        if lawyer_role:
                            # Get all permissions assigned to the lawyer role
                            lawyer_permissions = UserTypePermission.objects.filter(
                                user_type=lawyer_role, permission__is_active=True
                            ).values_list("permission_id", flat=True)

                            permission_ids.update(lawyer_permissions)
                except ImportError:
                    # If models can't be imported, try a different approach
                    try:
                        # Get the lawyer role directly
                        from apps.authentication.models import UserType

                        lawyer_role = UserType.objects.filter(static_name="lawyer").first()

                        if lawyer_role:
                            # Get all permissions assigned to the lawyer role
                            lawyer_permissions = UserTypePermission.objects.filter(
                                user_type=lawyer_role, permission__is_active=True
                            ).values_list("permission_id", flat=True)

                            permission_ids.update(lawyer_permissions)
                    except Exception:
                        pass
                except Exception:
                    pass

        # Get final permissions, respecting the hierarchy
        return (
            Permission.objects.filter(id__in=permission_ids)
            .exclude(id__in=denied_permissions)
            .filter(is_active=True)
            .distinct()
        )

    @staticmethod
    def get_permissions_by_role(role_static_name: str) -> List[Permission]:
        """
        Get all permissions assigned to a specific role

        Args:
            role_static_name: The static name of the role

        Returns:
            List[Permission]: A list of Permission objects
        """
        from apps.authentication.models import UserType

        try:
            user_type = UserType.objects.get(static_name=role_static_name, is_active=True)

            # Get permissions from user type
            type_permissions = UserTypePermission.objects.filter(user_type=user_type, permission__is_active=True).values_list(
                "permission_id", flat=True
            )

            return Permission.objects.filter(id__in=type_permissions, is_active=True).distinct()
        except UserType.DoesNotExist:
            return []

    @staticmethod
    def assign_permission_to_user(user: User, permission_code: str, is_granted: bool = True) -> UserPermission:
        """
        Assign a permission to a user

        Args:
            user: The user to assign the permission to
            permission_code: The code name of the permission
            is_granted: Whether to grant or deny the permission

        Returns:
            UserPermission: The created or updated UserPermission object
        """
        permission = Permission.objects.get(code_name=permission_code)

        user_permission, created = UserPermission.objects.update_or_create(
            user=user, permission=permission, defaults={"is_granted": is_granted}
        )

        return user_permission

    @staticmethod
    def assign_permission_to_user_type(user_type_id: str, permission_code: str) -> UserTypePermission:
        """
        Assign a permission to a user type (group)

        Args:
            user_type_id: The ID of the user type
            permission_code: The code name of the permission

        Returns:
            UserTypePermission: The created UserTypePermission object
        """
        from apps.authentication.models import UserType

        user_type = UserType.objects.get(pid=user_type_id)
        permission = Permission.objects.get(code_name=permission_code)

        user_type_permission, created = UserTypePermission.objects.get_or_create(user_type=user_type, permission=permission)

        return user_type_permission

    @staticmethod
    def remove_permission_from_user_type(user_type_id: str, permission_code: str) -> bool:
        """
        Remove a permission from a user type

        Args:
            user_type_id: The ID of the user type
            permission_code: The code name of the permission

        Returns:
            bool: True if the permission was removed, False otherwise
        """
        from apps.authentication.models import UserType

        try:
            user_type = UserType.objects.get(pid=user_type_id)
            permission = Permission.objects.get(code_name=permission_code)

            deleted, _ = UserTypePermission.objects.filter(user_type=user_type, permission=permission).delete()

            return deleted > 0
        except Exception:
            return False

    @staticmethod
    def remove_permission_from_user(user: User, permission_code: str) -> bool:
        """
        Remove a custom permission from a user

        Args:
            user: The user to remove the permission from
            permission_code: The code name of the permission

        Returns:
            bool: True if the permission was removed, False otherwise
        """
        try:
            permission = Permission.objects.get(code_name=permission_code)

            deleted, _ = UserPermission.objects.filter(user=user, permission=permission).delete()

            return deleted > 0
        except Exception:
            return False
