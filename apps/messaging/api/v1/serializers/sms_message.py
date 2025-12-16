from rest_framework import serializers

from apps.lawyer_office.api.v1.serializers.base import LawyerOfficeUserMinimalSerializer
from apps.messaging.models import SMSBalance, SMSTemplate, SMSPurchase, SMSMessage, SystemSMSTemplate
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class SMSMessageSerializer(TainoBaseModelSerializer):
    """Serializer for SMS messages"""

    sender = LawyerOfficeUserMinimalSerializer(read_only=True)

    class Meta:
        model = SMSMessage
        fields = [
            "pid",
            "sender",
            "recipient_number",
            "recipient_name",
            "content",
            "status",
            "source_type",
            "sent_at",
            "created_at",
        ]
        read_only_fields = fields
