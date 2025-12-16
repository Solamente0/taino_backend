# apps/ai_chat/api/admin/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.ai_chat.models import AISession, AIMessage, ChatAIConfig, LegalAnalysisLog
from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class AdminAIUserSerializer(serializers.ModelSerializer):
    """Admin serializer for user reference in AI chat"""

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "email", "phone_number", "avatar"]


class AdminAISessionSerializer(TainoBaseModelSerializer):
    """Admin serializer for AI sessions"""

    user = AdminAIUserSerializer(read_only=True)

    class Meta:
        model = AISession
        fields = [
            "pid",
            "user",
            "ai_type",
            "status",
            "title",
            "fee_amount",
            "duration_minutes",
            "start_date",
            "end_date",
            "unread_messages",
            "total_messages",
            "paid_with_coins",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class AdminAISessionDetailSerializer(AdminAISessionSerializer):
    """Admin detailed serializer for AI sessions"""

    class Meta(AdminAISessionSerializer.Meta):
        fields = AdminAISessionSerializer.Meta.fields + [
            "ai_context",
        ]


class AdminAIMessageSerializer(TainoBaseModelSerializer):
    """Admin serializer for AI messages"""

    sender = AdminAIUserSerializer(read_only=True)

    class Meta:
        model = AIMessage
        fields = [
            "pid",
            "ai_session",
            "sender",
            "message_type",
            "content",
            "attachment",
            "is_ai",
            "is_system",
            "is_read",
            "read_at",
            "is_failed",
            "failure_reason",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class AdminChatAIConfigSerializer(TainoBaseModelSerializer):
    """Admin serializer for AI configuration"""

    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ChatAIConfig
        fields = [
            "pid",
            "creator",
            "name",
            "description",
            "model_name",
            "api_key",
            "base_url",
            "system_prompt",
            "default_temperature",
            "default_max_tokens",
            "static_name",
            "rate_limit_per_minute",
            "is_default",
            "is_active",
        ]


class AdminLegalAnalysisLogSerializer(TainoBaseModelSerializer):
    """Admin serializer for legal analysis logs"""

    user = AdminAIUserSerializer(read_only=True)

    class Meta:
        model = LegalAnalysisLog
        fields = [
            "pid",
            "user",
            "analysis_text",
            "user_request_analysis_text",
            "ai_type",
            "user_request_choice",
            "ai_session",
            "is_content_only",
            "assistant_id",
            "thread_id",
            "run_id",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
