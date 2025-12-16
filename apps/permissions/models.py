from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, AdminStatusModel, DescriptiveModel, ActivableModel


User = get_user_model()


class PermissionCategory(TimeStampModel, DescriptiveModel):
    """
    Categories for grouping permissions logically
    """

    class Meta:
        verbose_name = "دسته بندی دسترسی"
        verbose_name_plural = "دسته بندی های دسترسی"
        ordering = ["name"]


class Permission(TimeStampModel, DescriptiveModel, ActivableModel):
    """
    Custom permission model to define granular permissions in the system
    """

    category = models.ForeignKey("PermissionCategory", on_delete=models.CASCADE, related_name="permissions")
    code_name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "سطح دسترسی"
        verbose_name_plural = "سطوح دسترسی"
        ordering = ["category__name", "name"]
        indexes = [
            models.Index(fields=["code_name"]),
        ]

    def __str__(self):
        return f"{self.category.name}: {self.name}"


class UserTypePermission(TimeStampModel):
    """
    Default permissions for each user type
    """

    # Using 'Group' as UserType in accordance with the project's naming ctainoention
    user_type = models.ForeignKey(
        "authentication.UserType",  # Assuming the Group model is in the authentication app
        on_delete=models.CASCADE,
        related_name="default_permissions",
    )
    permission = models.ForeignKey("Permission", on_delete=models.CASCADE, related_name="user_type_permissions")

    class Meta:
        verbose_name = "سطح دسترسی نقش کاربری"
        verbose_name_plural = "سطوح دسترسی نقش کاربری"
        unique_together = ("user_type", "permission")


class UserPermission(TimeStampModel):
    """
    Custom permissions assigned to individual users
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="custom_permissions")
    permission = models.ForeignKey("Permission", on_delete=models.CASCADE, related_name="user_permissions")
    # True means this permission is granted, False means explicitly denied
    is_granted = models.BooleanField(default=True, help_text=_("Whether this permission is granted or denied"))

    class Meta:
        verbose_name = "سطح دسترسی کاربر"
        verbose_name_plural = "سطوح دسترسی کاربر"
        unique_together = ("user", "permission")
