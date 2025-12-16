# apps/chat/models/chat_message.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.notification.services.alarm import NotificationService
from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel

User = get_user_model()


class MessageTypeEnum(models.TextChoices):
    TEXT = "text", _("متن")
    IMAGE = "image", _("تصویر")
    FILE = "file", _("فایل")
    VOICE = "voice", _("صوت")
    SYSTEM = "system", _("سیستمی")


class AIMessage(TimeStampModel, ActivableModel, AdminStatusModel):
    """
    Model for individual chat messages in a session
    """

    ai_session = models.ForeignKey(
        "AISession", on_delete=models.CASCADE, related_name="messages", verbose_name=_("جلسه گفتگو")
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages", verbose_name=_("فرستنده"))

    message_type = models.CharField(
        max_length=20, choices=MessageTypeEnum.choices, default=MessageTypeEnum.TEXT, verbose_name=_("نوع پیام")
    )

    content = models.TextField(verbose_name=_("محتوا"))

    # For media files
    attachment = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_message_attachments",
        verbose_name=_("فایل پیوست"),
    )

    # AI or system messages
    is_ai = models.BooleanField(default=False, verbose_name=_("پیام هوش مصنوعی"))
    is_system = models.BooleanField(default=False, verbose_name=_("پیام سیستمی"))

    # Read status
    is_read_by_client = models.BooleanField(default=False, verbose_name=_("خوانده شده توسط کاربر"))
    is_read_by_consultant = models.BooleanField(default=False, verbose_name=_("خوانده شده توسط مشاور"))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان خوانده شدن"))

    # If this message is synced to MongoDB (for the WebSocket part)
    is_synced_to_mongo = models.BooleanField(default=False, verbose_name=_("همگام‌سازی با مونگو"))
    mongo_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("شناسه مونگو"))

    # If the message failed to deliver
    is_failed = models.BooleanField(default=False, verbose_name=_("خطا در ارسال"))
    failure_reason = models.TextField(null=True, blank=True, verbose_name=_("دلیل خطا"))

    class Meta:
        verbose_name = _("پیام گفتگو")
        verbose_name_plural = _("پیام‌های گفتگو")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ai_session"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["message_type"]),
            models.Index(fields=["is_read_by_client"]),
            models.Index(fields=["is_read_by_consultant"]),
        ]

    def __str__(self):
        return f"Message from {self.sender} at {self.created_at}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Update read status based on sender
        if is_new:
            session = self.ai_session
            if session.client == self.sender:
                self.is_read_by_client = True
                session.unread_consultant_messages += 1
                # Add notification for consultant
                if session.consultant:
                    NotificationService.create_notification(
                        to_user=session.consultant,
                        name="پیغام جدید",
                        description=f"پیغام جدیدی از طرف {self.sender.first_name} {self.sender.last_name}",
                        link=f"/chat/{session.pid}",
                    )
            elif session.consultant == self.sender:
                self.is_read_by_consultant = True
                session.unread_client_messages += 1
                # Add notification for client
                NotificationService.create_notification(
                    to_user=session.client,
                    name="پیغام جدید",
                    description=f"پیغام جدید از طرف {self.sender.first_name} {self.sender.last_name}",
                    link=f"/chat/{session.pid}",
                )
            session.total_messages += 1
            session.save(update_fields=["unread_client_messages", "unread_consultant_messages", "total_messages"])

        super().save(*args, **kwargs)
