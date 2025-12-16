# apps/ai_chat/models/ai_message.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel

User = get_user_model()


class AIMessageTypeEnum(models.TextChoices):
    TEXT = "text", _("متن")
    IMAGE = "image", _("تصویر")
    FILE = "file", _("فایل")
    SYSTEM = "system", _("سیستمی")


class AIMessage(TimeStampModel, ActivableModel, AdminStatusModel):
    """
    Model for AI chat messages
    """
    ai_session = models.ForeignKey(
        "AISession", 
        on_delete=models.CASCADE, 
        related_name="messages", 
        verbose_name=_("جلسه هوش مصنوعی")
    )

    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="ai_sent_messages", 
        verbose_name=_("فرستنده")
    )

    message_type = models.CharField(
        max_length=20, 
        choices=AIMessageTypeEnum.choices, 
        default=AIMessageTypeEnum.TEXT, 
        verbose_name=_("نوع پیام")
    )

    content = models.TextField(verbose_name=_("محتوا"))

    # For media files
    attachment = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_message_attachments",
        verbose_name=_("فایل پیوست"),
    )

    # AI or system messages
    is_ai = models.BooleanField(default=False, verbose_name=_("پیام هوش مصنوعی"))
    is_system = models.BooleanField(default=False, verbose_name=_("پیام سیستمی"))

    # Read status
    is_read = models.BooleanField(default=False, verbose_name=_("خوانده شده"))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_("زمان خوانده شدن"))

    # If the message failed to deliver
    is_failed = models.BooleanField(default=False, verbose_name=_("خطا در ارسال"))
    failure_reason = models.TextField(null=True, blank=True, verbose_name=_("دلیل خطا"))

    class Meta:
        verbose_name = _("پیام هوش مصنوعی")
        verbose_name_plural = _("پیام‌های هوش مصنوعی")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ai_session"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["message_type"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"AI Message from {self.sender} at {self.created_at}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            session = self.ai_session
            if self.sender == session.user and not self.is_ai:
                self.is_read = True
                session.total_messages += 1
            else:
                session.unread_messages += 1
                session.total_messages += 1
            
            session.save(update_fields=["unread_messages", "total_messages"])

        super().save(*args, **kwargs)
