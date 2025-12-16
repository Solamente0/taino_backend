from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.case.models import TreatmentPlan, TreatmentGoal, Case
from apps.case.api.v1.serializers.treatment_plan import (
    TreatmentPlanSerializer,
    TreatmentGoalSerializer,
)
from base_utils.views.mobile import TainoMobileModelViewSet


class TreatmentPlanViewSet(TainoMobileModelViewSet):
    """
    ViewSet برای مدیریت برنامه‌های درمانی
    """
    serializer_class = TreatmentPlanSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        return TreatmentPlan.objects.filter(
            case__user=user
        ).select_related('case').prefetch_related('goals')
    
    @extend_schema(
        request=TreatmentGoalSerializer,
        responses={201: TreatmentGoalSerializer}
    )
    @action(detail=True, methods=['POST'], url_path='add-goal')
    def add_goal(self, request, pid=None):
        """
        افزودن هدف جدید به برنامه درمانی
        """
        treatment_plan = self.get_object()
        
        serializer = TreatmentGoalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        goal = TreatmentGoal.objects.create(
            treatment_plan=treatment_plan,
            **serializer.validated_data
        )
        
        return Response(
            TreatmentGoalSerializer(goal).data,
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        request=TreatmentGoalSerializer,
        responses={200: TreatmentGoalSerializer}
    )
    @action(detail=True, methods=['PATCH'], url_path='update-goal/(?P<goal_pid>[^/.]+)')
    def update_goal(self, request, pid=None, goal_pid=None):
        """
        بروزرسانی یک هدف
        """
        treatment_plan = self.get_object()
        
        try:
            goal = TreatmentGoal.objects.get(
                pid=goal_pid,
                treatment_plan=treatment_plan
            )
        except TreatmentGoal.DoesNotExist:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TreatmentGoalSerializer(
            goal,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # اگر هدف محقق شد، در تایم‌لاین ثبت کن
        if serializer.validated_data.get('is_achieved'):
            from apps.case.services.case import CaseService
            from apps.case.models import TimelineEventType
            
            CaseService.add_timeline_event(
                case=treatment_plan.case,
                event_type=TimelineEventType.GOAL_ACHIEVED,
                title="تحقق هدف",
                description=goal.description[:100],
                created_by=request.user,
                icon="🎯",
                color="green"
            )
        
        return Response(serializer.data)
