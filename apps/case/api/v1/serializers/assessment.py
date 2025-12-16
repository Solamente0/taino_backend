from rest_framework import serializers

from apps.case.models import Assessment, Case, Session
from base_utils.serializers.base import TainoBaseModelSerializer


class AssessmentListSerializer(TainoBaseModelSerializer):
    """
    سریالایزر لیست ارزیابی‌ها
    """
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    severity_level_display = serializers.CharField(source='get_severity_level_display', read_only=True, allow_null=True)
    
    class Meta:
        model = Assessment
        fields = [
            'pid',
            'case_number',
            'test_type',
            'test_type_display',
            'test_name',
            'date_taken',
            'raw_score',
            'percentile',
            'severity_level',
            'severity_level_display',
            'interpretation',
        ]
        read_only_fields = fields


class AssessmentDetailSerializer(TainoBaseModelSerializer):
    """
    سریالایزر جزئیات ارزیابی
    """
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    severity_level_display = serializers.CharField(source='get_severity_level_display', read_only=True, allow_null=True)
    session_number = serializers.IntegerField(source='session.session_number', read_only=True, allow_null=True)
    
    class Meta:
        model = Assessment
        fields = [
            'pid',
            'case_number',
            'test_type',
            'test_type_display',
            'test_name',
            'date_taken',
            'raw_score',
            'percentile',
            'interpretation',
            'severity_level',
            'severity_level_display',
            'questions_answers',
            'subscales',
            'ai_recommendations',
            'session_number',
            'counselor_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'pid',
            'date_taken',
            'created_at',
            'updated_at',
        ]


class AssessmentCreateSerializer(TainoBaseModelSerializer):
    """
    سریالایزر ایجاد ارزیابی
    """
    case = serializers.SlugRelatedField(
        queryset=Case.objects.all(),
        slug_field='pid'
    )
    session = serializers.SlugRelatedField(
        queryset=Session.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Assessment
        fields = [
            'case',
            'session',
            'test_type',
            'test_name',
            'raw_score',
            'percentile',
            'interpretation',
            'severity_level',
            'questions_answers',
            'subscales',
            'ai_recommendations',
            'counselor_notes',
        ]
    
    def to_representation(self, instance):
        return AssessmentDetailSerializer(instance, context=self.context).data
