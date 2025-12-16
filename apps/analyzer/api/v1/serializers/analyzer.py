# apps/analyzer/api/v1/serializers/analyzer.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.analyzer.models import AnalyzerLog
from apps.ai_chat.models import ChatAIConfig
from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class AnalyzerUserSerializer(serializers.ModelSerializer):
    """Serializer for user reference in analyzer"""

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "email", "phone_number", "avatar"]


class AnalyzerLogSerializer(TainoBaseModelSerializer):
    """Serializer for analyzer logs"""

    user = AnalyzerUserSerializer(read_only=True)
    ai_session = serializers.SlugRelatedField(slug_field="pid", read_only=True)

    class Meta:
        model = AnalyzerLog
        fields = [
            "pid",
            "user",
            "prompt",
            "analysis_text",
            "ai_type",
            "ai_session",
            "created_at",
        ]
        read_only_fields = fields


class DocumentAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for document analysis requests"""

    prompt = serializers.CharField(required=True, allow_blank=False, help_text="درخواست کاربر برای تحلیل اسناد")
    ai_session_id = serializers.CharField(required=False, allow_null=True, help_text="شناسه جلسه چت (اختیاری)")
    ai_type = serializers.CharField(required=False, default="v_x", help_text="نوع هوش مصنوعی")
    max_token_requested = serializers.IntegerField(default=None, allow_null=True)
    files = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True, help_text="فایل‌های پیوست (تصاویر و PDF)"
    )

    # ✅ ADD VOICE FIELDS
    voice_file = serializers.FileField(required=False, allow_null=True, help_text="فایل صوتی (اختیاری)")

    voice_duration = serializers.IntegerField(required=False, allow_null=True, help_text="مدت زمان صدا به ثانیه")

    @staticmethod
    def validate_ai_type(value):
        if ChatAIConfig.objects.filter(static_name=value, is_active=True).exists():
            return value
        raise ValidationError("نوع هوش مصنوعی انتخاب شده وجود ندارد!")

    def validate_prompt(self, value):
        if len(value.strip()) < 10:
            raise ValidationError("درخواست باید حداقل 10 کاراکتر باشد.")
        return value


    def validate_voice_file(self, value):
        """Validate voice file format and size"""
        if not value:
            return value

        # Check content type
        if not value.content_type or not value.content_type.startswith('audio/'):
            raise ValidationError("فرمت فایل صوتی معتبر نیست")

        # Check file size (50MB max)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise ValidationError(f"فایل صوتی بیش از حد بزرگ است. حداکثر: {max_size // (1024*1024)}MB")

        return value
