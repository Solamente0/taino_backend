from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, StaticalIdentifier


class AnalysisType(models.TextChoices):
    SENTIMENT = "sentiment", _("تحلیل احساسات")
    KEYWORD = "keyword", _("کلمات کلیدی")
    BEHAVIORAL_PATTERN = "behavioral_pattern", _("الگوهای رفتاری")
    CRISIS_PREDICTION = "crisis_prediction", _("پیش‌بینی بحران")
    PROGRESS_ANALYSIS = "progress_analysis", _("تحلیل پیشرفت")
    CUSTOM = "custom", _("تحلیل سفارشی")


class AIAnalysis(TimeStampModel, StaticalIdentifier):
    """
    تحلیل‌های هوش مصنوعی پرونده
    """
    
    case = models.ForeignKey(
        "Case",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
        verbose_name=_("پرونده")
    )
    
    analysis_type = models.CharField(
        max_length=30,
        choices=AnalysisType.choices,
        verbose_name=_("نوع تحلیل")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("عنوان")
    )
    
    # نتایج تحلیل
    result = models.JSONField(
        verbose_name=_("نتیجه تحلیل"),
        help_text=_("نتایج ساختاریافته به صورت JSON")
    )
    
    summary = models.TextField(
        blank=True,
        verbose_name=_("خلاصه")
    )
    
    # اطلاعات تحلیل
    data_sources = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("منابع داده"),
        help_text=_("جلسات، ارزیابی‌ها، ژورنال‌هایی که در تحلیل استفاده شدند")
    )
    
    ai_model_used = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("مدل AI استفاده شده")
    )
    
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("امتیاز اطمینان"),
        help_text=_("0 تا 1")
    )
    
    # توصیه‌ها
    recommendations = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("توصیه‌ها")
    )
    
    # بازخورد مشاور
    counselor_review = models.TextField(
        blank=True,
        verbose_name=_("بازخورد مشاور")
    )
    
    is_reviewed = models.BooleanField(
        default=False,
        verbose_name=_("بازبینی شده")
    )

    class Meta:
        verbose_name = _("تحلیل AI")
        verbose_name_plural = _("تحلیل‌های AI")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case", "-created_at"]),
            models.Index(fields=["analysis_type"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.case.case_number}"
