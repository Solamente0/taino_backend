"""
apps/activity_log/admin.py
Django admin configuration for ActivityLog
"""

from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from apps.activity_log.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "id",
        "user_display",
        "action_display",
        "level_display",
        "is_successful_display",
        "ip_address",
        "endpoint",
        "created_at",
    ]

    list_filter = [
        "action",
        "level",
        "is_successful",
        "created_at",
    ]

    search_fields = [
        "user__phone_number",
        "user__email",
        "user__first_name",
        "user__last_name",
        "description",
        "ip_address",
        "endpoint",
    ]

    readonly_fields = [
        "user",
        "action",
        "level",
        "description",
        "content_type",
        "object_id",
        "ip_address",
        "user_agent",
        "endpoint",
        "method",
        "metadata_display",
        "device_id",
        "is_successful",
        "error_message",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("اطلاعات کاربر", {"fields": ("user", "device_id", "ip_address")}),
        ("جزئیات عملیات", {"fields": ("action", "level", "description", "is_successful", "error_message")}),
        ("شیء مرتبط", {"fields": ("content_type", "object_id"), "classes": ("collapse",)}),
        ("اطلاعات درخواست", {"fields": ("endpoint", "method", "user_agent"), "classes": ("collapse",)}),
        ("داده‌های اضافی", {"fields": ("metadata_display",), "classes": ("collapse",)}),
        ("تاریخ‌ها", {"fields": ("created_at", "updated_at")}),
    )

    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        """Disable adding logs through admin"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing logs through admin"""
        return False

    def user_display(self, obj):
        """Display user with link"""
        if obj.user:
            return format_html('<a href="/admin/authentication/tainouser/{}/change/">{}</a>', obj.user.pk, obj.user)
        return "ناشناس"

    user_display.short_description = "کاربر"

    def action_display(self, obj):
        """Display action with color"""
        colors = {
            "login": "#28a745",
            "logout": "#6c757d",
            "create": "#007bff",
            "update": "#ffc107",
            "delete": "#dc3545",
            "error": "#dc3545",
        }
        color = colors.get(obj.action, "#6c757d")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_action_display())

    action_display.short_description = "عملیات"

    def level_display(self, obj):
        """Display level with badge"""
        badges = {
            "debug": "secondary",
            "info": "info",
            "warning": "warning",
            "error": "danger",
            "critical": "danger",
        }
        badge = badges.get(obj.level, "secondary")
        return format_html('<span class="badge badge-{}">{}</span>', badge, obj.get_level_display())

    level_display.short_description = "سطح"

    def is_successful_display(self, obj):
        """Display success status with icon"""
        if obj.is_successful:
            return format_html('<span style="color: green;">✓ موفق</span>')
        else:
            return format_html('<span style="color: red;">✗ ناموفق</span>')

    is_successful_display.short_description = "وضعیت"

    def metadata_display(self, obj):
        """Display metadata in formatted JSON"""
        import json

        if obj.metadata:
            formatted = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
            return format_html("<pre>{}</pre>", formatted)
        return "-"

    metadata_display.short_description = "داده‌های اضافی"

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related("user", "content_type")
