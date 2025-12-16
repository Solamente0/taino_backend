from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel, StaticalIdentifier

User = get_user_model()


class CaseStatus(models.TextChoices):
    ACTIVE = "active", _("فعال")
    PENDING = "pending", _("معلق")
    CLOSED = "closed", _("بسته شده")
    ARCHIVED = "archived", _("آرشیو شده")


class CaseType(models.TextChoices):
    INDIVIDUAL = "individual", _("فردی")
    COUPLE = "couple", _("زوجی")
    FAMILY = "family", _("خانوادگی")
    DIVORCE = "divorce", _("طلاق")
    ORGANIZATIONAL = "organizational", _("سازمانی")


class CasePriority(models.TextChoices):
    NORMAL = "normal", _("عادی")
    URGENT = "urgent", _("فوری")
    CRITICAL = "critical", _("بحرانی")


class Case(TimeStampModel, ActivableModel, AdminStatusModel, StaticalIdentifier):
    """
    مدل اصلی پرونده مشاوره
    """
    
    # شماره پرونده یکتا
    case_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
        verbose_name=_("شماره پرونده"),
        help_text=_("مثال: CNS-2024-00123")
    )
    
    # کاربر اصلی
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cases",
        verbose_name=_("کاربر")
    )
    
    # شریک (در صورت وجود - برای مشاوره زوجی)
    partner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partner_cases",
        verbose_name=_("شریک")
    )
    
    # مشاور مسئول
    assigned_counselor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
        verbose_name=_("مشاور مسئول")
    )
    
    # اطلاعات پایه
    status = models.CharField(
        max_length=20,
        choices=CaseStatus.choices,
        default=CaseStatus.ACTIVE,
        db_index=True,
        verbose_name=_("وضعیت")
    )
    
    case_type = models.CharField(
        max_length=30,
        choices=CaseType.choices,
        verbose_name=_("نوع پرونده")
    )
    
    priority = models.CharField(
        max_length=20,
        choices=CasePriority.choices,
        default=CasePriority.NORMAL,
        verbose_name=_("اولویت")
    )
    
    # توضیحات و تشخیص
    initial_complaint = models.TextField(
        verbose_name=_("شکایت اولیه"),
        help_text=_("دلیل مراجعه")
    )
    
    initial_diagnosis = models.TextField(
        blank=True,
        verbose_name=_("تشخیص اولیه")
    )
    
    current_diagnosis = models.TextField(
        blank=True,
        verbose_name=_("تشخیص فعلی")
    )
    
    symptoms = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("علائم و نشانه‌ها"),
        help_text=_("لیست علائم مشاهده شده")
    )
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ("mild", _("خفیف")),
            ("moderate", _("متوسط")),
            ("severe", _("شدید"))
        ],
        blank=True,
        verbose_name=_("شدت مشکل")
    )
    
    # عوامل موثر
    aggravating_factors = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("عوامل تشدید کننده"),
        help_text=_("استرس شغلی، مشکلات خانوادگی...")
    )
    
    protective_factors = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("عوامل محافظت کننده"),
        help_text=_("حمایت خانواده، ورزش منظم...")
    )
    
    # تگ‌ها
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("تگ‌ها"),
        help_text=_("#افسردگی #اضطراب")
    )
    
    # اطلاعات دموگرافیک
    demographic_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("اطلاعات دموگرافیک"),
        help_text=_("سن، جنسیت، تحصیلات، شغل")
    )
    
    # سابقه پزشکی
    medical_history = models.TextField(
        blank=True,
        verbose_name=_("سابقه پزشکی")
    )
    
    medications = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("داروهای مصرفی")
    )
    
    family_mental_health_history = models.TextField(
        blank=True,
        verbose_name=_("سابقه بیماری روانی در خانواده")
    )
    
    # تاریخ‌ها
    start_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("تاریخ شروع")
    )
    
    close_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ بسته شدن")
    )
    
    # پرونده‌های مرتبط
    related_cases = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        verbose_name=_("پرونده‌های مرتبط")
    )
    
    # یادداشت‌های داخلی (فقط برای مشاور)
    internal_notes = models.TextField(
        blank=True,
        verbose_name=_("یادداشت‌های داخلی"),
        help_text=_("فقط برای مشاور قابل مشاهده است")
    )
    
    # آمار پرونده
    total_sessions = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل جلسات")
    )
    
    total_assessments = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل ارزیابی‌ها")
    )
    
    progress_percentage = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("درصد پیشرفت"),
        help_text=_("0 تا 100")
    )

    class Meta:
        verbose_name = _("پرونده")
        verbose_name_plural = _("پرونده‌ها")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case_number"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["assigned_counselor", "status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.case_number} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            from apps.case.services.case_number_generator import CaseNumberGenerator
            self.case_number = CaseNumberGenerator.generate()
        super().save(*args, **kwargs)
