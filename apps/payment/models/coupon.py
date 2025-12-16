# apps/payment/models/coupon.py
import decimal

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from base_utils.base_models import TimeStampModel, ActivableModel

User = get_user_model()


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "درصدی"
    FIXED = "fixed", "مقدار ثابت"


class Coupon(TimeStampModel, ActivableModel):
    """Coupon model for discounts on payments"""

    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    discount_type = models.CharField(
        max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE, verbose_name="نوع تخفیف"
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=0, verbose_name="مقدار تخفیف", validators=[MinValueValidator(1)]
    )
    max_discount_amount = models.DecimalField(
        max_digits=12, decimal_places=0, null=True, blank=True, verbose_name="حداکثر مبلغ تخفیف"
    )
    valid_from = models.DateTimeField(default=timezone.now, verbose_name="تاریخ شروع اعتبار")
    valid_to = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پایان اعتبار")
    max_uses = models.PositiveIntegerField(default=1, verbose_name="حداکثر تعداد استفاده")
    current_uses = models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده فعلی")
    minimum_purchase_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="حداقل مبلغ خرید")

    # Filtering options
    specific_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="coupons", verbose_name="کاربر خاص"
    )
    country = models.ForeignKey(
        "country.Country", on_delete=models.SET_NULL, null=True, blank=True, related_name="coupons", verbose_name="کشور"
    )
    state = models.ForeignKey(
        "country.State", on_delete=models.SET_NULL, null=True, blank=True, related_name="coupons", verbose_name="استان"
    )
    city = models.ForeignKey(
        "country.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="coupons", verbose_name="شهر"
    )
    package = models.ForeignKey(
        "subscription.Package",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupons",
        verbose_name="پکیج اشتراک",
    )

    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}: {self.discount_value}"

    def is_valid(self, user=None, amount=None, package=None):
        """Check if the coupon is valid"""
        now = timezone.now()

        # Basic validity checks
        if not self.is_active:
            return False, "این کد تخفیف غیرفعال است"

        if self.valid_from and self.valid_from > now:
            return False, "این کد تخفیف هنوز فعال نشده است"

        if self.valid_to and self.valid_to < now:
            return False, "این کد تخفیف منقضی شده است"

        if self.current_uses >= self.max_uses:
            return False, "این کد تخفیف به حداکثر تعداد استفاده رسیده است"

        # Check user-specific coupon
        if self.specific_user and user and self.specific_user != user:
            return False, "این کد تخفیف برای کاربر دیگری است"

        # Check location-based restrictions
        if user:
            if self.country and user.country and self.country != user.country:
                return False, "این کد تخفیف برای کشور شما معتبر نیست"

            # Check user address for city/state if user doesn't have country info
            # This requires more complex logic with user addresses that we'll skip for brevity

        # Check minimum purchase amount
        if amount and self.minimum_purchase_amount > 0 and amount < self.minimum_purchase_amount:
            return False, f"حداقل مبلغ برای استفاده از این کد تخفیف {self.minimum_purchase_amount} است"

        # Check package-specific coupon
        if self.package and package and self.package != package:
            return False, "این کد تخفیف برای این پکیج اشتراک معتبر نیست"

        return True, "کد تخفیف معتبر است"

    def calculate_discount_amount(self, original_amount):
        """
        Calculate the discount amount based on the coupon type.
        """
        original_amount = decimal.Decimal(str(original_amount))

        if self.discount_type == DiscountType.PERCENTAGE:
            # Ensure the percentage is between 0 and 100.
            percentage = min(max(self.discount_value, 0), 100)

            # Calculate the discount amount.
            discount = (original_amount * decimal.Decimal(str(percentage))) / decimal.Decimal("100")

        else:  # DiscountType.FIXED
            # The discount cannot exceed the original amount.
            discount = min(self.discount_value, original_amount)

        # Apply maximum discount cap if it's set and the calculated discount exceeds it.
        if self.max_discount_amount and discount > self.max_discount_amount:
            discount = decimal.Decimal(str(self.max_discount_amount))

        return discount

    def use(self):
        """Mark the coupon as used once"""
        self.current_uses += 1
        self.save()

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"
        ordering = ["-created_at"]


class CouponUsage(TimeStampModel):
    """Track coupon usage history"""

    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages", verbose_name="کد تخفیف")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="coupon_usages", verbose_name="کاربر")
    original_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ اصلی")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ تخفیف")
    final_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ نهایی")
    applied_to = models.CharField(max_length=100, verbose_name="اعمال شده روی")
    applied_to_id = models.CharField(max_length=100, verbose_name="شناسه آیتم")

    def __str__(self):
        return f"{self.coupon.code} - {self.user} - {self.discount_amount}"

    class Meta:
        verbose_name = "استفاده از کد تخفیف"
        verbose_name_plural = "استفاده‌های کد تخفیف"
        ordering = ["-created_at"]
