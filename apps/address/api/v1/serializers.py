from rest_framework import serializers

from apps.address.models import Address
from apps.country.services.query import CountryQuery, CityQuery, StateQuery
from apps.country.services.serializers_field import (
    GlobalCityReadOnlySerializer,
    GlobalCountryReadOnlySerializer,
    GlobalStateReadOnlySerializer,
)
from base_utils.serializers.base import TainoBaseModelSerializer


class OutputAddressListRetrieveSerializer(TainoBaseModelSerializer):
    country = GlobalCountryReadOnlySerializer()
    state = GlobalStateReadOnlySerializer()
    city = GlobalCityReadOnlySerializer()

    class Meta:
        model = Address
        fields = ("name", "description", "postal_code", "country", "state", "city")
        read_only_fields = fields


class InputAddressListRetrieveSerializer(TainoBaseModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    country = serializers.SlugRelatedField(
        queryset=CountryQuery.get_visible_countries(), slug_field="pid", required=False, default=None
    )
    state = serializers.SlugRelatedField(
        queryset=StateQuery.get_visible_states(), slug_field="pid", required=False, default=None
    )
    city = serializers.SlugRelatedField(
        queryset=CityQuery.get_visible_cities(), slug_field="pid", required=False, default=None
    )

    class Meta:
        model = Address
        fields = ("creator", "postal_code", "country", "state", "city")

    def to_representation(self, instance):
        return OutputAddressListRetrieveSerializer(instance, context=self.context).data
