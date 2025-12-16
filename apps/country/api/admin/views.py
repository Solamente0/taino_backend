from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from base_utils.views.admin import TainoAdminModelViewSet
from .filters import CityAdminFilter, CountryAdminFilter, StateAdminFilter
from .serializers import (
    CountryAdminListRetrieveSerializer,
    CountryAdminUpdateSerializer,
    CityListRetrieveAdminSerializer,
    StateListRetrieveAdminSerializer,
    CityUpdateAdminSerializer,
    StateCreateUpdateAdminSerializer,
)
from apps.country.models import Country, City, State


class CountryAdminViewSet(TainoAdminModelViewSet):
    queryset = Country.objects.all()

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["name", "code", "dial_code", "country__name"]
    ordering_fields = ["name", "is_sms_enabled"]
    ordering = ["-is_sms_enabled", "name"]
    filterset_class = CountryAdminFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CountryAdminListRetrieveSerializer
        return CountryAdminUpdateSerializer


class CityAdminViewSet(TainoAdminModelViewSet):
    queryset = City.objects.all()

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["^name", "^city__name"]
    ordering_fields = ["name"]
    filterset_class = CityAdminFilter
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CityListRetrieveAdminSerializer
        return CityUpdateAdminSerializer


class StateAdminViewSet(TainoAdminModelViewSet):
    queryset = State.objects.all()

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["^name", "^state__name"]
    ordering_fields = ["name"]
    filterset_class = StateAdminFilter
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return StateListRetrieveAdminSerializer
        return StateCreateUpdateAdminSerializer
