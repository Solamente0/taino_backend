# apps/chat/api/v1/serializers.py
import base64
import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.chat.models import ChatSession, ChatMessage, ChatRequest, ChatSubscription, LawyerProposal
from apps.country.models import City
from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class ChatUserSerializer(serializers.ModelSerializer):
    """
    Serializer for user reference in chat
    """

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "email", "phone_number", "avatar"]


class ChatMessageSerializer(TainoBaseModelSerializer):
    """
    Serializer for chat messages
    """

    sender = ChatUserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "pid",
            "sender",
            "message_type",
            "content",
            "is_ai",
            "is_system",
            "is_read_by_client",
            "is_read_by_consultant",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields


class ChatMessageCreateSerializer(TainoBaseModelSerializer):
    """
    Serializer for creating chat messages
    """

    chat_session = serializers.SlugRelatedField(queryset=ChatSession.objects.all(), slug_field="pid")

    class Meta:
        model = ChatMessage
        fields = ["chat_session", "message_type", "content", "attachment"]

    def validate_chat_session(self, chat_session):
        """
        Validate the chat session
        """
        user = self.context["request"].user

        # Check if user is part of the chat
        if user != chat_session.client and user != chat_session.consultant:
            raise serializers.ValidationError(_("You are not a participant in this chat"))

        # Check if session is active
        if chat_session.status != "active":
            raise serializers.ValidationError(_("Chat session is not active"))

        # Check if consultant has subscription (if applicable)
        if user == chat_session.consultant:
            subscription = ChatSubscription.objects.filter(user=user, is_active=True, end_date__gte=timezone.now()).first()

            if not subscription or subscription.remaining_minutes <= 0:
                raise serializers.ValidationError(_("You have exceeded your subscription limit"))

        return chat_session

    def create(self, validated_data):
        """
        Create a new message
        """
        user = self.context["request"].user
        chat_session = validated_data["chat_session"]

        # Set read flags based on sender
        if user == chat_session.client:
            validated_data["is_read_by_client"] = True
            chat_session.unread_consultant_messages += 1
        else:
            validated_data["is_read_by_consultant"] = True
            chat_session.unread_client_messages += 1

        chat_session.total_messages += 1
        chat_session.save(update_fields=["unread_client_messages", "unread_consultant_messages", "total_messages"])

        validated_data["sender"] = user

        message = super().create(validated_data)

        # Sync to MongoDB if enabled
        from apps.chat.services.mongo_sync import MongoSyncService

        MongoSyncService.sync_chat_message_to_mongo(message)

        return message


class ChatSessionSerializer(TainoBaseModelSerializer):
    """
    Serializer for chat sessions
    """

    client = ChatUserSerializer(read_only=True)
    consultant = ChatUserSerializer(read_only=True)

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
            "created_at",
        ]
        read_only_fields = fields


class ChatSessionDetailSerializer(TainoBaseModelSerializer):
    """
    Detailed serializer for chat sessions
    """

    client = ChatUserSerializer(read_only=True)
    consultant = ChatUserSerializer(read_only=True)
    recent_messages = serializers.SerializerMethodField()
    remaining_minutes = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

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
            "recent_messages",
            "remaining_minutes",
            "is_expired",
            "created_at",
        ]
        read_only_fields = fields

    def get_recent_messages(self, obj):
        """
        Get the most recent messages
        """
        messages = ChatMessage.objects.filter(chat_session=obj, is_deleted=False).order_by("-created_at")[:10]

        return ChatMessageSerializer(reversed(messages), many=True).data

    def get_remaining_minutes(self, obj):
        """
        Get remaining time in minutes for this chat session
        """
        return obj.remaining_time_minutes

    def get_is_expired(self, obj):
        """
        Check if the chat session has expired
        """
        # A session is expired if:
        # 1. It has an end_time and current time is past it, or
        # 2. Its status is explicitly set to "expired"
        if obj.status == "expired":
            return True

        if obj.end_time:
            from django.utils import timezone

            return obj.end_time < timezone.now()

        return False


class ChatRequestSerializer(TainoBaseModelSerializer):
    """
    Serializer for chat requests
    """

    client = ChatUserSerializer(read_only=True)
    selected_lawyer = ChatUserSerializer(read_only=True)

    class Meta:
        model = ChatRequest
        fields = [
            "pid",
            "client",
            "selected_lawyer",
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
            "created_at",
        ]
        read_only_fields = fields


class ChatRequestCreateSerializer(TainoBaseModelSerializer):
    """سریالایزر ایجاد درخواست"""

    client = serializers.HiddenField(default=serializers.CurrentUserDefault())
    city = serializers.SlugRelatedField(queryset=City.objects.all(), slug_field="pid")

    class Meta:
        model = ChatRequest
        fields = ["client", "title", "description", "city", "specialization", "proposed_budget", "proposed_duration_days"]

    def create(self, validated_data):
        # تنظیم زمان انقضا (مثلاً 7 روز)
        validated_data["expires_at"] = timezone.now() + timedelta(days=7)
        validated_data["creator"] = self.context["request"].user

        return super().create(validated_data)


class LawyerProposalCreateSerializer(TainoBaseModelSerializer):
    """سریالایزر ارسال پیشنهاد توسط وکیل"""

    lawyer = serializers.HiddenField(default=serializers.CurrentUserDefault())
    chat_request = serializers.SlugRelatedField(queryset=ChatRequest.objects.filter(status="pending"), slug_field="pid")

    class Meta:
        model = LawyerProposal
        fields = ["lawyer", "chat_request", "proposal_message", "proposed_fee", "proposed_duration"]

    def validate(self, attrs):
        # بررسی اینکه وکیل در همان شهر باشد
        request = self.context["request"]
        chat_request = attrs["chat_request"]

        # فرض: وکیل city در پروفایلش دارد
        if hasattr(request.user, "city") and request.user.city != chat_request.city:
            raise serializers.ValidationError("شما فقط می‌توانید به درخواست‌های شهر خود پیشنهاد دهید")

        # بررسی تکراری نبودن
        if LawyerProposal.objects.filter(chat_request=chat_request, lawyer=request.user).exists():
            raise serializers.ValidationError("شما قبلاً به این درخواست پیشنهاد داده‌اید")

        return attrs


class LawyerProposalListSerializer(TainoBaseModelSerializer):
    """سریالایزر نمایش پیشنهادهای وکلا"""

    lawyer = ChatUserSerializer(read_only=True)

    class Meta:
        model = LawyerProposal
        fields = ["pid", "lawyer", "proposal_message", "proposed_fee", "proposed_duration", "status", "created_at"]
        read_only_fields = fields


class ChatRequestResponseSerializer(TainoBaseModelSerializer):
    """
    Serializer for responding to chat requests
    """

    status = serializers.ChoiceField(choices=["accepted", "rejected"])
    response_message = serializers.CharField(required=False, allow_blank=True)
    fee_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    time_limit_minutes = serializers.IntegerField(required=False)

    class Meta:
        model = ChatRequest
        fields = ["status", "response_message", "fee_amount", "time_limit_minutes"]

    def validate(self, attrs):
        """
        Validate the response
        """
        request = self.instance
        user = self.context["request"].user

        # Check if request is pending
        if request.status != "pending":
            raise serializers.ValidationError(_("This request has already been responded to"))

        # Check if user is the consultant
        if request.consultant and request.consultant != user:
            raise serializers.ValidationError(_("You are not the assigned consultant for this request"))

        # If accepting, check subscription
        if attrs["status"] == "accepted":
            subscription = ChatSubscription.objects.filter(user=user, is_active=True, end_date__gte=timezone.now()).first()

            if not subscription or subscription.remaining_chats <= 0:
                raise serializers.ValidationError(_("You have exceeded your subscription limit"))

        return attrs

    def update(self, instance, validated_data):
        """
        Update the chat request
        """
        user = self.context["request"].user
        status = validated_data.get("status")

        if status == "accepted":
            from apps.chat.services.chat_service import ChatService

            # Accept the chat request and create a session
            try:
                session = ChatService.accept_chat_request(
                    chat_request=instance,
                    consultant=user,
                    response_message=validated_data.get("response_message"),
                    fee_amount=validated_data.get("fee_amount"),
                    time_limit_minutes=validated_data.get("time_limit_minutes"),
                )

                # Instance has been updated by the service
                return instance
            except Exception as e:
                raise serializers.ValidationError(str(e))
        else:
            # Reject the request
            instance.status = "rejected"
            instance.consultant = user
            instance.response_message = validated_data.get("response_message")
            instance.responded_at = timezone.now()
            instance.save()

            return instance


class ChatRequestDetailSerializer(TainoBaseModelSerializer):
    """سریالایزر جزئیات درخواست"""

    client = ChatUserSerializer(read_only=True)
    city = serializers.StringRelatedField()
    proposals = LawyerProposalListSerializer(many=True, read_only=True)
    proposals_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRequest
        fields = [
            "pid",
            "client",
            "title",
            "description",
            "city",
            "specialization",
            "proposed_budget",
            "proposed_duration_days",
            "status",
            "expires_at",
            "created_at",
            "proposals_count",
            "proposals",
        ]
        read_only_fields = fields

    def get_proposals_count(self, obj):
        return obj.proposals.count()


class ChatSubscriptionSerializer(TainoBaseModelSerializer):
    """
    Serializer for chat subscriptions
    """

    user = ChatUserSerializer(read_only=True)
    remaining_chats = serializers.IntegerField(read_only=True)
    remaining_minutes = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

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
            "remaining_chats",
            "remaining_minutes",
            "price",
            "is_paid",
            "payment_date",
            "is_active",
        ]
        read_only_fields = fields
