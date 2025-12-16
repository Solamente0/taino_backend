# apps/chat/api/admin/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.chat.models import ChatSession, ChatMessage, ChatRequest, ChatSubscription
from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class AdminChatUserSerializer(serializers.ModelSerializer):
    """
    Admin serializer for user reference in chat
    """

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "email", "phone_number", "avatar"]


class AdminChatSessionSerializer(TainoBaseModelSerializer):
    """
    Admin serializer for chat sessions
    """

    client = AdminChatUserSerializer(read_only=True)
    consultant = AdminChatUserSerializer(read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "pid",
            "client",
            "consultant",
            "chat_type",
            "status",
            "title",
            "fee_amount",
            "time_limit_minutes",
            "start_time",
            "end_time",
            "unread_client_messages",
            "unread_consultant_messages",
            "total_messages",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class AdminChatSessionDetailSerializer(AdminChatSessionSerializer):
    """
    Admin detailed serializer for chat sessions
    """

    class Meta(AdminChatSessionSerializer.Meta):
        fields = AdminChatSessionSerializer.Meta.fields  # + [
        #    "ai_context",
        # ]


class AdminChatMessageSerializer(TainoBaseModelSerializer):
    """
    Admin serializer for chat messages
    """

    sender = AdminChatUserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "pid",
            "chat_session",
            "sender",
            "message_type",
            "content",
            "attachment",
            "is_ai",
            "is_system",
            "is_read_by_client",
            "is_read_by_consultant",
            "read_at",
            "is_failed",
            "failure_reason",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class AdminChatRequestSerializer(TainoBaseModelSerializer):
    """
    Admin serializer for chat requests
    """

    client = AdminChatUserSerializer(read_only=True)
    consultant = AdminChatUserSerializer(read_only=True)

    class Meta:
        model = ChatRequest
        fields = [
            "pid",
            "client",
            "consultant",
            "status",
            "title",
            "description",
            "chat_type",
            "proposed_fee",
            "proposed_time_minutes",
            "expires_at",
            "response_message",
            "responded_at",
            "specialization",
            "location_preference",
            "preferred_time",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class AdminChatSubscriptionSerializer(TainoBaseModelSerializer):
    """
    Admin serializer for chat subscriptions
    """

    user = AdminChatUserSerializer(read_only=True)

    class Meta:
        model = ChatSubscription
        fields = [
            "pid",
            "user",
            "subscription_type",
            "max_chats",
            "max_minutes",
            "start_date",
            "end_date",
            "used_chats",
            "used_minutes",
            "price",
            "is_paid",
            "payment_date",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class AdminChatSubscriptionCreateUpdateSerializer(TainoBaseModelSerializer):
    """
    Admin serializer for creating/updating chat subscriptions
    """

    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field="pid")
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ChatSubscription
        fields = [
            "user",
            "creator",
            "subscription_type",
            "max_chats",
            "max_minutes",
            "start_date",
            "end_date",
            "used_chats",
            "used_minutes",
            "price",
            "is_paid",
            "payment_date",
            "is_active",
        ]
