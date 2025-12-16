# apps/ai_chat/api/v1/serializers.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .base import AIUserSerializer, ChatAIConfigSerializer
from apps.ai_chat.models import AISession, AIMessage, ChatAIConfig
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer

# test


class AIMessageSerializer(TainoBaseModelSerializer):
    """Serializer for AI messages"""

    sender = AIUserSerializer(read_only=True)

    class Meta:
        model = AIMessage
        fields = [
            "pid",
            "sender",
            "message_type",
            "content",
            "is_ai",
            "is_system",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields


class AISessionSerializer(TainoBaseModelSerializer):
    """Serializer for AI sessions"""

    user = AIUserSerializer(read_only=True)

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
            "created_at",
        ]
        read_only_fields = fields


class CreateAISessionSerializer(TainoBaseSerializer):
    """Serializer for creating AI session"""

    title = serializers.CharField(required=False, allow_null=True, max_length=255)

    ai_config = serializers.SlugRelatedField(queryset=ChatAIConfig.objects.all(), slug_field="pid", required=True)
    temperature = serializers.FloatField(required=False, min_value=0, max_value=2, default=0.7)
    max_tokens = serializers.IntegerField(required=False, min_value=100, max_value=10000, default=4000)
    #
    # def validate_ai_config_id(self, value):
    #     try:
    #         ai_config = ChatAIConfig.objects.get(pid=value, is_active=True)
    #         return ai_config
    #     except ChatAIConfig.DoesNotExist:
    #         raise serializers.ValidationError("پیکربندی هوش مصنوعی یافت نشد")


class AISessionDetailSerializer(TainoBaseModelSerializer):
    """Detailed serializer for AI sessions"""

    user = AIUserSerializer(read_only=True)
    ai_config = ChatAIConfigSerializer(read_only=True)
    recent_messages = serializers.SerializerMethodField()
    is_readonly = serializers.BooleanField(read_only=True)
    readonly_reason_display = serializers.SerializerMethodField()
    limits_info = serializers.SerializerMethodField()
    pricing_info = serializers.SerializerMethodField()

    class Meta:
        model = AISession
        fields = [
            "pid",
            "user",
            "ai_config",
            "status",
            "title",
            "total_messages",
            "total_input_tokens",
            "total_output_tokens",
            "total_tokens_used",
            "total_cost_coins",
            "temperature",
            "max_tokens",
            "is_readonly",
            "readonly_reason",
            "readonly_reason_display",
            "limits_info",
            "pricing_info",
            "recent_messages",
            "created_at",
        ]
        read_only_fields = fields

    def get_recent_messages(self, obj):
        messages = AIMessage.objects.filter(ai_session=obj, is_deleted=False).order_by("-created_at")[:10]
        return AIMessageSerializer(reversed(messages), many=True).data

    def get_readonly_reason_display(self, obj):
        if not obj.is_readonly:
            return None

        reasons = {
            "max_messages_reached": "حداکثر تعداد پیام‌ها به پایان رسیده است",
            "max_tokens_reached": "حداکثر تعداد توکن‌ها به پایان رسیده است",
        }
        return reasons.get(obj.readonly_reason, obj.readonly_reason)

    def get_limits_info(self, obj):
        """Get information about session limits"""
        if not obj.ai_config or not obj.ai_config.general_config:
            return None

        general_config = obj.ai_config.general_config

        return {
            "max_messages": general_config.max_messages_per_chat,
            "current_messages": obj.total_messages,
            "remaining_messages": max(0, general_config.max_messages_per_chat - obj.total_messages),
            "max_tokens": general_config.max_tokens_per_chat,
            "current_tokens": obj.total_tokens_used,
            "remaining_tokens": max(0, general_config.max_tokens_per_chat - obj.total_tokens_used),
            "is_readonly": obj.is_readonly,
        }

    def get_pricing_info(self, obj):
        """Get pricing information for this session"""
        if not obj.ai_config:
            return None

        info = {
            "pricing_type": obj.ai_config.pricing_type,
            "pricing_type_display": obj.ai_config.get_pricing_type_display(),
            "is_message_based": obj.ai_config.is_message_based_pricing(),
            # "is_token_based": obj.ai_config.is_token_based_pricing(),
            "total_cost_so_far": float(obj.total_cost_coins),
        }

        if obj.ai_config.is_message_based_pricing():
            info.update(
                {
                    "cost_per_message": float(obj.ai_config.cost_per_message),
                    "estimated_next_message_cost": float(obj.ai_config.cost_per_message),
                }
            )

        return info


class AIMessageCreateSerializer(TainoBaseModelSerializer):
    """Serializer for creating AI messages"""

    ai_session = serializers.SlugRelatedField(queryset=AISession.objects.all(), slug_field="pid")
    # ✅ اضافه کردن فیلد فایل
    files = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True, help_text="لیست فایل‌های ضمیمه (تصویر یا PDF)"
    )

    class Meta:
        model = AIMessage
        fields = ["ai_session", "message_type", "content", "files"]

    def validate_ai_session(self, ai_session):
        """Validate the AI session"""
        user = self.context["request"].user

        if user != ai_session.user:
            raise serializers.ValidationError(_("You are not the owner of this AI session"))

        if ai_session.status != "active":
            raise serializers.ValidationError(_("AI session is not active"))

        return ai_session

    def validate_files(self, files):
        """اعتبارسنجی فایل‌ها"""
        if not files:
            return []

        validated_files = []

        for file in files:
            from base_utils.file_processor import FileProcessorService

            file_type = FileProcessorService.get_file_type(file)

            if not file_type:
                raise serializers.ValidationError(
                    f"فرمت فایل {file.name} پشتیبانی نمی‌شود. "
                    f"فرمت‌های مجاز: {', '.join(FileProcessorService.ALLOWED_IMAGE_FORMATS)}, pdf"
                )

            if file_type == "image":
                is_valid, error = FileProcessorService.validate_image(file)
                if not is_valid:
                    raise serializers.ValidationError(error)

            elif file_type == "document":
                # max_pages را از کانفیگ می‌گیریم
                is_valid, error, _ = FileProcessorService.validate_pdf(file, max_pages=50)
                if not is_valid:
                    raise serializers.ValidationError(error)

            validated_files.append(file)

        return validated_files

    def validate(self, data):
        """اعتبارسنجی کلی"""
        # حداقل یکی از content یا files باید وجود داشته باشد
        if not data.get("content") and not data.get("files"):
            raise serializers.ValidationError("حداقل باید یک متن یا یک فایل ارسال شود")

        return data

    def create(self, validated_data):
        """ایجاد پیام با فایل"""
        user = self.context["request"].user
        ai_session = validated_data["ai_session"]
        files = validated_data.pop("files", [])

        # ایجاد پیام
        message = AIMessage.objects.create(
            ai_session=ai_session,
            sender=user,
            content=validated_data.get("content", ""),
            message_type=validated_data["message_type"],
        )

        # ذخیره اطلاعات فایل‌ها در متادیتا (بدون ذخیره فایل)
        if files:

            file_metadata = []
            for file in files:
                from base_utils.file_processor import FileProcessorService

                file_type = FileProcessorService.get_file_type(file)
                metadata = {"name": file.name, "type": file_type, "size": file.size}

                if file_type == "document":
                    metadata["pages"] = FileProcessorService.count_pdf_pages(file)

                file_metadata.append(metadata)

            # ذخیره در ai_context پیام (اگر فیلد وجود دارد)
            if hasattr(message, "metadata"):
                message.metadata = {"files": file_metadata}
                message.save()

        return message
