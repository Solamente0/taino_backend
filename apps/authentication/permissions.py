import logging
import uuid

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from apps.authentication.models import UserDevice

logger = logging.getLogger(__name__)
User = get_user_model()


class SingleDevicePermission(permissions.BasePermission):
    """
    Permission to ensure a user can only be logged in from one device at a time.
    """

    def get_device_id(self, request):
        """Get device ID from cookies or headers"""
        device_id = request.COOKIES.get("device_id")
        if not device_id:
            device_id = request.META.get("HTTP_X_DEVICE_ID")
        #
        # if not device_id:
        #     device_id = str(uuid.uuid4())

        return device_id

    def has_permission(self, request, view):
        """Check if the request comes from the authorized device"""
        # Skip permission for admin paths and authenticate endpoints
        if (
            request.path.startswith("/admin/")
            or request.path.startswith("/api/auth/login")
            or request.path.startswith("/api/auth/logout")
        ):
            return True

        device_id = self.get_device_id(request)

        data = request.data
        user = request.user

        if user and user.is_authenticated:
            if not device_id:
                raise PermissionDenied(_("Device ID missing"))

        if "username" in data:
            phone_number = data.get("username")[1:]
            user = User.objects.get(phone_number=phone_number)
            #
            # if not device_id:
            #     device_id = str(uuid.uuid4())

        if device_id:
            # Get active device for this user
            active_device = UserDevice.get_active_device(user)
            # If there's an active device and it's not this one
            if active_device and active_device.device_id != device_id:
                # Existing active session on another device
                raise PermissionDenied("شما با یک دستگاه دیگر وارد سیستم شده اید. باید ابتدا از آن دستگاه خارج شوید!")
            return True

        return True  # Allow non-authenticated requests to pass through
