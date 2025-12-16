from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, StaticalIdentifier


class AssessmentType(models.TextChoices):
    BECK_DEPRESSION = "beck_depression", _("تست افسردگی Beck")
    BECK_ANXIETY = "beck_anxiety", _("تست اضطراب Beck")
    DASS_21 = "dass_21", _("تست DASS-21")
    PERSONALITY = "personality", _("تست شخصیت")
    RELATIONSHIP = "relationship", _("ارزیابی رابطه")
    CUSTOM = "custom", _("ارزیابی سفارشی")


class Assessment(TimeStampModel, StaticalIdentifier):
    """
    مدل ارزیابی‌ها و تست‌های روانشناختی
    """
    
    case = models.ForeignKey(
        "Case",
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("پرونده")
    )
    
    test_type = models.CharField(
        max_length=50,
        choices=AssessmentType.choices,
        verbose_name=_("نوع تست")
    )
    
    test_name = models.CharField(
        max_length=200,
        verbose_name=_("نام تست")
    )
    
    date_taken = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("تاریخ انجام")
    )
    
    # نتایج
    raw_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("نمره خام")
    )
    
    percentile = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("صدک"),
        help_text=_("مقایسه با جامعه")
    )
    
    interpretation = models.TextField(
        blank=True,
        verbose_name=_("تفسیر نتایج")
    )
    
    severity_level = models.CharField(
        max_length=20,
        choices=[
            ("minimal", _("حداقل")),
            ("mild", _("خفیف")),
            ("moderate", _("متوسط")),
            ("severe", _("شدید")),
            ("very_severe", _("بسیار شدید"))
        ],
        blank=True,
        verbose_name=_("سطح شدت")
    )
    
    # جزئیات تست
    questions_answers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("سوالات و پاسخ‌ها"),
        help_text=_("ذخیره کامل پاسخ‌های تست")
    )
    
    subscales = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("خرده‌مقیاس‌ها"),
        help_text=_("نمرات بخش‌های مختلف تست")
    )
    
    # توصیه‌های AI
    ai_recommendations = models.TextField(
        blank=True,
        verbose_name=_("توصیه‌های AI")
    )
    
    # ارتباط با جلسه
    session = models.ForeignKey(
        "Session",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessments",
        verbose_name=_("جلسه مرتبط")
    )
    
    # یادداشت‌های مشاور
    counselor_notes = models.TextField(
        blank=True,
        verbose_name=_("یادداشت‌های مشاور")
    )

    class Meta:
        verbose_name = _("ارزیابی")
        verbose_name_plural = _("ارزیابی‌ها")
        ordering = ["-date_taken"]
        indexes = [
            models.Index(fields=["case", "-date_taken"]),
            models.Index(fields=["test_type"]),
        ]

    def __str__(self):
        return f"{self.test_name} - {self.case.case_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # بروزرسانی تعداد ارزیابی‌ها در پرونده
        self.case.total_assessments = self.case.assessments.count()
        self.case.save(update_fields=['total_assessments'])
