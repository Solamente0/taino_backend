# apps/ai_chat/api/admin/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.ai_chat.models import AISession, AIMessage, ChatAIConfig, LegalAnalysisLog
from apps.ai_chat.api.admin.serializers import (
    AdminAISessionSerializer,
    AdminAISessionDetailSerializer,
    AdminAIMessageSerializer,
    AdminChatAIConfigSerializer,
    AdminLegalAnalysisLogSerializer,
)
from base_utils.views.admin import (
    TainoAdminGenericViewSet,
    TainoAdminListModelMixin,
    TainoAdminRetrieveModelMixin,
    TainoAdminCreateModelMixin,
    TainoAdminUpdateModelMixin,
)


class AdminAISessionViewSet(TainoAdminListModelMixin, TainoAdminRetrieveModelMixin, TainoAdminGenericViewSet):
    """Admin ViewSet for AI sessions"""

    queryset = AISession.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AdminAISessionDetailSerializer
        return AdminAISessionSerializer


class AdminAIMessageViewSet(TainoAdminListModelMixin, TainoAdminRetrieveModelMixin, TainoAdminGenericViewSet):
    """Admin ViewSet for AI messages"""

    queryset = AIMessage.objects.all().order_by("-created_at")
    serializer_class = AdminAIMessageSerializer

    @extend_schema(responses={200: AdminAIMessageSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="session/(?P<session_id>[^/.]+)")
    def session_messages(self, request, session_id=None):
        """Get messages for a specific AI session"""
        queryset = AIMessage.objects.filter(ai_session__pid=session_id).order_by("created_at")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdminChatAIConfigViewSet(
    TainoAdminListModelMixin,
    TainoAdminRetrieveModelMixin,
    TainoAdminCreateModelMixin,
    TainoAdminUpdateModelMixin,
    TainoAdminGenericViewSet,
):
    """Admin ViewSet for AI configuration"""

    queryset = ChatAIConfig.objects.all().order_by("-created_at")
    serializer_class = AdminChatAIConfigSerializer


class AdminLegalAnalysisLogViewSet(TainoAdminListModelMixin, TainoAdminRetrieveModelMixin, TainoAdminGenericViewSet):
    """Admin ViewSet for legal analysis logs"""

    queryset = LegalAnalysisLog.objects.all().order_by("-created_at")
    serializer_class = AdminLegalAnalysisLogSerializer
