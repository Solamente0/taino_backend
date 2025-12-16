# apps/wallet/api/v1/views.py
from django.conf import settings
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status, serializers
from rest_framework.decorators import action, authentication_classes, permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.payment.api.v1.serializers import PaymentSerializer
from apps.payment.services.payment import PaymentService
from apps.wallet.api.v1.serializers import (
    WalletBalanceSerializer,
    WalletDetailSerializer,
    TransactionSerializer,
    DepositFundsSerializer,
    WithdrawFundsSerializer,
    BuyCoinsSerializer,
    UseCoinsSerializer,
    CoinSettingsSerializer,
    CoinCtainoersionSerializer,
    CoinPackageSerializer,
)
from apps.wallet.models import CoinSettings, CoinPackage
from apps.wallet.services.wallet import WalletService
from apps.wallet.services.query import WalletQuery
from base_utils.views.mobile import TainoMobileGenericViewSet


class WalletViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for user wallet operations
    """

    def get_serializer_class(self):
        if self.action == "balance":
            return WalletBalanceSerializer
        elif self.action == "deposit":
            return DepositFundsSerializer
        elif self.action == "withdraw":
            return WithdrawFundsSerializer
        elif self.action == "transactions":
            return TransactionSerializer
        elif self.action == "buy_coins":
            return BuyCoinsSerializer
        elif self.action == "use_coins":
            return UseCoinsSerializer
        elif self.action == "ctainoert_currency":
            return CoinCtainoersionSerializer
        return WalletDetailSerializer

    def get_queryset(self):
        # This will prevent listing all wallets
        return WalletQuery.get_active_wallets()

    def get_permissions(self):
        if self.action == "verify_deposit":
            return []
        else:
            return [perm() for perm in TainoMobileGenericViewSet.permission_classes]

    @extend_schema(responses={200: WalletDetailSerializer})
    @action(detail=False, methods=["GET"], url_path="details")
    def details(self, request):
        """
        Get detailed information about the user's wallet
        """
        wallet = WalletService.get_or_create_wallet(self.request.user)
        serializer = WalletDetailSerializer(wallet)
        return Response(serializer.data)

    @extend_schema(responses={200: WalletBalanceSerializer})
    @action(detail=False, methods=["GET"], url_path="balance")
    def balance(self, request):
        """
        Get current wallet balance (both Rial and Coin)
        """
        wallet = WalletService.get_or_create_wallet(self.request.user)
        serializer = WalletBalanceSerializer(wallet)
        return Response(serializer.data)

    # apps/wallet/api/v1/views.py - updated deposit method with Zarinpal integration and coin support

    @extend_schema(request=DepositFundsSerializer, responses={200: TransactionSerializer})
    @action(detail=False, methods=["POST"], url_path="deposit")
    def deposit(self, request):
        """
        Deposit funds to wallet via payment gateway

        Creates a payment request with Zarinpal and returns the payment URL
        for the user to complete the payment. After payment, the funds will
        be deposited to the user's wallet or ctainoerted to coins if buy_coins=True.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        description = serializer.validated_data.get("description", "Wallet deposit")
        coupon_code = serializer.validated_data.get("coupon_code")
        buy_coins = serializer.validated_data.get("buy_coins", True)

        # Create a payment request using PaymentService
        from apps.payment.services.payment import PaymentService

        payment_service = PaymentService()

        # Create a callback path that points to our wallet-specific verification endpoint
        callback_path = "/api/wallet/v1/verify-deposit/"

        # Add info about buying coins to the description if needed
        if buy_coins:
            coin_amount = CoinSettings.ctainoert_rial_to_coin(amount)
            description = f"{description} (خرید {coin_amount} سکه)"

        payment = payment_service.create_payment(
            user=request.user, amount=amount, description=description, callback_path=callback_path, coupon_code=coupon_code
        )

        if payment.status == "failed":
            return Response(
                {"success": False, "message": payment.error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If payment is already verified (happens with 100% discount coupon)
        if payment.verified:
            try:
                if buy_coins:
                    # Buy coins directly
                    tran = WalletService.buy_coins_from_payment(
                        user=request.user,
                        rial_amount=amount,
                        reference_id=payment.ref_id or f"coupon-{payment.pid}",
                        description=description,
                    )
                else:
                    # Deposit the amount to the wallet
                    tran = WalletService.deposit(
                        user=request.user,
                        amount=amount,
                        reference_id=payment.ref_id or f"coupon-{payment.pid}",
                        description=description,
                    )

                return Response(
                    {
                        "success": True,
                        "message": "Deposit completed with coupon discount",
                        "transaction": TransactionSerializer(tran).data,
                        "buy_coins": buy_coins,
                    }
                )

            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Return the payment URL for redirection
        return Response(
            {"success": True, "payment_id": payment.pid, "payment_url": payment.payment_url, "buy_coins": buy_coins},
            status=status.HTTP_200_OK,
        )

    # apps/wallet/api/v1/views.py - Fixed verify_deposit method

    @extend_schema(responses={200: TransactionSerializer})
    @action(detail=False, methods=["GET"], url_path="verify-deposit", authentication_classes=[], permission_classes=[])
    def verify_deposit(self, request):
        """
        Verify a wallet deposit payment

        This endpoint is called by the payment gateway after the user completes
        or cancels the payment. It verifies the payment and deposits the funds
        to the user's wallet if successful.
        """
        payment_id = request.query_params.get("payment_id")

        if not payment_id:
            return Response({"error": "Payment ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the payment using PaymentService
        payment_service = PaymentService()
        payment = payment_service.get_payment_by_pid(payment_id)

        if not payment:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        user = payment.user

        # If payment is already verified, no need to verify again
        if payment.verified:
            return Response(
                {"success": True, "message": "Payment already verified", "payment": PaymentSerializer(payment).data}
            )

        # Verify the payment
        verified = payment_service.verify_payment(payment)

        if not verified:
            # Payment verification failed - redirect to failure page
            redirect_url = (
                f"{settings.PAYMENT_FAILURE_FRONT_BASE_URL}?" f"payment_id={payment.pid}&message={payment.error_message}"
            )
            return redirect(redirect_url)

        # Payment verified successfully
        try:
            # Check if this is a coin purchase by looking for package info in metadata
            package_pid = payment.metadata.get("package_pid") if payment.metadata else None

            if package_pid:
                # This is a coin package purchase
                try:
                    package = CoinPackage.objects.get(pid=package_pid, is_active=True)
                except CoinPackage.DoesNotExist:
                    return Response({"error": "پکیج سکه یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

                coin_amount = package.value

                # Create description with coupon info if applicable
                if payment.coupon is not None and payment.discount_amount > 0:
                    description = (
                        f"خرید {coin_amount} سکه با پرداخت {payment.amount} ریال " f"(تخفیف {payment.discount_amount} ریال)"
                    )
                else:
                    description = f"خرید {coin_amount} سکه با پرداخت {payment.amount} ریال"

                # Add coins to wallet
                created_transaction = WalletService.reward_coins(
                    user=user, coin_amount=coin_amount, reference_id=payment.ref_id, description=description
                )
            else:
                # Regular deposit to wallet
                created_transaction = WalletService.deposit(
                    user=user,
                    amount=payment.original_amount,
                    reference_id=payment.ref_id,
                    description=f"واریز به کیف پول - شماره پیگیری: {payment.pid}",
                )

            # Redirect to success page
            success_url = (
                f"{settings.PAYMENT_SUCCESS_FRONT_BASE_URL}?"
                f"payment_id={payment.pid}&"
                f"transaction_id={created_transaction.pid}&"
                f"ref_id={payment.ref_id}"
            )
            return redirect(success_url)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error in verify_deposit: {str(e)}")

            return Response({"error": "خطا در پردازش پرداخت"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(request=WithdrawFundsSerializer, responses={200: TransactionSerializer})
    @action(detail=False, methods=["POST"], url_path="withdraw")
    def withdraw(self, request):
        """
        Withdraw funds from wallet
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        description = serializer.validated_data.get("description", "")

        try:
            tran = WalletService.withdraw(user=request.user, amount=amount, description=description)
            return Response(TransactionSerializer(tran).data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # apps/wallet/api/v1/views.py - Updated buy_coins action in WalletViewSet

    @extend_schema(
        request=inline_serializer(
            name="BuyCoinPackageSerializer",
            fields={
                "package_pid": serializers.CharField(required=True, help_text="شناسه پکیج سکه"),
                "payment_method": serializers.ChoiceField(
                    choices=["bank", "wallet"], default="bank", help_text="روش پرداخت: bank (درگاه بانکی) یا wallet (کیف پول)"
                ),
            },
        ),
        responses={
            200: inline_serializer(
                name="BuyCoinPackageResponse",
                fields={
                    "payment_url": serializers.URLField(required=False),
                    "message": serializers.CharField(required=False),
                    "total_price": serializers.DecimalField(max_digits=12, decimal_places=0),
                    "coin_amount": serializers.IntegerField(),
                    "package_label": serializers.CharField(),
                },
            )
        },
        description="خرید پکیج سکه با استفاده از قیمت تعریف شده در پکیج",
    )
    @action(detail=False, methods=["post"], url_path="buy-coins")
    def buy_coins(self, request):
        """
        Purchase a coin package using its defined price

        This replaces the old pricing system that used exchange_rate.
        Now each package has its own specific price.
        """
        package_pid = request.data.get("package_pid")
        payment_method = request.data.get("payment_method", "bank")

        if not package_pid:
            return Response({"error": "package_pid الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the package
        try:
            package = CoinPackage.objects.get(pid=package_pid, is_active=True)
        except CoinPackage.DoesNotExist:
            return Response({"error": "پکیج سکه یافت نشد یا غیرفعال است"}, status=status.HTTP_404_NOT_FOUND)

        # Verify user has access to this package (role check)
        user = request.user
        if package.role:
            if not hasattr(user, "role") or not user.role or user.role != package.role:
                return Response({"error": "شما دسترسی به این پکیج را ندارید"}, status=status.HTTP_403_FORBIDDEN)

        # Use the package's price
        total_price = package.price
        coin_amount = package.value

        if payment_method == "bank":
            # Create payment gateway transaction with package info in metadata
            from apps.payment.services.payment import PaymentService

            payment_service = PaymentService()

            # Store package info in payment metadata for verification later
            metadata = {"package_pid": package.pid, "coin_amount": coin_amount, "package_label": package.label}
            print("metadata===", flush=True)
            payment = payment_service.create_payment(
                user=request.user,
                amount=total_price,
                description=f"خرید پکیج {package.label} ({coin_amount} سکه)",
                callback_path="/api/wallet/v1/verify-deposit/",
                metadata=metadata,  # Pass metadata to payment
            )

            return Response(
                {
                    "payment_url": payment.payment_url,
                    "total_price": total_price,
                    "coin_amount": coin_amount,
                    "package_label": package.label,
                }
            )

        elif payment_method == "wallet":
            # Deduct from wallet and add coins
            from apps.wallet.services.wallet import WalletService

            if WalletService.get_wallet_balance(request.user) < total_price:
                return Response({"error": "موجودی کیف پول کافی نیست"}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct balance
            WalletService.withdraw(
                user=request.user, amount=total_price, description=f"خرید پکیج {package.label} ({coin_amount} سکه)"
            )

            # Add coins using the exact package value
            WalletService.reward_coins(user=request.user, coin_amount=coin_amount, description=f"خرید پکیج {package.label}")

            return Response(
                {
                    "message": "پکیج سکه با موفقیت خریداری شد",
                    "coin_amount": coin_amount,
                    "total_price": total_price,
                    "package_label": package.label,
                }
            )

        return Response({"error": "روش پرداخت نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=UseCoinsSerializer, responses={200: TransactionSerializer})
    @action(detail=False, methods=["POST"], url_path="use-coins")
    def use_coins(self, request):
        """
        Use coins from wallet
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        coin_amount = serializer.validated_data["coin_amount"]
        description = serializer.validated_data.get("description", "استفاده از سکه")

        try:
            tran = WalletService.use_coins(user=request.user, coin_amount=coin_amount, description=description)
            return Response(TransactionSerializer(tran).data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=CoinCtainoersionSerializer, responses={200: CoinCtainoersionSerializer})
    @action(detail=False, methods=["POST"], url_path="ctainoert-currency")
    def ctainoert_currency(self, request):
        """
        Ctainoert between rial and coins (just calculation, no actual transaction)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rial_amount = serializer.validated_data.get("rial_amount")
        coin_amount = serializer.validated_data.get("coin_amount")
        exchange_rate = CoinSettings.get_exchange_rate()

        result = {"exchange_rate": exchange_rate}

        if rial_amount:
            result["rial_amount"] = rial_amount
            result["coin_amount"] = CoinSettings.ctainoert_rial_to_coin(rial_amount)
        else:
            result["coin_amount"] = coin_amount
            result["rial_amount"] = CoinSettings.ctainoert_coin_to_rial(coin_amount)

        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(responses={200: TransactionSerializer(many=True)})
    @action(detail=False, methods=["GET"], url_path="transactions")
    def transactions(self, request):
        """
        Get transaction history
        """
        transaction_type = request.query_params.get("type")
        coin_only = request.query_params.get("coin_only", "false").lower() == "true"

        transactions = WalletQuery.get_user_transactions(user_id=request.user.pid, transaction_type=transaction_type)

        # Filter for coin transactions if requested
        if coin_only:
            transactions = transactions.filter(coin_amount__gt=0)

        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)


class CoinSettingsViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for coin settings (admin only)
    """

    serializer_class = CoinSettingsSerializer

    def get_queryset(self):
        return CoinSettings.objects.all().order_by("-created_at")

    @extend_schema(responses={200: CoinSettingsSerializer})
    @action(detail=False, methods=["GET"], url_path="current")
    def current(self, request):
        """
        Get current coin settings
        """
        settings = CoinSettings.get_default()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class CoinPackageViewSet(TainoMobileGenericViewSet):
    """
    ViewSet for coin packages - shows role-based packages
    """

    serializer_class = CoinPackageSerializer

    def get_permissions(self):
        # Allow authenticated users to see their packages
        # Optionally allow anonymous users to see generic packages
        if self.action == "list":
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """
        Get packages based on user's role
        - If user is authenticated: return packages for their role + generic packages
        - If user is anonymous: return only generic packages
        """
        user = self.request.user

        if user and user.is_authenticated:
            # Get packages for this user's role
            return CoinPackage.get_packages_for_user(user)

        # For anonymous users, show only generic packages
        return CoinPackage.objects.filter(is_active=True, role__isnull=True).order_by("order", "value")

    @extend_schema(
        responses={200: CoinPackageSerializer(many=True)},
        description="دریافت لیست پکیج‌های سکه بر اساس نقش کاربر. پکیج‌های عمومی و پکیج‌های مخصوص نقش کاربر نمایش داده می‌شوند.",
    )
    def list(self, request):
        """
        List all active coin packages for the current user's role

        Returns packages that are either:
        1. Generic (no role specified)
        2. Specific to the user's role
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
