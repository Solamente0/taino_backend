from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.case.models import Assessment
from apps.case.api.v1.serializers.assessment import (
    AssessmentListSerializer,
    AssessmentDetailSerializer,
    AssessmentCreateSerializer,
)
from apps.case.api.v1.filters import AssessmentFilter
from base_utils.views.mobile import TainoMobileModelViewSet


class AssessmentViewSet(TainoMobileModelViewSet):
    """
    ViewSet برای مدیریت ارزیابی‌ها
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AssessmentFilter
    ordering_fields = ['date_taken', 'raw_score']
    ordering = ['-date_taken']
    
    def get_queryset(self):
        user = self.request.user
        
        # فقط ارزیابی‌های پرونده‌های مرتبط با کاربر
        return Assessment.objects.filter(
            case__user=user
        ).select_related('case', 'session')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentListSerializer
        elif self.action == 'create':
            return AssessmentCreateSerializer
        return AssessmentDetailSerializer
    
    def perform_create(self, serializer):
        from apps.case.services.case import CaseService
        from apps.case.models import TimelineEventType
        
        assessment = serializer.save()
        
        # ثبت در تایم‌لاین
        CaseService.add_timeline_event(
            case=assessment.case,
            event_type=TimelineEventType.ASSESSMENT_COMPLETED,
            title=f"تست {assessment.test_name}",
            description=f"نمره: {assessment.raw_score}",
            created_by=self.request.user,
            icon="📊",
            color="purple"
        )
