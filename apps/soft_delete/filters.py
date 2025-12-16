from django.contrib.admin import SimpleListFilter
from rest_framework.filters import BaseFilterBackend


class SoftDeleteFilterBackend(BaseFilterBackend):
    """Only filter objects not soft deleted!"""

    def filter_queryset(self, request, queryset, view):
        return queryset.filter(is_deleted=False, deleted_at__isnull=True)


class AdminSoftDeleteFilter(SimpleListFilter):
    title = "is deleted"
    parameter_name = "is_deleted"

    def lookups(self, request, model_admin):
        return (
            ("true", "Deleted Softly"),
            # ('false', 'Not Deleted'),
            # ('all', 'All'),
        )

    def queryset(self, request, queryset):
        value = {
            "true": False,
            "false": True,
            "all": "ALL",
        }[self.value() or "false"]
        # if value == 'ALL':
        #     return queryset

        return queryset.filter(deleted_at__isnull=value)
