from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, DescriptiveModel

User = get_user_model()


class CRMUserEngagement(TimeStampModel):
    """
    Track user engagement metrics for CRM decisions
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="crm_engagement", verbose_name=_("کاربر"))

    # Activity metrics
    last_login_date = models.DateTimeField(null=True, blank=True, verbose_name=_("آخرین ورود"))

    last_activity_date = models.DateTimeField(null=True, blank=True, verbose_name=_("آخرین فعالیت"))

    total_activities = models.PositiveIntegerField(default=0, verbose_name=_("تعداد کل فعالیت‌ها"))

    activities_last_7_days = models.PositiveIntegerField(default=0, verbose_name=_("فعالیت‌های 7 روز اخیر"))

    activities_last_30_days = models.PositiveIntegerField(default=0, verbose_name=_("فعالیت‌های 30 روز اخیر"))

    # Subscription metrics
    has_active_subscription = models.BooleanField(default=False, verbose_name=_("اشتراک فعال دارد"))

    subscription_expire_date = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ انقضای اشتراک"))

    subscription_days_remaining = models.IntegerField(null=True, blank=True, verbose_name=_("روزهای باقیمانده اشتراک"))

    subscription_usage_percent = models.FloatField(null=True, blank=True, verbose_name=_("درصد استفاده از اشتراک"))

    # Engagement scores
    engagement_score = models.FloatField(
        default=0.0, verbose_name=_("امتیاز تعامل"), help_text=_("امتیاز 0-100 بر اساس فعالیت کاربر")
    )

    churn_risk_score = models.FloatField(
        default=0.0, verbose_name=_("امتیاز خطر ترک"), help_text=_("امتیاز 0-100، بالاتر = خطر بیشتر")
    )

    class Meta:
        verbose_name = _("تعامل کاربر CRM")
        verbose_name_plural = _("تعاملات کاربران CRM")

    def __str__(self):
        return f"{self.user.get_full_name()} - Engagement: {self.engagement_score}"
