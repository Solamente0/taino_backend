from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel

User = get_user_model()


class UserProfile(TimeStampModel):
    """
    UserProfile model to store additional user information
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Lawyer-specific fields
    license_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("شماره پروانه وکالت"))
    bar_association = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("کانون وکلا"))
    lawyer_type = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("نوع وکالت"))
    office_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("تلفن دفتر"))
    office_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("آدرس دفتر"))
    office_location = models.JSONField(blank=True, null=True, verbose_name=_("موقعیت دفتر"))

    # Legal entity fields
    legal_entity_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("نام شخص حقوقی"))
    legal_entity_id = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("شناسه شخص حقوقی"))
    legal_entity_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("تلفن شخص حقوقی"))

    # Secretary fields
    is_secretary = models.BooleanField(default=False, verbose_name=_("منشی وکیل"))
    lawyer = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="secretaries", null=True, blank=True, verbose_name=_("وکیل مربوطه")
    )

    # Address and archive cabinet
    address = models.ForeignKey(
        "address.Address",
        on_delete=models.SET_NULL,
        related_name="user_profiles",
        null=True,
        blank=True,
        verbose_name=_("آدرس"),
    )
    archive_cabinet = models.ForeignKey(
        "lawyer_office.ArchiveCabinet",
        on_delete=models.SET_NULL,
        related_name="user_profiles",
        null=True,
        blank=True,
        verbose_name=_("کمد بایگانی"),
    )

    class Meta:
        verbose_name = _("پروفایل کاربر")
        verbose_name_plural = _("پروفایل های کاربر")

    def __str__(self):
        return f"Profile for {self.user.first_name} {self.user.last_name}"
