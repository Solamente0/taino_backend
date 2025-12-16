# apps/payment/api/v1/serializers.py
from rest_framework import serializers
from apps.payment.models import Payment
from base_utils.serializers.base import TainoBaseModelSerializer

# apps/payment/api/v1/serializers.py - add these to existing serializers
from rest_framework import serializers
from apps.payment.models import Coupon, CouponUsage
from apps.country.services.serializers_field import (
    GlobalCountryReadOnlySerializer,
    GlobalStateReadOnlySerializer,
    GlobalCityReadOnlySerializer,
)


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for Coupon model"""

    discount_type_display = serializers.CharField(source="get_discount_type_display", read_only=True)
    country = GlobalCountryReadOnlySerializer(read_only=True)
    state = GlobalStateReadOnlySerializer(read_only=True)
    city = GlobalCityReadOnlySerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    is_fully_used = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            "pid",
            "code",
            "description",
            "discount_type",
            "discount_type_display",
            "discount_value",
            "max_discount_amount",
            "valid_from",
            "valid_to",
            "max_uses",
            "current_uses",
            "minimum_purchase_amount",
            "specific_user",
            "country",
            "state",
            "city",
            "package",
            "is_active",
            "is_expired",
            "is_fully_used",
            "created_at",
        ]
        read_only_fields = ["pid", "current_uses", "created_at"]

    def get_is_expired(self, obj):
        from django.utils import timezone

        if obj.valid_to:
            return obj.valid_to < timezone.now()
        return False

    def get_is_fully_used(self, obj):
        return obj.current_uses >= obj.max_uses


class CouponCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating coupons"""

    class Meta:
        model = Coupon
        fields = [
            "code",
            "description",
            "discount_type",
            "discount_value",
            "max_discount_amount",
            "valid_from",
            "valid_to",
            "max_uses",
            "minimum_purchase_amount",
            "specific_user",
            "country",
            "state",
            "city",
            "package",
            "is_active",
        ]

    def validate(self, data):
        # Validate discount value
        if data.get("discount_type") == "percentage" and data.get("discount_value", 0) > 100:
            raise serializers.ValidationError({"discount_value": "درصد تخفیف نمی‌تواند بیشتر از 100 باشد"})

        # Validate dates
        if "valid_from" in data and "valid_to" in data and data["valid_from"] and data["valid_to"]:
            if data["valid_from"] >= data["valid_to"]:
                raise serializers.ValidationError({"valid_to": "تاریخ پایان باید بعد از تاریخ شروع باشد"})

        # Validate geographic hierarchy
        if "city" in data and data["city"] and "state" in data and data["state"]:
            if data["city"].state != data["state"]:
                raise serializers.ValidationError({"city": "شهر باید متعلق به استان انتخاب شده باشد"})

        if "state" in data and data["state"] and "country" in data and data["country"]:
            if data["state"].country != data["country"]:
                raise serializers.ValidationError({"state": "استان باید متعلق به کشور انتخاب شده باشد"})

        return data


class CouponUsageSerializer(serializers.ModelSerializer):
    """Serializer for CouponUsage model"""

    coupon_code = serializers.CharField(source="coupon.code", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = CouponUsage
        fields = [
            "pid",
            "coupon",
            "coupon_code",
            "user",
            "user_name",
            "original_amount",
            "discount_amount",
            "final_amount",
            "applied_to",
            "applied_to_id",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class ApplyCouponSerializer(serializers.Serializer):
    """Serializer for applying coupon code"""

    code = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, required=True)
    package_pid = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_code(self, value):
        try:
            return Coupon.objects.get(code=value, is_active=True)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("کد تخفیف نامعتبر است")

    def validate(self, data):
        coupon = data["code"]  # This is now the Coupon object
        user = self.context["request"].user
        amount = data["amount"]

        # Get package if provided
        package = None
        if "package_pid" in data and data["package_pid"]:
            from apps.subscription.models import Package

            try:
                package = Package.objects.get(pid=data["package_pid"])
            except Package.DoesNotExist:
                raise serializers.ValidationError({"package_pid": "پکیج مورد نظر یافت نشد"})

        # Check if coupon is valid
        is_valid, message = coupon.is_valid(user=user, amount=amount, package=package)
        if not is_valid:
            raise serializers.ValidationError({"code": message})

        # Add package to data
        data["package"] = package
        return data


class OutputCouponSerializer(serializers.Serializer):
    original_amount = serializers.CharField(allow_null=True, default=None, read_only=True)
    discount_amount = serializers.CharField(allow_null=True, default=None, read_only=True)
    final_amount = serializers.CharField(allow_null=True, default=None, read_only=True)
    coupon_code = serializers.CharField(allow_null=True, default=None, read_only=True)


# Update PaymentSerializer to include coupon information
class PaymentSerializer(TainoBaseModelSerializer):
    """Serializer for Payment model"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    coupon_code = serializers.SerializerMethodField(read_only=True)
    has_discount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "pid",
            "amount",
            "original_amount",
            "description",
            "status",
            "status_display",
            "payment_url",
            "verified",
            "ref_id",
            "created_at",
            "coupon",
            "coupon_code",
            "discount_amount",
            "has_discount",
        ]
        read_only_fields = fields

    def get_coupon_code(self, obj):
        return obj.coupon.code if obj.coupon else None

    def get_has_discount(self, obj):
        return obj.discount_amount > 0


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating a payment"""

    amount = serializers.DecimalField(max_digits=12, decimal_places=0)
    description = serializers.CharField(max_length=255)
    callback_path = serializers.CharField(max_length=255, required=False)
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
