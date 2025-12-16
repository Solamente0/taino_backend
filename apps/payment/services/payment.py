# apps/payment/services/payment.py - updated with ZarinpalPaymentConfig support
import logging
from django.urls import reverse
from django.conf import settings
from apps.payment.models import Payment, PaymentStatus, ZarinpalPaymentConfig
from apps.payment.services.ipg.zarinpal import ZarinpalService
from apps.payment.services.coupon import CouponService

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment operations"""

    def __init__(self):
        """Initialize payment service with payment gateway"""
        self.zarinpal = ZarinpalService()

    def create_payment(self, user, amount, description, callback_path=None, coupon_code=None, metadata=None):
        """
        Create a new payment request

        Args:
            user: User making the payment
            amount: Payment amount in Tomans
            description: Payment description
            callback_path: Path to redirect after payment (e.g., '/api/payment/v1/verify/')
            coupon_code: Optional coupon code to apply discount

        Returns:
            Payment: Created payment object with payment URL
        """
        original_amount = amount
        discount_amount = 0
        coupon = None

        # Apply coupon if provided
        if coupon_code:
            is_valid, message, coupon_obj, discount = CouponService.validate_coupon(coupon_code, user, amount)

            if is_valid and coupon_obj:
                discount_amount = discount
                amount = original_amount - discount_amount
                coupon = coupon_obj

                # Update description to include the discount
                if discount_amount > 0:
                    description = f"{description} (تخفیف: {discount_amount} تومان)"

        # Create payment record
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            original_amount=original_amount,
            description=description,
            status=PaymentStatus.PENDING,
            coupon=coupon,
            discount_amount=discount_amount,
            metadata=metadata,
        )

        # Build the callback URL
        if callback_path:
            # If a specific callback path is provided, use it
            callback_url = f"{settings.BASE_URL}{callback_path}?payment_id={payment.pid}"
        else:
            # Otherwise, use the default verification endpoint
            callback_url = f"{settings.BASE_URL}{reverse('payment:payment_v1:verify')}?payment_id={payment.pid}"

        payment.callback_url = callback_url
        payment.save()

        # If amount is zero due to coupon (100% discount), mark as successful without gateway
        if amount <= 0:
            payment.status = PaymentStatus.SUCCESSFUL
            payment.verified = True
            payment.save()

            # Record coupon usage
            if coupon:
                CouponService.use_coupon(
                    coupon=coupon,
                    user=user,
                    original_amount=original_amount,
                    discount_amount=discount_amount,
                    applied_to="payment",
                    applied_to_id=payment.pid,
                )

            logger.info(f"Payment {payment.pid} completed with 100% discount")
            return payment

        # Request payment from Zarinpal
        success, result, data = self.zarinpal.request_payment(
            amount=int(amount),
            description=description,
            callback_url=callback_url,
            mobile=user.phone_number if hasattr(user, "phone_number") else None,
            email=user.email if hasattr(user, "email") else None,
        )

        if success:
            payment.authority = data.get("Authority")
            payment.payment_url = result
            payment.save()
        else:
            payment.status = PaymentStatus.FAILED
            payment.error_message = result
            payment.error_code = data.get("Status", "unknown")
            payment.save()
            logger.error(f"Payment creation failed: {result}")

        return payment

    def verify_payment(self, payment):
        """
        Verify a payment with Zarinpal

        Args:
            payment: Payment object to verify

        Returns:
            bool: True if payment was verified, False otherwise
        """
        if payment.verified:
            return True

        if not payment.authority:
            logger.error(f"Cannot verify payment {payment.pid}: No authority token")
            return False

        success, ref_id, data = self.zarinpal.verify_payment(authority=payment.authority, amount=int(payment.amount))

        if success:
            payment.status = PaymentStatus.SUCCESSFUL
            payment.ref_id = ref_id
            payment.verified = True
            payment.save()

            # Record coupon usage if a coupon was applied
            if payment.coupon and payment.discount_amount > 0:
                CouponService.use_coupon(
                    coupon=payment.coupon,
                    user=payment.user,
                    original_amount=payment.original_amount,
                    discount_amount=payment.discount_amount,
                    applied_to="payment",
                    applied_to_id=payment.pid,
                )

            return True
        else:
            payment.status = PaymentStatus.FAILED
            payment.error_code = data.get("Status", "unknown")
            payment.error_message = "Payment verification failed"
            payment.save()
            logger.error(f"Payment verification failed: {data}")
            return False

    def get_payment_by_pid(self, pid):
        """Get payment by pid"""
        try:
            return Payment.objects.get(pid=pid)
        except Payment.DoesNotExist:
            return None

    def get_payment_by_authority(self, authority):
        """Get payment by Zarinpal authority"""
        try:
            return Payment.objects.get(authority=authority)
        except Payment.DoesNotExist:
            return None

    def calculate_discounted_amount(self, amount, coupon_code, user):
        """
        Calculate the discounted amount for a given coupon code

        Args:
            amount: Original amount
            coupon_code: Coupon code to apply
            user: User applying the coupon

        Returns:
            tuple: (successful, message, discounted_amount, discount_amount, coupon)
        """
        if not coupon_code:
            return True, "No coupon applied", amount, 0, None

        is_valid, message, coupon, discount_amount = CouponService.validate_coupon(coupon_code, user, amount)

        if not is_valid or not coupon:
            return False, message, amount, 0, None

        discounted_amount = amount - discount_amount

        return True, "Coupon applied successfully", discounted_amount, discount_amount, coupon
