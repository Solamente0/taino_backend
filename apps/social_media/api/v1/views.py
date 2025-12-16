from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from base_utils.filters import IsActiveFilterBackend
from base_utils.views.mobile import TainoMobileReadOnlyModelViewSet
from .serializers import SocialMediaTypeListSerializer
from ...services.query import SocialMediaTypeQuery


class SocialMediaTypeViewSet(TainoMobileReadOnlyModelViewSet):
    queryset = SocialMediaTypeQuery.get_visible_medias()
    serializer_class = SocialMediaTypeListSerializer

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = [
        "type",
    ]
    ordering_fields = [
        "type",
    ]
    ordering = ["-created_at"]
