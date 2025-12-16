import logging

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.version.api.admin.filters import AppVersionAdminFilter
from apps.version.api.admin.serializers import (
    InputAdminVersionModelSerializer,
    OutputAdminVersionModelSerializer,
    InputAdminPIDListAppVersionModelSerializer,
)
from apps.version.models import AppVersion
from base_utils.views.admin import TainoAdminModelViewSet

log = logging.getLogger(__name__)
User = get_user_model()


class VersionModelViewSetAPI(TainoAdminModelViewSet):
    queryset = AppVersion.objects.all()
    filterset_class = AppVersionAdminFilter
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["os", "version_name", "build_number"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OutputAdminVersionModelSerializer
        return InputAdminVersionModelSerializer

    @extend_schema(request=InputAdminPIDListAppVersionModelSerializer, responses={200: {"message": "Done"}})
    @action(detail=False, methods=["patch"], url_path="bulk-expire", url_name="bulk-expire-api")
    def expire_versions(self, request, *args, **kwargs):
        input_serializer = InputAdminPIDListAppVersionModelSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        version_objs = input_serializer.validated_data.get("pid")
        version_objs.update(status="expired")

        return Response({"message": "Done"}, status=status.HTTP_200_OK)

    @extend_schema(request=InputAdminPIDListAppVersionModelSerializer)
    @action(detail=False, methods=["delete"], url_path="bulk-delete", url_name="bulk-delete-api")
    def delete_versions(self, request, *args, **kwargs):
        input_serializer = InputAdminPIDListAppVersionModelSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        version_objs = input_serializer.validated_data.get("pid")
        version_objs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
