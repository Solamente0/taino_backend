from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.permissions.models import Permission, PermissionCategory, UserPermission, UserTypePermission

from base_utils.serializers.base import TainoBaseModelSerializer


User = get_user_model()


class PermissionCategoryAdminSerializer(TainoBaseModelSerializer):
    """
    Serializer for permission categories in admin API
    """

    class Meta:
        model = PermissionCategory
        fields = [
            "pid",
            "name",
            "description",
        ]


class PermissionAdminSerializer(TainoBaseModelSerializer):
    """
    Serializer for permissions in admin API
    """

    category = PermissionCategoryAdminSerializer(read_only=True)
    category_id = serializers.SlugRelatedField(
        queryset=PermissionCategory.objects.all(), slug_field="pid", source="category", write_only=True
    )

    class Meta:
        model = Permission
        fields = ["pid", "name", "description", "code_name", "category", "category_id", "is_active"]


class UserTypePermissionAdminSerializer(TainoBaseModelSerializer):
    """
    Serializer for user type permissions in admin API
    """

    permission = PermissionAdminSerializer(read_only=True)
    permission_id = serializers.SlugRelatedField(
        queryset=Permission.objects.all(), slug_field="pid", source="permission", write_only=True
    )

    user_type_name = serializers.CharField(source="user_type.name", read_only=True)

    class Meta:
        model = UserTypePermission
        fields = ["pid", "user_type", "user_type_name", "permission", "permission_id"]
        read_only_fields = ["pid"]


class UserPermissionAdminSerializer(TainoBaseModelSerializer):
    """
    Serializer for user permissions in admin API
    """

    permission = PermissionAdminSerializer(read_only=True)
    permission_id = serializers.SlugRelatedField(
        queryset=Permission.objects.all(), slug_field="pid", source="permission", write_only=True
    )

    username = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = UserPermission
        fields = ["pid", "user", "username", "permission", "permission_id", "is_granted"]
        read_only_fields = ["pid"]


class BulkAssignPermissionsSerializer(TainoBaseModelSerializer):
    """
    Serializer for bulk assigning permissions to a user type
    """

    user_type_id = serializers.CharField(required=True)
    permission_ids = serializers.ListField(child=serializers.CharField(), required=True)

    class Meta:
        model = UserTypePermission
        fields = ["user_type_id", "permission_ids"]


class BulkAssignUserPermissionsSerializer(TainoBaseModelSerializer):
    """
    Serializer for bulk assigning permissions to a user
    """

    user_id = serializers.CharField(required=True)
    permission_ids = serializers.ListField(child=serializers.CharField(), required=True)
    is_granted = serializers.BooleanField(default=True)

    class Meta:
        model = UserPermission
        fields = ["user_id", "permission_ids", "is_granted"]
