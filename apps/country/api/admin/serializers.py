from rest_framework import serializers

from apps.country.models import Country, City, State
from base_utils.serializers.base import TainoBaseModelSerializer


class CountryAdminListRetrieveSerializer(TainoBaseModelSerializer):
    flag = serializers.FileField()

    class Meta:
        model = Country
        fields = ["pid", "name", "code", "flag", "dial_code", "is_sms_enabled"]
        read_only_fields = fields


class CountryAdminUpdateSerializer(TainoBaseModelSerializer):

    class Meta:
        model = Country
        fields = ["is_sms_enabled"]

    def to_representation(self, instance):
        return CountryAdminListRetrieveSerializer(instance=instance, context=self.context).data


class StateListRetrieveAdminSerializer(TainoBaseModelSerializer):
    country = CountryAdminListRetrieveSerializer()

    class Meta:
        model = State
        fields = ["pid", "name", "country"]
        read_only_fields = fields


class StateCityRetrieveAdminSerializer(TainoBaseModelSerializer):

    class Meta:
        model = State
        fields = [
            "pid",
            "name",
        ]
        read_only_fields = fields


class StateCreateUpdateAdminSerializer(TainoBaseModelSerializer):
    country = serializers.SlugRelatedField(queryset=Country.objects.all(), slug_field="pid")

    class Meta:
        model = State
        fields = ["pid", "name", "country"]
        read_only_fields = fields


class CityListRetrieveAdminSerializer(TainoBaseModelSerializer):
    country = CountryAdminListRetrieveSerializer()
    state = StateCityRetrieveAdminSerializer()

    class Meta:
        model = City
        fields = ["pid", "name", "country", "state"]
        read_only_fields = fields


class CityUpdateAdminSerializer(TainoBaseModelSerializer):
    country = serializers.SlugRelatedField(queryset=Country.objects.all(), slug_field="pid", required=False)
    state = serializers.SlugRelatedField(queryset=State.objects.all(), slug_field="pid", required=False)

    class Meta:
        model = City
        fields = ["pid", "name", "state", "country"]
        read_only_fields = fields
