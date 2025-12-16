# apps/payment/services/coupon.py
import logging
from django.utils import timezone
from apps.payment.models import Coupon, CouponUsage
from django.db import transaction

logger = logging.getLogger(__name__)


class CouponService:
    """Service for handling coupon operations"""

    @staticmethod
    def validate_coupon(code, user, amount=None, package=None):
        """
        Validate a coupon code for a specific user and amount

        Args:
            code (str): The coupon code
            user: The user trying to use the coupon
            amount (Decimal, optional): The purchase amount
            package (Package, optional): The subscription package

        Returns:
            tuple: (valid, message, coupon_object, discount_amount)
        """
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            return False, "کد تخفیف نامعتبر است", None, 0

        is_valid, message = coupon.is_valid(user=user, amount=amount, package=package)

        if not is_valid:
            return False, message, None, 0

        # Calculate discount
        discount_amount = 0
        if amount:
            discount_amount = coupon.calculate_discount_amount(amount)

        return True, "کد تخفیف معتبر است", coupon, discount_amount

    @staticmethod
    def apply_coupon(coupon, user, amount, applied_to="payment", applied_to_id=None):
        """
        Apply a coupon to calculate the discounted amount

        Args:
            coupon (Coupon): The coupon object
            user: The user applying the coupon
            amount (Decimal): The original amount
            applied_to (str): The type of item the coupon is applied to
            applied_to_id (str): The ID of the item

        Returns:
            tuple: (discounted_amount, discount_amount)
        """
        discount_amount = coupon.calculate_discount_amount(amount)
        discounted_amount = amount - discount_amount

        return discounted_amount, discount_amount

    @staticmethod
    @transaction.atomic
    def use_coupon(coupon, user, original_amount, discount_amount, applied_to="payment", applied_to_id=None):
        """
        Mark coupon as used and record usage

        Args:
            coupon (Coupon): The coupon object
            user: The user who used the coupon
            original_amount (Decimal): The original amount before discount
            discount_amount (Decimal): The discount amount applied
            applied_to (str): The type of item the coupon is applied to
            applied_to_id (str): The ID of the item

        Returns:
            CouponUsage: The created coupon usage record
        """
        # Update coupon usage counter
        coupon.use()

        # Record usage
        final_amount = original_amount - discount_amount
        usage = CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            original_amount=original_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            applied_to=applied_to,
            applied_to_id=applied_to_id if applied_to_id else "",
        )

        logger.info(
            f"Coupon {coupon.code} used by {user}. Original: {original_amount}, "
            f"Discount: {discount_amount}, Final: {final_amount}"
        )

        return usage

    @staticmethod
    def get_valid_coupons_for_user(user):
        """
        Get all valid coupons for a specific user

        Args:
            user: The user to check coupons for

        Returns:
            QuerySet: Valid coupons for the user
        """
        now = timezone.now()

        # Basic validity filters
        queryset = (
            Coupon.objects.filter(
                is_active=True,
                valid_from__lte=now,
            )
            .filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gt=now))
            .filter(models.Q(current_uses__lt=models.F("max_uses")))
        )

        # User-specific coupons
        user_coupons = queryset.filter(specific_user=user)

        # Location-based coupons
        if hasattr(user, "country") and user.country:
            country_coupons = queryset.filter(country=user.country, specific_user__isnull=True)

            # State and city based on user's country
            if hasattr(user, "state") and user.state:
                state_coupons = queryset.filter(state=user.state, country=user.country, specific_user__isnull=True)

                if hasattr(user, "city") and user.city:
                    city_coupons = queryset.filter(
                        city=user.city, state=user.state, country=user.country, specific_user__isnull=True
                    )

                    return user_coupons | country_coupons | state_coupons | city_coupons

                return user_coupons | country_coupons | state_coupons

            return user_coupons | country_coupons

        # General coupons (no restrictions)
        general_coupons = queryset.filter(
            specific_user__isnull=True, country__isnull=True, state__isnull=True, city__isnull=True, package__isnull=True
        )

        return user_coupons | general_coupons
