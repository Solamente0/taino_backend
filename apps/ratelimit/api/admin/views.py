import logging

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.ratelimit.models import RateLimitConfig
from base_utils.views.admin import TainoAdminModelViewSet
from .serializers import (
    InputAdminRateLimitModelSerializer,
    OutputAdminRateLimitModelSerializer,
)

log = logging.getLogger(__name__)
User = get_user_model()

swagger_app_part = "RateLimit"


class RateLimitModelViewSetAPI(TainoAdminModelViewSet):
    queryset = RateLimitConfig.objects.all()

    serializer_class = OutputAdminRateLimitModelSerializer
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)

    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OutputAdminRateLimitModelSerializer
        return InputAdminRateLimitModelSerializer
