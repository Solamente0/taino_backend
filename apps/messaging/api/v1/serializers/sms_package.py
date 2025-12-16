from apps.messaging.models import SMSPackage
from base_utils.serializers.base import TainoBaseModelSerializer


class SMSPackageSerializer(TainoBaseModelSerializer):
    """
    Serializer for SMS packages
    """

    class Meta:
        model = SMSPackage
        fields = ["pid", "value", "label", "coin_cost", "description"]
