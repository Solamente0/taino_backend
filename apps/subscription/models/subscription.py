# apps/subscription/models.py
from django.db import models
from django.contrib.auth import get_user_model
from base_utils.base_models import TimeStampModel, ActivableModel

User = get_user_model()


class SubscriptionPeriod(models.TextChoices):
    MONTHLY = "monthly", "یک ماهه"
    QUARTERLY = "quarterly", "سه ماهه"
    BIANNUAL = "biannual", "شش ماهه"
    ANNUAL = "annual", "یک ساله"


class SubscriptionStatus(models.TextChoices):
    PENDING = "pending", "در انتظار پرداخت"
    ACTIVE = "active", "فعال"
    EXPIRED = "expired", "منقضی شده"
    CANCELED = "canceled", "لغو شده"


class Package(TimeStampModel, ActivableModel):
    """Subscription package model"""

    name = models.CharField(max_length=100, verbose_name="نام پکیج")
    description = models.TextField(verbose_name="توضیحات", help_text="Markdown supported")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="قیمت")
    period = models.CharField(
        max_length=20, choices=SubscriptionPeriod.choices, default=SubscriptionPeriod.MONTHLY, verbose_name="دوره زمانی"
    )
    features = models.JSONField(default=None, null=True, blank=True, verbose_name="ویژگی‌ها")

    def __str__(self):
        return f"{self.name} - {self.get_period_display()}"

    class Meta:
        verbose_name = "پکیج اشتراک"
        verbose_name_plural = "پکیج‌های اشتراک"
