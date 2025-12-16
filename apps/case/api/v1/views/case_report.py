from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.case.models import Case
from apps.case.services.query import CaseQuery
from base_utils.views.mobile import TainoMobileGenericViewSet


class CaseReportViewSet(TainoMobileGenericViewSet):
    """
    ViewSet برای تولید گزارش‌های پرونده
    """
    
    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'case_number': {'type': 'string'},
                'user_info': {'type': 'object'},
                'sessions': {'type': 'array'},
                'assessments': {'type': 'array'},
                'treatment_plan': {'type': 'object'},
                'progress': {'type': 'object'},
            }
        }}
    )
    @action(detail=False, methods=['GET'], url_path='generate/(?P<case_pid>[^/.]+)')
    def generate(self, request, case_pid=None):
        """
        تولید گزارش کامل پرونده برای دانلود PDF
        این API داده‌های لازم برای تولید PDF در فرانت را برمی‌گرداند
        """
        try:
            case = CaseQuery.get_case_with_relations(case_pid)
        except Case.DoesNotExist:
            return Response(
                {'error': 'Case not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی
        user = request.user
        if case.user != user and case.partner != user and case.assigned_counselor != user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # آماده‌سازی داده‌ها برای گزارش
        from apps.case.api.v1.serializers.case import CaseDetailSerializer
        from apps.case.api.v1.serializers.session import SessionListSerializer
        from apps.case.api.v1.serializers.assessment import AssessmentListSerializer
        from apps.case.api.v1.serializers.treatment_plan import TreatmentPlanSerializer
        from apps.case.services.case_analytics import CaseAnalytics
        
        report_data = {
            'case': CaseDetailSerializer(case, context={'request': request}).data,
            'sessions': SessionListSerializer(
                case.sessions.all(),
                many=True,
                context={'request': request}
            ).data,
            'assessments': AssessmentListSerializer(
                case.assessments.all(),
                many=True,
                context={'request': request}
            ).data,
            'treatment_plan': None,
            'progress': CaseAnalytics.get_case_summary(case),
            'mood_trend': CaseAnalytics.get_mood_trend(case, days=90),
        }
        
        # اضافه کردن برنامه درمانی
        if hasattr(case, 'treatment_plan'):
            report_data['treatment_plan'] = TreatmentPlanSerializer(
                case.treatment_plan,
                context={'request': request}
            ).data
        
        return Response(report_data)
