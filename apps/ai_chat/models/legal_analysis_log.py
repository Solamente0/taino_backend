# apps/ai_chat/models/legal_analysis_log.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel
from base_utils.enums import LegalDocumentAnalysisType

User = get_user_model()


class LegalAnalysisLog(TimeStampModel, ActivableModel, AdminStatusModel):
    """
    Model to store legal analysis request logs
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="legal_analysis_logs", 
        verbose_name=_("کاربر")
    )
    
    analysis_text = models.TextField(verbose_name=_("متن تحلیل"), null=True, blank=True)
    user_request_analysis_text = models.TextField(
        verbose_name=_("متن تحلیل براساس درخواست کاربر"), 
        null=True, 
        blank=True
    )

    ai_type = models.CharField(default="v_x", null=True, blank=True)

    user_request_choice = models.CharField(
        _("نوع درخواست کاربر"),
        choices=LegalDocumentAnalysisType.choices,
        default=LegalDocumentAnalysisType.LEGAL_DOCUMENT_ANALYSIS,
        max_length=100,
        null=True,
        blank=True,
    )

    # Reference to AI session instead of chat session
    ai_session = models.ForeignKey(
        "AISession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="legal_analysis_logs",
        verbose_name=_("جلسه هوش مصنوعی"),
    )

    # Track if analysis was done using only content (without files)
    is_content_only = models.BooleanField(default=False, verbose_name=_("فقط متن"))

    # Track OpenAI processing details
    assistant_id = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("شناسه دستیار"))
    thread_id = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("شناسه مکالمه"))
    run_id = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("شناسه اجرا"))

    class Meta:
        verbose_name = _("گزارش تحلیل حقوقی")
        verbose_name_plural = _("گزارش‌های تحلیل حقوقی")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["ai_session"]),
        ]

    def __str__(self):
        return f"Legal Analysis for {self.user} at {self.created_at}"
