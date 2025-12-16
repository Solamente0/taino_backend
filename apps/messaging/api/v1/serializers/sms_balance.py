from apps.lawyer_office.api.v1.serializers.base import LawyerOfficeUserMinimalSerializer
from apps.messaging.models import SMSBalance
from base_utils.serializers.base import TainoBaseModelSerializer


class SMSBalanceSerializer(TainoBaseModelSerializer):
    """Serializer for user's SMS balance"""

    user = LawyerOfficeUserMinimalSerializer(read_only=True)

    class Meta:
        model = SMSBalance
        fields = ["pid", "user", "balance", "created_at", "updated_at"]
        read_only_fields = fields
