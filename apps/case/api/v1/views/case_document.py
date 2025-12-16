from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.case.models import CaseDocument
from apps.case.api.v1.serializers.case_document import (
    CaseDocumentSerializer,
    CaseDocumentCreateSerializer,
)
from apps.case.api.v1.filters import CaseDocumentFilter
from base_utils.views.mobile import TainoMobileModelViewSet


class CaseDocumentViewSet(TainoMobileModelViewSet):
    """
    ViewSet برای مدیریت اسناد پرونده
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CaseDocumentFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # فقط اسناد غیر محرمانه یا اسناد محرمانه‌ای که کاربر مشاور است
        queryset = CaseDocument.objects.filter(
            case__user=user
        ).select_related('case', 'file', 'uploaded_by')
        
        # اگر کاربر مشاور نیست، اسناد محرمانه را نشان نده
        if not (hasattr(user, 'role') and user.role and user.role.static_name == 'counselor'):
            queryset = queryset.filter(is_confidential=False)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CaseDocumentCreateSerializer
        return CaseDocumentSerializer
    
    def perform_create(self, serializer):
        from apps.case.services.case import CaseService
        from apps.case.models import TimelineEventType
        
        document = serializer.save()
        
        # ثبت در تایم‌لاین
        CaseService.add_timeline_event(
            case=document.case,
            event_type=TimelineEventType.DOCUMENT_UPLOADED,
            title="آپلود سند",
            description=document.title,
            created_by=self.request.user,
            icon="📄",
            color="gray"
        )
