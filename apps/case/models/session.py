from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, StaticalIdentifier

User = get_user_model()


class SessionType(models.TextChoices):
    TEXT_CHAT = "text_chat", _("چت متنی")
    VOICE_CHAT = "voice_chat", _("چت صوتی")
    VIDEO_CHAT = "video_chat", _("چت تصویری")
    GROUP = "group", _("گروهی")
    IN_PERSON = "in_person", _("حضوری")


class SessionStatus(models.TextChoices):
    SCHEDULED = "scheduled", _("برنامه‌ریزی شده")
    COMPLETED = "completed", _("انجام شده")
    CANCELLED = "cancelled", _("لغو شده")
    NO_SHOW = "no_show", _("عدم حضور")


class Session(TimeStampModel, StaticalIdentifier):
    """
    مدل جلسات مشاوره
    """
    
    case = models.ForeignKey(
        "Case",
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("پرونده")
    )
    
    session_number = models.PositiveIntegerField(
        verbose_name=_("شماره جلسه"),
        help_text=_("شماره جلسه در این پرونده")
    )
    
    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        verbose_name=_("نوع جلسه")
    )
    
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED,
        verbose_name=_("وضعیت")
    )
    
    scheduled_datetime = models.DateTimeField(
        verbose_name=_("تاریخ و ساعت برنامه‌ریزی شده")
    )
    
    actual_start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ و ساعت شروع واقعی")
    )
    
    actual_end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ و ساعت پایان واقعی")
    )
    
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("مدت زمان (دقیقه)")
    )
    
    # محتوا
    summary = models.TextField(
        blank=True,
        verbose_name=_("خلاصه جلسه"),
        help_text=_("خلاصه تولید شده توسط AI یا مشاور")
    )
    
    key_topics = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("موضوعات کلیدی")
    )
    
    chat_transcript = models.TextField(
        blank=True,
        verbose_name=_("متن کامل چت")
    )
    
    # فایل‌ها
    audio_file = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="session_audios",
        verbose_name=_("فایل صوتی")
    )
    
    video_file = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="session_videos",
        verbose_name=_("فایل تصویری")
    )
    
    # یادداشت‌های مشاور
    counselor_notes = models.TextField(
        blank=True,
        verbose_name=_("یادداشت‌های مشاور"),
        help_text=_("یادداشت‌های خصوصی مشاور")
    )
    
    # ارتباط با AI Chat Session
    ai_chat_session = models.ForeignKey(
        "ai_chat.AISession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_sessions",
        verbose_name=_("جلسه چت AI")
    )
    
    # تکالیف جلسه بعد
    homework_assigned = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("تکالیف تعیین شده")
    )
    
    # ارزیابی جلسه
    client_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("امتیاز مراجع"),
        help_text=_("از 1 تا 5")
    )
    
    client_feedback = models.TextField(
        blank=True,
        verbose_name=_("بازخورد مراجع")
    )

    class Meta:
        verbose_name = _("جلسه")
        verbose_name_plural = _("جلسات")
        ordering = ["-scheduled_datetime"]
        unique_together = [["case", "session_number"]]
        indexes = [
            models.Index(fields=["case", "-scheduled_datetime"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"جلسه {self.session_number} - {self.case.case_number}"

    def save(self, *args, **kwargs):
        if not self.session_number:
            # محاسبه شماره جلسه
            last_session = Session.objects.filter(case=self.case).order_by('-session_number').first()
            self.session_number = (last_session.session_number + 1) if last_session else 1
        
        # محاسبه مدت زمان
        if self.actual_start_datetime and self.actual_end_datetime:
            delta = self.actual_end_datetime - self.actual_start_datetime
            self.duration_minutes = int(delta.total_seconds() / 60)
        
        super().save(*args, **kwargs)
        
        # بروزرسانی تعداد جلسات در پرونده
        if self.status == SessionStatus.COMPLETED:
            self.case.total_sessions = self.case.sessions.filter(status=SessionStatus.COMPLETED).count()
            self.case.save(update_fields=['total_sessions'])
