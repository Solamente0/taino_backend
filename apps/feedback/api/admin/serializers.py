import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.feedback.models import FeedBack
from base_utils.serializers.base import TainoBaseModelSerializer

log = logging.getLogger(__name__)


class InputFeedbackModelSerializer(TainoBaseModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FeedBack
        fields = ("creator", "message", "feedback_type", "status")


class AdminUserMinimalSerializer(TainoBaseModelSerializer):
    avatar = serializers.FileField(allow_null=True, required=False)

    class Meta:
        model = get_user_model()
        fields = (
            "pid",
            "avatar",
            "first_name",
            "last_name",
            "email",
        )


class OutputFeedbackModelSerializer(TainoBaseModelSerializer):
    creator = AdminUserMinimalSerializer()

    class Meta:
        model = FeedBack
        fields = ["pid", "creator", "created_at", "message", "feedback_type", "status"]
        read_only_fields = fields
