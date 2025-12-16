from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from base_utils.views.admin import TainoAdminModelViewSet
from .serializers import SocialMediaTypeAdminCreateUpdateSerializer, SocialMediaTypeAdminListRetrieveSerializer
from ...models import SocialMediaType


class SocialMediaTypeAdminViewSet(TainoAdminModelViewSet):
    queryset = SocialMediaType.objects.all()

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = [
        "type",
    ]
    ordering_fields = [
        "type",
    ]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return SocialMediaTypeAdminListRetrieveSerializer
        return SocialMediaTypeAdminCreateUpdateSerializer
