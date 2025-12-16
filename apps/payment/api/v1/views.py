# apps/payment/api/v1/views.py
import logging
from django.shortcuts import redirect
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payment.models import Payment
from apps.payment.services.payment import PaymentService
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    ApplyCouponSerializer,
    OutputCouponSerializer,
    CouponSerializer,
)
from base_utils.views.mobile import TainoMobileGenericViewSet
from ...services.coupon import CouponService

logger = logging.getLogger(__name__)


class CouponViewSet(TainoMobileGenericViewSet):
    """
    API endpoint for user-side coupon operations
    """

    serializer_class = CouponSerializer

    def get_queryset(self):
        """Only return valid coupons for the current user"""
        logger.info("Getting valid coupons for user %s", self.request.user)
        return CouponService.get_valid_coupons_for_user(self.request.user)

    @action(detail=False, methods=["post"])
    def validate(self, request):
        """Validate a coupon code"""
        logger.info("Validating coupon for user %s with data: %s", request.user, request.data)
        serializer = ApplyCouponSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            logger.warning("Coupon validation failed for user %s: %s", request.user, serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        coupon = serializer.validated_data["code"]  # This is now the Coupon object
        amount = serializer.validated_data["amount"]
        package = serializer.validated_data.get("package")
        logger.debug("Coupon '%s' is valid for amount %s", coupon.code, amount)

        # Calculate discount
        discount_amount = coupon.calculate_discount_amount(amount)
        discounted_amount = amount - discount_amount
        logger.info(
            "Calculated discount for coupon '%s': original_amount=%s, discount_amount=%s, final_amount=%s",
            coupon.code,
            amount,
            discount_amount,
            discounted_amount,
        )

        return Response(
            {
                "original_amount": amount,
                "discount_amount": discount_amount,
                "final_amount": discounted_amount,
                "coupon": CouponSerializer(coupon).data,
                "message": "کد تخفیف معتبر است",
            }
        )


class PaymentViewSet(TainoMobileGenericViewSet):
    """
    API for managing payments.

    list:
        Retrieve all payments for the current user.

    retrieve:
        Retrieve a specific payment by pid.

    create_payment:
        Create a new payment request with Zarinpal.

        Required fields:
        - amount: Payment amount in Tomans
        - description: Payment description

        Optional fields:
        - callback_path: Custom callback path for payment verification

        Returns payment object with payment_url for redirecting user to Zarinpal.
    """

    serializer_class = PaymentSerializer

    def get_queryset(self):
        """Return only the current user's payments"""
        logger.info("Fetching payments for user %s", self.request.user)
        return Payment.objects.filter(user=self.request.user).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        """List all payments for the current user"""
        logger.info("User %s is requesting a list of their payments.", request.user)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific payment"""
        instance = self.get_object()
        logger.info("User %s is retrieving payment with PID %s.", request.user, instance.pid)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def create_payment(self, request):
        """Create a new payment with optional coupon support"""
        logger.info("User %s is attempting to create a new payment with data: %s", request.user, request.data)
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get coupon code if provided
        coupon_code = serializer.validated_data.get("coupon_code")

        payment_service = PaymentService()
        payment = payment_service.create_payment(
            user=request.user,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data["description"],
            callback_path=serializer.validated_data.get("callback_path"),
            coupon_code=coupon_code,
        )

        if payment.status == "failed":
            logger.error(
                "Payment creation failed for user %s with amount %s: %s",
                request.user,
                serializer.validated_data["amount"],
                payment.error_message,
            )
            return Response(
                {"success": False, "message": payment.error_message, "payment": PaymentSerializer(payment).data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Payment request successfully created for user %s. PID: %s, Amount: %s", request.user, payment.pid, payment.amount
        )
        return Response({"success": True, "payment": PaymentSerializer(payment).data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def check_status(self, request):
        """Check status of a payment after redirect from Zarinpal"""
        payment_id = request.query_params.get("payment_id")
        logger.info("User %s is checking status for payment_id: %s", request.user, payment_id)

        if not payment_id:
            logger.warning("Payment ID is missing in check_status request from user %s", request.user)
            return Response({"error": "Payment ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        payment_service = PaymentService()
        payment = payment_service.get_payment_by_pid(payment_id)

        if not payment:
            logger.error("Payment with PID %s not found.", payment_id)
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Only allow users to check their own payments
        if payment.user != request.user:
            logger.warning(
                "User %s attempted to access another user's payment (PID: %s, Owner: %s)",
                request.user,
                payment.pid,
                payment.user,
            )
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        logger.info(
            "Status check successful for payment PID %s for user %s. Current status: %s",
            payment.pid,
            request.user,
            payment.status,
        )
        return Response(
            {
                "payment": PaymentSerializer(payment).data,
            }
        )

    @extend_schema(request=ApplyCouponSerializer, responses={201: OutputCouponSerializer})
    @action(detail=False, methods=["post"])
    def apply_coupon(self, request):
        """Apply a coupon code to calculate the discounted amount"""
        logger.info("User %s is attempting to apply a coupon with data: %s", request.user, request.data)
        serializer = ApplyCouponSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        coupon = serializer.validated_data["code"]
        amount = serializer.validated_data["amount"]
        logger.debug("Coupon '%s' is being applied to amount %s for user %s", coupon.code, amount, request.user)

        # Calculate discount
        discount_amount = coupon.calculate_discount_amount(amount)
        discounted_amount = amount - discount_amount
        logger.info(
            "Coupon application successful. Original: %s, Discount: %s, Final: %s", amount, discount_amount, discounted_amount
        )

        output = OutputCouponSerializer(
            instance={
                "original_amount": amount,
                "discount_amount": discount_amount,
                "final_amount": discounted_amount,
                "coupon_code": coupon.code,
            }
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


class VerifyPaymentAPIView(APIView):
    """
    API for verifying payments from Zarinpal callback.

    This endpoint is called by Zarinpal after user completes or cancels payment.
    It verifies the payment and redirects user to appropriate page based on payment status.

    Expected query parameters:
    - payment_id: Payment PID
    - Authority: Zarinpal authority token
    - Status: Payment status ('OK' or 'NOK')

    Redirects to:
    - /payment/success for successful payments
    - /payment/failed for failed payments
    - /payment/canceled for canceled payments
    """

    permission_classes = []  # No permission required for callback

    def get(self, request, *args, **kwargs):
        """Handle Zarinpal callback"""
        payment_id = request.GET.get("payment_id")
        authority = request.GET.get("Authority")
        status_param = request.GET.get("Status")
        logger.info(
            "Received Zarinpal callback. payment_id: %s, authority: %s, status: %s", payment_id, authority, status_param
        )

        payment_service = PaymentService()

        # Get payment by pid or authority
        payment = None
        if payment_id:
            payment = payment_service.get_payment_by_pid(payment_id)
        elif authority:
            payment = payment_service.get_payment_by_authority(authority)

        if not payment:
            logger.error("Payment not found in Zarinpal callback. PID: %s, Authority: %s", payment_id, authority)
            return redirect(f"{settings.PAYMENT_FAILURE_FRONT_BASE_URL}?message=پرداخت یافت نشد")

        # Check if the payment was canceled by user
        if status_param != "OK":
            logger.info("Payment PID %s was canceled by user.", payment.pid)
            payment.status = "canceled"
            payment.error_message = "پرداخت توسط کاربر لغو شد"
            payment.save()
            return redirect(f"{settings.PAYMENT_CANCELED_FRONT_BASE_URL}?payment_id={payment.pid}")

        # Verify payment
        logger.info("Attempting to verify payment PID %s with Authority %s", payment.pid, authority)
        verified = payment_service.verify_payment(payment)

        if verified:
            logger.info("Payment PID %s successfully verified. Ref ID: %s", payment.pid, payment.ref_id)
            # Add this section to deposit to user wallet after verification
            from apps.wallet.services.wallet import WalletService

            WalletService.deposit(
                user=payment.user,
                amount=payment.amount,
                reference_id=payment.ref_id,
                description=f"Payment verified:c {payment.description}",
            )
            logger.info("Deposited %s to user %s's wallet.", payment.amount, payment.user)
            # Redirect to success page
            return redirect(f"{settings.PAYMENT_SUCCESS_FRONT_BASE_URL}?payment_id={payment.pid}&ref_id={payment.ref_id}")
        else:
            logger.error("Payment verification failed for PID %s. Error: %s", payment.pid, payment.error_message)
            # Redirect to failed page
            return redirect(
                f"{settings.PAYMENT_FAILURE_FRONT_BASE_URL}?payment_id={payment.pid}&message={payment.error_message}"
            )


class PaymentWebhookAPIView(APIView):
    """API view for handling payment webhooks from Zarinpal"""

    permission_classes = []  # No permission required for webhooks

    def post(self, request, *args, **kwargs):
        # Handle webhook data
        # This depends on Zarinpal's webhook format - check their documentation
        authority = request.data.get("authority")
        p_status = request.data.get("status")
        logger.info("Received Zarinpal webhook. Authority: %s, Status: %s", authority, p_status)

        if not authority:
            logger.warning("Webhook request received with no authority.")
            return Response({"error": "Authority is required"}, status=status.HTTP_400_BAD_REQUEST)

        payment_service = PaymentService()
        payment = payment_service.get_payment_by_authority(authority)

        if not payment:
            logger.error("Payment not found for authority %s in webhook request.", authority)
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Process payment status update
        if p_status == "success":
            logger.info("Webhook for authority %s indicates success. Verifying payment.", authority)
            payment_service.verify_payment(payment)
        elif p_status == "failed":
            logger.warning("Webhook for authority %s indicates failure.", authority)
            payment.status = "failed"
            payment.save()
        else:
            logger.warning("Unknown status '%s' in webhook for authority %s", p_status, authority)

        return Response({"status": "success"})
