from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.ai_chat.api.v1.serializers.base import OCRFileSerializer, AIUserSerializer
from apps.ai_chat.models import LegalAnalysisLog, ChatAIConfig
from base_utils.enums import LegalDocumentAnalysisType
from base_utils.serializers.base import TainoBaseSerializer, TainoBaseModelSerializer


class InitialPetitionSerializer(TainoBaseSerializer):
    """Serializer for 'دادخواست بدوی' section"""

    title = serializers.CharField(default="دادخواست بدوی", read_only=True)
    files = OCRFileSerializer(many=True, required=False, default=[])
    content = serializers.CharField(required=False, allow_blank=True)


class PleadingsSerializer(TainoBaseSerializer):
    """Serializer for 'لوایح طرفین پرونده' section"""

    title = serializers.CharField(default="لوایح طرفین پرونده", read_only=True)
    files = OCRFileSerializer(many=True, required=False, default=[])
    content = serializers.CharField(required=False, allow_blank=True)


class FirstInstanceJudgmentSerializer(TainoBaseSerializer):
    """Serializer for 'دادنامه بدوی' section"""

    title = serializers.CharField(default="دادنامه بدوی", read_only=True)
    files = OCRFileSerializer(many=True, required=False, default=[])
    content = serializers.CharField(required=False, allow_blank=True)


class AppealSerializer(TainoBaseSerializer):
    """Serializer for 'تجدید نظر خواهی' section"""

    title = serializers.CharField(default="تجدید نظر خواهی", read_only=True)
    files = OCRFileSerializer(many=True, required=False, default=[])
    content = serializers.CharField(required=False, allow_blank=True)


class LegalAnalysisLogSerializer(TainoBaseModelSerializer):
    """Serializer for legal analysis logs"""

    user = AIUserSerializer(read_only=True)
    ai_session = serializers.SlugRelatedField(slug_field="pid", read_only=True)

    class Meta:
        model = LegalAnalysisLog
        fields = ["pid", "user", "analysis_text", "ai_session", "assistant_id", "thread_id", "run_id", "created_at"]
        read_only_fields = fields


class LegalDocumentAnalysisRequestSerializer(TainoBaseSerializer):
    """Serializer for legal document analysis requests"""

    initial_petition = InitialPetitionSerializer(required=False)
    pleadings = PleadingsSerializer(required=False)
    first_instance_judgment = FirstInstanceJudgmentSerializer(required=False)
    appeal = AppealSerializer(required=False)

    prompt = serializers.CharField(required=False, allow_blank=True, help_text="Custom prompt or description for analysis")
    legal_analysis_user_request_choice = serializers.ChoiceField(
        choices=LegalDocumentAnalysisType.choices,
        default=LegalDocumentAnalysisType.LEGAL_DOCUMENT_ANALYSIS,
        help_text="Type of legal analysis requested",
    )
    ai_session_id = serializers.CharField(required=False, allow_null=True)
    ai_type = serializers.CharField(required=False, default="v_x")

    @staticmethod
    def validate_ai_type(value):
        if ChatAIConfig.objects.filter(static_name=value).exists():
            return value
        raise ValidationError("نوع هوش مصنوعی انتخاب شده وجود ندارد!")

    def validate(self, data):
        """At least one section must be provided"""
        if not any(
            [data.get("initial_petition"), data.get("pleadings"), data.get("first_instance_judgment"), data.get("appeal")]
        ):
            raise serializers.ValidationError("At least one document section must be provided")
        return data


class AnalyzerLogSerializer(TainoBaseModelSerializer):
    """Serializer for analyzer logs"""

    user = AIUserSerializer(read_only=True)
    ai_session = serializers.SlugRelatedField(slug_field="pid", read_only=True)
    analysis_type = serializers.SerializerMethodField()

    class Meta:
        model = None  # Will be set dynamically
        fields = [
            "pid",
            "user",
            "prompt",
            "analysis_text",
            "ai_type",
            "ai_session",
            "analysis_type",
            "created_at",
        ]
        read_only_fields = fields

    def get_analysis_type(self, obj):
        return "document_analysis"
