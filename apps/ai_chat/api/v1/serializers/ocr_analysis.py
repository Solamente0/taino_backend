from rest_framework import serializers

from apps.ai_chat.api.v1.serializers.legal_analysis import (
    InitialPetitionSerializer,
    PleadingsSerializer,
    FirstInstanceJudgmentSerializer,
    AppealSerializer,
)
from base_utils.serializers.base import TainoBaseSerializer


class OCRAnalysisRequestSerializer(TainoBaseSerializer):
    """Combined serializer for OCR analysis request"""

    initial_petition = InitialPetitionSerializer(required=False)
    pleadings = PleadingsSerializer(required=False)
    first_instance_judgment = FirstInstanceJudgmentSerializer(required=False)
    appeal = AppealSerializer(required=False)

    content = serializers.CharField(required=False, allow_blank=True, help_text="Direct text input for analysis")
    use_content_only = serializers.BooleanField(
        required=False, default=False, help_text="If true, use only content field and ignore files"
    )

    def validate(self, data):
        """At least one section must be provided or content must be non-empty"""
        if not data.get("content") and not any(
            [data.get("initial_petition"), data.get("pleadings"), data.get("first_instance_judgment"), data.get("appeal")]
        ):
            raise serializers.ValidationError("Either document sections or content text must be provided")
        return data


class OCRResultSerializer(TainoBaseSerializer):
    """Serializer for OCR analysis result"""

    analysis = serializers.CharField()
    status = serializers.CharField()
