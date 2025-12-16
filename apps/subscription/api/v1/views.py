# apps/subscription/api/v1/views.py
import logging
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.subscription.services.subscription import SubscriptionService

from apps.payment.api.v1.serializers import PaymentSerializer
from apps.subscription.models import Package, UserSubscription, SubscriptionPeriod
from apps.payment.models import Payment
from apps.payment.services.payment import PaymentService
from apps.wallet.api.v1.serializers import TransactionSerializer
from .serializers import PackageSerializer, UserSubscriptionSerializer, SubscribeSerializer
from base_utils.views.mobile import TainoMobileGenericViewSet, TainoMobileReadOnlyModelViewSet
from base_utils.filters import IsActiveFilterBackend

logger = logging.getLogger(__name__)


class PackageViewSet(TainoMobileReadOnlyModelViewSet):
    """ViewSet for listing subscription packages"""

    queryset = Package.objects.all()
    serializer_class = PackageSerializer

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["name", "description"]
    filterset_fields = ["period"]
    ordering_fields = ["price", "created_at"]
    ordering = ["price"]


class UserSubscriptionViewSet(TainoMobileGenericViewSet):
    """ViewSet for user subscriptions"""

    serializer_class = UserSubscriptionSerializer

    def get_queryset(self):
        """Return only the current user's subscriptions"""
        return UserSubscription.objects.filter(user=self.request.user).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        """List all subscriptions for the current user"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific subscription"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(responses={200: UserSubscriptionSerializer})
    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get the current active subscription for the user"""
        from apps.subscription.services.subscription import SubscriptionService

        subscription = SubscriptionService.get_active_subscription(request.user)

        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        else:
            return Response({"message": "No active subscription found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(request=SubscribeSerializer)
    @action(detail=False, methods=["post"])
    def subscribe(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the package
        package = Package.objects.get(pid=serializer.validated_data["package_pid"])

        # Check if user wants to pay with coins
        use_coins = serializer.validated_data.get("use_coins", True)

        # Check if the user already has an active subscription
        from apps.subscription.services.subscription import SubscriptionService

        current_subscription = SubscriptionService.get_active_subscription(request.user)

        # Check if user has sufficient funds (either rial or coins)
        from apps.wallet.services.wallet import WalletService

        if use_coins:
            # Ctainoert price to coins
            # coin_amount = CoinSettings.ctainoert_rial_to_coin(package.price)
            coin_amount = package.price

            # Check if user has enough coins
            if WalletService.get_wallet_coin_balance(request.user) >= coin_amount:
                # Handle subscription based on whether user already has one
                if current_subscription and current_subscription.status == "active":
                    # Extend the existing subscription
                    subscription = current_subscription

                    # Calculate the new end date by adding the package period to the current end date
                    if package.period == SubscriptionPeriod.MONTHLY:
                        subscription.end_date = subscription.end_date + timedelta(days=30)
                    elif package.period == SubscriptionPeriod.QUARTERLY:
                        subscription.end_date = subscription.end_date + timedelta(days=90)
                    elif package.period == SubscriptionPeriod.BIANNUAL:
                        subscription.end_date = subscription.end_date + timedelta(days=180)
                    elif package.period == SubscriptionPeriod.ANNUAL:
                        subscription.end_date = subscription.end_date + timedelta(days=365)

                    # Update the package to the new one
                    subscription.package = package
                    subscription.save()
                else:
                    # Create a new subscription (active state)
                    subscription = UserSubscription.objects.create(
                        user=request.user, package=package, status="active", start_date=timezone.now()
                    )

                    # Set end date based on package period
                    if package.period == SubscriptionPeriod.MONTHLY:
                        subscription.end_date = subscription.start_date + timedelta(days=30)
                    elif package.period == SubscriptionPeriod.QUARTERLY:
                        subscription.end_date = subscription.start_date + timedelta(days=90)
                    elif package.period == SubscriptionPeriod.BIANNUAL:
                        subscription.end_date = subscription.start_date + timedelta(days=180)
                    elif package.period == SubscriptionPeriod.ANNUAL:
                        subscription.end_date = subscription.start_date + timedelta(days=365)

                    subscription.save()

                # Process payment from wallet using coins
                try:
                    transaction = WalletService.use_coins(
                        user=request.user, coin_amount=coin_amount, description=f"خرید اشتراک {package.name} با سکه"
                    )
                    SubscriptionService.update_user_premium_status(request.user, True)
                    return Response(
                        {
                            "subscription": UserSubscriptionSerializer(subscription).data,
                            "transaction": TransactionSerializer(transaction).data,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                except ValueError as e:
                    # If payment fails, delete the subscription only if it's new
                    if not current_subscription:
                        subscription.delete()
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {
                        "error": "موجودی سکه کافی نیست",
                        "required_coin_amount": coin_amount,
                        "current_coin_balance": WalletService.get_wallet_coin_balance(request.user),
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )
        else:
            # Pay with normal balance
            if WalletService.get_wallet_balance(request.user) >= package.price:
                # Handle subscription based on whether user already has one
                if current_subscription and current_subscription.status == "active":
                    # Extend the existing subscription
                    subscription = current_subscription

                    # Calculate the new end date by adding the package period to the current end date
                    if package.period == SubscriptionPeriod.MONTHLY:
                        subscription.end_date = subscription.end_date + timedelta(days=30)
                    elif package.period == SubscriptionPeriod.QUARTERLY:
                        subscription.end_date = subscription.end_date + timedelta(days=90)
                    elif package.period == SubscriptionPeriod.BIANNUAL:
                        subscription.end_date = subscription.end_date + timedelta(days=180)
                    elif package.period == SubscriptionPeriod.ANNUAL:
                        subscription.end_date = subscription.end_date + timedelta(days=365)

                    # Update the package to the new one
                    subscription.package = package
                    subscription.save()

                else:
                    # Create a new subscription (active state)
                    subscription = UserSubscription.objects.create(
                        user=request.user, package=package, status="active", start_date=timezone.now()
                    )

                    # Set end date based on package period
                    if package.period == SubscriptionPeriod.MONTHLY:
                        subscription.end_date = subscription.start_date + timedelta(days=30)
                    elif package.period == SubscriptionPeriod.QUARTERLY:
                        subscription.end_date = subscription.start_date + timedelta(days=90)
                    elif package.period == SubscriptionPeriod.BIANNUAL:
                        subscription.end_date = subscription.start_date + timedelta(days=180)
                    elif package.period == SubscriptionPeriod.ANNUAL:
                        subscription.end_date = subscription.start_date + timedelta(days=365)

                    subscription.save()

                # Process payment from wallet
                transaction = WalletService.pay_for_consultation(
                    user=request.user, amount=package.price, description=f"Subscription to {package.name}"
                )
                SubscriptionService.update_user_premium_status(request.user, True)
                return Response(
                    {
                        "subscription": UserSubscriptionSerializer(subscription).data,
                        "transaction": TransactionSerializer(transaction).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                # If insufficient funds, guide user to deposit
                return Response(
                    {
                        "error": "Insufficient funds in wallet",
                        "required_amount": package.price,
                        "current_balance": WalletService.get_wallet_balance(request.user),
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

    @action(detail=True, methods=["get"])
    def verify_payment(self, request, pid=None):
        """Verify payment and activate subscription after redirect from payment gateway"""
        subscription = self.get_object()

        # Check if subscription already active
        if subscription.status == "active":
            SubscriptionService.update_user_premium_status(subscription.user, True)

            return Response(
                {
                    "message": "This subscription is already active",
                    "subscription": UserSubscriptionSerializer(subscription).data,
                }
            )

        # Check payment status
        if not subscription.last_payment:
            return Response({"error": "No payment found for this subscription"}, status=status.HTTP_400_BAD_REQUEST)

        # If payment is already verified, activate the subscription
        if subscription.last_payment.verified:
            # Check if this is an extension of an existing subscription
            extend_subscription_pid = None
            if hasattr(subscription, "metadata") and subscription.metadata:
                extend_subscription_pid = subscription.metadata.get("extend_subscription_pid")

            if extend_subscription_pid:
                try:
                    # Find the original subscription to extend
                    original_subscription = UserSubscription.objects.get(pid=extend_subscription_pid)

                    if original_subscription.status == "active":
                        # Determine subscription period
                        now = timezone.now()

                        # Calculate extension based on package period
                        if subscription.package.period == SubscriptionPeriod.MONTHLY:
                            extension = timedelta(days=30)
                        elif subscription.package.period == SubscriptionPeriod.QUARTERLY:
                            extension = timedelta(days=90)
                        elif subscription.package.period == SubscriptionPeriod.BIANNUAL:
                            extension = timedelta(days=180)
                        elif subscription.package.period == SubscriptionPeriod.ANNUAL:
                            extension = timedelta(days=365)
                        else:
                            extension = timedelta(days=30)  # Default to monthly

                        # Update the original subscription
                        original_subscription.end_date = original_subscription.end_date + extension
                        original_subscription.package = subscription.package
                        original_subscription.save()

                        # Mark current subscription as completed since we extended the original one
                        subscription.status = "completed"
                        subscription.save()

                        return Response(
                            {
                                "message": "Subscription extended successfully",
                                "subscription": UserSubscriptionSerializer(original_subscription).data,
                            }
                        )
                    else:
                        # Original subscription is no longer active, create new subscription
                        pass
                except UserSubscription.DoesNotExist:
                    # Original subscription doesn't exist anymore, create new subscription
                    pass

            # If we get here, we're activating a new subscription
            # Determine subscription period
            now = timezone.now()

            if subscription.package.period == SubscriptionPeriod.MONTHLY:
                end_date = now + timedelta(days=30)
            elif subscription.package.period == SubscriptionPeriod.QUARTERLY:
                end_date = now + timedelta(days=90)
            elif subscription.package.period == SubscriptionPeriod.BIANNUAL:
                end_date = now + timedelta(days=180)
            elif subscription.package.period == SubscriptionPeriod.ANNUAL:
                end_date = now + timedelta(days=365)
            else:
                end_date = now + timedelta(days=30)  # Default to monthly

            # Update subscription
            subscription.status = "active"
            subscription.start_date = now
            subscription.end_date = end_date
            subscription.save()

            return Response(
                {
                    "message": "Subscription activated successfully",
                    "subscription": UserSubscriptionSerializer(subscription).data,
                }
            )
        else:
            # Payment is not verified yet, this may happen if there was
            # an issue with the redirect from Zarinpal
            return Response(
                {"message": "Payment not yet verified", "subscription": UserSubscriptionSerializer(subscription).data},
                status=status.HTTP_202_ACCEPTED,
            )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pid=None):
        """Cancel a subscription"""
        subscription = self.get_object()

        if subscription.status != "active":
            return Response({"error": "Only active subscriptions can be canceled"}, status=status.HTTP_400_BAD_REQUEST)

        subscription.status = "canceled"
        subscription.save()
        SubscriptionService.sync_premium_status_with_subscription(request.user)

        return Response(
            {"message": "Subscription canceled successfully", "subscription": UserSubscriptionSerializer(subscription).data}
        )

    # در فایل apps/subscription/api/v1/views.py

    @extend_schema(request=SubscribeSerializer)
    @action(detail=False, methods=["post"])
    def top_up_and_subscribe(self, request):
        """Subscribe to a package via payment gateway with optional coupon support"""
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the package
        package = Package.objects.get(pid=serializer.validated_data["package_pid"])

        # Get coupon code if provided
        coupon_code = serializer.validated_data.get("coupon_code")

        # Check if the user already has an active subscription
        from apps.subscription.services.subscription import SubscriptionService

        current_subscription = SubscriptionService.get_active_subscription(request.user)

        # Create pending subscription or update existing one
        if current_subscription and current_subscription.status == "active":
            # We'll update this subscription after payment is verified, for now create a pending one for payment
            subscription = UserSubscription.objects.create(
                user=request.user,
                package=package,
                status="pending",
                # Store the original subscription id to link them after verification
                metadata={"extend_subscription_pid": current_subscription.pid},
            )
        else:
            # Create new pending subscription
            subscription = UserSubscription.objects.create(user=request.user, package=package, status="pending")

        # Create payment with Zarinpal
        from apps.payment.services.payment import PaymentService

        payment_service = PaymentService()

        callback_path = f"/api/subscription/v1/subscriptions/{subscription.pid}/verify-payment-and-subscribe/"
        payment = payment_service.create_payment(
            user=request.user,
            amount=package.price,
            description=f"Subscription to {package.name}",
            callback_path=callback_path,
            coupon_code=coupon_code,
        )

        # Link payment to subscription
        subscription.last_payment = payment
        subscription.save()

        # If the payment was fully covered by coupon (100% discount)
        if payment.status == "successful" and payment.verified:
            # If we need to extend an existing subscription
            if current_subscription and current_subscription.status == "active":
                # Calculate the new end date by adding the package period to the current end date
                if package.period == SubscriptionPeriod.MONTHLY:
                    current_subscription.end_date = current_subscription.end_date + timedelta(days=30)
                elif package.period == SubscriptionPeriod.QUARTERLY:
                    current_subscription.end_date = current_subscription.end_date + timedelta(days=90)
                elif package.period == SubscriptionPeriod.BIANNUAL:
                    current_subscription.end_date = current_subscription.end_date + timedelta(days=180)
                elif package.period == SubscriptionPeriod.ANNUAL:
                    current_subscription.end_date = current_subscription.end_date + timedelta(days=365)

                # Update the package to the new one
                current_subscription.package = package
                current_subscription.save()

                # Update the pending subscription to link to the extended one
                subscription.status = "completed"  # Mark as completed since we extended the existing one
                subscription.save()
                SubscriptionService.update_user_premium_status(current_subscription.user, True)

                return Response(
                    {
                        "message": "اشتراک با موفقیت تمدید شد (استفاده از کد تخفیف)",
                        "subscription": UserSubscriptionSerializer(current_subscription).data,
                        "payment": PaymentSerializer(payment).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                # This is a new subscription
                subscription.status = "active"
                subscription.start_date = timezone.now()

                # Set end date based on package period
                if package.period == SubscriptionPeriod.MONTHLY:
                    subscription.end_date = subscription.start_date + timedelta(days=30)
                elif package.period == SubscriptionPeriod.QUARTERLY:
                    subscription.end_date = subscription.start_date + timedelta(days=90)
                elif package.period == SubscriptionPeriod.BIANNUAL:
                    subscription.end_date = subscription.start_date + timedelta(days=180)
                elif package.period == SubscriptionPeriod.ANNUAL:
                    subscription.end_date = subscription.start_date + timedelta(days=365)

                subscription.save()
                SubscriptionService.update_user_premium_status(current_subscription.user, True)

                return Response(
                    {
                        "message": "اشتراک با موفقیت فعال شد (استفاده از کد تخفیف)",
                        "subscription": UserSubscriptionSerializer(subscription).data,
                        "payment": PaymentSerializer(payment).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        return Response(
            {"subscription": UserSubscriptionSerializer(subscription).data, "payment_url": payment.payment_url},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=SubscribeSerializer)
    @action(detail=False, methods=["post"])
    def subscribe_with_payment(self, request):
        """Subscribe to a package via bank payment (not coins)"""
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        package = Package.objects.get(pid=serializer.validated_data["package_pid"])
        coupon_code = serializer.validated_data.get("coupon_code")

        # Get pricing for subscription
        from apps.pricing.services.pricing_service import PricingService
        pricing_info = PricingService.get_price(
            user=request.user,
            feature=f"subscription_{package.period}",
            use_coins=False  # Force bank payment
        )

        # Use package price or pricing system price
        final_price = pricing_info['price'] if pricing_info['price'] > 0 else package.price

        # Create payment with Zarinpal
        from apps.payment.services.payment import PaymentService
        payment_service = PaymentService()

        # Create pending subscription
        subscription = UserSubscription.objects.create(
            user=request.user,
            package=package,
            status="pending"
        )

        callback_path = f"/api/subscription/v1/subscriptions/{subscription.pid}/verify/"
        payment = payment_service.create_payment(
            user=request.user,
            amount=final_price,
            description=f"خرید اشتراک {package.name}",
            callback_path=callback_path,
            coupon_code=coupon_code,
        )

        subscription.last_payment = payment
        subscription.save()

        return Response(
            {
                "subscription": UserSubscriptionSerializer(subscription).data,
                "payment_url": payment.payment_url
            },
            status=status.HTTP_201_CREATED,
        )
