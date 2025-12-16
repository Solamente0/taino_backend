from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from apps.permissions.api.admin.filters import (
    PermissionCategoryFilter,
    PermissionFilter,
    UserTypePermissionFilter,
    UserPermissionFilter,
)
from apps.permissions.api.admin.serializers import (
    PermissionCategoryAdminSerializer,
    PermissionAdminSerializer,
    UserTypePermissionAdminSerializer,
    UserPermissionAdminSerializer,
    BulkAssignPermissionsSerializer,
    BulkAssignUserPermissionsSerializer,
)
from apps.permissions.models import Permission, PermissionCategory, UserPermission, UserTypePermission
from apps.permissions.services.permissions import PermissionService
from base_utils.views.admin import TainoAdminModelViewSet


User = get_user_model()


class PermissionCategoryAdminViewSet(TainoAdminModelViewSet):
    """
    Admin API for permission categories
    """

    queryset = PermissionCategory.objects.all()
    serializer_class = PermissionCategoryAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = PermissionCategoryFilter

    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class PermissionAdminViewSet(TainoAdminModelViewSet):
    """
    Admin API for permissions
    """

    queryset = Permission.objects.all().select_related("category")

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = PermissionFilter

    search_fields = ["name", "description", "code_name", "category__name"]
    ordering_fields = ["name", "code_name", "category__name", "created_at"]
    ordering = ["category__name", "name"]

    def get_serializer_class(self):
        return PermissionAdminSerializer


class UserTypePermissionAdminViewSet(TainoAdminModelViewSet):
    """
    Admin API for user type permissions
    """

    queryset = UserTypePermission.objects.all().select_related("user_type", "permission", "permission__category")
    serializer_class = UserTypePermissionAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = UserTypePermissionFilter

    search_fields = ["user_type__name", "permission__name", "permission__code_name"]
    ordering_fields = ["user_type__name", "permission__name", "created_at"]
    ordering = ["user_type__name", "permission__category__name", "permission__name"]

    @extend_schema(request=BulkAssignPermissionsSerializer, responses={200: UserTypePermissionAdminSerializer(many=True)})
    @action(["POST"], detail=False, url_path="bulk-assign", url_name="bulk_assign")
    def bulk_assign(self, request, *args, **kwargs):
        """
        Bulk assign permissions to a user type
        """
        serializer = BulkAssignPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_type_id = serializer.validated_data["user_type_id"]
        permission_ids = serializer.validated_data["permission_ids"]

        from apps.authentication.models import UserType

        try:
            user_type = UserType.objects.get(pid=user_type_id)
            permissions = Permission.objects.filter(pid__in=permission_ids)

            created_permissions = []
            for permission in permissions:
                user_type_permission, created = UserTypePermission.objects.get_or_create(
                    user_type=user_type, permission=permission
                )
                created_permissions.append(user_type_permission)

            return Response(
                UserTypePermissionAdminSerializer(created_permissions, many=True, context=self.get_serializer_context()).data,
                status=status.HTTP_200_OK,
            )
        except Group.DoesNotExist:
            return Response({"error": "User type not found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={204: None})
    @action(["DELETE"], detail=False, url_path="bulk-remove", url_name="bulk_remove")
    def bulk_remove(self, request, *args, **kwargs):
        """
        Bulk remove permissions from a user type
        """
        user_type_id = request.query_params.get("user_type_id")
        permission_ids = request.query_params.getlist("permission_ids")

        if not user_type_id or not permission_ids:
            return Response({"error": "user_type_id and permission_ids are required"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.authentication.models import UserType

        try:
            user_type = UserType.objects.get(pid=user_type_id)
            permissions = Permission.objects.filter(pid__in=permission_ids)

            UserTypePermission.objects.filter(user_type=user_type, permission__in=permissions).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Group.DoesNotExist:
            return Response({"error": "User type not found"}, status=status.HTTP_404_NOT_FOUND)


class UserPermissionAdminViewSet(TainoAdminModelViewSet):
    """
    Admin API for user permissions
    """

    queryset = UserPermission.objects.all().select_related("user", "permission", "permission__category")
    serializer_class = UserPermissionAdminSerializer

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = UserPermissionFilter

    search_fields = ["user__first_name", "user__last_name", "permission__name", "permission__code_name"]
    ordering_fields = ["user__first_name", "user__last_name", "permission__name", "created_at"]
    ordering = ["user__first_name", "user__last_name", "permission__category__name", "permission__name"]

    @extend_schema(request=BulkAssignUserPermissionsSerializer, responses={200: UserPermissionAdminSerializer(many=True)})
    @action(["POST"], detail=False, url_path="bulk-assign", url_name="bulk_assign")
    def bulk_assign(self, request, *args, **kwargs):
        """
        Bulk assign permissions to a user
        """
        serializer = BulkAssignUserPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]
        permission_ids = serializer.validated_data["permission_ids"]
        is_granted = serializer.validated_data["is_granted"]

        try:
            user = User.objects.get(pid=user_id)
            permissions = Permission.objects.filter(pid__in=permission_ids)

            created_permissions = []
            for permission in permissions:
                user_permission, created = UserPermission.objects.update_or_create(
                    user=user, permission=permission, defaults={"is_granted": is_granted}
                )
                created_permissions.append(user_permission)

            return Response(
                UserPermissionAdminSerializer(created_permissions, many=True, context=self.get_serializer_context()).data,
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={204: None})
    @action(["DELETE"], detail=False, url_path="bulk-remove", url_name="bulk_remove")
    def bulk_remove(self, request, *args, **kwargs):
        """
        Bulk remove permissions from a user
        """
        user_id = request.query_params.get("user_id")
        permission_ids = request.query_params.getlist("permission_ids")

        if not user_id or not permission_ids:
            return Response({"error": "user_id and permission_ids are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pid=user_id)
            permissions = Permission.objects.filter(pid__in=permission_ids)

            UserPermission.objects.filter(user=user, permission__in=permissions).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
