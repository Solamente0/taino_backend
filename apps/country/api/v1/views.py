from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from base_utils.filters import IsActiveFilterBackend
from base_utils.views.mobile import TainoMobileReadOnlyModelViewSet
from .filters import CityFilter, CountryFilter, StateFilter
from .serializers import CityListRetrieveSerializer, StateListSerializer
from .serializers import CountryListRetrieveSerializer
from apps.country.services.query import CountryQuery, CityQuery, StateQuery


class CountryViewSet(TainoMobileReadOnlyModelViewSet):
    queryset = CountryQuery.get_visible_countries()
    serializer_class = CountryListRetrieveSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]  # mobiles use it with is_sms_enable filter before login screen for registration

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = CountryFilter
    search_fields = ["name", "code", "country__name"]
    ordering_fields = ["name", "code"]
    ordering = ["-is_sms_enabled", "name"]


class StateViewSet(TainoMobileReadOnlyModelViewSet):
    queryset = StateQuery.get_visible_states()
    serializer_class = StateListSerializer

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["^name", "^state__name"]
    ordering_fields = ["name"]
    filterset_class = StateFilter
    ordering = ["name"]


class CityViewSet(TainoMobileReadOnlyModelViewSet):
    queryset = CityQuery.get_visible_cities()
    serializer_class = CityListRetrieveSerializer

    filter_backends = [IsActiveFilterBackend, SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["^name", "^city__name"]
    ordering_fields = ["name"]
    filterset_class = CityFilter
    ordering = ["name"]
