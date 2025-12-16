from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.case.models import Case, CaseTimeline
from base_utils.serializers.base import TainoBaseModelSerializer

User = get_user_model()


class CaseTimelineSerializer(TainoBaseModelSerializer):
    """
    سریالایزر برای رویدادهای تایم‌لاین
    """
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = CaseTimeline
        fields = [
            'pid',
            'event_type',
            'title',
            'description',
            'created_by_name',
            'metadata',
            'icon',
            'color',
            'created_at',
        ]
        read_only_fields = fields


class CaseListSerializer(TainoBaseModelSerializer):
    """
    سریالایزر لیست پرونده‌ها
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    partner_name = serializers.CharField(source='partner.get_full_name', read_only=True, allow_null=True)
    counselor_name = serializers.CharField(source='assigned_counselor.get_full_name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    case_type_display = serializers.CharField(source='get_case_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'pid',
            'case_number',
            'user_name',
            'partner_name',
            'counselor_name',
            'status',
            'status_display',
            'case_type',
            'case_type_display',
            'priority',
            'priority_display',
            'total_sessions',
            'total_assessments',
            'progress_percentage',
            'start_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class CaseDetailSerializer(TainoBaseModelSerializer):
    """
    سریالایزر جزئیات پرونده
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    partner_name = serializers.CharField(source='partner.get_full_name', read_only=True, allow_null=True)
    counselor_name = serializers.CharField(source='assigned_counselor.get_full_name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    case_type_display = serializers.CharField(source='get_case_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True, allow_null=True)
    timeline = CaseTimelineSerializer(source='timeline_events', many=True, read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'pid',
            'case_number',
            'user_name',
            'partner_name',
            'counselor_name',
            'status',
            'status_display',
            'case_type',
            'case_type_display',
            'priority',
            'priority_display',
            'initial_complaint',
            'initial_diagnosis',
            'current_diagnosis',
            'symptoms',
            'severity',
            'severity_display',
            'aggravating_factors',
            'protective_factors',
            'tags',
            'demographic_info',
            'medical_history',
            'medications',
            'family_mental_health_history',
            'total_sessions',
            'total_assessments',
            'progress_percentage',
            'start_date',
            'close_date',
            'internal_notes',
            'timeline',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'pid',
            'case_number',
            'total_sessions',
            'total_assessments',
            'start_date',
            'created_at',
            'updated_at',
            'timeline',
        ]


class CaseCreateSerializer(TainoBaseModelSerializer):
    """
    سریالایزر ایجاد پرونده
    """
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    partner = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    assigned_counselor = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Case
        fields = [
            'user',
            'partner',
            'assigned_counselor',
            'case_type',
            'priority',
            'initial_complaint',
            'demographic_info',
            'medical_history',
            'medications',
            'family_mental_health_history',
            'tags',
        ]
    
    def create(self, validated_data):
        from apps.case.services.case import CaseService
        
        # اگر user تعیین نشده، کاربر جاری را استفاده کن
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        
        case = CaseService.create_case(**validated_data)
        return case
    
    def to_representation(self, instance):
        return CaseDetailSerializer(instance, context=self.context).data


class CaseUpdateSerializer(TainoBaseModelSerializer):
    """
    سریالایزر بروزرسانی پرونده
    """
    assigned_counselor = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='pid',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Case
        fields = [
            'assigned_counselor',
            'status',
            'priority',
            'initial_diagnosis',
            'current_diagnosis',
            'symptoms',
            'severity',
            'aggravating_factors',
            'protective_factors',
            'tags',
            'medical_history',
            'medications',
            'family_mental_health_history',
            'internal_notes',
            'progress_percentage',
        ]
    
    def update(self, instance, validated_data):
        from apps.case.services.case import CaseService
        
        # اگر status تغییر کرده باشد
        if 'status' in validated_data and validated_data['status'] != instance.status:
            new_status = validated_data.pop('status')
            updated_by = self.context['request'].user
            CaseService.update_case_status(instance, new_status, updated_by)
        
        # بروزرسانی سایر فیلدها
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance
    
    def to_representation(self, instance):
        return CaseDetailSerializer(instance, context=self.context).data


class CaseSummarySerializer(serializers.Serializer):
    """
    سریالایزر خلاصه آماری پرونده
    """
    completed_sessions = serializers.IntegerField()
    total_assessments = serializers.IntegerField()
    daily_logs_count = serializers.IntegerField()
    avg_mood_30days = serializers.FloatField(allow_null=True)
    progress_percentage = serializers.IntegerField()
