from django.db.models import QuerySet

from apps.country.models import Country, City, State
from base_utils.services import AbstractBaseQuery


class CountryQuery(AbstractBaseQuery):

    @staticmethod
    def get_visible_countries(base_queryset: QuerySet[Country] = None) -> QuerySet[Country]:
        if not base_queryset:
            base_queryset = Country.objects.all()

        return base_queryset.filter(is_active=True)

    @staticmethod
    def get_countries_with_enabled_sms_panel(base_queryset: QuerySet[Country] = None) -> QuerySet[Country]:
        if not base_queryset:
            base_queryset = CountryQuery.get_visible_countries()

        return base_queryset.filter(is_sms_enabled=True)

    @staticmethod
    def all() -> QuerySet[Country]:
        return Country.objects.all()


class CityQuery(AbstractBaseQuery):

    @staticmethod
    def get_visible_cities(base_queryset: QuerySet[City] = None) -> QuerySet[City]:
        if not base_queryset:
            base_queryset = City.objects.all()

        return base_queryset.filter(is_active=True)

    @staticmethod
    def all() -> QuerySet[City]:
        return City.objects.all()


class StateQuery(AbstractBaseQuery):

    @staticmethod
    def get_visible_states(base_queryset: QuerySet[State] = None) -> QuerySet[State]:
        if not base_queryset:
            base_queryset = State.objects.all()

        return base_queryset.filter(is_active=True)

    @staticmethod
    def all() -> QuerySet[State]:
        return State.objects.all()
