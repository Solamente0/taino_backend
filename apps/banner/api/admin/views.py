from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.banner.api.admin.serializers import (
    BannerAdminListSerializer,
    BannerAdminCreateUpdateSerializer,
)
from apps.banner.models import Banner
from base_utils.views.admin import TainoAdminModelViewSet


class BannerAdminViewSet(TainoAdminModelViewSet):
    queryset = Banner.objects.all()

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["header_text", "footer_text", "link"]
    ordering_fields = ["created_at", "updated_at"]
    filterset_fields = ["header_text", "footer_text", "link"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return BannerAdminListSerializer
        return BannerAdminCreateUpdateSerializer
