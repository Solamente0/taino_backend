from rest_framework import serializers

from apps.activity_log.models import ActivityLog, ActivityLogAction, ActivityLogLevel
from base_utils.serializers.base import TainoBaseModelSerializer


class ActivityLogListSerializer(TainoBaseModelSerializer):
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


class ActivityLogDetailSerializer(TainoBaseModelSerializer):
    """Serializer for detailed activity log view"""

    action_display = serializers.CharField(source="get_action_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    content_type_name = serializers.SerializerMethodField(read_only=True)

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
            "content_type_name",
            "object_id",
            "ip_address",
            "endpoint",
            "method",
            "metadata",
            "device_id",
            "is_successful",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_user_info(self, obj):
        """Return basic user information"""
        if obj.user:
            return {
                "pid": obj.user.pid,
                "phone_number": obj.user.phone_number,
                "full_name": obj.user.get_full_name(),
            }
        return None

    def get_content_type_name(self, obj):
        """Return content type name if available"""
        if obj.content_type:
            return {
                "app_label": obj.content_type.app_label,
                "model": obj.content_type.model,
                "name": str(obj.content_type),
            }
        return None


class ActivityLogStatsSerializer(serializers.Serializer):
    """Serializer for activity log statistics"""

    total_activities = serializers.IntegerField()
    successful_activities = serializers.IntegerField()
    failed_activities = serializers.IntegerField()
    success_rate = serializers.FloatField()
    action_breakdown = serializers.ListField()
    level_breakdown = serializers.ListField()
    recent_activities = ActivityLogListSerializer(many=True, read_only=True)


class ActivityLogFilterSerializer(serializers.Serializer):
    """Serializer for filtering activity logs"""

    action = serializers.ChoiceField(choices=ActivityLogAction.choices, required=False, help_text="فیلتر بر اساس نوع عملیات")
    level = serializers.ChoiceField(choices=ActivityLogLevel.choices, required=False, help_text="فیلتر بر اساس سطح لاگ")
    is_successful = serializers.BooleanField(required=False, help_text="فیلتر بر اساس موفقیت عملیات")
    date_from = serializers.DateTimeField(required=False, help_text="از تاریخ (ISO 8601)")
    date_to = serializers.DateTimeField(required=False, help_text="تا تاریخ (ISO 8601)")
    search = serializers.CharField(required=False, help_text="جستجو در توضیحات و endpoint")


class UserActivitySummarySerializer(serializers.Serializer):
    """Serializer for user activity summary"""

    user_pid = serializers.CharField()
    total_activities = serializers.IntegerField()
    login_count = serializers.IntegerField()
    last_login = serializers.DateTimeField(allow_null=True)
    failed_activities_count = serializers.IntegerField()
    most_common_action = serializers.CharField()
    devices_used = serializers.IntegerField()
