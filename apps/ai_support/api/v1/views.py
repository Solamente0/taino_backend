# apps/ai_support/api/v1/views.py
import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.ai_support.models import SupportSession, SupportMessage, SupportAIConfig
from apps.ai_support.api.v1.serializers import (
    SupportSessionSerializer,
    SupportSessionDetailSerializer,
    SupportMessageSerializer,
    CreateSupportSessionSerializer,
    SupportAIConfigSerializer,
)
from base_utils.views.mobile import (
    TainoMobileGenericViewSet,
    TainoMobileListModelMixin,
    TainoMobileRetrieveModelMixin,
)

logger = logging.getLogger(__name__)


class SupportAIConfigViewSet(TainoMobileListModelMixin, TainoMobileGenericViewSet):
    """ViewSet for AI configuration (read-only for users)"""

    permission_classes = [IsAuthenticated]
    serializer_class = SupportAIConfigSerializer

    def get_queryset(self):
        return SupportAIConfig.objects.filter(is_active=True)

    @extend_schema(responses={200: SupportAIConfigSerializer})
    @action(detail=False, methods=["get"], url_path="active")
    def get_active_config(self, request):
        """Get the currently active AI configuration"""
        config = SupportAIConfig.get_active_config()
        print(f"Activated configs -> {config=}")
        if not config:
            return Response({"detail": "هیچ پیکربندی فعالی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(config)
        return Response(serializer.data)


class SupportSessionViewSet(TainoMobileListModelMixin, TainoMobileRetrieveModelMixin, TainoMobileGenericViewSet):
    """ViewSet for support sessions"""

    permission_classes = [IsAuthenticated]
    serializer_class = SupportSessionSerializer

    def get_queryset(self):
        user = self.request.user
        return SupportSession.objects.filter(user=user, is_deleted=False).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SupportSessionDetailSerializer
        return SupportSessionSerializer

    @extend_schema(request=CreateSupportSessionSerializer, responses={200: SupportSessionDetailSerializer})
    @action(detail=False, methods=["post"], url_path="create")
    def create_session(self, request):
        """Create a new support session"""
        serializer = CreateSupportSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        subject = serializer.validated_data.get("subject", "پشتیبانی")

        try:
            # Create session
            session = SupportSession.objects.create(user=user, status="active", subject=subject)

            # Create welcome message
            SupportMessage.objects.create(
                session=session,
                sender=user,
                content="سلام! به پشتیبانی خوش آمدید. چطور می‌تونم کمکتون کنم؟",
                message_type="text",
                is_ai=True,
            )

            response_serializer = SupportSessionDetailSerializer(session)
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"Error creating support session: {e}")
            return Response({"detail": "خطا در ایجاد جلسه پشتیبانی"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: SupportSessionSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="my-sessions")
    def my_sessions(self, request):
        """Get all support sessions for the user"""
        queryset = self.filter_queryset(self.get_queryset())

        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses={200: SupportSessionDetailSerializer})
    @action(detail=True, methods=["post"], url_path="close")
    def close_session(self, request, pid=None):
        """Close a support session"""
        try:
            session = SupportSession.objects.get(pid=pid, user=request.user, is_deleted=False)

            session.status = "closed"
            session.save(update_fields=["status"])

            # Create closing message
            SupportMessage.objects.create(
                session=session,
                sender=session.user,
                content="جلسه پشتیبانی بسته شد. ممنون از شما!",
                message_type="text",
                is_ai=True,
            )

            serializer = SupportSessionDetailSerializer(session)
            return Response(serializer.data)

        except SupportSession.DoesNotExist:
            return Response({"detail": "جلسه پشتیبانی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)


class SupportMessageViewSet(TainoMobileListModelMixin, TainoMobileGenericViewSet):
    """ViewSet for support messages"""

    permission_classes = [IsAuthenticated]
    serializer_class = SupportMessageSerializer

    def get_queryset(self):
        return SupportMessage.objects.none()

    @extend_schema(responses={200: SupportMessageSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="session/(?P<session_id>[^/.]+)")
    def session_messages(self, request, session_id=None):
        """Get messages for a specific support session"""
        try:
            session = SupportSession.objects.get(pid=session_id, is_deleted=False)

            if request.user != session.user:
                return Response({"detail": "شما مالک این جلسه نیستید"}, status=status.HTTP_403_FORBIDDEN)

            queryset = SupportMessage.objects.filter(session=session, is_deleted=False).order_by("created_at")

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except SupportSession.DoesNotExist:
            return Response({"detail": "جلسه پشتیبانی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
