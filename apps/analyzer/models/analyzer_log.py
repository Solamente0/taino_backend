from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel

User = get_user_model()


class AnalyzerLog(TimeStampModel, ActivableModel, AdminStatusModel):
    """
    Model to store document analysis request logs
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="analyzer_logs",
        verbose_name=_("کاربر")
    )

    prompt = models.TextField(verbose_name=_("درخواست کاربر"))
    analysis_text = models.TextField(verbose_name=_("متن تحلیل"), null=True, blank=True)

    ai_type = models.CharField(
        max_length=50,
        default="v_x",
        null=True,
        blank=True,
        verbose_name=_("نوع هوش مصنوعی")
    )

    # Reference to AI session if used within a chat context
    ai_session = models.ForeignKey(
        "ai_chat.AISession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyzer_logs",
        verbose_name=_("جلسه هوش مصنوعی"),
    )

    class Meta:
        verbose_name = _("گزارش تحلیل اسناد")
        verbose_name_plural = _("گزارش‌های تحلیل اسناد")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["ai_session"]),
            models.Index(fields=["ai_type"]),
        ]

    def __str__(self):
        return f"Analysis for {self.user} at {self.created_at}"
