import logging
import uuid
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.authentication.models import UserDevice
from base_utils.services import AbstractBaseService

User = get_user_model()
logger = logging.getLogger(__name__)


class DeviceService(AbstractBaseService):
    """
    Service for managing user devices and ensuring single-device login policy.
    """

    @staticmethod
    def register_device(user, device_id, user_agent, ip_address, device_name=None):
        """
        Register a new device for a user and deactivate any previously active devices.
        """
        # Deactivate any existing active devices for this user
        UserDevice.deactivate_all_user_devices(user)

        # Create or update the device record
        device, created = UserDevice.objects.update_or_create(
            user=user,
            device_id=device_id,
            defaults={"user_agent": user_agent, "ip_address": ip_address, "device_name": device_name, "is_active": True},
        )

        return device

    @staticmethod
    def deactivate_device(user, device_id):
        """
        Deactivate a specific device.
        """
        try:
            device = UserDevice.objects.get(user=user, device_id=device_id)
            device.is_active = False
            device.save(update_fields=["is_active"])
            return True
        except UserDevice.DoesNotExist:
            return False

    @staticmethod
    def deactivate_all_devices(user):
        """
        Deactivate all devices for a user.
        """
        return UserDevice.deactivate_all_user_devices(user)

    @staticmethod
    def get_user_devices(user):
        """
        Get all devices for a user.
        """
        return UserDevice.objects.filter(user=user).order_by("-last_login")

    @staticmethod
    def get_active_device(user):
        """
        Get the active device for a user.
        """
        return UserDevice.get_active_device(user)

    @staticmethod
    def generate_device_id():
        """
        Generate a unique device identifier.
        """
        return str(uuid.uuid4())

    @staticmethod
    def activate_device(user, device_id):
        """
        Activate a specific device and deactivate all others.
        """
        try:
            # Deactivate all devices first
            UserDevice.deactivate_all_user_devices(user)

            # Activate the requested device
            device = UserDevice.objects.get(user=user, device_id=device_id)
            device.is_active = True
            device.save(update_fields=["is_active", "last_login"])
            return device
        except UserDevice.DoesNotExist:
            raise ValidationError(_("Device not found"))
