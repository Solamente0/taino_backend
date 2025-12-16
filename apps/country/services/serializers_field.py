from rest_framework import serializers

from apps.country.models import Country, City, State
from base_utils.serializers.base import TainoBaseModelSerializer


class GlobalCountryReadOnlySerializer(TainoBaseModelSerializer):
    flag = serializers.FileField()

    class Meta:
        model = Country
        fields = ["pid", "name", "code", "flag", "dial_code"]
        read_only_fields = fields


class GlobalCountryMinimalReadOnlySerializer(TainoBaseModelSerializer):
    flag = serializers.FileField()

    class Meta:
        model = Country
        fields = ["pid", "name", "code"]
        read_only_fields = fields


class GlobalStateReadOnlySerializer(TainoBaseModelSerializer):

    class Meta:
        model = State
        fields = ["pid", "name", "pre_number"]
        read_only_fields = fields


class GlobalCityReadOnlySerializer(TainoBaseModelSerializer):
    class Meta:
        model = City
        fields = ["pid", "name"]
        read_only_fields = fields
