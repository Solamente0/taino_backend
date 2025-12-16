"""
apps/activity_log/api/v1/filters.py
Filters for ActivityLog API
"""

import django_filters
from django.db.models import Q

from apps.activity_log.models import ActivityLog, ActivityLogAction, ActivityLogLevel


class ActivityLogFilter(django_filters.FilterSet):
    """Filter for activity logs"""

    action = django_filters.ChoiceFilter(field_name="action", choices=ActivityLogAction.choices, label="نوع عملیات")

    level = django_filters.ChoiceFilter(field_name="level", choices=ActivityLogLevel.choices, label="سطح لاگ")

    is_successful = django_filters.BooleanFilter(field_name="is_successful", label="موفقیت‌آمیز")

    date_from = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte", label="از تاریخ")

    date_to = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte", label="تا تاریخ")

    search = django_filters.CharFilter(method="filter_search", label="جستجو")

    ip_address = django_filters.CharFilter(field_name="ip_address", lookup_expr="icontains", label="آدرس IP")

    endpoint = django_filters.CharFilter(field_name="endpoint", lookup_expr="icontains", label="مسیر API")

    device_id = django_filters.CharFilter(field_name="device_id", lookup_expr="exact", label="شناسه دستگاه")

    class Meta:
        model = ActivityLog
        fields = [
            "action",
            "level",
            "is_successful",
            "date_from",
            "date_to",
            "search",
            "ip_address",
            "endpoint",
            "device_id",
        ]

    def filter_search(self, queryset, name, value):
        """Search in description, endpoint, and error_message"""
        return queryset.filter(
            Q(description__icontains=value) | Q(endpoint__icontains=value) | Q(error_message__icontains=value)
        )
