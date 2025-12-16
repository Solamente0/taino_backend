from rest_framework import serializers

from apps.activity_log.models import ActivityLog, ActivityLogAction, ActivityLogLevel
from base_utils.serializers.base import TainoBaseModelSerializer


class AdminActivityLogListSerializer(TainoBaseModelSerializer):
    """Serializer for listing activity logs"""

    action_display = serializers.CharField(source="get_action_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "pid",
            "action",
            "action_display",
            "level",
            "level_display",
            "description",
            "is_successful",
            "created_at",
        ]
        read_only_fields = fields


class AdminActivityLogListSerializer(TainoBaseModelSerializer):
    """Serializer for admin listing of activity logs"""

    action_display = serializers.CharField(source="get_action_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "pid",
            "user_info",
            "action",
            "action_display",
            "level",
            "level_display",
            "description",
            "ip_address",
            "endpoint",
            "is_successful",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_info(self, obj):
        """Return basic user information"""
        if obj.user:
            return {
                "pid": obj.user.pid,
                "vekalat_id": obj.user.vekalat_id,
                "phone_number": obj.user.phone_number,
                "email": obj.user.email,
                "full_name": obj.user.get_full_name(),
            }
        return None


class AdminActivityLogDetailSerializer(TainoBaseModelSerializer):
    """Serializer for admin detailed view of activity logs"""

    action_display = serializers.CharField(source="get_action_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    content_type_info = serializers.SerializerMethodField(read_only=True)
    age_in_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "pid",
            "user_info",
            "action",
            "action_display",
            "level",
            "level_display",
            "description",
            "content_type_info",
            "object_id",
            "ip_address",
            "user_agent",
            "endpoint",
            "method",
            "metadata",
            "device_id",
            "is_successful",
            "error_message",
            "age_in_days",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_user_info(self, obj):
        """Return detailed user information"""
        if obj.user:
            return {
                "pid": obj.user.pid,
                "vekalat_id": obj.user.vekalat_id,
                "phone_number": obj.user.phone_number,
                "email": obj.user.email,
                "first_name": obj.user.first_name,
                "last_name": obj.user.last_name,
                "is_active": obj.user.is_active,
                "has_premium_account": obj.user.has_premium_account,
            }
        return None

    def get_content_type_info(self, obj):
        """Return detailed content type information"""
        if obj.content_type:
            return {
                "id": obj.content_type.id,
                "app_label": obj.content_type.app_label,
                "model": obj.content_type.model,
                "name": str(obj.content_type),
            }
        return None


class AdminActivityLogStatsSerializer(serializers.Serializer):
    """Serializer for activity log statistics"""

    total_activities = serializers.IntegerField()
    successful_activities = serializers.IntegerField()
    failed_activities = serializers.IntegerField()
    success_rate = serializers.FloatField()
    action_breakdown = serializers.ListField()
    level_breakdown = serializers.ListField()
    recent_activities = AdminActivityLogListSerializer(many=True, read_only=True)


class AdminActivityLogFilterSerializer(serializers.Serializer):
    """Serializer for filtering activity logs"""

    action = serializers.ChoiceField(choices=ActivityLogAction.choices, required=False, help_text="فیلتر بر اساس نوع عملیات")
    level = serializers.ChoiceField(choices=ActivityLogLevel.choices, required=False, help_text="فیلتر بر اساس سطح لاگ")
    is_successful = serializers.BooleanField(required=False, help_text="فیلتر بر اساس موفقیت عملیات")
    date_from = serializers.DateTimeField(required=False, help_text="از تاریخ (ISO 8601)")
    date_to = serializers.DateTimeField(required=False, help_text="تا تاریخ (ISO 8601)")
    search = serializers.CharField(required=False, help_text="جستجو در توضیحات و endpoint")


class AdminUserActivitySummarySerializer(serializers.Serializer):
    """Serializer for user activity summary"""

    user_pid = serializers.CharField()
    total_activities = serializers.IntegerField()
    login_count = serializers.IntegerField()
    last_login = serializers.DateTimeField(allow_null=True)
    failed_activities_count = serializers.IntegerField()
    most_common_action = serializers.CharField()
    devices_used = serializers.IntegerField()
