from apps.setting.models import GeneralSetting
from base_utils.serializers.base import TainoBaseModelSerializer


class GeneralSettingMobileSerializer(TainoBaseModelSerializer):
    class Meta:
        model = GeneralSetting
        fields = ["key", "value"]
        read_only_fields = fields
