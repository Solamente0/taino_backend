import base64

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.chat.models import (
    ChatSession,
    ChatMessage,
    ChatRequest,
    ChatSubscription,
    ChatRequestStatusEnum,
    LawyerProposal,
    ChatTypeEnum,
    ChatSessionStatusEnum,
)
from apps.notification.services.alarm import NotificationService
from .serializers import (
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
    ChatRequestSerializer,
    ChatRequestCreateSerializer,
    ChatRequestResponseSerializer,
    ChatSubscriptionSerializer,
    ChatRequestDetailSerializer,
    LawyerProposalListSerializer,
    LawyerProposalCreateSerializer,
)
from apps.chat.services.chat_service import ChatService
from base_utils.views.mobile import (
    TainoMobileCreateModelMixin,
    TainoMobileRetrieveModelMixin,
    TainoMobileListModelMixin,
)
from apps.setting.services.query import GeneralSettingsQuery

import os
import logging
import tempfile
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils.translation import gettext_lazy as _

from base_utils.views.mobile import TainoMobileGenericViewSet

logger = logging.getLogger(__name__)


class ChatSessionViewSet(TainoMobileListModelMixin, TainoMobileRetrieveModelMixin, TainoMobileGenericViewSet):
    """
    ViewSet for chat sessions
    """

    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        user = self.request.user

        # Get sessions where user is client or consultant
        return ChatSession.objects.filter(Q(client=user) | Q(consultant=user), is_deleted=False).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChatSessionDetailSerializer
        return ChatSessionSerializer

    @extend_schema(responses={200: ChatSessionSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="my-sessions")
    def my_sessions(self, request):
        """
        Get sessions where user is a participant
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Filter by status if provided
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by type if provided
        type_param = request.query_params.get("type")
        if type_param:
            queryset = queryset.filter(chat_type=type_param)

        # Filter by role if provided
        role_param = request.query_params.get("role")
        if role_param == "client":
            queryset = queryset.filter(client=request.user)
        elif role_param == "consultant":
            queryset = queryset.filter(consultant=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses={200: ChatSessionDetailSerializer})
    @action(detail=True, methods=["post"], url_path="end-session")
    def end_session(self, request, pid=None):
        """
        End an active chat session
        """
        chat_session = self.get_object()

        # Check if user is participant
        if request.user != chat_session.client and request.user != chat_session.consultant:
            return Response({"detail": _("You are not a participant in this chat")}, status=status.HTTP_403_FORBIDDEN)

        # Check if session is active
        if chat_session.status != "active":
            return Response({"detail": _("Chat session is not active")}, status=status.HTTP_400_BAD_REQUEST)

        # End the session
        reason = request.data.get("reason", "")
        try:
            ChatService.end_chat_session(chat_session=chat_session, ended_by=request.user, reason=reason)

            return Response(self.get_serializer(chat_session).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: ChatSessionSerializer})
    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pid=None):
        """
        Mark all messages as read for the user
        """
        chat_session = self.get_object()

        # Check if user is participant
        if request.user != chat_session.client and request.user != chat_session.consultant:
            return Response({"detail": _("You are not a participant in this chat")}, status=status.HTTP_403_FORBIDDEN)

        # Mark messages as read
        ChatService.mark_messages_as_read(chat_session=chat_session, user=request.user)

        return Response(self.get_serializer(chat_session).data)


class ChatMessageViewSet(TainoMobileListModelMixin, TainoMobileCreateModelMixin, TainoMobileGenericViewSet):
    """
    ViewSet for chat messages
    """

    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ChatMessageCreateSerializer
        return ChatMessageSerializer

    @extend_schema(responses={200: ChatMessageSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="session/(?P<session_id>[^/.]+)")
    def session_messages(self, request, session_id=None):
        """
        Get messages for a specific chat session
        """
        try:
            # Check if user is participant
            chat_session = ChatSession.objects.get(pid=session_id, is_deleted=False)

            if request.user != chat_session.client and request.user != chat_session.consultant:
                return Response({"detail": _("You are not a participant in this chat")}, status=status.HTTP_403_FORBIDDEN)

            # Get messages
            queryset = ChatMessage.objects.filter(chat_session=chat_session, is_deleted=False).order_by("created_at")

            # Pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except ChatSession.DoesNotExist:
            return Response({"detail": _("Chat session not found")}, status=status.HTTP_404_NOT_FOUND)


class ChatRequestViewSet(
    TainoMobileListModelMixin,
    TainoMobileRetrieveModelMixin,
    TainoMobileCreateModelMixin,
    TainoMobileGenericViewSet,
):
    """
    ViewSet برای مدیریت درخواست‌های مشاوره
    """

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "description", "specialization"]
    filterset_fields = ["status", "city", "specialization"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        # کاربران عادی: درخواست‌های خودشان
        if not hasattr(user, "role") or user.role.static_name not in ["lawyer"]:
            return ChatRequest.objects.filter(client=user, is_deleted=False)

        # وکلا: درخواست‌های شهر خودشان
        if hasattr(user, "city"):
            return ChatRequest.objects.filter(city=user.city, status=ChatRequestStatusEnum.PENDING, is_deleted=False)

        return ChatRequest.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ChatRequestCreateSerializer
        if self.action == "retrieve":
            return ChatRequestDetailSerializer
        return ChatRequestSerializer

    @action(detail=False, methods=["get"])
    def my_requests(self, request):
        """درخواست‌های من"""
        queryset = ChatRequest.objects.filter(client=request.user, is_deleted=False).order_by("-created_at")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ChatRequestSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ChatRequestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def available_requests(self, request):
        """
        درخواست‌های موجود برای وکلا
        (فقط درخواست‌های شهر خودشان)
        """
        if not hasattr(request.user, "city"):
            return Response({"detail": "شما باید شهر خود را در پروفایل تعیین کنید"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = ChatRequest.objects.filter(
            city=request.user.city, status=ChatRequestStatusEnum.PENDING, expires_at__gt=timezone.now(), is_deleted=False
        ).order_by("-created_at")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ChatRequestDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ChatRequestDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(request=None, responses={200: ChatRequestDetailSerializer})
    @action(detail=True, methods=["post"])
    def cancel(self, request, pid=None):
        """لغو درخواست توسط کاربر"""
        chat_request = self.get_object()

        if chat_request.client != request.user:
            return Response({"detail": "فقط صاحب درخواست می‌تواند آن را لغو کند"}, status=status.HTTP_403_FORBIDDEN)

        if chat_request.status != ChatRequestStatusEnum.PENDING:
            return Response({"detail": "فقط درخواست‌های در انتظار قابل لغو هستند"}, status=status.HTTP_400_BAD_REQUEST)

        chat_request.status = ChatRequestStatusEnum.CANCELLED
        chat_request.save()

        return Response(ChatRequestDetailSerializer(chat_request).data)


class ChatSubscriptionViewSet(TainoMobileListModelMixin, TainoMobileRetrieveModelMixin, TainoMobileGenericViewSet):
    """
    ViewSet for chat subscriptions
    """

    serializer_class = ChatSubscriptionSerializer

    def get_queryset(self):
        return ChatSubscription.objects.filter(user=self.request.user).order_by("-created_at")

    @extend_schema(responses={200: ChatSubscriptionSerializer})
    @action(detail=False, methods=["get"], url_path="active")
    def active_subscription(self, request):
        """
        Get active subscription for current user
        """
        subscription = ChatSubscription.objects.filter(
            user=request.user, is_active=True, end_date__gte=timezone.now()
        ).first()

        if not subscription:
            return Response({"detail": _("No active subscription found")}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)


class LawyerProposalViewSet(
    TainoMobileListModelMixin,
    TainoMobileRetrieveModelMixin,
    TainoMobileCreateModelMixin,
    TainoMobileGenericViewSet,
):
    """
    ViewSet برای مدیریت پیشنهادهای وکلا
    """

    def get_queryset(self):
        user = self.request.user

        # وکلا: پیشنهادهای خودشان
        if hasattr(user, "role") and user.role.static_name == "lawyer":
            return LawyerProposal.objects.filter(lawyer=user, is_deleted=False)

        # کاربران: پیشنهادهای مربوط به درخواست‌هایشان
        return LawyerProposal.objects.filter(chat_request__client=user, is_deleted=False)

    def get_serializer_class(self):
        if self.action == "create":
            return LawyerProposalCreateSerializer
        return LawyerProposalListSerializer

    @extend_schema(request=None, responses={200: ChatSessionDetailSerializer})
    @action(detail=True, methods=["post"])
    def accept(self, request, pid=None):
        """قبول پیشنهاد توسط کاربر و ایجاد جلسه چت"""
        proposal = self.get_object()
        chat_request = proposal.chat_request

        # بررسی مالکیت
        if chat_request.client != request.user:
            return Response({"detail": "فقط صاحب درخواست می‌تواند پیشنهاد را قبول کند"}, status=status.HTTP_403_FORBIDDEN)

        # بررسی وضعیت
        if chat_request.status != ChatRequestStatusEnum.PENDING:
            return Response({"detail": "این درخواست قابل قبول نیست"}, status=status.HTTP_400_BAD_REQUEST)

        # ایجاد جلسه چت
        with transaction.atomic():
            # ایجاد سشن
            chat_session = ChatSession.objects.create(
                client=chat_request.client,
                consultant=proposal.lawyer,
                chat_type=ChatTypeEnum.LAWYER,
                status=ChatSessionStatusEnum.ACTIVE,
                title=chat_request.title,
                fee_amount=proposal.proposed_fee,
                time_limit_minutes=proposal.proposed_duration * 24 * 60,  # روز به دقیقه
                start_time=timezone.now(),
                creator=request.user,
            )

            # به‌روزرسانی درخواست
            chat_request.status = ChatRequestStatusEnum.ACCEPTED
            chat_request.selected_lawyer = proposal.lawyer
            chat_request.chat_session = chat_session
            chat_request.save()

            # به‌روزرسانی پیشنهاد
            proposal.status = "accepted"
            proposal.responded_at = timezone.now()
            proposal.save()

            # رد سایر پیشنهادها
            LawyerProposal.objects.filter(chat_request=chat_request).exclude(pid=proposal.pid).update(
                status="rejected", responded_at=timezone.now()
            )

            # ارسال نوتیفیکیشن به وکیل
            NotificationService.create_notification(
                to_user=proposal.lawyer,
                name="پیشنهاد شما پذیرفته شد",
                description=f"پیشنهاد شما برای درخواست «{chat_request.title}» پذیرفته شد",
                link=f"/chat/sessions/{chat_session.pid}",
            )

            # ارسال نوتیفیکیشن به کاربر
            NotificationService.create_notification(
                to_user=chat_request.client,
                name="جلسه چت شما آماده است",
                description=f"جلسه چت با {proposal.lawyer.get_full_name()} برای «{chat_request.title}» آماده است",
                link=f"/chat/sessions/{chat_session.pid}",
            )

            # پیام سیستمی
            ChatService.send_system_message(
                chat_session=chat_session, content=f"جلسه چت با موفقیت ایجاد شد. مدت زمان: {proposal.proposed_duration} روز"
            )

        return Response(ChatSessionDetailSerializer(chat_session).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses={200: LawyerProposalListSerializer})
    @action(detail=True, methods=["post"])
    def reject(self, request, pid=None):
        """رد پیشنهاد توسط کاربر"""
        proposal = self.get_object()

        if proposal.chat_request.client != request.user:
            return Response({"detail": "فقط صاحب درخواست می‌تواند پیشنهاد را رد کند"}, status=status.HTTP_403_FORBIDDEN)

        proposal.status = "rejected"
        proposal.responded_at = timezone.now()
        proposal.save()

        # ارسال نوتیفیکیشن به وکیل
        NotificationService.create_notification(
            to_user=proposal.lawyer,
            name="پیشنهاد شما رد شد",
            description=f"پیشنهاد شما برای درخواست «{proposal.chat_request.title}» رد شد",
            link=None,
        )

        return Response(LawyerProposalListSerializer(proposal).data)
