# apps/ai_chat/api/v1/views.py
import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from apps.ai_chat.models import AISession, AIMessage
from base_utils.views.mobile import TainoMobileGenericViewSet, TainoMobileCreateModelMixin, TainoMobileListModelMixin

from apps.ai_chat.api.v1.serializers import AIMessageSerializer, AIMessageCreateSerializer


logger = logging.getLogger(__name__)


class AIMessageViewSet(TainoMobileListModelMixin, TainoMobileCreateModelMixin, TainoMobileGenericViewSet):
    """ViewSet for AI messages"""

    serializer_class = AIMessageSerializer

    def get_queryset(self):
        return AIMessage.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return AIMessageCreateSerializer
        return AIMessageSerializer

    @extend_schema(responses={200: AIMessageSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="session/(?P<session_id>[^/.]+)")
    def session_messages(self, request, session_id=None):
        """Get messages for a specific AI session"""
        try:
            ai_session = AISession.objects.get(pid=session_id, is_deleted=False)

            if request.user != ai_session.user:
                return Response(
                    {"detail": _("You are not the owner of this AI session")},
                    status=status.HTTP_403_FORBIDDEN,
                )

            queryset = AIMessage.objects.filter(ai_session=ai_session, is_deleted=False).order_by("created_at")

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except AISession.DoesNotExist:
            return Response({"detail": _("AI session not found")}, status=status.HTTP_404_NOT_FOUND)
