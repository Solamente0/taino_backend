from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.lawyer_office.api.v1.serializers.base import LawyerOfficeUserMinimalSerializer
from apps.messaging.models import SMSBalance, SMSTemplate, SMSPurchase, SMSMessage, SystemSMSTemplate
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class SMSPurchaseSerializer(TainoBaseModelSerializer):
    """Serializer for SMS purchases"""

    user = LawyerOfficeUserMinimalSerializer(read_only=True)

    class Meta:
        model = SMSPurchase
        fields = ["pid", "user", "coins_spent", "sms_quantity", "purchase_date", "created_at"]
        read_only_fields = fields


class SMSPurchaseCreateSerializer(TainoBaseSerializer):
    """Serializer for creating SMS purchases"""

    coins = serializers.IntegerField(min_value=1, write_only=True)

    def validate_coins(self, value):
        # Add validation logic if needed
        # For example, check if user has enough coins
        user = self.context["request"].user
        if user.wallet.coin_balance > int(value):
            return value
        raise ValidationError("موجودی سکه کافی نیست")

    def create(self, validated_data):
        from apps.messaging.services.sms_service import SMSService

        user = self.context["request"].user
        coins = validated_data.get("coins")

        # Purchase SMS with coins
        success, sms_quantity, message = SMSService.purchase_sms_with_coins(user, coins)

        if not success:
            raise serializers.ValidationError(message)

        # Return purchase info
        return {
            "success": success,
            "coins_spent": coins,
            "sms_quantity": sms_quantity,
            "balance": SMSService.check_user_sms_balance(user),
            "message": message,
        }

    def to_representation(self, instance):
        return instance
