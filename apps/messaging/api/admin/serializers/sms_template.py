from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.messaging.api.admin.serializers.base import AdminUserMinimalSerializer
from apps.messaging.models import SMSTemplate, SystemSMSTemplate
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer

User = get_user_model()


class AdminSMSTemplateSerializer(TainoBaseModelSerializer):
    """Admin serializer for SMS templates"""

    creator = AdminUserMinimalSerializer(read_only=True)
    creator_id = serializers.SlugRelatedField(
        source="creator", queryset=User.objects.filter(is_active=True), slug_field="pid", write_only=True, required=False
    )

    class Meta:
        model = SMSTemplate
        fields = [
            "pid",
            "name",
            "template_type",
            "content",
            "is_system",
            "creator",
            "creator_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["pid", "created_at", "updated_at"]


class AdminSystemSMSTemplateSerializer(TainoBaseModelSerializer):
    """Admin serializer for system SMS templates"""

    class Meta:
        model = SystemSMSTemplate
        fields = ["pid", "code", "name", "template_content", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["pid", "created_at", "updated_at"]


class AdminSystemTemplateTestSerializer(TainoBaseSerializer):
    """Serializer for testing system templates"""

    template_id = serializers.CharField(required=True)
    context = serializers.DictField(required=True)

    def validate_template_id(self, value):
        try:
            template = SystemSMSTemplate.objects.get(pid=value, is_active=True)
            return template
        except SystemSMSTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found")

    def create(self, validated_data):
        from apps.messaging.services.utils import format_sms_template

        template = validated_data["template_id"]
        context = validated_data["context"]

        # Format template
        success, formatted_message, error = format_sms_template(template.code, context)

        return {
            "success": success,
            "template_code": template.code,
            "template_name": template.name,
            "formatted_message": formatted_message,
            "error": error,
            "context": context,
        }
