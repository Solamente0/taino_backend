# apps/wallet/api/admin/serializers.py
from rest_framework import serializers

from apps.authentication.models import UserType
from apps.wallet.models import Wallet, Transaction, CoinSettings, CoinPackage
from base_utils.serializers.base import TainoBaseModelSerializer
from apps.user.api.admin.serializers import AdminUserMinimalSerializer


class AdminWalletSerializer(TainoBaseModelSerializer):
    """Admin serializer for wallet model"""

    user = AdminUserMinimalSerializer(read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ["pid", "user", "user_name", "balance", "coin_balance", "currency", "is_active", "created_at"]
        read_only_fields = fields

    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "Unknown"


class AdminTransactionSerializer(TainoBaseModelSerializer):
    """Admin serializer for transaction model"""

    wallet = AdminWalletSerializer(read_only=True)
    user_name = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "pid",
            "wallet",
            "user_name",
            "amount",
            "coin_amount",
            "type",
            "type_display",
            "status",
            "status_display",
            "exchange_rate",
            "description",
            "reference_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        if obj.wallet and obj.wallet.user:
            return f"{obj.wallet.user.first_name} {obj.wallet.user.last_name}"
        return "Unknown"


class AdminCoinSettingsSerializer(TainoBaseModelSerializer):
    """Admin serializer for coin settings model"""

    class Meta:
        model = CoinSettings
        fields = ["pid", "exchange_rate", "description", "is_active", "is_default", "created_at"]
        read_only_fields = fields


class AdminCoinSettingsCreateUpdateSerializer(TainoBaseModelSerializer):
    """Admin serializer for creating and updating coin settings"""

    class Meta:
        model = CoinSettings
        fields = ["exchange_rate", "description", "is_active", "is_default"]

    def validate_exchange_rate(self, value):
        if value <= 0:
            raise serializers.ValidationError("Exchange rate must be greater than zero")
        return value

    def validate(self, data):
        # If this is marked as default, ensure it's also active
        if data.get("is_default", False) and not data.get("is_active", True):
            data["is_active"] = True
        return data


class AdminCoinPackageSerializer(TainoBaseModelSerializer):
    """Admin serializer for viewing coin packages"""

    role_name = serializers.CharField(source="role.name", read_only=True, allow_null=True)
    price_per_coin = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CoinPackage
        fields = [
            "pid",
            "value",
            "label",
            "price",
            "price_per_coin",
            "role",
            "role_name",
            "order",
            "description",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["pid", "created_at", "price_per_coin", "role_name"]


class AdminCoinPackageCreateUpdateSerializer(TainoBaseModelSerializer):
    """Admin serializer for creating and updating coin packages"""

    role = serializers.SlugRelatedField(
        queryset=UserType.objects.filter(is_active=True),
        slug_field="pid",
        required=False,
        allow_null=True,
        help_text="نقش کاربری - اگر خالی باشد، برای همه نمایش داده می‌شود",
    )

    class Meta:
        model = CoinPackage
        fields = ["value", "label", "price", "role", "order", "description", "is_active"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("قیمت باید بیشتر از صفر باشد")
        return value

    def validate_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد سکه باید بیشتر از صفر باشد")
        return value

    def to_representation(self, instance):
        return AdminCoinPackageSerializer(instance, context=self.context).data
