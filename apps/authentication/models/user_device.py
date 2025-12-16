from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from base_utils.base_models import TimeStampModel, AdminStatusModel

User = get_user_model()


class UserDevice(TimeStampModel, AdminStatusModel):
    """
    Model to track and manage user devices.
    Ensures that a user can only be logged in from one device at a time.
    """

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="devices", verbose_name=_("کاربر"))
    device_id = models.CharField(
        max_length=255, verbose_name=_("شناسه دستگاه"), help_text=_("A unique identifier for the device")
    )
    device_name = models.CharField(max_length=255, verbose_name=_("نام دستگاه"), null=True, blank=True)
    user_agent = models.TextField(verbose_name=_("User Agent"), help_text=_("Browser/Application information"))
    ip_address = models.GenericIPAddressField(verbose_name=_("آدرس IP"), null=True, blank=True)
    last_login = models.DateTimeField(auto_now=True, verbose_name=_("آخرین ورود"))
    is_active = models.BooleanField(
        default=True, verbose_name=_("فعال"), help_text=_("Indicates if this device has an active session")
    )

    class Meta:
        verbose_name = _("دستگاه کاربر")
        verbose_name_plural = _("دستگاه‌های کاربر")
        unique_together = ["user", "device_id"]

    def __str__(self):
        return f"{self.user} - {self.device_name or self.device_id}"

    @classmethod
    def deactivate_all_user_devices(cls, user):
        """Deactivate all active devices for a user"""
        return cls.objects.filter(user=user, is_active=True).update(is_active=False)

    @classmethod
    def get_active_device(cls, user):
        """Get the currently active device for a user, if any"""
        return cls.objects.filter(user=user, is_active=True).first()
