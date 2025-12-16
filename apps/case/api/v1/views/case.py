from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.case.models import Case
from apps.case.api.v1.serializers.case import (
    CaseListSerializer,
    CaseDetailSerializer,
    CaseCreateSerializer,
    CaseUpdateSerializer,
    CaseSummarySerializer,
)
from apps.case.api.v1.filters import CaseFilter
from apps.case.services.query import CaseQuery
from apps.case.services.case_analytics import CaseAnalytics
from base_utils.views.mobile import TainoMobileModelViewSet


class CaseViewSet(TainoMobileModelViewSet):
    """
    ViewSet برای مدیریت پرونده‌ها
    """
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CaseFilter
    search_fields = ['case_number', 'user__first_name', 'user__last_name', 'initial_complaint']
    ordering_fields = ['created_at', 'updated_at', 'case_number', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # اگر کاربر مشاور است، پرونده‌های محول شده را نشان بده
        if hasattr(user, 'role') and user.role and user.role.static_name == 'counselor':
            return CaseQuery.get_counselor_cases(user)
        
        # در غیر این صورت پرونده‌های خود کاربر
        return CaseQuery.get_user_cases(user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CaseListSerializer
        elif self.action == 'create':
            return CaseCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CaseUpdateSerializer
        return CaseDetailSerializer
    
    @extend_schema(responses={200: CaseSummarySerializer})
    @action(detail=True, methods=['GET'], url_path='summary')
    def summary(self, request, pid=None):
        """
        دریافت خلاصه آماری پرونده
        """
        case = self.get_object()
        summary_data = CaseAnalytics.get_case_summary(case)
        serializer = CaseSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'mood_trend': {'type': 'array'},
            }
        }}
    )
    @action(detail=True, methods=['GET'], url_path='mood-trend')
    def mood_trend(self, request, pid=None):
        """
        دریافت روند خلق و خو
        """
        case = self.get_object()
        days = int(request.query_params.get('days', 30))
        trend_data = CaseAnalytics.get_mood_trend(case, days)
        return Response({'mood_trend': trend_data})
    
    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'assessment_trends': {'type': 'array'},
            }
        }}
    )
    @action(detail=True, methods=['GET'], url_path='assessment-trends')
    def assessment_trends(self, request, pid=None):
        """
        دریافت روند نمرات تست‌ها
        """
        case = self.get_object()
        test_type = request.query_params.get('test_type')
        
        if not test_type:
            return Response(
                {'error': 'test_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trend_data = CaseAnalytics.get_assessment_trends(case, test_type)
        return Response({'assessment_trends': trend_data})
    
    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'goals': {'type': 'array'},
            }
        }}
    )
    @action(detail=True, methods=['GET'], url_path='goals-progress')
    def goals_progress(self, request, pid=None):
        """
        دریافت پیشرفت اهداف درمانی
        """
        case = self.get_object()
        goals_data = CaseAnalytics.get_treatment_goals_progress(case)
        return Response({'goals': goals_data})
    
    @extend_schema(
        request=None,
        responses={200: CaseDetailSerializer}
    )
    @action(detail=True, methods=['POST'], url_path='close')
    def close_case(self, request, pid=None):
        """
        بستن پرونده
        """
        from apps.case.services.case import CaseService
        
        case = self.get_object()
        reason = request.data.get('reason', '')
        
        closed_case = CaseService.close_case(case, request.user, reason)
        serializer = CaseDetailSerializer(closed_case, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(responses={200: CaseDetailSerializer})
    @action(detail=True, methods=['GET'], url_path='timeline')
    def timeline(self, request, pid=None):
        """
        دریافت تایم‌لاین کامل پرونده
        """
        case = self.get_object()
        serializer = CaseDetailSerializer(case, context={'request': request})
        return Response({
            'timeline': serializer.data.get('timeline', [])
        })
