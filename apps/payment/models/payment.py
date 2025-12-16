# apps/payment/models/payment.py - with coupon support
from django.db import models
from django.contrib.auth import get_user_model
from base_utils.base_models import TimeStampModel
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "در انتظار پرداخت"
    SUCCESSFUL = "successful", "موفق"
    FAILED = "failed", "ناموفق"
    CANCELED = "canceled", "لغو شده"
    REFUNDED = "refunded", "بازگشت وجه"


class Payment(TimeStampModel):
    """Payment model for tracking payment transactions"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments", verbose_name="کاربر")
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ")
    original_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ اصلی", null=True, blank=True)
    description = models.TextField(max_length=255, verbose_name="توضیحات")
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name="وضعیت"
    )
    authority = models.CharField(max_length=255, null=True, blank=True, verbose_name="کد پیگیری زرین‌پال")
    ref_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="شناسه مرجع")
    callback_url = models.CharField(max_length=255, null=True, blank=True, verbose_name="آدرس بازگشت")
    payment_url = models.CharField(max_length=255, null=True, blank=True, verbose_name="آدرس درگاه پرداخت")
    verified = models.BooleanField(default=False, verbose_name="تایید شده")
    error_code = models.CharField(max_length=20, null=True, blank=True, verbose_name="کد خطا")
    error_message = models.CharField(max_length=255, null=True, blank=True, verbose_name="پیام خطا")

    # Coupon integration
    coupon = models.ForeignKey(
        "payment.Coupon", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments", verbose_name="کد تخفیف"
    )
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مقدار تخفیف")
    metadata = models.JSONField(null=True, blank=True, verbose_name=_("متادیتا"))

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.amount} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Set original_amount if not set and is a new record
        if self._state.adding and not self.original_amount:
            self.original_amount = self.amount
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
