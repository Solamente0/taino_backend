import django_filters

from apps.version.models import AppVersion
from base_utils.base_models import AdminStatusChoices


class AppVersionAdminFilter(django_filters.FilterSet):
    os = django_filters.ChoiceFilter(choices=AppVersion.OSTypes.choices, lookup_expr="exact")
    update_status = django_filters.ChoiceFilter(choices=AppVersion.UpdateStatus.choices, lookup_expr="exact")
    admin_status = django_filters.ChoiceFilter(choices=AdminStatusChoices.choices, lookup_expr="exact")
    updated_at = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = AppVersion
        fields = [
            "os",
            "update_status",
            "admin_status",
            "updated_at",
        ]
