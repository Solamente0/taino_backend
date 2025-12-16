from django.utils.translation import gettext_lazy as _
from functools import wraps
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from apps.permissions.services.permissions import PermissionService


def permission_required(permission_code):
    """
    Decorator to check if the user has a specific permission

    Args:
        permission_code: The code name of the permission

    Usage:
        @permission_required('app.create_something')
        def some_view(request, ...):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view, request, *args, **kwargs):
            if PermissionService.has_permission(request.user, permission_code):
                return view_func(view, request, *args, **kwargs)
            raise PermissionDenied(_("You don't have permission to perform this action"))

        return _wrapped_view

    return decorator


def any_permission_required(permission_codes):
    """
    Decorator to check if the user has any of the specified permissions

    Args:
        permission_codes: List of permission code names

    Usage:
        @any_permission_required(['app.create_something', 'app.edit_something'])
        def some_view(request, ...):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view, request, *args, **kwargs):
            for permission_code in permission_codes:
                if PermissionService.has_permission(request.user, permission_code):
                    return view_func(view, request, *args, **kwargs)
            raise PermissionDenied(_("You don't have permission to perform this action"))

        return _wrapped_view

    return decorator


def all_permissions_required(permission_codes):
    """
    Decorator to check if the user has all of the specified permissions

    Args:
        permission_codes: List of permission code names

    Usage:
        @all_permissions_required(['app.create_something', 'app.edit_something'])
        def some_view(request, ...):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view, request, *args, **kwargs):
            for permission_code in permission_codes:
                if not PermissionService.has_permission(request.user, permission_code):
                    raise PermissionDenied(_("You don't have permission to perform this action"))
            return view_func(view, request, *args, **kwargs)

        return _wrapped_view

    return decorator
