from apps.messaging.api.admin.serializers.base import AdminUserMinimalSerializer
from apps.messaging.models import SMSMessage
from base_utils.serializers.base import TainoBaseModelSerializer


class AdminSMSMessageSerializer(TainoBaseModelSerializer):
    """Admin serializer for SMS messages"""

    sender = AdminUserMinimalSerializer(read_only=True)
    creator = AdminUserMinimalSerializer(read_only=True)

    class Meta:
        model = SMSMessage
        fields = [
            "pid",
            "sender",
            "creator",
            "recipient_number",
            "recipient_name",
            "content",
            "status",
            "source_type",
            "sent_at",
            "error_message",
            "client",
            "case",
            "calendar_event",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
