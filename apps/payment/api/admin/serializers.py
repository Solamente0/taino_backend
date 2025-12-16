# apps/payment/api/admin/serializers.py
from rest_framework import serializers
from apps.payment.models import Coupon, CouponUsage, ZarinpalPaymentConfig
from apps.payment.api.v1.serializers import CouponSerializer, CouponCreateUpdateSerializer, CouponUsageSerializer


class AdminZarinpalConfigSerializer(serializers.ModelSerializer):
    """Serializer for ZarinpalPaymentConfig model"""

    class Meta:
        model = ZarinpalPaymentConfig
        fields = [
            "pid",
            "merchant_id",
            "api_key",
            "is_sandbox",
            "description",
            "is_active",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]


class AdminZarinpalConfigCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating ZarinpalPaymentConfig"""

    class Meta:
        model = ZarinpalPaymentConfig
        fields = [
            "merchant_id",
            "api_key",
            "is_sandbox",
            "description",
            "is_active",
            "is_default",
        ]

    def validate_merchant_id(self, value):
        if not value:
            raise serializers.ValidationError("Merchant ID is required")
        return value

    def validate(self, data):
        # If this is marked as default, ensure it's also active
        if data.get("is_default", False) and not data.get("is_active", True):
            data["is_active"] = True
        return data
