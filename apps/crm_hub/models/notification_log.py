from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.crm_hub.models.crm_campaign import NotificationChannel
from base_utils.base_models import TimeStampModel, ActivableModel, DescriptiveModel

User = get_user_model()


class CRMNotificationLog(TimeStampModel):
    """
    Log all CRM notifications sent to users
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="crm_notifications", verbose_name=_("کاربر"))

    campaign = models.ForeignKey(
        "CRMCampaign", on_delete=models.SET_NULL, null=True, related_name="notification_logs", verbose_name=_("کمپین")
    )

    channel = models.CharField(max_length=20, choices=NotificationChannel.choices, verbose_name=_("کانال ارسال"))

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", _("در انتظار")),
            ("sent", _("ارسال شده")),
            ("failed", _("ناموفق")),
            ("delivered", _("تحویل داده شده")),
            ("opened", _("باز شده")),
            ("clicked", _("کلیک شده")),
        ],
        default="pending",
        verbose_name=_("وضعیت"),
    )

    subject = models.CharField(max_length=255, blank=True, verbose_name=_("موضوع"))

    content = models.TextField(verbose_name=_("محتوا"))

    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان ارسال"))

    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان تحویل"))

    opened_at = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان باز شدن"))

    error_message = models.TextField(blank=True, verbose_name=_("پیام خطا"))

    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("اطلاعات اضافی"))

    class Meta:
        verbose_name = _("لاگ اعلان CRM")
        verbose_name_plural = _("لاگ‌های اعلان CRM")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["campaign", "status"]),
            models.Index(fields=["channel", "status"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.channel} - {self.status}"
