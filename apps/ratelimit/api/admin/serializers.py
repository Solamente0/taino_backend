from rest_framework import serializers

from apps.ratelimit.models import RateLimitConfig
from base_utils.serializers.base import TainoBaseModelSerializer


class InputAdminRateLimitModelSerializer(TainoBaseModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = RateLimitConfig
        fields = (
            "creator",
            "name",
            "key",
            "rate",
            "group",
            "method",
            "method_name",
            "block",
        )


class OutputAdminRateLimitModelSerializer(TainoBaseModelSerializer):
    class Meta:
        model = RateLimitConfig
        fields = (
            "pid",
            "created_at",
            "updated_at",
            "creator",
            "name",
            "key",
            "rate",
            "group",
            "method",
            "method_name",
            "block",
        )
