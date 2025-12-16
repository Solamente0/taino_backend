from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, StaticalIdentifier


class TreatmentPlan(TimeStampModel, StaticalIdentifier):
    """
    برنامه درمانی
    """
    
    case = models.OneToOneField(
        "Case",
        on_delete=models.CASCADE,
        related_name="treatment_plan",
        verbose_name=_("پرونده")
    )
    
    # روش‌های درمانی
    treatment_methods = models.JSONField(
        default=list,
        verbose_name=_("روش‌های درمانی"),
        help_text=_("CBT, ACT, Mindfulness...")
    )
    
    # تمرینات تجویز شده
    prescribed_exercises = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("تمرینات تجویز شده")
    )
    
    # یادداشت‌های کلی
    general_notes = models.TextField(
        blank=True,
        verbose_name=_("یادداشت‌های کلی")
    )
    
    # تاریخ بازبینی بعدی
    next_review_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ بازبینی بعدی")
    )

    class Meta:
        verbose_name = _("برنامه درمانی")
        verbose_name_plural = _("برنامه‌های درمانی")

    def __str__(self):
        return f"برنامه درمانی - {self.case.case_number}"


class TreatmentGoal(TimeStampModel, StaticalIdentifier):
    """
    اهداف درمانی
    """
    
    treatment_plan = models.ForeignKey(
        TreatmentPlan,
        on_delete=models.CASCADE,
        related_name="goals",
        verbose_name=_("برنامه درمانی")
    )
    
    goal_type = models.CharField(
        max_length=20,
        choices=[
            ("short_term", _("کوتاه‌مدت (1-3 ماه)")),
            ("long_term", _("بلندمدت (6-12 ماه)"))
        ],
        verbose_name=_("نوع هدف")
    )
    
    description = models.TextField(
        verbose_name=_("شرح هدف")
    )
    
    target_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ هدف")
    )
    
    progress_percentage = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("درصد پیشرفت"),
        help_text=_("0 تا 100")
    )
    
    is_achieved = models.BooleanField(
        default=False,
        verbose_name=_("محقق شده")
    )
    
    achieved_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ تحقق")
    )
    
    # یادداشت‌ها
    notes = models.TextField(
        blank=True,
        verbose_name=_("یادداشت‌ها")
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ترتیب نمایش")
    )

    class Meta:
        verbose_name = _("هدف درمانی")
        verbose_name_plural = _("اهداف درمانی")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.get_goal_type_display()} - {self.description[:50]}"
