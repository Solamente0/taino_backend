from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from base_utils.views.admin import (
    TainoAdminCreateModelMixin,
    TainoAdminUpdateModelMixin,
    TainoAdminRetrieveModelMixin,
    TainoAdminGenericViewSet,
    TainoAdminListModelMixin,
)
from .filters import GeneralSettingFilter
from .serializers import (
    GeneralSettingAdminListRetrieveSerializer,
    GeneralSettingAdminCreateUpdateSerializer,
)
from ...models import GeneralSetting


class GeneralSettingAdminViewSet(
    TainoAdminCreateModelMixin,
    TainoAdminUpdateModelMixin,
    TainoAdminRetrieveModelMixin,
    TainoAdminListModelMixin,
    TainoAdminGenericViewSet,
):
    queryset = GeneralSetting.objects.all()

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = GeneralSettingFilter

    search_fields = ["key"]
    ordering_fields = ["key"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return GeneralSettingAdminListRetrieveSerializer
        return GeneralSettingAdminCreateUpdateSerializer

    @extend_schema(
        responses={200: GeneralSettingAdminListRetrieveSerializer},
    )
    @action(["PUT"], detail=False, url_path="bulk", url_name="bulk")
    def bulk(self, request, *kwargs):
        # Update settings in DB
        for key in request.data:
            GeneralSetting.objects.filter(key=key).update(value=request.data[key])

        # Invalidate cache for updated keys
        from apps.setting.services.query import GeneralSettingsQuery

        for key in request.data.keys():
            GeneralSettingsQuery._invalidate_cache(key)

        return Response(
            GeneralSettingAdminListRetrieveSerializer(
                GeneralSetting.objects.filter(key__in=request.data.keys()),
                many=True,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )
