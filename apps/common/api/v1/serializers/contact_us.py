# Add these to apps/common/api/v1/serializers.py
from apps.common.models import ContactUs
from base_utils.serializers.base import TainoBaseModelSerializer


class ContactUsSerializer(TainoBaseModelSerializer):
    class Meta:
        model = ContactUs
        fields = ["name", "email", "phone", "subject", "message"]
