from rest_framework import serializers

from apps.country.models import Country, City, State
from base_utils.serializers.base import TainoBaseModelSerializer


class CountryListRetrieveSerializer(TainoBaseModelSerializer):
    flag = serializers.FileField()

    class Meta:
        model = Country
        fields = ["pid", "name", "code", "flag", "dial_code"]
        read_only_fields = fields


class StateListSerializer(TainoBaseModelSerializer):
    country = CountryListRetrieveSerializer()

    class Meta:
        model = State
        fields = ["pid", "country", "name"]
        read_only_fields = fields


class StateCityRetrieveSerializer(TainoBaseModelSerializer):

    class Meta:
        model = State
        fields = ["pid", "name"]
        read_only_fields = fields


class CityListRetrieveSerializer(TainoBaseModelSerializer):
    state = StateCityRetrieveSerializer()
    country = CountryListRetrieveSerializer()

    class Meta:
        model = City
        fields = ["pid", "state", "country", "name"]
        read_only_fields = fields
