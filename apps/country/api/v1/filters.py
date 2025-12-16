import django_filters

from apps.country.models import City, Country, State


class CityFilter(django_filters.FilterSet):
    country_code = django_filters.CharFilter(field_name="country__code", lookup_expr="iexact")
    country_pid = django_filters.CharFilter(field_name="country_pid", lookup_expr="exact")
    state_name = django_filters.CharFilter(field_name="state__name", lookup_expr="icontains")
    state_pid = django_filters.CharFilter(field_name="state_pid", lookup_expr="exact")

    class Meta:
        model = City
        fields = ["country_code", "country_pid", "state_name", "state_pid"]


class StateFilter(django_filters.FilterSet):
    country_code = django_filters.CharFilter(field_name="country__code", lookup_expr="exact")
    country_pid = django_filters.CharFilter(field_name="country_pid", lookup_expr="exact")

    class Meta:
        model = State
        fields = ["country_code", "country_pid"]


class CountryFilter(django_filters.FilterSet):
    is_sms_enabled = django_filters.BooleanFilter(field_name="is_sms_enabled", lookup_expr="exact")

    class Meta:
        model = Country
        fields = ["is_sms_enabled"]
