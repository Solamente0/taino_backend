from rest_framework import serializers

from apps.lawyer_office.api.v1.serializers.base import LawyerOfficeUserMinimalSerializer
from apps.messaging.models import SMSBalance, SMSTemplate, SMSPurchase, SMSMessage, SystemSMSTemplate
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class SMSTemplateSerializer(TainoBaseModelSerializer):
    """Serializer for SMS templates"""

    creator = LawyerOfficeUserMinimalSerializer(read_only=True)

    class Meta:
        model = SMSTemplate
        fields = ["pid", "name", "template_type", "content", "is_system", "creator", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "is_system", "creator", "created_at", "updated_at"]


class SMSTemplateCreateUpdateSerializer(TainoBaseModelSerializer):
    """Serializer for creating and updating SMS templates"""

    class Meta:
        model = SMSTemplate
        fields = ["name", "template_type", "content", "is_active"]

    def create(self, validated_data):
        # Set creator to current user
        validated_data["creator"] = self.context["request"].user
        # System templates can only be created by admins
        validated_data["is_system"] = False
        return super().create(validated_data)
