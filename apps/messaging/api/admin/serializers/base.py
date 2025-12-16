from django.contrib.auth import get_user_model
from rest_framework import serializers

from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class AdminUserMinimalSerializer(TainoBaseModelSerializer):
    """Minimal serializer for user information in admin interfaces"""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["pid", "first_name", "last_name", "full_name", "email", "phone_number", "is_active"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email or obj.phone_number
