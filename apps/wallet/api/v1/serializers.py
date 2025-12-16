from rest_framework import serializers
from apps.wallet.models import Wallet, Transaction, CoinSettings, CoinPackage
from base_utils.serializers.base import TainoBaseModelSerializer


class WalletBalanceSerializer(TainoBaseModelSerializer):
    """
    Simple serializer to retrieve wallet balance
    """

    balance = serializers.DecimalField(max_digits=20, decimal_places=0, read_only=True)
    coin_balance = serializers.DecimalField(max_digits=20, decimal_places=0, read_only=True)
    currency = serializers.CharField(read_only=True)
    coin_exchange_rate = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ["balance", "coin_balance", "currency", "coin_exchange_rate"]

    def get_coin_exchange_rate(self, obj):
        return CoinSettings.get_exchange_rate()


class WalletDetailSerializer(TainoBaseModelSerializer):
    """
    Serializer for wallet details
    """

    user_name = serializers.SerializerMethodField()
    coin_exchange_rate = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ["pid", "user_name", "balance", "coin_balance", "currency", "coin_exchange_rate", "is_active", "created_at"]
        read_only_fields = fields

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email or obj.user.phone_number

    def get_coin_exchange_rate(self, obj):
        return CoinSettings.get_exchange_rate()


class TransactionSerializer(TainoBaseModelSerializer):
    """
    Serializer for transactions
    """

    type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    has_coin_transaction = serializers.SerializerMethodField()
    metadata = serializers.JSONField(read_only=True)  # Add metadata field

    class Meta:
        model = Transaction
        fields = [
            "pid",
            "amount",
            "coin_amount",
            "type",
            "type_display",
            "status",
            "status_display",
            "description",
            "reference_id",
            "exchange_rate",
            "has_coin_transaction",
            "metadata",  # Include metadata in API response
            "created_at",
        ]
        read_only_fields = fields

    def get_type_display(self, obj):
        return obj.get_type_display()

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_has_coin_transaction(self, obj):
        return obj.coin_amount > 0


class CoinSettingsSerializer(TainoBaseModelSerializer):
    """
    Serializer for coin settings
    """

    class Meta:
        model = CoinSettings
        fields = ["pid", "exchange_rate", "description", "is_active", "is_default", "created_at"]
        read_only_fields = ["pid", "created_at"]


# apps/wallet/api/v1/serializers.py - updated DepositFundsSerializer


class DepositFundsSerializer(serializers.Serializer):
    """
    Serializer for depositing funds
    """

    amount = serializers.DecimalField(max_digits=20, decimal_places=0)
    description = serializers.CharField(required=False, allow_blank=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    buy_coins = serializers.BooleanField(required=False, default=False)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def validate_coupon_code(self, value):
        if not value:
            return value

        # Validate coupon if provided
        from apps.payment.services.coupon import CouponService

        user = self.context["request"].user
        amount = self.initial_data.get("amount")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            # Don't validate coupon if amount is invalid
            # Amount validation will catch this
            return value

        is_valid, message, coupon, _ = CouponService.validate_coupon(value, user, amount)

        if not is_valid:
            raise serializers.ValidationError(message)

        return value


class BuyCoinsSerializer(serializers.Serializer):
    """
    Serializer for buying coins with wallet balance
    """

    rial_amount = serializers.DecimalField(max_digits=20, decimal_places=0)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_rial_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")

        user = self.context["request"].user
        from apps.wallet.services.wallet import WalletService

        balance = WalletService.get_wallet_balance(user)
        if balance < value:
            raise serializers.ValidationError("Insufficient funds in wallet")

        return value

    def to_representation(self, instance):
        result = {
            "rial_amount": instance["amount"],
            "coin_amount": instance["coin_amount"],
            "exchange_rate": instance["exchange_rate"],
            "transaction_id": instance["pid"],
            "description": instance["description"],
            "created_at": instance["created_at"],
        }
        return result


class UseCoinsSerializer(serializers.Serializer):
    """
    Serializer for using coins
    """

    coin_amount = serializers.DecimalField(max_digits=20, decimal_places=0)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_coin_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Coin amount must be greater than zero")

        user = self.context["request"].user
        from apps.wallet.services.wallet import WalletService

        coin_balance = WalletService.get_wallet_coin_balance(user)
        if coin_balance < value:
            raise serializers.ValidationError("موجودی سکه کافی نیست")

        return value


class WithdrawFundsSerializer(serializers.Serializer):
    """
    Serializer for withdrawing funds
    """

    amount = serializers.DecimalField(max_digits=20, decimal_places=0)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")

        user = self.context["request"].user
        from apps.wallet.services.wallet import WalletService

        balance = WalletService.get_wallet_balance(user)
        if balance < value:
            raise serializers.ValidationError("Insufficient funds")

        return value


class CoinCtainoersionSerializer(serializers.Serializer):
    """
    Serializer for ctainoerting between rials and coins
    """

    rial_amount = serializers.DecimalField(max_digits=20, decimal_places=0, required=False)
    coin_amount = serializers.DecimalField(max_digits=20, decimal_places=0, required=False)

    def validate(self, data):
        if not data.get("rial_amount") and not data.get("coin_amount"):
            raise serializers.ValidationError("Either rial_amount or coin_amount must be provided")

        if data.get("rial_amount") and data.get("coin_amount"):
            raise serializers.ValidationError("Only one of rial_amount or coin_amount should be provided")

        return data

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance

        result = {
            "rial_amount": instance.get("rial_amount", 0),
            "coin_amount": instance.get("coin_amount", 0),
            "exchange_rate": CoinSettings.get_exchange_rate(),
        }
        return result


class CoinPackageSerializer(TainoBaseModelSerializer):
    """
    Serializer for coin packages with price per coin calculation
    """

    price_per_coin = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, help_text="قیمت هر سکه در این پکیج"
    )
    role_name = serializers.CharField(
        source="role.name", read_only=True, allow_null=True, help_text="نام نقش کاربری که این پکیج برای آن است"
    )

    class Meta:
        model = CoinPackage
        fields = ["pid", "value", "label", "price", "price_per_coin", "description", "role_name", "order"]
        read_only_fields = fields
