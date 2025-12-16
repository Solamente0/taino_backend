from rest_framework import serializers

from apps.case.models import DailyLog, Case
from base_utils.serializers.base import TainoBaseModelSerializer


class DailyLogSerializer(TainoBaseModelSerializer):
    """
    سریالایزر ژورنال روزانه
    """
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    
    class Meta:
        model = DailyLog
        fields = [
            'pid',
            'case_number',
            'log_date',
            'mood_score',
            'mood_notes',
            'sleep_hours',
            'sleep_quality',
            'medications_taken',
            'medication_compliance',
            'physical_activity_minutes',
            'physical_activity_type',
            'homework_completed',
            'stressful_events',
            'positive_events',
            'general_notes',
            'specific_symptoms',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['pid', 'created_at', 'updated_at']


class DailyLogCreateSerializer(TainoBaseModelSerializer):
    """
    سریالایزر ایجاد ژورنال روزانه
    """
    case = serializers.SlugRelatedField(
        queryset=Case.objects.all(),
        slug_field='pid'
    )
    
    class Meta:
        model = DailyLog
        fields = [
            'case',
            'log_date',
            'mood_score',
            'mood_notes',
            'sleep_hours',
            'sleep_quality',
            'medications_taken',
            'medication_compliance',
            'physical_activity_minutes',
            'physical_activity_type',
            'homework_completed',
            'stressful_events',
            'positive_events',
            'general_notes',
            'specific_symptoms',
        ]
    
    def to_representation(self, instance):
        return DailyLogSerializer(instance, context=self.context).data
