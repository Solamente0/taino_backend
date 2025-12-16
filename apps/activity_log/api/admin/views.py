"""
apps/activity_log/api/admin/views.py
Admin views for activity logs
"""

from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from apps.activity_log.api.admin.filters import AdminActivityLogFilter
from apps.activity_log.api.admin.serializers import (
    AdminActivityLogListSerializer,
    AdminActivityLogDetailSerializer,
    AdminActivityLogStatsSerializer,
    AdminUserActivitySummarySerializer,
)
from apps.activity_log.models import ActivityLog
from apps.activity_log.services.query import ActivityLogQuery
from base_utils.views.admin import TainoAdminReadOnlyModelViewSet


class AdminActivityLogViewSet(TainoAdminReadOnlyModelViewSet):
    """
    Admin ViewSet for viewing all activity logs.

    Admins can view logs for all users with advanced filtering.
    """

    queryset = ActivityLog.objects.all()
    serializer_class = AdminActivityLogListSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = AdminActivityLogFilter
    search_fields = [
        "user__phone_number",
        "user__email",
        "user__first_name",
        "user__last_name",
        "description",
        "ip_address",
        "endpoint",
    ]
    ordering_fields = ["created_at", "action", "level", "user"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Optimize queryset with select_related"""
        return ActivityLog.objects.select_related("user", "content_type").all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "retrieve":
            return AdminActivityLogDetailSerializer
        elif self.action in ["stats", "system_stats"]:
            return AdminActivityLogStatsSerializer
        elif self.action == "user_summary":
            return AdminUserActivitySummarySerializer
        return AdminActivityLogListSerializer

    @extend_schema(
        summary="لیست تمام فعالیت‌ها (ادمین)",
        description="دریافت لیست تمام فعالیت‌های سیستم با امکان فیلتر پیشرفته",
        parameters=[
            OpenApiParameter(name="user_pid", description="فیلتر بر اساس کاربر", required=False),
            OpenApiParameter(name="action", description="فیلتر بر اساس نوع عملیات", required=False),
            OpenApiParameter(name="level", description="فیلتر بر اساس سطح", required=False),
        ],
        responses={200: AdminActivityLogListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all activities"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="جزئیات فعالیت (ادمین)",
        description="دریافت جزئیات کامل یک فعالیت",
        responses={200: AdminActivityLogDetailSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        """Get detailed view of a single activity"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="آمار سیستم",
        description="دریافت آمار کلی فعالیت‌های سیستم",
        parameters=[OpenApiParameter(name="days", description="تعداد روزهای گذشته (پیش‌فرض: 7)", required=False, type=int)],
        responses={200: AdminActivityLogStatsSerializer},
    )
    @action(detail=False, methods=["GET"], url_path="system-stats")
    def system_stats(self, request):
        """
        Get system-wide activity statistics.
        """
        days = int(request.query_params.get("days", 7))

        stats = ActivityLogQuery.get_system_stats(days=days)

        # Get recent activities
        recent_activities = ActivityLog.objects.order_by("-created_at")[:10]
        stats["recent_activities"] = AdminActivityLogListSerializer(recent_activities, many=True).data

        serializer = self.get_serializer(stats)
        return Response(serializer.data)

    @extend_schema(
        summary="آمار کاربر خاص",
        description="دریافت آمار فعالیت‌های یک کاربر خاص",
        parameters=[
            OpenApiParameter(
                name="user_pid", description="شناسه کاربر", required=True, type=str, location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(name="days", description="تعداد روزهای گذشته", required=False, type=int),
        ],
        responses={200: AdminActivityLogStatsSerializer},
    )
    @action(detail=False, methods=["GET"], url_path="user-stats")
    def user_stats(self, request):
        """Get statistics for a specific user"""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        user_pid = request.query_params.get("user_pid")
        if not user_pid:
            return Response({"error": "user_pid is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pid=user_pid)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        days = int(request.query_params.get("days", 7))
        stats = ActivityLogQuery.get_user_stats(user=user, days=days)

        # Get recent activities
        recent_activities = ActivityLog.objects.filter(user=user).order_by("-created_at")[:10]

        stats["recent_activities"] = AdminActivityLogListSerializer(recent_activities, many=True).data

        serializer = self.get_serializer(stats)
        return Response(serializer.data)

    @extend_schema(
        summary="خلاصه فعالیت کاربران",
        description="دریافت خلاصه فعالیت‌های همه کاربران",
        responses={200: AdminUserActivitySummarySerializer(many=True)},
    )
    @action(detail=False, methods=["GET"], url_path="user-summary")
    def user_summary(self, request):
        """Get activity summary for all users"""
        from django.contrib.auth import get_user_model
        from apps.activity_log.models import ActivityLogAction

        User = get_user_model()

        # Get summary data
        summaries = ActivityLogQuery.get_users_activity_summary(limit=100)

        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="فعالیت‌های خطا",
        description="دریافت لیست فعالیت‌هایی که با خطا مواجه شده‌اند",
        responses={200: AdminActivityLogListSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"], url_path="errors")
    def error_logs(self, request):
        """Get logs with errors"""
        from apps.activity_log.models import ActivityLogLevel

        error_logs = ActivityLog.objects.filter(
            Q(is_successful=False) | Q(level__in=[ActivityLogLevel.ERROR, ActivityLogLevel.CRITICAL])
        ).order_by("-created_at")[:100]

        serializer = AdminActivityLogListSerializer(error_logs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="فعالیت‌های مشکوک",
        description="دریافت فعالیت‌های مشکوک (تلاش‌های ناموفق متعدد)",
        responses={200: AdminActivityLogListSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"], url_path="suspicious")
    def suspicious_activities(self, request):
        """Get suspicious activities (multiple failed attempts)"""
        from datetime import timedelta

        # Get IPs with multiple failed attempts in last hour
        one_hour_ago = timezone.now() - timedelta(hours=1)

        suspicious_ips = (
            ActivityLog.objects.filter(created_at__gte=one_hour_ago, is_successful=False)
            .values("ip_address")
            .annotate(failed_count=Count("id"))
            .filter(failed_count__gte=5)
            .values_list("ip_address", flat=True)
        )

        # Get all activities from suspicious IPs
        suspicious_logs = ActivityLog.objects.filter(ip_address__in=suspicious_ips).order_by("-created_at")[:100]

        serializer = AdminActivityLogListSerializer(suspicious_logs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="فعالیت‌های اخیر بر اساس IP",
        description="دریافت فعالیت‌های یک آدرس IP خاص",
        parameters=[
            OpenApiParameter(
                name="ip_address", description="آدرس IP", required=True, type=str, location=OpenApiParameter.QUERY
            )
        ],
        responses={200: AdminActivityLogListSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"], url_path="by-ip")
    def activities_by_ip(self, request):
        """Get activities by IP address"""
        ip_address = request.query_params.get("ip_address")
        if not ip_address:
            return Response({"error": "ip_address is required"}, status=status.HTTP_400_BAD_REQUEST)

        logs = ActivityLog.objects.filter(ip_address=ip_address).order_by("-created_at")[:100]

        serializer = AdminActivityLogListSerializer(logs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="گزارش روزانه",
        description="دریافت گزارش فعالیت‌های روزانه",
        parameters=[OpenApiParameter(name="date", description="تاریخ (YYYY-MM-DD)", required=False, type=str)],
        responses={200: dict},
    )
    @action(detail=False, methods=["GET"], url_path="daily-report")
    def daily_report(self, request):
        """Get daily activity report"""
        from datetime import datetime

        date_str = request.query_params.get("date")
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = timezone.now().date()

        # Get activities for the date
        start_of_day = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))

        daily_logs = ActivityLog.objects.filter(created_at__gte=start_of_day, created_at__lte=end_of_day)

        # Calculate statistics
        total = daily_logs.count()
        successful = daily_logs.filter(is_successful=True).count()
        failed = daily_logs.filter(is_successful=False).count()
        unique_users = daily_logs.values("user").distinct().count()

        # Action breakdown
        action_breakdown = daily_logs.values("action").annotate(count=Count("id")).order_by("-count")

        report = {
            "date": target_date,
            "total_activities": total,
            "successful_activities": successful,
            "failed_activities": failed,
            "unique_users": unique_users,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "action_breakdown": list(action_breakdown),
        }

        return Response(report)

    @extend_schema(
        summary="پاک‌سازی دستی لاگ‌ها",
        description="پاک‌سازی لاگ‌های قدیمی‌تر از تعداد روز مشخص شده",
        parameters=[
            OpenApiParameter(name="days", description="لاگ‌های قدیمی‌تر از این تعداد روز پاک شوند", required=False, type=int)
        ],
        responses={200: dict},
    )
    @action(detail=False, methods=["POST"], url_path="cleanup")
    def cleanup_logs(self, request):
        """Manually trigger log cleanup"""
        from apps.activity_log.tasks import delete_old_activity_logs

        days = int(request.query_params.get("days", 10))

        # Trigger the task
        task = delete_old_activity_logs.delay()

        return Response({"message": f"Cleanup task triggered for logs older than {days} days", "task_id": task.id})
