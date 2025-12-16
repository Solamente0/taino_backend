from rest_framework import permissions
from apps.permissions.services.permissions import PermissionService


class HasPermission(permissions.BasePermission):
    """
    Custom permission class to check if user has specific permission
    """

    def __init__(self, permission_code):
        self.permission_code = permission_code

    def has_permission(self, request, view):
        return PermissionService.has_permission(request.user, self.permission_code)


class HasAnyPermission(permissions.BasePermission):
    """
    Custom permission class to check if user has any of the specified permissions
    """

    def __init__(self, permission_codes):
        self.permission_codes = permission_codes

    def has_permission(self, request, view):
        for permission_code in self.permission_codes:
            if PermissionService.has_permission(request.user, permission_code):
                return True
        return False


class HasAllPermissions(permissions.BasePermission):
    """
    Custom permission class to check if user has all of the specified permissions
    """

    def __init__(self, permission_codes):
        self.permission_codes = permission_codes

    def has_permission(self, request, view):
        for permission_code in self.permission_codes:
            if not PermissionService.has_permission(request.user, permission_code):
                return False
        return True