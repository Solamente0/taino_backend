# apps/chat/models/subscription.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import TimeStampModel, ActivableModel, AdminStatusModel

User = get_user_model()


class ChatSubscriptionTypeEnum(models.TextChoices):
    DAILY = "daily", _("روزانه")
    WEEKLY = "weekly", _("هفتگی")
    MONTHLY = "monthly", _("ماهانه")
    YEARLY = "yearly", _("سالانه")


class ChatSubscription(TimeStampModel, ActivableModel, AdminStatusModel):
    """
    Model for lawyer chat subscriptions
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_subscriptions", verbose_name=_("کاربر"))

    subscription_type = models.CharField(
        max_length=20,
        choices=ChatSubscriptionTypeEnum.choices,
        default=ChatSubscriptionTypeEnum.MONTHLY,
        verbose_name=_("نوع اشتراک"),
    )

    # Subscription limits
    max_chats = models.PositiveIntegerField(default=100, verbose_name=_("حداکثر گفتگو"))
    max_minutes = models.PositiveIntegerField(default=600, verbose_name=_("حداکثر دقیقه"))

    # Subscription period
    start_date = models.DateTimeField(verbose_name=_("تاریخ شروع"))
    end_date = models.DateTimeField(verbose_name=_("تاریخ پایان"))

    # Usage metrics
    used_chats = models.PositiveIntegerField(default=0, verbose_name=_("گفتگوهای استفاده شده"))
    used_minutes = models.PositiveIntegerField(default=0, verbose_name=_("دقایق استفاده شده"))

    # Payment information
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("قیمت"))
    is_paid = models.BooleanField(default=False, verbose_name=_("پرداخت شده"))
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ پرداخت"))
    payment_reference = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("مرجع پرداخت"))

    class Meta:
        verbose_name = _("اشتراک گفتگو")
        verbose_name_plural = _("اشتراک‌های گفتگو")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["subscription_type"]),
            models.Index(fields=["end_date"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_subscription_type_display()} - {self.start_date}"

    @property
    def is_active(self):
        """Check if subscription is still active"""
        from django.utils import timezone

        return self.is_active and self.start_date <= timezone.now() <= self.end_date

    @property
    def remaining_chats(self):
        """Get remaining chats"""
        return max(0, self.max_chats - self.used_chats)

    @property
    def remaining_minutes(self):
        """Get remaining minutes"""
        return max(0, self.max_minutes - self.used_minutes)
