from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel

User = get_user_model()


class TimelineEventType(models.TextChoices):
    CASE_CREATED = "case_created", _("ایجاد پرونده")
    CASE_STATUS_CHANGED = "case_status_changed", _("تغییر وضعیت پرونده")
    SESSION_COMPLETED = "session_completed", _("انجام جلسه")
    ASSESSMENT_COMPLETED = "assessment_completed", _("انجام ارزیابی")
    GOAL_ACHIEVED = "goal_achieved", _("تحقق هدف")
    DOCUMENT_UPLOADED = "document_uploaded", _("آپلود سند")
    NOTE_ADDED = "note_added", _("افزودن یادداشت")
    DIAGNOSIS_UPDATED = "diagnosis_updated", _("بروزرسانی تشخیص")
    TREATMENT_PLAN_UPDATED = "treatment_plan_updated", _("بروزرسانی برنامه درمانی")
    OTHER = "other", _("سایر")


class CaseTimeline(TimeStampModel):
    """
    تاریخچه رویدادهای پرونده
    """
    
    case = models.ForeignKey(
        "Case",
        on_delete=models.CASCADE,
        related_name="timeline_events",
        verbose_name=_("پرونده")
    )
    
    event_type = models.CharField(
        max_length=30,
        choices=TimelineEventType.choices,
        verbose_name=_("نوع رویداد")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("عنوان")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("توضیحات")
    )
    
    # کاربری که رویداد را ایجاد کرد
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="case_timeline_events",
        verbose_name=_("ایجادکننده")
    )
    
    # متادیتای اضافی
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("متادیتا"),
        help_text=_("اطلاعات اضافی رویداد")
    )
    
    # آیکون یا رنگ برای نمایش
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("آیکون")
    )
    
    color = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("رنگ")
    )

    class Meta:
        verbose_name = _("رویداد تاریخچه")
        verbose_name_plural = _("رویدادهای تاریخچه")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case", "-created_at"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
