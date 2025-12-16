from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, CreatorModel, ActivableModel, AdminStatusModel

User = get_user_model()


class SMSMessage(TimeStampModel, CreatorModel, ActivableModel, AdminStatusModel):
    """
    Model to store SMS messages sent to clients
    """

    STATUS_CHOICES = (
        ("pending", _("در انتظار ارسال")),
        ("sent", _("ارسال شده")),
        ("failed", _("ناموفق")),
        ("insufficient_balance", _("موجودی ناکافی")),
    )

    SOURCE_TYPE_CHOICES = (
        ("manual", _("ارسال دستی")),
        ("auto_court_session", _("یادآوری خودکار جلسه")),
        ("auto_objection", _("یادآوری خودکار اعتراض")),
        ("auto_exchange", _("یادآوری خودکار تبادل لایحه")),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_sms")
    recipient_number = models.CharField(max_length=20, verbose_name=_("شماره گیرنده"))
    recipient_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("نام گیرنده"))
    content = models.TextField(verbose_name=_("متن پیامک"))
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending", verbose_name=_("وضعیت"))
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES, default="manual", verbose_name=_("نوع منبع"))
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ ارسال"))
    error_message = models.TextField(blank=True, null=True, verbose_name=_("پیام خطا"))

    # Reference to related objects
    client = models.ForeignKey(
        "lawyer_office.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_messages",
        verbose_name=_("موکل"),
    )
    case = models.ForeignKey(
        "lawyer_office.LawOfficeCase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_messages",
        verbose_name=_("پرونده"),
    )
    calendar_event = models.ForeignKey(
        "court_calendar.CourtCalendarEvent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_messages",
        verbose_name=_("رویداد تقویم"),
    )

    class Meta:
        verbose_name = _("پیامک")
        verbose_name_plural = _("پیامک ها")
        ordering = ["-created_at"]

    def __str__(self):
        return f"پیامک به {self.recipient_name or self.recipient_number} - {self.get_status_display()}"
