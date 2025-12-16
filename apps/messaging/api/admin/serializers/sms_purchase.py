from apps.messaging.api.admin.serializers.base import AdminUserMinimalSerializer
from apps.messaging.models import SMSPurchase
from base_utils.serializers.base import TainoBaseModelSerializer


class AdminSMSPurchaseSerializer(TainoBaseModelSerializer):
    """Admin serializer for SMS purchases"""

    user = AdminUserMinimalSerializer(read_only=True)

    class Meta:
        model = SMSPurchase
        fields = ["pid", "user", "coins_spent", "sms_quantity", "purchase_date", "is_active", "created_at", "updated_at"]
        read_only_fields = fields
