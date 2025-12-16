from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.case.models import DailyLog
from apps.case.api.v1.serializers.daily_log import (
    DailyLogSerializer,
    DailyLogCreateSerializer,
)
from apps.case.api.v1.filters import DailyLogFilter
from base_utils.views.mobile import TainoMobileModelViewSet


class DailyLogViewSet(TainoMobileModelViewSet):
    """
    ViewSet برای مدیریت ژورنال‌های روزانه
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = DailyLogFilter
    ordering_fields = ['log_date']
    ordering = ['-log_date']
    
    def get_queryset(self):
        user = self.request.user
        
        return DailyLog.objects.filter(
            case__user=user
        ).select_related('case')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DailyLogCreateSerializer
        return DailyLogSerializer
