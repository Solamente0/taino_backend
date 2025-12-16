from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, StaticalIdentifier


class DocumentType(models.TextChoices):
    MEDICAL_REPORT = "medical_report", _("گزارش پزشکی")
    PRESCRIPTION = "prescription", _("نسخه دارو")
    LEGAL_DOCUMENT = "legal_document", _("مدرک قانونی")
    CONSENT_FORM = "consent_form", _("فرم رضایت‌نامه")
    ASSESSMENT_RESULT = "assessment_result", _("نتیجه ارزیابی")
    OTHER = "other", _("سایر")


class CaseDocument(TimeStampModel, StaticalIdentifier):
    """
    اسناد و مدارک پرونده
    """

    case = models.ForeignKey(
        "Case",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("پرونده")
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        verbose_name=_("نوع سند")
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("عنوان")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("توضیحات")
    )

    file = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.CASCADE,
        related_name="case_documents",
        verbose_name=_("فایل")
    )

    # ارتباط با جلسه یا ارزیابی
    session = models.ForeignKey(
        "Session",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("جلسه مرتبط")
    )

    assessment = models.ForeignKey(
        "Assessment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("ارزیابی مرتبط")
    )

    # آپلودر
    uploaded_by = models.ForeignKey(
        "authentication.TainoUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_case_documents",
        verbose_name=_("آپلودکننده")
    )

    # متادیتا
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("تگ‌ها")
    )

    is_confidential = models.BooleanField(
        default=False,
        verbose_name=_("محرمانه"),
        help_text=_("فقط برای مشاور قابل مشاهده")
    )

    class Meta:
        verbose_name = _("سند پرونده")
        verbose_name_plural = _("اسناد پرونده")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case", "-created_at"]),
            models.Index(fields=["document_type"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.case.case_number}"
