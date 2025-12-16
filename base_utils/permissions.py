import logging

from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.services.auth import TainoAuthenticationBackend

log = logging.getLogger(__name__)
User = get_user_model()


class BasePermissionChecker:

    @staticmethod
    def is_mobile_user(user: User) -> bool:
        return user and user.is_active and (user.is_admin == False or user.is_superuser)  # and (user.is_superuser == False)

    @staticmethod
    def is_admin_user(user: User) -> bool:
        return user and user.is_active and (user.is_admin or user.is_superuser)


class HasTainoMobileUserPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return BasePermissionChecker.is_mobile_user(user)


class HasTainoAdminUserPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return BasePermissionChecker.is_admin_user(user)


class RefreshHasAdminAccess(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        try:
            refresh = RefreshToken(request.data.get("refresh"))
            user_id = refresh.get("user_pid")
            user = User.objects.get(pid=user_id)
            if not BasePermissionChecker.is_admin_user(user):
                raise PermissionDenied()
            return True
        except Exception as e:
            raise PermissionDenied()


class AccessTokenHasAdminAccess(BasePermission):
    def has_permission(self, request, view):
        try:
            username = request.data.get("username")
            password = request.data.get("password")
            auth_backend = TainoAuthenticationBackend(username, password)
            user = auth_backend.authenticate_credentials()
            if not BasePermissionChecker.is_admin_user(user):
                raise PermissionDenied()
            return True
        except Exception as e:
            return False
