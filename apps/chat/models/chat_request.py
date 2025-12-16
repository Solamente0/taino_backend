# apps/chat/models/chat_request.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel, CreatorModel

User = get_user_model()


class ChatRequestStatusEnum(models.TextChoices):
    PENDING = "pending", _("در انتظار")
    ACCEPTED = "accepted", _("پذیرفته شده")
    REJECTED = "rejected", _("رد شده")
    CANCELLED = "cancelled", _("لغو شده")
    EXPIRED = "expired", _("منقضی شده")
    COMPLETED = "completed", _("تکمیل شده")


class ChatTypeEnum(models.TextChoices):
    LAWYER = "lawyer", _("گفتگو با وکیل")
    ADMIN = "admin", _("گفتگو با پشتیبانی")


class ChatRequest(TimeStampModel, ActivableModel, AdminStatusModel, CreatorModel):
    """
    درخواست مشاوره از کاربر (مثل یک آگهی در سایت‌های فریلنسر)
    """

    # اطلاعات درخواست‌دهنده
    client = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_requests", verbose_name=_("کاربر درخواست‌دهنده")
    )

    # مشخصات درخواست
    title = models.CharField(max_length=255, verbose_name=_("عنوان درخواست"))
    description = models.TextField(verbose_name=_("شرح درخواست"))

    # موقعیت مکانی (برای نمایش به وکلای همان شهر)
    country = models.ForeignKey("country.Country", on_delete=models.CASCADE, verbose_name=_("کشور"))
    state = models.ForeignKey("country.State", on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("استان"))
    city = models.ForeignKey("country.City", on_delete=models.CASCADE, verbose_name=_("شهر"))

    # تخصص مورد نیاز
    specialization = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("تخصص مورد نیاز"))

    # بودجه و زمان پیشنهادی
    proposed_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("بودجه پیشنهادی"))
    proposed_duration_days = models.PositiveIntegerField(default=7, verbose_name=_("مدت زمان پیشنهادی (روز)"))

    # این فیلدها اضافه شدند
    proposed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("حق‌الوکاله پیشنهادی"))
    proposed_time_minutes = models.PositiveIntegerField(default=30, verbose_name=_("زمان پیشنهادی (دقیقه)"))

    # وضعیت
    status = models.CharField(
        max_length=20, choices=ChatRequestStatusEnum.choices, default=ChatRequestStatusEnum.PENDING, verbose_name=_("وضعیت")
    )

    # زمان انقضا
    expires_at = models.DateTimeField(verbose_name=_("زمان انقضا"))

    chat_type = models.CharField(
        max_length=20, choices=ChatTypeEnum.choices, default=ChatTypeEnum.LAWYER, verbose_name=_("نوع گفتگو")
    )

    # وکیل انتخاب شده (پس از تایید)
    selected_lawyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_chat_requests",
        verbose_name=_("وکیل انتخاب شده"),
    )
    # پاسخ و زمان پاسخ (این فیلدها اضافه شدند)
    response_message = models.TextField(null=True, blank=True, verbose_name=_("پیام پاسخ"))
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان پاسخ"))

    # ترجیحات (این فیلدها اضافه شدند)
    location_preference = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("ترجیح مکانی"))
    preferred_time = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان ترجیحی"))
    # جلسه چت ایجاد شده
    chat_session = models.OneToOneField(
        "ChatSession", on_delete=models.SET_NULL, null=True, blank=True, related_name="request", verbose_name=_("جلسه چت")
    )

    class Meta:
        verbose_name = _("درخواست مشاوره")
        verbose_name_plural = _("درخواست‌های مشاوره")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["selected_lawyer"]),  # اضافه شد
            models.Index(fields=["status"]),
            models.Index(fields=["city"]),
            models.Index(fields=["specialization"]),
            models.Index(fields=["chat_type"]),  # اضافه شد
        ]

    def __str__(self):
        return f"{self.title} - {self.client.get_full_name() if hasattr(self.client, 'get_full_name') else self.client}"


class LawyerProposal(TimeStampModel, ActivableModel, AdminStatusModel):
    """
    پیشنهاد وکیل برای یک درخواست (مثل bid در سایت‌های فریلنسر)
    """

    # درخواست مرتبط
    chat_request = models.ForeignKey(
        ChatRequest, on_delete=models.CASCADE, related_name="proposals", verbose_name=_("درخواست")
    )

    # وکیل
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="proposals", verbose_name=_("وکیل"))

    # پیشنهاد وکیل
    proposal_message = models.TextField(verbose_name=_("پیام پیشنهاد"))
    proposed_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("حق‌الوکاله پیشنهادی"))
    proposed_duration = models.PositiveIntegerField(verbose_name=_("مدت زمان پیشنهادی (روز)"))

    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", _("در انتظار")),
            ("accepted", _("پذیرفته شده")),
            ("rejected", _("رد شده")),
        ],
        default="pending",
        verbose_name=_("وضعیت"),
    )

    # زمان پاسخ
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان پاسخ"))

    class Meta:
        verbose_name = _("پیشنهاد وکیل")
        verbose_name_plural = _("پیشنهادهای وکلا")
        ordering = ["-created_at"]
        unique_together = [["chat_request", "lawyer"]]
        indexes = [
            models.Index(fields=["chat_request"]),
            models.Index(fields=["lawyer"]),
            models.Index(fields=["status"]),
        ]
