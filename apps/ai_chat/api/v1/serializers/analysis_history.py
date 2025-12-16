# OCR and Legal Analysis Serializers (move from chat app)
from rest_framework import serializers

from apps.ai_chat.api.v1.serializers import AIUserSerializer
from apps.ai_chat.models import LegalAnalysisLog, ChatAIConfig
from apps.analyzer.models import AnalyzerLog
from apps.contract.models import ContractLog
from apps.file_to_text.models import FileToTextLog
from base_utils.enums import LegalDocumentAnalysisType
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class CombinedAnalysisHistorySerializer(TainoBaseSerializer):
    """Combined serializer for both legal and document analysis history"""

    pid = serializers.CharField(read_only=True)
    user = AIUserSerializer(read_only=True)
    ai_session_id = serializers.SerializerMethodField()
    ai_type = serializers.CharField(read_only=True)
    ai_type_details = serializers.SerializerMethodField()  # Add this line
    analysis_type = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    # Legal analysis specific fields
    analysis_text = serializers.CharField(read_only=True, allow_null=True)
    user_request_analysis_text = serializers.CharField(read_only=True, allow_null=True)
    user_request_choice = serializers.CharField(read_only=True, allow_null=True)
    user_request_choice_display = serializers.SerializerMethodField()

    # Document analysis specific fields
    prompt = serializers.CharField(read_only=True, allow_null=True)

    # file to text specific fields
    extracted_text = serializers.CharField(read_only=True, allow_null=True)

    def get_ai_session_id(self, obj):
        if hasattr(obj, "ai_session") and obj.ai_session:
            return str(obj.ai_session.pid)
        return None

    def get_analysis_type(self, obj):
        """Determine which type of analysis this is"""
        if isinstance(obj, LegalAnalysisLog):
            return "legal_analysis"
        elif isinstance(obj, AnalyzerLog):
            return "document_analysis"
        else:  # AnalyzerLog
            return "file_to_text"

    def get_user_request_choice_display(self, obj):
        """Get display text for user request choice (only for legal analysis)"""
        if isinstance(obj, LegalAnalysisLog) and obj.user_request_choice:
            return LegalDocumentAnalysisType.get_sanitized_label_for_key(obj.user_request_choice)
        return None

    def get_ai_type_details(self, obj):
        """Get AI type details from ServiceItem"""
        from apps.common.models import ServiceItem

        if not hasattr(obj, "ai_type") or not obj.ai_type:
            return None

        # Remove strength suffixes from static_name
        suffixes_to_remove = ["_very_strong", "_strong", "_medium", "_special", "_unique"]
        filtered_static_name = obj.ai_type

        for suffix in suffixes_to_remove:
            if filtered_static_name.endswith(suffix):
                filtered_static_name = filtered_static_name[: -len(suffix)]
                break

        try:
            ai_type = ChatAIConfig.objects.get(static_name=obj.ai_type)
            service = ServiceItem.objects.get(static_name=filtered_static_name, is_active=True)
            return {
                "name": service.name,
                "description": service.description,
                "ai_type_name": ai_type.name,
                "static_name": service.static_name,
            }
        except Exception as e:
            print(f"Exception while getting AIType ---> {e}", flush=True)
            # Fallback if service not found
            return {
                "name": obj.ai_type,
                "ai_type_name": obj.ai_type,
                "description": None,
                "static_name": filtered_static_name,
            }

    def to_representation(self, instance):
        """Customize representation based on analysis type"""
        data = super().to_representation(instance)

        # Remove null fields based on type
        if isinstance(instance, LegalAnalysisLog):
            # Remove document analysis specific fields
            data.pop("prompt", None)
            data.pop("extracted_text", None)
        elif isinstance(instance, FileToTextLog):
            data.pop("prompt", None)
            data.pop("user_request_analysis_text", None)
            data.pop("user_request_choice", None)
            data.pop("user_request_choice_display", None)

        else:  # AnalyzerLog
            # Remove legal analysis specific fields
            data.pop("user_request_analysis_text", None)
            data.pop("user_request_choice", None)
            data.pop("user_request_choice_display", None)

        return data


class AIHistoryUpdateSerializer(TainoBaseSerializer):
    """Serializer for updating AI history items"""

    analysis_text = serializers.CharField(required=False, allow_blank=True)
    contract_text = serializers.CharField(required=False, allow_blank=True)
    extracted_text = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        # Ensure at least one field is provided
        if not any([attrs.get("analysis_text"), attrs.get("contract_text"), attrs.get("extracted_text")]):
            raise serializers.ValidationError("حداقل یکی از فیلدها باید مقدار داشته باشد")
        return attrs


class AITypeDetailsSerializer(serializers.Serializer):
    """Serializer for AI type details"""

    name = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    ai_type_name = serializers.CharField(required=False, allow_null=True)
    ai_type = serializers.CharField(required=False, allow_null=True)


class AIHistoryItemSerializer(serializers.Serializer):
    """
    Unified serializer for all AI history items
    Combines data from AnalyzerLog, ContractLog, and FileToTextLog
    """

    pid = serializers.CharField(read_only=True)
    user = AIUserSerializer(read_only=True)
    ai_session_id = serializers.CharField(required=False, allow_null=True)
    ai_type = serializers.CharField(required=False, allow_null=True)
    analysis_type = serializers.CharField(required=False)
    created_at = serializers.DateTimeField(read_only=True)

    # Content fields
    analysis_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    extracted_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    prompt = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # Additional fields
    user_request_analysis_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    user_request_choice = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    user_request_choice_display = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # AI type details
    ai_type_details = AITypeDetailsSerializer(required=False, allow_null=True)


class AnalyzerLogSerializer(TainoBaseModelSerializer):
    """Serializer for AnalyzerLog model"""

    user = AIUserSerializer(read_only=True)
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


class ContractLogSerializer(TainoBaseModelSerializer):
    """Serializer for ContractLog model"""

    user = AIUserSerializer(read_only=True)
    ai_session = serializers.SlugRelatedField(slug_field="pid", read_only=True)

    class Meta:
        model = ContractLog
        fields = [
            "pid",
            "user",
            "prompt",
            "contract_text",
            "ai_type",
            "ai_session",
            "created_at",
        ]
        read_only_fields = fields


class FileToTextLogSerializer(TainoBaseModelSerializer):
    """Serializer for FileToTextLog model"""

    user = AIUserSerializer(read_only=True)

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
            "ai_type",
            "created_at",
        ]
        read_only_fields = fields
