# apps/file_to_text/api/v1/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.file_to_text.models import FileToTextLog
from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class FileToTextUserSerializer(serializers.ModelSerializer):
    """Serializer for user reference"""

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "email", "phone_number"]


class FileToTextLogSerializer(TainoBaseModelSerializer):
    """Serializer for file to text logs"""

    user = FileToTextUserSerializer(read_only=True)

    class Meta:
        model = FileToTextLog
        fields = [
            "pid",
            "user",
            "original_filename",
            "extracted_text",
            "file_type",
            "file_size",
            "coins_used",
            "character_count",
            "word_count",
            "created_at",
        ]
        read_only_fields = fields


class FileToTextSubmitSerializer(serializers.Serializer):
    """Serializer for submitting file to text ctainoersion"""

    filename = serializers.CharField(
        required=True,
        max_length=255,
        help_text="نام فایل"
    )
    
    extracted_text = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="متن استخراج شده از فایل"
    )
    
    file_type = serializers.CharField(
        required=True,
        max_length=50,
        help_text="نوع فایل (pdf, jpg, png, ...)"
    )
    
    file_size = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="حجم فایل به بایت"
    )

    def validate_extracted_text(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("متن استخراج شده باید حداقل 10 کاراکتر باشد.")
        return value
