from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel


class DailyLog(TimeStampModel):
    """
    ژورنال روزانه مراجع
    """

    case = models.ForeignKey("Case", on_delete=models.CASCADE, related_name="daily_logs", verbose_name=_("پرونده"))

    log_date = models.DateField(verbose_name=_("تاریخ"), db_index=True)

    # خلق و خو
    mood_score = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("نمره خلق و خو"), help_text=_("1 (بسیار بد) تا 10 (عالی)")
    )

    mood_notes = models.TextField(blank=True, verbose_name=_("یادداشت‌های خلق و خو"))

    # خواب
    sleep_hours = models.FloatField(null=True, blank=True, verbose_name=_("ساعات خواب"))

    sleep_quality = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("کیفیت خواب"), help_text=_("1 (بسیار بد) تا 10 (عالی)")
    )

    # داروها
    medications_taken = models.JSONField(
        default=list, blank=True, verbose_name=_("داروهای مصرف شده"), help_text=_("لیست داروهای مصرف شده امروز")
    )

    medication_compliance = models.BooleanField(default=True, verbose_name=_("پایبندی به دارو"))

    # فعالیت فیزیکی
    physical_activity_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("دقایق فعالیت فیزیکی"))

    physical_activity_type = models.CharField(max_length=200, blank=True, verbose_name=_("نوع فعالیت فیزیکی"))

    # تکالیف
    homework_completed = models.JSONField(default=list, blank=True, verbose_name=_("تکالیف انجام شده"))

    # رویدادها و استرس‌ها
    stressful_events = models.TextField(blank=True, verbose_name=_("رویدادهای استرس‌زا"))

    positive_events = models.TextField(blank=True, verbose_name=_("رویدادهای مثبت"))

    # یادداشت کلی
    general_notes = models.TextField(blank=True, verbose_name=_("یادداشت کلی روز"))

    # علائم ویژه
    specific_symptoms = models.JSONField(
        default=list, blank=True, verbose_name=_("علائم ویژه"), help_text=_("علائم خاصی که امروز تجربه شده")
    )

    class Meta:
        verbose_name = _("ژورنال روزانه")
        verbose_name_plural = _("ژورنالهای روزانه")
        ordering = ["-log_date"]
        unique_together = [["case", "log_date"]]
        indexes = [
            models.Index(fields=["case", "-log_date"]),
        ]

    def __str__(self):
        return f"{self.case.case_number} - {self.log_date}"
