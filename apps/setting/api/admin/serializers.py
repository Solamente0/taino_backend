from rest_framework import serializers

from apps.setting.models import GeneralSetting
from base_utils.serializers.base import TainoBaseModelSerializer


class GeneralSettingAdminListRetrieveSerializer(TainoBaseModelSerializer):
    class Meta:
        model = GeneralSetting
        fields = [
            "pid",
            "key",
            "value",
            "is_active",
        ]
        read_only_fields = fields


class GeneralSettingAdminCreateUpdateSerializer(TainoBaseModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GeneralSetting
        fields = [
            "creator",
            "is_active",
            "key",
            "value",
            "is_active",
        ]

    def to_representation(self, instance):
        return GeneralSettingAdminListRetrieveSerializer(instance=instance, context=self.context).data
