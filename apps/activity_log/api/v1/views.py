"""
apps/activity_log/api/v1/views.py
Mobile user views for activity logs
"""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.activity_log.api.v1.filters import ActivityLogFilter
from apps.activity_log.api.v1.serializers import (
    ActivityLogListSerializer,
    ActivityLogDetailSerializer,
    ActivityLogStatsSerializer,
)
from apps.activity_log.models import ActivityLog
from apps.activity_log.services.query import ActivityLogQuery
from base_utils.views.mobile import TainoMobileReadOnlyModelViewSet


class ActivityLogViewSet(TainoMobileReadOnlyModelViewSet):
    """
    ViewSet for mobile users to view their own activity logs.

    Users can only see their own activity logs.
    """

    serializer_class = ActivityLogListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ActivityLogFilter
    ordering_fields = ["created_at", "action", "level"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return only the current user's activity logs"""
        return ActivityLog.objects.filter(user=self.request.user).select_related("user", "content_type")

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "retrieve":
            return ActivityLogDetailSerializer
        elif self.action == "stats":
            return ActivityLogStatsSerializer
        return ActivityLogListSerializer

    @extend_schema(
        summary="لیست فعالیت‌های من",
        description="دریافت لیست فعالیت‌های کاربر جاری با امکان فیلتر و مرتب‌سازی",
        parameters=[
            OpenApiParameter(name="action", description="فیلتر بر اساس نوع عملیات", required=False, type=str),
            OpenApiParameter(name="level", description="فیلتر بر اساس سطح لاگ", required=False, type=str),
            OpenApiParameter(name="is_successful", description="فیلتر بر اساس موفقیت عملیات", required=False, type=bool),
            OpenApiParameter(name="date_from", description="از تاریخ", required=False, type=str),
            OpenApiParameter(name="date_to", description="تا تاریخ", required=False, type=str),
        ],
        responses={200: ActivityLogListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of user's activities"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="جزئیات فعالیت", description="دریافت جزئیات کامل یک فعالیت", responses={200: ActivityLogDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """Get detailed view of a single activity"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="آمار فعالیت‌های من",
        description="دریافت آمار و خلاصه فعالیت‌های کاربر در 7 روز گذشته",
        responses={200: ActivityLogStatsSerializer},
    )
    @action(detail=False, methods=["GET"], url_path="stats")
    def stats(self, request):
        """
        Get activity statistics for the current user.
        Returns summary of activities in the last 7 days.
        """
        stats = ActivityLogQuery.get_user_stats(user=request.user, days=7)

        # Get recent activities
        recent_activities = ActivityLog.objects.filter(user=request.user).order_by("-created_at")[:10]

        stats["recent_activities"] = ActivityLogListSerializer(recent_activities, many=True).data

        serializer = self.get_serializer(stats)
        return Response(serializer.data)

    @extend_schema(
        summary="فعالیت‌های ناموفق",
        description="دریافت لیست فعالیت‌های ناموفق کاربر",
        responses={200: ActivityLogListSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"], url_path="failed")
    def failed_activities(self, request):
        """Get list of failed activities"""
        failed_logs = ActivityLog.objects.filter(user=request.user, is_successful=False).order_by("-created_at")[:50]

        serializer = ActivityLogListSerializer(failed_logs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="آخرین ورودها",
        description="دریافت لیست آخرین ورودهای کاربر",
        responses={200: ActivityLogListSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"], url_path="logins")
    def recent_logins(self, request):
        """Get recent login activities"""
        from apps.activity_log.models import ActivityLogAction

        logins = ActivityLog.objects.filter(user=request.user, action=ActivityLogAction.LOGIN).order_by("-created_at")[:20]

        serializer = ActivityLogListSerializer(logins, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="فعالیت‌های مالی",
        description="دریافت لیست فعالیت‌های مرتبط با پرداخت و کیف پول",
        responses={200: ActivityLogListSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"], url_path="financial")
    def financial_activities(self, request):
        """Get financial related activities"""
        from apps.activity_log.models import ActivityLogAction

        financial_actions = [
            ActivityLogAction.PAYMENT_INITIATED,
            ActivityLogAction.PAYMENT_SUCCESS,
            ActivityLogAction.PAYMENT_FAILED,
            ActivityLogAction.WALLET_CHARGE,
            ActivityLogAction.WALLET_DEBIT,
            ActivityLogAction.SUBSCRIPTION_PURCHASED,
        ]

        activities = ActivityLog.objects.filter(user=request.user, action__in=financial_actions).order_by("-created_at")[:50]

        serializer = ActivityLogListSerializer(activities, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="تعداد فعالیت‌های امروز", description="دریافت تعداد فعالیت‌های انجام شده امروز", responses={200: dict}
    )
    @action(detail=False, methods=["GET"], url_path="today-count")
    def today_count(self, request):
        """Get count of today's activities"""
        from django.utils import timezone
        from datetime import timedelta

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        count = ActivityLog.objects.filter(user=request.user, created_at__gte=today_start).count()

        return Response({"count": count, "date": today_start.date()})
