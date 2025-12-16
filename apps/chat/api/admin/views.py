# apps/chat/api/admin/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.chat.models import ChatSession, ChatMessage, ChatRequest, ChatSubscription
from apps.chat.api.admin.serializers import (
    AdminChatSessionSerializer,
    AdminChatSessionDetailSerializer,
    AdminChatMessageSerializer,
    AdminChatRequestSerializer,
    AdminChatSubscriptionSerializer,
    AdminChatSubscriptionCreateUpdateSerializer,
)
from base_utils.views.admin import (
    TainoAdminGenericViewSet,
    TainoAdminListModelMixin,
    TainoAdminRetrieveModelMixin,
    TainoAdminCreateModelMixin,
    TainoAdminUpdateModelMixin,
)


class AdminChatSessionViewSet(TainoAdminListModelMixin, TainoAdminRetrieveModelMixin, TainoAdminGenericViewSet):
    """
    Admin ViewSet for chat sessions
    """

    queryset = ChatSession.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AdminChatSessionDetailSerializer
        return AdminChatSessionSerializer


class AdminChatMessageViewSet(TainoAdminListModelMixin, TainoAdminRetrieveModelMixin, TainoAdminGenericViewSet):
    """
    Admin ViewSet for chat messages
    """

    queryset = ChatMessage.objects.all().order_by("-created_at")
    serializer_class = AdminChatMessageSerializer

    @extend_schema(responses={200: AdminChatMessageSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="session/(?P<session_id>[^/.]+)")
    def session_messages(self, request, session_id=None):
        """
        Get messages for a specific chat session
        """
        queryset = ChatMessage.objects.filter(chat_session__pid=session_id).order_by("created_at")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdminChatRequestViewSet(TainoAdminListModelMixin, TainoAdminRetrieveModelMixin, TainoAdminGenericViewSet):
    """
    Admin ViewSet for chat requests
    """

    queryset = ChatRequest.objects.all().order_by("-created_at")
    serializer_class = AdminChatRequestSerializer


class AdminChatSubscriptionViewSet(
    TainoAdminListModelMixin,
    TainoAdminRetrieveModelMixin,
    TainoAdminCreateModelMixin,
    TainoAdminUpdateModelMixin,
    TainoAdminGenericViewSet,
):
    """
    Admin ViewSet for chat subscriptions
    """

    queryset = ChatSubscription.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AdminChatSubscriptionCreateUpdateSerializer
        return AdminChatSubscriptionSerializer
