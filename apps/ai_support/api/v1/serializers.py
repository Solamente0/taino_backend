# apps/ai_support/api/v1/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.ai_support.models import SupportSession, SupportMessage, SupportAIConfig
from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class SupportUserSerializer(serializers.ModelSerializer):
    """Serializer for user in support chat"""
    
    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "email", "avatar"]


class SupportAIConfigSerializer(TainoBaseModelSerializer):
    """Serializer for AI configuration (public info only)"""
    
    class Meta:
        model = SupportAIConfig
        fields = [
            "pid",
            "name",
            "model_name",
            "temperature",
            "max_tokens",
            "ctainoersation_history_limit",
            "is_default"
        ]
        read_only_fields = fields


class SupportUserSerializer(serializers.ModelSerializer):
    """Serializer for user in support chat"""
    
    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "email", "avatar"]


class SupportMessageSerializer(TainoBaseModelSerializer):
    """Serializer for support messages"""
    
    sender = SupportUserSerializer(read_only=True)
    
    class Meta:
        model = SupportMessage
        fields = [
            "pid",
            "sender",
            "message_type",
            "content",
            "attachment",
            "is_ai",
            "is_read",
            "read_at",
            "created_at"
        ]
        read_only_fields = fields


class SupportSessionSerializer(TainoBaseModelSerializer):
    """Serializer for support sessions"""
    
    user = SupportUserSerializer(read_only=True)
    
    class Meta:
        model = SupportSession
        fields = [
            "pid",
            "user",
            "status",
            "subject",
            "total_messages",
            "unread_messages",
            "created_at"
        ]
        read_only_fields = fields


class SupportSessionDetailSerializer(SupportSessionSerializer):
    """Detailed serializer for support session"""
    
    recent_messages = serializers.SerializerMethodField()
    
    class Meta(SupportSessionSerializer.Meta):
        fields = SupportSessionSerializer.Meta.fields + ["recent_messages"]
    
    def get_recent_messages(self, obj):
        messages = SupportMessage.objects.filter(
            session=obj,
            is_deleted=False
        ).order_by("-created_at")[:20]
        return SupportMessageSerializer(reversed(messages), many=True).data


class CreateSupportSessionSerializer(serializers.Serializer):
    """Serializer for creating support session"""
    
    subject = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=255
    )


class SendSupportMessageSerializer(serializers.Serializer):
    """Serializer for sending support message"""
    
    session_id = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    message_type = serializers.ChoiceField(
        choices=["text", "image", "file"],
        default="text"
    )
    
    def validate_session_id(self, value):
        try:
            session = SupportSession.objects.get(pid=value, is_deleted=False)
            return session
        except SupportSession.DoesNotExist:
            raise serializers.ValidationError("جلسه پشتیبانی یافت نشد")
