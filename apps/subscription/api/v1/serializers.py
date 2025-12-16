# apps/subscription/api/v1/serializers.py
from rest_framework import serializers
from apps.subscription.models import Package, UserSubscription
from apps.payment.api.v1.serializers import PaymentSerializer
from base_utils.serializers.base import TainoBaseModelSerializer


class PackageSerializer(TainoBaseModelSerializer):
    """Serializer for Package model"""

    period_display = serializers.CharField(source="get_period_display", read_only=True)

    class Meta:
        model = Package
        fields = ["pid", "name", "description", "price", "period", "period_display", "features", "created_at"]
        read_only_fields = fields


class UserSubscriptionSerializer(TainoBaseModelSerializer):
    """Serializer for UserSubscription model"""

    package = PackageSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    last_payment = PaymentSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField(read_only=True)
    is_expiring_soon = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "pid",
            "package",
            "status",
            "status_display",
            "start_date",
            "end_date",
            "last_payment",
            "created_at",
            "days_remaining",
            "is_expiring_soon",
        ]
        read_only_fields = fields

    def get_days_remaining(self, obj):
        """Calculate number of days remaining in subscription"""
        from apps.subscription.services.subscription import SubscriptionService

        return SubscriptionService.get_days_remaining(obj)

    def get_is_expiring_soon(self, obj):
        """Check if subscription is expiring within 7 days"""
        from apps.subscription.services.subscription import SubscriptionService

        return SubscriptionService.is_subscription_expiring_soon(obj)


class SubscribeSerializer(serializers.Serializer):
    """Serializer for creating a subscription with optional coupon and coin payment"""

    package_pid = serializers.CharField()
    coupon_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    use_coins = serializers.BooleanField(required=False, default=True)

    def validate_package_pid(self, value):
        try:
            package = Package.objects.get(pid=value, is_active=True)
            return value
        except Package.DoesNotExist:
            raise serializers.ValidationError("Package not found or inactive")

    def validate(self, data):
        data = super().validate(data)

        # Validate coupon if provided
        if "coupon_code" in data and data["coupon_code"]:
            try:
                package = Package.objects.get(pid=data["package_pid"])

                from apps.payment.services.coupon import CouponService

                is_valid, message, coupon, _ = CouponService.validate_coupon(
                    data["coupon_code"], self.context["request"].user, package.price, package
                )

                if not is_valid:
                    raise serializers.ValidationError({"coupon_code": message})

            except Package.DoesNotExist:
                # Will be caught by validate_package_pid
                pass

        return data
