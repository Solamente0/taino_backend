import django_filters
from django.contrib.auth import get_user_model
from rest_framework.filters import BaseFilterBackend

User = get_user_model()


class UserFilterBacked(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(id=request.user.id)


class TainoUserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ("id", "email", "phone_number", "vekalat_id")
