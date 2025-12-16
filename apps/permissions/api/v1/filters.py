import django_filters

from apps.permissions.models import Permission, PermissionCategory


class PermissionCategoryFilter(django_filters.FilterSet):
    """
    Filter for permission categories in mobile API
    """

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = PermissionCategory
        fields = ["name"]


class PermissionFilter(django_filters.FilterSet):
    """
    Filter for permissions in mobile API
    """

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    code_name = django_filters.CharFilter(field_name="code_name", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="category__pid")

    class Meta:
        model = Permission
        fields = ["name", "code_name", "category"]
