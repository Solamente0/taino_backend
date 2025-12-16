from django.contrib.auth import get_user_model
from rest_framework import serializers

from base_utils.serializers.base import TainoBaseSerializer

User = get_user_model()


class AdminSMSStatsSerializer(TainoBaseSerializer):
    """Serializer for SMS statistics"""

    start_date = serializers.DateTimeField(required=False, allow_null=True)
    end_date = serializers.DateTimeField(required=False, allow_null=True)
    user_id = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        from apps.messaging.services.utils import get_sms_statistics

        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")
        user_id = validated_data.get("user_id")

        # Get statistics
        stats = get_sms_statistics(start_date, end_date, user_id)

        return stats
