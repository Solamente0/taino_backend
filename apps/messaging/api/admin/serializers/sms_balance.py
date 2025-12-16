from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.messaging.api.admin.serializers.base import AdminUserMinimalSerializer
from apps.messaging.models import SMSBalance
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer

User = get_user_model()


class AdminSMSBalanceSerializer(TainoBaseModelSerializer):
    """Admin serializer for SMS balance records"""

    user = AdminUserMinimalSerializer(read_only=True)
    user_id = serializers.SlugRelatedField(
        source="user", queryset=User.objects.filter(is_active=True), slug_field="pid", write_only=True
    )

    class Meta:
        model = SMSBalance
        fields = ["pid", "user", "user_id", "balance", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]

    def validate_user_id(self, value):
        # Check if balance already exists for this user
        if self.instance is None and SMSBalance.objects.filter(user=value).exists():
            raise serializers.ValidationError("SMS balance already exists for this user")
        return value


class AdminSMSBalanceUpdateSerializer(TainoBaseModelSerializer):
    """Admin serializer for updating SMS balance records"""

    class Meta:
        model = SMSBalance
        fields = ["balance", "is_active"]


class AdminAddSMSBalanceSerializer(TainoBaseSerializer):
    """Serializer for adding SMS balance to a user"""

    user_id = serializers.CharField(required=True)
    amount = serializers.IntegerField(min_value=1, required=True)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate_user_id(self, value):
        try:
            user = User.objects.get(pid=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

    def create(self, validated_data):
        from apps.messaging.services.sms_service import SMSService

        user = validated_data["user_id"]
        amount = validated_data["amount"]
        note = validated_data.get("note", "")

        # Add balance
        previous_balance = SMSService.check_user_sms_balance(user)
        new_balance = SMSService.add_sms_balance(user, amount)

        # Create admin action log if available
        # try:
        #     from django.apps.admin_panel.models import AdminActionLog
        #
        #     AdminActionLog.objects.create(
        #         admin_user=self.context["request"].user,
        #         action_type="add_sms_balance",
        #         affected_user=user,
        #         description=f"Added {amount} SMS credits. Previous balance: {previous_balance}, New balance: {new_balance}. Note: {note}",
        #         data={"previous_balance": previous_balance, "amount_added": amount, "new_balance": new_balance, "note": note},
        #     )
        # except ImportError:
        #     # AdminActionLog not available, continue without logging
        #     pass

        return {
            "user": {
                "pid": user.pid,
                "full_name": f"{user.first_name} {user.last_name}".strip() or user.email or user.phone_number,
                "email": user.email,
                "phone_number": user.phone_number,
            },
            "previous_balance": previous_balance,
            "amount_added": amount,
            "new_balance": new_balance,
        }


class AdminBulkAddSMSBalanceSerializer(TainoBaseSerializer):
    """Serializer for adding SMS balance to multiple users"""

    user_ids = serializers.ListField(child=serializers.CharField(), min_length=1, required=True)
    amount = serializers.IntegerField(min_value=1, required=True)
    note = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        from apps.messaging.services.utils import add_sms_balance_to_users

        user_ids = validated_data["user_ids"]
        amount = validated_data["amount"]
        note = validated_data.get("note", "")

        # Add balance to all users
        result = add_sms_balance_to_users(user_ids, amount)

        # Create admin action log if available
        # try:
        #     from apps.admin_panel.models import AdminActionLog
        #
        #     AdminActionLog.objects.create(
        #         admin_user=self.context["request"].user,
        #         action_type="bulk_add_sms_balance",
        #         description=f"Added {amount} SMS credits to {result['success_count']} of {result['total']} users. Note: {note}",
        #         data={
        #             "user_ids": user_ids,
        #             "amount_added": amount,
        #             "success_count": result["success_count"],
        #             "total": result["total"],
        #             "note": note,
        #         },
        #     )
        # except ImportError:
        #     # AdminActionLog not available, continue without logging
        #     pass

        return result


class AdminLowBalanceUsersSerializer(TainoBaseSerializer):
    """Serializer for low balance users"""

    threshold = serializers.IntegerField(min_value=0, default=5)

    def create(self, validated_data):
        from apps.messaging.services.utils import check_low_balance_users

        threshold = validated_data.get("threshold", 5)

        # Get users with low balance
        users = check_low_balance_users(threshold)

        return {"threshold": threshold, "count": len(users), "users": users}
