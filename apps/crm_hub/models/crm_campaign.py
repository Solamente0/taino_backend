"""
apps/crm_hub/models.py
CRM Hub models for user tracking and notifications
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, DescriptiveModel

User = get_user_model()


class CRMCampaignType(models.TextChoices):
    """Types of CRM campaigns"""
    WELCOME = "welcome", "خوش‌آمدگویی"
    ENGAGEMENT = "engagement", "افزایش تعامل"
    RETENTION = "retention", "حفظ کاربر"
    SUBSCRIPTION = "subscription", "اشتراک"
    REACTIVATION = "reactivation", "بازگشت کاربر"
    CUSTOM = "custom", "سفارشی"


class NotificationChannel(models.TextChoices):
    """Notification delivery channels"""
    EMAIL = "email", "ایمیل"
    SMS = "sms", "پیامک"
    PUSH = "push", "اعلان موبایل"
    WHATSAPP = "whatsapp", "واتساپ"
    IN_APP = "in_app", "درون‌برنامه‌ای"


class CRMCampaign(TimeStampModel, ActivableModel, DescriptiveModel):
    """
    CRM Campaign configuration stored in database
    Each campaign defines when and how to engage users
    """
    static_name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name=_("نام یکتا"),
        help_text=_("نام یکتا برای شناسایی کمپین (مثال: zero_day_email)")
    )

    campaign_type = models.CharField(
        max_length=20,
        choices=CRMCampaignType.choices,
        default=CRMCampaignType.CUSTOM,
        verbose_name=_("نوع کمپین")
    )

    trigger_days = models.PositiveIntegerField(
        default=0,
        verbose_name=_("روز اجرا"),
        help_text=_("تعداد روز پس از ثبت‌نام یا آخرین فعالیت")
    )

    channels = models.JSONField(
        default=list,
        verbose_name=_("کانال‌های ارسال"),
        help_text=_("لیست کانال‌های ارسال مثل email, sms, push")
    )

    # Conditions
    require_no_activity = models.BooleanField(
        default=False,
        verbose_name=_("نیاز به عدم فعالیت"),
        help_text=_("آیا کاربر نباید در این مدت فعالیتی داشته باشد؟")
    )

    require_no_subscription = models.BooleanField(
        default=False,
        verbose_name=_("نیاز به عدم اشتراک"),
        help_text=_("آیا کاربر نباید اشتراک فعال داشته باشد؟")
    )

    subscription_expire_threshold = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("آستانه انقضای اشتراک"),
        help_text=_("درصد باقیمانده اشتراک (مثلاً 20 برای 20%)")
    )

    # Template content
    email_subject = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("موضوع ایمیل")
    )

    email_template = models.TextField(
        blank=True,
        verbose_name=_("قالب ایمیل"),
        help_text=_("از پلیس‌هولدرهایی مثل {user_name}, {days} استفاده کنید")
    )

    sms_template = models.TextField(
        blank=True,
        verbose_name=_("قالب پیامک")
    )

    push_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("عنوان اعلان")
    )

    push_body = models.TextField(
        blank=True,
        verbose_name=_("متن اعلان")
    )

    # Advanced settings
    priority = models.PositiveSmallIntegerField(
        default=5,
        verbose_name=_("اولویت"),
        help_text=_("اولویت اجرا (1 = بالاترین)")
    )

    max_sends_per_user = models.PositiveIntegerField(
        default=1,
        verbose_name=_("حداکثر ارسال به هر کاربر"),
        help_text=_("تعداد دفعات ارسال این کمپین به هر کاربر")
    )

    target_user_roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("نقش‌های هدف"),
        help_text=_("لیست static_name نقش‌های کاربری (خالی = همه)")
    )

    class Meta:
        verbose_name = _("کمپین CRM")
        verbose_name_plural = _("کمپین‌های CRM")
        ordering = ['priority', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.static_name})"
