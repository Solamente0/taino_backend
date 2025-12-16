from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from apps.user.api.admin.serializers import AdminChangePasswordSerializer
from apps.user.api.admin.serializers import (
    AdminUserDetailSerializer,
    AdminUserListSerializer,
    AdminUserCreateUpdateModelSerializer,
    AdminOutputUserProfileModelSerializer,
)
from base_utils.views.admin import TainoAdminModelViewSet
from .filters import TainoUserFilter

User = get_user_model()


class AdminUserViewSet(TainoAdminModelViewSet):
    queryset = User.objects.all()

    filter_backends = (
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    )

    search_fields = [
        "first_name",
        "last_name",
        "vekalat_id",
        "phone_number",
        "email",
    ]
    ordering = ["-date_joined"]

    filterset_class = TainoUserFilter

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AdminUserDetailSerializer
        if self.action == "list":
            return AdminUserListSerializer
        return AdminUserCreateUpdateModelSerializer

    @extend_schema(request=AdminChangePasswordSerializer)
    @action(
        detail=True,
        url_path="change-password",
        methods=["patch"],
        name="change-password",
    )
    def change_password(self, request, *args, **kwargs):
        user_obj = self.get_object()
        serializer = AdminChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check old password
        if not user_obj.check_password(serializer.data.get("old_password")):
            return Response(
                {"old_password": [_("Wrong password.")]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_obj.set_password(serializer.data.get("new_password"))
        user_obj.save()
        return Response()

    @extend_schema(responses={200: AdminOutputUserProfileModelSerializer})
    @action(detail=False, methods=["GET"], url_path="profile", url_name="profile")
    def profile(self, request, *args, **kwargs):
        output = AdminOutputUserProfileModelSerializer(instance=request.user, context={"request": request})
        return Response(output.data, status=status.HTTP_200_OK)
