import django_filters

from apps.permissions.models import Permission, PermissionCategory, UserPermission, UserTypePermission


class PermissionCategoryFilter(django_filters.FilterSet):
    """
    Filter for permission categories in admin API
    """

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = PermissionCategory
        fields = ["name"]


class PermissionFilter(django_filters.FilterSet):
    """
    Filter for permissions in admin API
    """

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    code_name = django_filters.CharFilter(field_name="code_name", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="category__pid")
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Permission
        fields = ["name", "code_name", "category", "is_active"]


class UserTypePermissionFilter(django_filters.FilterSet):
    """
    Filter for user type permissions in admin API
    """

    user_type = django_filters.CharFilter(field_name="user_type__pid")
    permission = django_filters.CharFilter(field_name="permission__pid")
    permission_name = django_filters.CharFilter(field_name="permission__name", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="permission__category__pid")

    class Meta:
        model = UserTypePermission
        fields = ["user_type", "permission", "permission_name", "category"]


class UserPermissionFilter(django_filters.FilterSet):
    """
    Filter for user permissions in admin API
    """

    user = django_filters.CharFilter(field_name="user__pid")
    permission = django_filters.CharFilter(field_name="permission__pid")
    permission_name = django_filters.CharFilter(field_name="permission__name", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="permission__category__pid")
    is_granted = django_filters.BooleanFilter(field_name="is_granted")

    class Meta:
        model = UserPermission
        fields = ["user", "permission", "permission_name", "category", "is_granted"]
