from django_filters.rest_framework import filters
from rest_framework.filters import BaseFilterBackend

from base_utils.base_models import AdminStatusChoices


class IsActiveFilterBackend(BaseFilterBackend):
    "Works in conjunction with ActivableModel"

    def filter_queryset(self, request, queryset, view):
        return queryset.filter(is_active=True)


class AllowedAdminStatusFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        return queryset.filter(admin_status__in=AdminStatusChoices.get_allowed_status_for_clients())


class CreatorFilterBackend(BaseFilterBackend):
    """Only filter objects created by the current user"""

    def filter_queryset(self, request, queryset, view):
        return queryset.filter(creator=request.user)


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass
