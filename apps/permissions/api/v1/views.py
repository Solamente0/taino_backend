from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.permissions.api.v1.filters import PermissionCategoryFilter, PermissionFilter
from apps.permissions.api.v1.serializers import (
    PermissionCategorySerializer,
    PermissionSerializer,
    UserPermissionStatusSerializer,
    RolePermissionsSerializer,
)
from apps.permissions.models import Permission, PermissionCategory
from apps.permissions.services.permissions import PermissionService
from base_utils.permissions import HasTainoMobileUserPermission
from base_utils.views.mobile import TainoMobileGenericViewSet, TainoMobileListModelMixin


class PermissionCategoryViewSet(TainoMobileListModelMixin, TainoMobileGenericViewSet):
    """
    Mobile API for permission categories
    """

    queryset = PermissionCategory.objects.all()
    serializer_class = PermissionCategorySerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = PermissionCategoryFilter

    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]


class PermissionViewSet(TainoMobileListModelMixin, TainoMobileGenericViewSet):
    """
    Mobile API for permissions
    """

    queryset = Permission.objects.filter(is_active=True).select_related("category")
    serializer_class = PermissionSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = PermissionFilter

    search_fields = ["name", "code_name"]
    ordering_fields = ["name", "code_name", "category__name"]
    ordering = ["category__name", "name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return []
        return [IsAuthenticated(), HasTainoMobileUserPermission()]

    @extend_schema(request=UserPermissionStatusSerializer, responses={200: UserPermissionStatusSerializer})
    @action(["POST"], detail=False, url_path="check", url_name="check")
    def check_permission(self, request, *args, **kwargs):
        """
        Check if the current user has a specific permission
        """
        serializer = UserPermissionStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        permission_code = serializer.validated_data["permission_code"]
        has_permission = PermissionService.has_permission(request.user, permission_code)

        return Response({"permission_code": permission_code, "has_permission": has_permission}, status=status.HTTP_200_OK)

    @extend_schema(responses={200: PermissionSerializer(many=True)})
    @action(["GET"], detail=False, url_path="my-permissions", url_name="my_permissions")
    def my_permissions(self, request, *args, **kwargs):
        """
        Get all permissions assigned to the current user
        """
        permissions = PermissionService.get_user_permissions(request.user)

        return Response(
            PermissionSerializer(permissions, many=True, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(responses={200: RolePermissionsSerializer})
    @action(["GET"], detail=False, url_path="role-permissions", url_name="role_permissions")
    def role_permissions(self, request, *args, **kwargs):
        """
        Get all permissions assigned to the current user's role
        """
        user = request.user
        role = user.role

        if not role:
            return Response({"detail": "User has no assigned role"}, status=status.HTTP_404_NOT_FOUND)

        permissions = PermissionService.get_permissions_by_role(role.static_name)

        data = {
            "role": role.static_name,
            "role_name": role.name,
            "permissions": PermissionSerializer(permissions, many=True, context=self.get_serializer_context()).data,
        }

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: PermissionSerializer(many=True)})
    @action(["GET"], detail=False, url_path="by-category", url_name="by_category")
    def by_category(self, request, *args, **kwargs):
        """
        Get all permissions assigned to the current user, grouped by category
        """
        user = request.user
        permissions = PermissionService.get_user_permissions(user)

        # Group permissions by category
        permissions_by_category = {}
        for permission in permissions:
            category_name = permission.category.name
            if category_name not in permissions_by_category:
                permissions_by_category[category_name] = {
                    "category": PermissionCategorySerializer(permission.category).data,
                    "permissions": [],
                }
            permissions_by_category[category_name]["permissions"].append(
                PermissionSerializer(permission, context=self.get_serializer_context()).data
            )

        return Response(list(permissions_by_category.values()), status=status.HTTP_200_OK)
