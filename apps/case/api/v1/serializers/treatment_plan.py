from rest_framework import serializers

from apps.case.models import TreatmentPlan, TreatmentGoal, Case
from base_utils.serializers.base import TainoBaseModelSerializer


class TreatmentGoalSerializer(TainoBaseModelSerializer):
    """
    سریالایزر اهداف درمانی
    """
    goal_type_display = serializers.CharField(source='get_goal_type_display', read_only=True)
    
    class Meta:
        model = TreatmentGoal
        fields = [
            'pid',
            'goal_type',
            'goal_type_display',
            'description',
            'target_date',
            'progress_percentage',
            'is_achieved',
            'achieved_date',
            'notes',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['pid', 'created_at', 'updated_at']


class TreatmentPlanSerializer(TainoBaseModelSerializer):
    """
    سریالایزر برنامه درمانی
    """
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    goals = TreatmentGoalSerializer(many=True, read_only=True)
    
    class Meta:
        model = TreatmentPlan
        fields = [
            'pid',
            'case_number',
            'treatment_methods',
            'prescribed_exercises',
            'general_notes',
            'next_review_date',
            'goals',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['pid', 'created_at', 'updated_at']
