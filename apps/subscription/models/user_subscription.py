from django.contrib.auth import get_user_model
from django.db import models

from apps.subscription.models.subscription import SubscriptionStatus
from base_utils.base_models import TimeStampModel

User = get_user_model()


class UserSubscription(TimeStampModel):
    """User subscription model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="کاربر")
    package = models.ForeignKey("Package", on_delete=models.CASCADE, related_name="subscriptions", verbose_name="پکیج")
    status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.PENDING, verbose_name="وضعیت"
    )
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پایان")
    last_payment = models.OneToOneField(
        "payment.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription",
        verbose_name="آخرین پرداخت",
    )
    metadata = models.JSONField(null=True, blank=True, verbose_name="متادیتا")  # اضافه کردن فیلد metadata

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.package.name}"

    class Meta:
        verbose_name = "اشتراک کاربر"
        verbose_name_plural = "اشتراک‌های کاربران"
