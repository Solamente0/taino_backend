import django_filters

from apps.setting.models import GeneralSetting


class GeneralSettingFilter(django_filters.FilterSet):
    key = django_filters.CharFilter(field_name="key", lookup_expr="icontains")

    class Meta:
        model = GeneralSetting
        fields = ["key"]
