import logging

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.version.api.v1.serializers import (
    InputAppVersionSerializer,
    OutputAppVersionModelSerializer,
    OutputAppVersionStatusModelSerializer,
    VersionStatusCheckSerializer,
)
from apps.version.models import AppVersion

log = logging.getLogger(__name__)


class AppVersionsGenericViewSetAPI(GenericViewSet):
    permission_classes = ()
    authentication_classes = ()

    serializer_class = OutputAppVersionModelSerializer

    def get_queryset(self):
        os = self.request.query_params.get("os", None)
        if os is None:
            raise ValidationError(_("os is required"))
        return AppVersion.objects.filter(os=os)

    @extend_schema(
        parameters=[InputAppVersionSerializer],
        responses={200: OutputAppVersionStatusModelSerializer},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="status",
        url_name="status",
        permission_classes=[],
        authentication_classes=[],
    )
    def version_status(self, request, *args, **kwargs):
        output = VersionStatusCheckSerializer(context=self.get_serializer_context())
        return Response(data=output.data, status=status.HTTP_200_OK)
