from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema

from apps.case.models import Session
from apps.case.api.v1.serializers.session import (
    SessionListSerializer,
    SessionDetailSerializer,
    SessionCreateSerializer,
    SessionUpdateSerializer,
)
from apps.case.api.v1.filters import SessionFilter
from base_utils.views.mobile import TainoMobileModelViewSet


class SessionViewSet(TainoMobileModelViewSet):
    """
    ViewSet برای مدیریت جلسات
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SessionFilter
    ordering_fields = ['scheduled_datetime', 'session_number']
    ordering = ['-scheduled_datetime']
    
    def get_queryset(self):
        user = self.request.user
        
        # فقط جلسات پرونده‌های مرتبط با کاربر
        return Session.objects.filter(
            case__user=user
        ).select_related('case')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SessionListSerializer
        elif self.action == 'create':
            return SessionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SessionUpdateSerializer
        return SessionDetailSerializer
    
    def perform_create(self, serializer):
        from apps.case.services.case import CaseService
        from apps.case.models import TimelineEventType
        
        session = serializer.save()
        
        # ثبت در تایم‌لاین
        CaseService.add_timeline_event(
            case=session.case,
            event_type=TimelineEventType.SESSION_COMPLETED,
            title=f"جلسه {session.session_number}",
            description=f"جلسه {session.get_session_type_display()} برنامه‌ریزی شد",
            created_by=self.request.user,
            icon="🎤",
            color="blue"
        )
