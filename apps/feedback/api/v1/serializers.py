from rest_framework import serializers

from apps.feedback.models import FeedBack
from base_utils.serializers.base import TainoBaseModelSerializer


class InputFeedbackModelSerializer(TainoBaseModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FeedBack
        fields = ("creator", "message", "feedback_type")


class OutputFeedbackModelSerializer(TainoBaseModelSerializer):
    class Meta:
        model = FeedBack
        fields = ("pid", "message", "feedback_type")
        read_only_fields = fields
