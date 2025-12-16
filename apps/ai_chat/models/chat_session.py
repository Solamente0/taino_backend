# apps/chat/models/ai_session.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import (
    TimeStampModel,
    ActivableModel,
    AdminStatusModel,
    CreatorModel,
)

User = get_user_model()


class AISessionStatusEnum(models.TextChoices):
    PENDING = "pending", _("در انتظار")
    ACTIVE = "active", _("فعال")
    COMPLETED = "completed", _("تکمیل شده")
    EXPIRED = "expired", _("منقضی شده")
    CANCELLED = "cancelled", _("لغو شده")


class ChatTypeEnum(models.TextChoices):
    AI = "ai", _("گفتگو با هوش مصنوعی")


class AISession(TimeStampModel, ActivableModel, AdminStatusModel, CreatorModel):
    """
    Model for chat sessions between users and lawyers/admin/AI
    """

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client_ai_sessions", verbose_name=_("کاربر"))

    chat_type = models.CharField(
        max_length=20, choices=ChatTypeEnum.choices, default=ChatTypeEnum.LAWYER, verbose_name=_("نوع گفتگو")
    )

    status = models.CharField(
        max_length=20, choices=AISessionStatusEnum.choices, default=AISessionStatusEnum.PENDING, verbose_name=_("وضعیت")
    )

    title = models.CharField(max_length=255, verbose_name=_("عنوان"))

    # Fee and time details
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("مبلغ"))
    time_limit_minutes = models.PositiveIntegerField(default=30, verbose_name=_("محدودیت زمان (دقیقه)"))

    start_date = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان شروع"))
    end_date = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان پایان"))

    # For AI chat, we can store the last context
    ai_context = models.JSONField(null=True, blank=True, verbose_name=_("کانتکست هوش مصنوعی"))

    # Meta data
    total_messages = models.PositiveIntegerField(default=0, verbose_name=_("تعداد کل پیام‌ها"))
    unread_client_messages = models.PositiveIntegerField(default=0, verbose_name=_("پیام‌های خوانده نشده کاربر"))
    unread_consultant_messages = models.PositiveIntegerField(default=0, verbose_name=_("پیام‌های خوانده نشده مشاور"))

    # If this chat is synced to MongoDB (for the WebSocket part)
    is_synced_to_mongo = models.BooleanField(default=False, verbose_name=_("همگام‌سازی با مونگو"))
    mongo_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("شناسه مونگو"))

    class Meta:
        verbose_name = _("جلسه گفتگو")
        verbose_name_plural = _("جلسات گفتگو")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["consultant"]),
            models.Index(fields=["status"]),
            models.Index(fields=["chat_type"]),
        ]

    def __str__(self):
        return f"{self.get_chat_type_display()} - {self.client} - {self.created_at}"

    def mark_all_read_for_client(self):
        """Mark all messages as read for the client"""
        self.unread_client_messages = 0
        self.save(update_fields=["unread_client_messages"])
        self.messages.filter(is_read_by_client=False).update(is_read_by_client=True)

    def mark_all_read_for_consultant(self):
        """Mark all messages as read for the consultant"""
        self.unread_consultant_messages = 0
        self.save(update_fields=["unread_consultant_messages"])
        self.messages.filter(is_read_by_consultant=False).update(is_read_by_consultant=True)

    @property
    def remaining_time_seconds(self):
        """
        Calculate the remaining time for this chat session in seconds.
        Returns 0 if the session has expired.
        """
        from django.utils import timezone

        if not self.end_date:
            return 0

        now = timezone.now()

        if now > self.end_date:
            return 0

        # Calculate remaining time in seconds
        delta = self.end_date - now
        return delta.total_seconds()

    @property
    def remaining_time_minutes(self):
        """
        Calculate the remaining time for this chat session in minutes.
        Returns 0 if the session has expired.
        """
        return int(self.remaining_time_seconds / 60)
