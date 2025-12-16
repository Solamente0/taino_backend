from rest_framework import serializers

from apps.permissions.models import Permission, PermissionCategory
from base_utils.serializers.base import TainoBaseModelSerializer


class PermissionCategorySerializer(TainoBaseModelSerializer):
    """
    Serializer for permission categories in mobile API
    """

    class Meta:
        model = PermissionCategory
        fields = ["pid", "name", "description"]
        read_only_fields = fields


class PermissionSerializer(TainoBaseModelSerializer):
    """
    Serializer for permissions in mobile API
    """

    category = PermissionCategorySerializer(read_only=True)

    class Meta:
        model = Permission
        fields = ["pid", "name", "description", "code_name", "category"]
        read_only_fields = fields


class UserPermissionStatusSerializer(TainoBaseModelSerializer):
    """
    Serializer for checking if a user has a specific permission
    """

    permission_code = serializers.CharField(required=True)
    has_permission = serializers.BooleanField(read_only=True)

    class Meta:
        model = Permission
        fields = ["permission_code", "has_permission"]


class RolePermissionsSerializer(serializers.Serializer):
    """
    Serializer for permissions based on user role
    """

    role = serializers.CharField(read_only=True)
    role_name = serializers.CharField(read_only=True)
    permissions = PermissionSerializer(many=True, read_only=True)
