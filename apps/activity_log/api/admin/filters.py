"""
apps/activity_log/api/admin/filters.py
Filters for ActivityLog API
"""

import django_filters
from apps.activity_log.api.v1.filters import ActivityLogFilter
from apps.activity_log.models import ActivityLog


class AdminActivityLogFilter(ActivityLogFilter):
    """Extended filter for admin with user filtering"""

    user_pid = django_filters.CharFilter(field_name="user__pid", lookup_expr="exact", label="شناسه کاربر")

    user_phone = django_filters.CharFilter(field_name="user__phone_number", lookup_expr="icontains", label="شماره تلفن")

    user_email = django_filters.CharFilter(field_name="user__email", lookup_expr="icontains", label="ایمیل")

    has_error = django_filters.BooleanFilter(method="filter_has_error", label="دارای خطا")

    class Meta:
        model = ActivityLog
        fields = ActivityLogFilter.Meta.fields + [
            "user_pid",
            "user_phone",
            "user_email",
            "has_error",
        ]

    def filter_has_error(self, queryset, name, value):
        """Filter logs that have error messages"""
        if value:
            return queryset.exclude(error_message="")
        return queryset.filter(error_message="")
